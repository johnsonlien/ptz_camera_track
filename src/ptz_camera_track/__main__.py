from ptz_camera_track.cli.parse import get_cli_parser

from ptz_camera_track.camera.camera_controller import CameraController
from ptz_camera_track.camera.zoom import ZoomStrategy

from ptz_camera_track.control.target_selector import TargetSelector

from ptz_camera_track.servo.relative_servo import RelativeAngularServo
from ptz_camera_track.servo.thread_safe_servo_controller import TSServoController, ServoConfig

from ptz_camera_track.tracker.tracker import Tracker

from enum import Enum
import cv2
import logging

kp_pan = 3
kp_tilt = 3
UNLOCK_AREA_RATIO=0.12

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

    pan_servo_config = ServoConfig(
        23,
        min_angle=-60.0,
        max_angle=60.0,
        initial_angle=0
    )
    tilt_servo_config = ServoConfig(
        24,
        min_angle=-40,
        max_angle=40,
        initial_angle=-20,
    )
    servo_controller = TSServoController(pan_servo_config, tilt_servo_config)
    lock_status = LockStatus.UNLOCKED
    track_id = None

    threshold = parser.threshold
    with CameraController(device_index=parser.camera_index) as camera: 
        width, height = camera.get_frame_size()
        try:
            while True:
                frame = camera.read_frame()
                frame_h, frame_w = frame.shape[:2]

                results = tracker.track_frame(frame)
                
                # Handle lock state transition
                if results.boxes.id is not None and lock_status == LockStatus.UNLOCKED:
                    lock_status = LockStatus.LOCKED
                    
                    track_id = targeter.select(results)

                elif results.boxes.id is None and lock_status == LockStatus.LOCKED:
                    lock_status = LockStatus.UNLOCKED
                    track_id = None

                if lock_status == LockStatus.LOCKED:
                    x1, y1, x2, y2 = map(int, results.boxes.xyxy[0].tolist())

                    logger.debug(f"{x1=}, {y1=}, {x2=}, {y2=}")
                    x_center, y_center = (x2 - x1) / 2, (y2 - y1) / 2
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
                    frame = zoom_strategy.zoom(
                        frame,
                        strategy = "affine",
                        zoom_scale = parser.zoom,
                        center=(x_center, y_center) 
                    )
                
                    # Calculate the difference from target's box center from 
                    # screen's center and normalize it
                    error_x = (x_center - frame_w / 2) / (frame_w / 2)
                    error_y = (y_center - frame_h) / (frame_h / 2)

                    # Calculate how much to adjust servos
                    pan_delta = kp_pan * error_x * 10
                    tilt_delta = kp_tilt * error_y * 10
                    # Only move servos when passed by a certain threshold
                    if (-threshold < pan_delta > threshold) and (-threshold < tilt_delta > threshold):
                        x_angle = servo_controller.get_angle("pan_servo")
                        y_angle = servo_controller.get_angle("tilt_servo")

                        new_x = x_angle + pan_delta
                        new_y = y_angle + tilt_delta
                        logging.info(f"Panning to {new_x} and tilting to {new_y}") 
                        servo_controller.move_both_async(new_x, new_y)
                    elif -threshold < pan_delta > threshold:
                        x_angle = servo_controller.get_angle("pan_servo")
                        
                        new_x = x_angle + pan_angle
                        logging.info(f"Panning to {new_x}")
                        servo_controller.set_angle_async("pan_servo", new_x)
                    elif -threshold < tilt_delta > threshold:
                        y_angle = servo_controller.get_angle("tilt_servo")

                        new_y = y_angle + tilt_delta
                        logging.info(f"Tilting to {new_y}")
                        servo_controller.set_angle_async("tilt_servo", new_y)

                cv2.imshow(f"Tracking Window", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            logging.info("Detaching servos...")
            servo_controller.shutdown()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
