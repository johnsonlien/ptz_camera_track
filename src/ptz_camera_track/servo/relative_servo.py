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
        min_pulse_width = 0.6/1000,
        max_pulse_width = 2.3/1000,
        frame_width = 20/1000
    ):
        absolute_min = starting_angle + min_offset
        absolute_max = starting_angle + max_offset

        super().__init__(pin, min_angle=absolute_min, max_angle=absolute_max, min_pulse_width=min_pulse_width, max_pulse_width=max_pulse_width, frame_width=frame_width)

        self.starting_angle = starting_angle
        self.min_offset = min_offset
        self.max_offset = max_offset
        self.reset_angle()

    def reset_angle(self):
        """
        Move angle to starting angle
        """
        self.angle = self.starting_angle

    def move_relative(self, delta_degrees):
        """
        Move by delta_degrees from current angle, clamped to the servo's abs min/max angles
        """

        target = (self.angle if self.angle is not None else self.starting_angle) + delta_degrees
        self.angle = max(self.min_angle, min(self.max_angle, target))

    @property
    def offset_from_start(self):
        current = self.angle if self.angle is not None else self.starting_angle
        return current - self.starting_angle
