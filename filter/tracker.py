import cv2
import numpy as np
from .Kalman import Kalman_filter

class Kalman_tracker:
    def __init__(self, id, bbox,frame):
        self.id = id
        self.tracker = cv2.TrackerKCF_create()
        self.bbox = bbox
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        self.tracker.init(frame,self.bbox)
        x,y,w,h = self.bbox
        self.kf = Kalman_filter(x+w/2,y+h/2)
        self.misses = 0

    def predict_center(self):
        return self.kf.predict()
    
    def update_loss(self,frame,box):
        self.tracker = cv2.TrackerKCF_create()
        x,y,w,h = box
        self.bbox = (x,y,w,h)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        self.tracker.init(frame,self.bbox)
        self.misses = 0
    
    def update(self,frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        ok, bbox = self.tracker.update(frame)
        if ok:
            x,y,w,h = bbox
            self.center_x,self.center_y = x+w/2,y+h/2
            self.kf.correct(self.center_x,self.center_y)
            self.misses = 0
            return (int(self.center_x),int(self.center_y)),ok
        else:
            self.misses+=1
            predict_x,predict_y = self.kf.predict()
            return (int(predict_x),int(predict_y)),ok

    def get_last_position(self):
        return (self.center_x,self.center_y)