from ptz_camera_track.servo.relative_servo import RelativeAngularServo

class ServoController:
    """
    Coordinates a pan servo and tilt servo
    """

    def __init__(self, pan_servo: RelativeAngularServo, tilt_servo: RelativeAngularServo):
        self.pan_servo = pan_servo
        self.tilt_servo = tilt_servo

    def nudge(self, pan_delta, tilt_delta):
        print(f"Panning {pan_delta} degrees and tilting {tilt_delta} degrees")

        self.pan_servo.move_angle(pan_delta)
        self.tilt_servo.move_angle(tilt_delta)


    def reset(self):
        """Go back to starting positions"""

        self.pan_servo.reset_angle()
        self.tilt_servo.reset_angle()
