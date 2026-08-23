from ptz_camera_track.cli.parse import get_cli_parser
from ptz_camera_track.camera.camera_controller import CameraController
from ptz_camera_track.camera.zoom import ZoomStrategy
from ptz_camera_track.control.target_selector import TargetSelector
#from ptz_camera_track.servo.servo_controller import ServoController
#from ptz_camera_track.servo.relative_servo import RelativeAngularServo
from ptz_camera_track.tracker.tracker import Tracker

import cv2


kp_pan = 3
kp_tilt = 3
UNLOCK_AREA_RATIO=0.12

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
        classes=[0]
    )
    targeter = TargetSelector()
    zoom_strategy = ZoomStrategy()
    with CameraController(device_index=parser.camera_index) as camera: 
        width, height = camera.get_frame_size()
        while True:
            frame = camera.read_frame()
            frame_h, frame_w = frame.shape[:2]

            results = tracker.track_frame(frame)
            idx = results[0].boxes.id.tolist().index(results[0])
            x_center, y_center, w, h = results[0].boxes.xywh[idx].tolist()
            
            zoomed_frame = zoom_strategy.zoom_affine(
                frame, 
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
            
            cv2.imshow("Camera Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
