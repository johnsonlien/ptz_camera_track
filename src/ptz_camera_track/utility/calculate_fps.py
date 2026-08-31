import time
import cv2
  
class FPSCalculator:
    def __init__(self, alpha : float = 0.1):
        self.alpha = 0.1
        self.prev_time = 0
        self.smoothed_fps = 0

    def calculate_fps(self, frame) -> None:
        cur_time = time.time()
        time_diff = cur_time - self.prev_time

        if time_diff > 0:
            raw_fps = 1 / time_diff
        else:
            raw_fps = 0

        self.prev_time = cur_time

        self.smoothed_fps = (self.alpha * raw_fps) + ( (1.0 - self.alpha) * self.smoothed_fps)

        cv2.putText(
            frame,
            f"FPS: {self.smoothed_fps:.1f}",
            (10, 40), # Top left corner
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),    # Green
            2, 
            cv2.LINE_AA
        )
