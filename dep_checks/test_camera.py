#!/usr/bin/env python3 

import cv2 
import sys
import time

camera_index = 0
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("Could not open camera")
    sys.exit()    

prev_time = 0
new_time = 0

# For FPS Calculations
fps_smoothed = 0
alpha = 0.1

while True:
    ret, frame = cap.read() 
    
    cur_time = time.time()
    time_diff = cur_time - prev_time
    prev_time = cur_time 

    if time_diff > 0:
        current_fps = 1 / time_diff
    else:
        current_fps = 0

    # Smooth FPS
    fps_smoothed = (alpha * current_fps) + ((1.0 - alpha) * fps_smoothed)

    cv2.putText(
        frame,
        f"FPS: {int(fps_smoothed)}",
        (10, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )
    if not ret:
        print("Error could not grab frame.")
        break

    cv2.imshow("USB Webcam feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release(0)
cv2.destroyAllWindows()
