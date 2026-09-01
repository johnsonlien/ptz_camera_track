import sys
import time

from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory 


# ====
# Configurations
# ====

PAN_PIN = 13 
TILT_PIN = 12

MIN_ANGLE = -90.0
MAX_ANGLE = 90.0
START_ANGLE = 0

STEP_DEGREE = 3.0
MAX_PULSE_WIDTH = 2.1 / 1000
MIN_PULSE_WIDTH = 0.9 / 1000

class PanTiltController:
    """
    Wraps two servos with clamped, absolute and relative angle control
    """

    def __init__(self, pan_pin=PAN_PIN, tilt_pin=TILT_PIN):
        try:
            factory = PiGPIOFactory()
        except Exception:
            factory = None
        
        kwargs = dict(
            min_angle=MIN_ANGLE,
            max_angle=MAX_ANGLE,
            min_pulse_width=MIN_PULSE_WIDTH,
            max_pulse_width=MAX_PULSE_WIDTH,
            initial_angle=START_ANGLE
        )

        if factory:
            kwargs["pin_factory"] = factory

        self.pan_servo = AngularServo(pan_pin, **kwargs)
        self.tilt_servo = AngularServo(tilt_pin, **kwargs)
        self._pan_angle = START_ANGLE
        self._tilt_angle = START_ANGLE


servo_pan = AngularServo(
    PAN_PIN,
    min_angle=-120,
    max_angle=120,
    min_pulse_width=MIN_PULSE_WIDTH,
    max_pulse_width=MAX_PULSE_WIDTH,
)
servo_tilt = AngularServo(
    TILT_PIN,
    min_angle=-90,
    max_angle=130,
    min_pulse_width=MIN_PULSE_WIDTH,
    max_pulse_width=MAX_PULSE_WIDTH
)

def move_to(pan_angle, tilt_angle, settle_time=0.5):
    servo_pan.angle = pan_angle
    servo_tilt.angle = tilt_angle
    time.sleep(settle_time)


def sweep_demo():
    print("Centering...")
    x, y = 0, 50
    move_to(x, y)
    print("Sweeping pan...")
    
    for angle in range(-120, 120, 10):
        print(f"Panning {angle} degrees")
        move_to(x, y, settle_time=0.1)

    print("Sweeping tilt...")
    for angle in range(-90, 90, 10):

        print(f"Tilting {angle} degrees")
        move_to(0, angle, settle_time=1)

    print("Returning to center...")
    move_to(0,50)

if __name__ == "__main__":
    try:
        sweep_demo()
    finally:
        move_to(0, 120)
        servo_pan.detach()
        servo_tilt.detach()
        print("Done. Servos detached.")
