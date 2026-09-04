import time
import cv2
  
class FPSCalculator:
    def __init__(self, alpha : float = 0.1):
        self.alpha = alpha
        self.prev_time = None
        self.smoothed_time_diff = 0

    def calculate_fps(self, frame) -> None:
        cur_time = time.time()

        if self.prev_time is not None:
            time_diff = cur_time - self.prev_time
            self.smoothed_time_diff = (
                (self.alpha * time_diff) + ((1.0 - self.alpha) * self.smoothed_time_diff)
            )

        self.prev_time = cur_time

        smoothed_fps = 1 / self.smoothed_time_diff if self.smoothed_time_diff > 0 else 0

        cv2.putText(
            frame,
            f"FPS: {smoothed_fps:.1f}",
            (10, 40), # Top left corner
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),    # Green
            2, 
            cv2.LINE_AA
        )
