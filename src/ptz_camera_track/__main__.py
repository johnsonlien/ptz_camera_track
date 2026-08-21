from ptz_camera_track.cli.parse import get_cli_parser

#from ptz_camera_track.camera.camera_controller import CameraController
from ptz_camera_track.servo.servo_controller import ServoController
from ptz_camera_track.servo.relative_servo import RelativeAngularServo
#from ptz_camera_track.tracker.tracking import Tracker

import cv2




def main():
    parser = get_cli_parser()
    parser.parse_args()
    
    pan_config = dict(
        pin = parser["pan-pin"],
        min_angle = parser["pan_min_angle"],
        max_angle = parser["pan_max_angle"],
        min_pulse = parser["pan_min_pulse"],
        max_pulse = parser["pan_max_pulse"],
    )

    pan_servo = RelativeAngularServo(
        parser.pan_pin,
        min_angle = parser.pan_min_angle,
        max_angle = parser.pan_max_angle,
        min_pulse_width = parser.pan_min_pulse,
        max_pulse_width = parser.pan_max_pulse
    )
    
    tilt_servo = RelativeAngularServo(
        parser.tilt_pin,
        min_angle = parser.tilt_min_angle,
        max_angle = parser.tilt_max_angle,
        min_pulse_width = parser.min_pulse_width,
        max_pulse_width = parser.max_pulse_width
    )

    servo_controller = ServoController(pan_servo, tilt_servo)


if __name__ == "__main__":
    main()
