import cv2
import threading
import time
from picamera2 import Picamera2
class Frame_Grabber():
    def __init__(self,src = 0):
        self.cam = Picamera2()
        self.config = self.cam.create_video_configuration(main={"size": (640, 480)})
        self.cam.configure(self.config)
        self.frame = None
        self.lock = threading.Lock()
        self.stopped = False
    
    def start(self):
        self.cam.start
        threading.Thread(target=self.update, daemon=True).start()
    
    def update(self):
        while not self.stopped:
            ret, f = self.cam.capture_array()
            if not ret:
                break
            with self.lock:
                self.frame = f.copy()
            time.sleep(0)
        
    def dimensions(self):
        size = self.config["main"]["size"]
        fps = 30  # approximate, Picamera2 doesn't give exact
        return size[0], size[1], fps
    
    def read_data(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.stopped = True
        self.cam.close()