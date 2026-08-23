class FakeServo(AngularServo):
    def __init__(self, pin, min_angle=-90, max_angle=90, min_pulse_width=0.06/1000, max_pulse_width=2.5/1000):
        self.pin = pin
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width
        
        self.angle = 0

    def move(self, angle: float):
        self.angle = angle

