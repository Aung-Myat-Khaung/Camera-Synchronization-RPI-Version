import cv2
import queue
import threading
import numpy as np

from camera.camera_setting import Frame_Grabber
from config.config import FRAME_SIZE, COLORS, MAX_MISSES, MIN_AREA, WIDTH, HEIGHT, MAX_TRACKERS,available_ID
from config.ip_list import IP_ADDR
from filter.hsv_filter import find_blob
from filter.canny_hough import detect_circle
from filter.Hungarian import assign
from filter.tracker import Kalman_tracker
from connection.client import Client_Com
from connection.server import Sever_Com



def _check_mask_area(x, y, r, contour):
    circle_mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    cv2.circle(circle_mask, (x, y), r, 255, -1)

    contour_mask = np.zeros_like(circle_mask)
    cv2.drawContours(contour_mask, [contour], -1, 255, -1)

    overlap = cv2.bitwise_and(circle_mask, contour_mask)
    return cv2.countNonZero(overlap) / cv2.countNonZero(circle_mask)


def canny_hough(frame, circle_queue):

    circle_queue.put(detect_circle(frame))


def hsv_mask(frame, hsv_queue):

    hsv_queue.put(find_blob(frame, [(COLORS['green']['lower'], COLORS['green']['higher'])]))


def fuse_detections(hsv_queue, circle_queue):

    hsv_frame = hsv_queue.get()
    circles = circle_queue.get()

    contours, _ = cv2.findContours(hsv_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    used_circ = set()
    bboxes = []

    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area > 4500:
            for i, (x, y, r) in enumerate(circles):
                if i in used_circ:
                    continue
                if cv2.pointPolygonTest(cnt, (x, y), False) >= 0 and _check_mask_area(x, y, r, cnt) > 0.75:
                    used_circ.add(i)
                    bboxes.append((x - r, y - r, 2 * r, 2 * r))
        elif area > MIN_AREA:
            bboxes.append(cv2.boundingRect(cnt))

    return bboxes


stream = Frame_Grabber()
stream.start()
threading.Thread(target=Sever_Com,daemon=True).start()
sc_width, sc_height, fps = stream.dimensions()

trackers = []                         
tracker_id = 0
client = Client_Com(host=IP_ADDR["Main"]["addr"],port =IP_ADDR["Main"]["port"])
client.send_camera_data(7,"green")

hsv_queue = queue.Queue(maxsize=1)
circle_queue = queue.Queue(maxsize=1)

while True:
    frame = stream.read_data()
    if frame is None or frame.size == 0:
        continue
    t1 = threading.Thread(target=hsv_mask, args=(frame, hsv_queue))
    t2 = threading.Thread(target=canny_hough, args=(frame, circle_queue))
    t1.start(); t2.start(); t1.join(); t2.join()
    detections = fuse_detections(hsv_queue, circle_queue)
    mt, un_t, un_d = assign(trackers, detections)

    for r, c in mt:
        trackers[r].update_loss(frame, detections[c])
        trackers[r].misses = 0

    for r in un_t:
        trackers[r].misses += 1

    for c in un_d:
        x, y, w, h = detections[c]

        if w < 10 or h < 10:
            continue

        if x < FRAME_SIZE[0]*0.1 or x + w > FRAME_SIZE[0]*0.9 or y < FRAME_SIZE[1]*0.1 or y + h > FRAME_SIZE[1]*0.9:
            continue
        if available_ID:
            new_id, items = available_ID.popitem()
        else:
            tracker_id +=1
            new_id = tracker_id
        trackers.append(Kalman_tracker(new_id, detections[c], frame))


    alive_trackers = []
    for t in trackers:
        if t.misses < MAX_MISSES:
            alive_trackers.append(t)
        else:
            available_ID[t.id] = {
                    "id": t.id,
                    "color": "green"
                }
            x,y = (t.get_last_position())
            if x <sc_width*0.15:
                client = Client_Com(host=IP_ADDR["Main"]["addr"],port =IP_ADDR["Main"]["port"])
                client.send_camera_data(t.id,"green")
            if x>sc_width*0.85:
                client = Client_Com(host=IP_ADDR["Main"]["addr"],port =IP_ADDR["Main"]["port"])
                client.send_camera_data(t.id,"green")
 
    trackers = alive_trackers

    for t in trackers:
        (cx, cy), ok = t.update(frame)
        x, y, w, h = t.bbox
        colour = (0, 255, 0) if ok else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), colour, 2)
        cv2.putText(frame, f"ID {t.id}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1)
    cv2.imshow("Multi-Ball Tracker", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

stream.stop()
cv2.destroyAllWindows()