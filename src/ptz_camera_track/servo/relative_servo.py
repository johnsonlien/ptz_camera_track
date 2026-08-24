from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import AngularServo, Device


class RelativeAngularServo(AngularServo):
    """
    Angular Servo that tracks the starting angle and clamps 
    """

    def __init__(self,
        pin,
        starting_angle, 
        min_offset = -90,
        max_offset = 90,
        min_pulse_width = 0.5/1000,
        max_pulse_width = 2.5/1000,
        frame_width = 20/1000
    ):
        self.pin = pin
        # Have this class handle min/max angles so AngularServo does not throw an exception
        self.absolute_min = starting_angle + min_offset
        self.absolute_max = starting_angle + max_offset

        super().__init__(pin, min_angle=-220.0, max_angle=220.0, min_pulse_width=min_pulse_width, max_pulse_width=max_pulse_width, frame_width=frame_width)

        self.starting_angle = starting_angle
        self.min_offset = min_offset
        self.max_offset = max_offset
        self.reset_angle()
    
    def __del__(self):
        print(f"Servo on pin {self.pin} is detaching...")
        try:
            self.detach()
        except Exception:
            print("Couldn't detach servo. Might have already been detached")
            return

    def reset_angle(self):
        """
        Move angle to starting angle
        """
        self.angle = self.starting_angle

    def move_angle(self, delta_degrees):
        """
        Move by delta_degrees from current angle, clamped to the servo's abs min/max angles
        """

        target = (self.angle if self.angle is not None else self.starting_angle) + delta_degrees
        self.angle = max(self.absolute_min, min(self.absolute_max, target))

    @property
    def offset_from_start(self):
        current = self.angle if self.angle is not None else self.starting_angle
        return current - self.starting_angle
