from ptz_camera_track.cli.parse import get_cli_parser
from ptz_camera_track.camera.camera_controller import CameraController
from ptz_camera_track.camera.zoom import ZoomStrategy
from ptz_camera_track.control.target_selector import TargetSelector
#from ptz_camera_track.servo.servo_controller import ServoController
#from ptz_camera_track.servo.relative_servo import RelativeAngularServo
from ptz_camera_track.tracker.tracker import Tracker


from enum import Enum
import cv2


kp_pan = 3
kp_tilt = 3
UNLOCK_AREA_RATIO=0.12

class LockStatus(Enum):
    UNLOCKED = 0 
    LOCKED = 1


def main():
    parser = get_cli_parser()
    #parser.parse_args()
    
#    pan_config = dict(
#        pin = parser["pan-pin"],
#        min_angle = parser["pan_min_angle"],
#        max_angle = parser["pan_max_angle"],
#        min_pulse = parser["pan_min_pulse"],
#        max_pulse = parser["pan_max_pulse"],
#    )
#
#    pan_servo = RelativeAngularServo(
#        parser.pan_pin,
#        min_angle = parser.pan_min_angle,
#        max_angle = parser.pan_max_angle,
#        min_pulse_width = parser.pan_min_pulse,
#        max_pulse_width = parser.pan_max_pulse
#    )
#    
#    tilt_servo = RelativeAngularServo(
#        parser.tilt_pin,
#        min_angle = parser.tilt_min_angle,
#        max_angle = parser.tilt_max_angle,
#        min_pulse_width = parser.min_pulse_width,
#        max_pulse_width = parser.max_pulse_width
#    )
#
#    servo_controller = ServoController(pan_servo, tilt_servo)
    
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

    lock_status = LockStatus.UNLOCKED
    track_id = None
    with CameraController(device_index=parser.camera_index) as camera: 
        width, height = camera.get_frame_size()
        while True:
            frame = camera.read_frame()
            frame_h, frame_w = frame.shape[:2]

            results = tracker.track_frame(frame)
            
            # Handle lock state transition
            if results.boxes.id is not None and lock_status == LockStatus.UNLOCKED:
                lock_status = LockStatus.LOCKED
                
                # track_id = self.selector.select(results)
                # print(f"Track ID: {track_id}")
                
                # idx = results.boxes.id.tolist().index(target_id)
                # x_center, y_center, w, h = results.boxes.xywh[idx].tolist()

            elif results.boxes.id is None and lock_status == LockStatus.LOCKED:
                lock_status = LockStatus.UNLOCKED


            if lock_status == LockStatus.LOCKED:
                x1, y1, x2, y2 = map(int, results.boxes.xyxy[0].tolist())

                print(f"{x1=}, {y1=}, {x2=}, {y2=}")
                x_center, y_center = (x2 - x1) / 2, (y2 - y1) / 2
                print(f"Locked target center: ({x_center}, {y_center})")

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
                pan_delta = kp_pan * error_x * 100 
                tilt_delta = kp_tilt * error_y * 100

                # Move servos
                print(f"Panning {pan_delta}")
                print(f"Tilting {tilt_delta}")
            
            cv2.imshow(f"Tracking Window", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
