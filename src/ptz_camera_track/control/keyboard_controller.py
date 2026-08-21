import cv2

class KeyboardController:
    ARROW_MAP = {
        # Raspberry Pi Arrow Key Mapping
        81: (-1, 0),    # left
        82: (0, -1),    # up
        83: (1, 0),     # right
        84: (0, 1),     # down
        
        # WSL Arrow key mapping
        65361: (-1, 0),
        65362: (0, -1),
        65363: (1, 0),
        65364: (0, 1),
    }

    def __init__(self, servo_controller, tracking_loop, step_degrees=3):
        self.servo_controller = servo_controller
        self.tracking_loop = tracking_loop
        self.step_degrees = step_degrees

    def handle_key(self, key):
        if key == -1:
            return True

        if key in self.ARROW_MAP:
            
            if not self.tracking_loop.tracking_enabled:
                pan_dir, tilt_dir = self.ARROW_MAP[key]

                self.servo_controller.nudge(
                    pan_dir * self.step_degrees,
                    tilt_dir * self.step_degrees
                )
            return True

        key_char = chr(key & 0xFF) if 0 <= key < 256 else ""
        if key_char == "t":
            # Toggle tracking
            self.tracking_loop.zoom_enabled = not self.tracking_loop.zoom_enabled
            print(f"Toggled tracking to {self.tracking_loop.zoom_enabled}")

        elif key_char == "h":
            print("Reseting servos to starting angle")
            self.servo_controller.reset_angle()
        
        elif key_char == "q":
            return False
        return True
