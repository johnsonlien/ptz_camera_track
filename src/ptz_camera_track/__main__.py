from ptz_camera_track.cli.parse import get_cli_parser

from ptz_camera_track.camera.camera_controller import CameraController
from ptz_camera_track.camera.zoom import ZoomStrategy

from ptz_camera_track.control.keyboard_controller import KeyboardServoController
from ptz_camera_track.control.target_selector import TargetSelector

from ptz_camera_track.servo.thread_safe_servo_controller import TSServoController, ServoConfig

from ptz_camera_track.tracker.tracker import Tracker

from ptz_camera_track.utility.calculate_fps import FPSCalculator

from enum import Enum
import cv2
import logging
import time

# kp_pan and kp_tilt are used to adjust how much the servos will move
# when needing to move. This should by dynamically calculated based on
# object we are tracking
# i.e humans don't jerk in movement as quickly as fish so we can probably
# bump up this number for fish specifically
kp_pan = 6
kp_tilt = 6

class LockStatus(Enum):
    UNLOCKED = 0 
    LOCKED = 1

def main():
    parser = get_cli_parser()
    
    # Handle logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=parser.logging,
    )
    logging.info(f"Loading {parser.model}...")
    tracker = Tracker(
        model_path=parser.model,
        tracker_config=f"{parser.track_config}.yaml",
        conf=parser.confidence,
        # yolo11n.pt            '0' -> 'person'
        # yolo11n_fish.pt       '0' -> 'fish"
        classes=[0] # yolo11n.pt has '0' as person, the custom yolo11n_fish.pt uses '0' for fish 
    )
    targeter = TargetSelector()
    zoom_strategy = ZoomStrategy()
    fps_calc = FPSCalculator()
    pan_servo_config = ServoConfig(
        12,
        min_angle=-60.0,
        max_angle=60.0,
        min_pulse_width=0.0009,
        max_pulse_width=0.0023,
        initial_angle=0,
        alpha=0.8,
    )
    tilt_servo_config = ServoConfig(
        19,
        min_angle=-10,
        max_angle=40,
        min_pulse_width=0.0009,
        max_pulse_width=0.0023,
        initial_angle=0,
        alpha=0.8,
    )
    
    lock_status = LockStatus.UNLOCKED
    track_id = None
    threshold = parser.threshold
    detect_every = max(1, parser.detect_every)

    with CameraController(device_index=parser.camera_index) as camera: 
        servo_controller = TSServoController(pan_servo_config, tilt_servo_config)
        keyboard_controller = KeyboardServoController(servo_controller)
        frame_count = 0
        results = None
        try:
            # Used to calculate FPS
            while True:
                frame = camera.read_frame()

                frame_h, frame_w = frame.shape[:2]

                frame_count += 1
                # Only run detection every `detect_every` frames to reduce CPU load;
                # frames in between reuse the last detection result.
                if results is None or frame_count % detect_every == 0:
                    results = tracker.track_frame(frame)

                # Handle lock state transition
                if results.boxes.id is not None and lock_status == LockStatus.UNLOCKED:
                    lock_status = LockStatus.LOCKED
                    track_id = targeter.select(results)
                    logging.info(f"Locked onto a target!")

                elif lock_status == LockStatus.LOCKED and (
                    results.boxes.id is None or track_id not in results.boxes.id.tolist()
                ):
                    lock_status = LockStatus.UNLOCKED
                    track_id = None
                    targeter.release()
                
                # Perform object detection, zooming, panning, and tilting only when we are locked onto something
                if lock_status == LockStatus.LOCKED:
                    box_idx = results.boxes.id.tolist().index(track_id)
                    x1, y1, x2, y2 = map(int, results.boxes.xyxy[box_idx].tolist())

                    logger.debug(f"{x1=}, {y1=}, {x2=}, {y2=}")
                    x_center, y_center = (x2 + x1) / 2, (y2 + y1) / 2
                    logger.debug(f"Locked target center: ({x_center}, {y_center})")

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame, 
                        f"ID: {track_id}",
                        (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )
                    box_area = max(0, x2 - x1) * max(0, y2 - y1)
                    frame_area = frame_w * frame_h
                    target_area_ratio = box_area / frame_area if frame_area else 0.0
                    logger.debug(f"Target area ratio: {target_area_ratio:.4f}")

                    # Only zoom in while the target is still small in frame; once it's
                    # big enough on its own, zooming further would just push it out of view.
                    if target_area_ratio <= parser.zoom_threshold:

                        # Future improvement:
                        #   - have zoom scale between min and max range of target 
                        frame = zoom_strategy.zoom(
                            frame,
                            strategy = "affine",
                            zoom_scale = parser.zoom,
                            center=(x_center, y_center)
                        )

                    # Calculate the difference from target's box center from
                    # screen's center and normalize it
                    error_x = (x_center - frame_w / 2) / (frame_w / 2) # [-1, 1]
                    error_y = (y_center - frame_h / 2) / (frame_h / 2)
                    logging.debug(f"Error: ({error_x}, {error_y})")
                    # Calculate how much to adjust servos
                    pan_delta = -kp_pan * error_x * 3
                    tilt_delta = -kp_tilt * error_y * 2
                    
                    # Only move servos when passed by a certain threshold
                    x_outside_threshold = pan_delta < -threshold or pan_delta > threshold
                    y_outside_threshold = tilt_delta < -threshold or tilt_delta > threshold

                    if x_outside_threshold:
                        x_angle = servo_controller.get_angle("pan_servo")
                        new_x = x_angle + pan_delta
                        logging.info(f"Panning to {new_x}")
                        servo_controller.ease_to_async("pan_servo", new_x)

                    if y_outside_threshold:
                        y_angle = servo_controller.get_angle("tilt_servo")
                        new_y = y_angle + tilt_delta
                        logging.info(f"Tilting to {new_y}")
                        servo_controller.ease_to_async("tilt_servo", new_y)

                fps_calc.calculate_fps(frame)
                cv2.imshow(f"Tracking Window", frame)

                key = cv2.waitKey(1) & 0xFF
                keyboard_controller.handle_key(key)
                if key == ord('q'):
                    break
        finally:
            logging.info("Detaching servos...")
            servo_controller.shutdown()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
