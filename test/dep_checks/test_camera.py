#!/usr/bin/env python3 

import cv2 
import sys

camera_index = 0
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("Could not open camera")
    sys.exit()    


while True:
    ret, frame = cap.read() 

    if not ret:
        print("Error could not grab frame.")
        break

    cv2.imshow("USB Webcam feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release(0)
cv2.destroyAllWindows()
