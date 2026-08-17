import time
from gpiozero import AngularServo, Device

servo_pan = AngularServo(
    18,
    min_angle=-120,
    max_angle=120,
    min_pulse_width=0.5 / 1000,
    max_pulse_width=2.5 / 1000,
)
#servo_tilt = AngularServo(
#    18,
#    min_angle=-90,
#    max_angle=90,
#    min_pulse_width=0.5 / 1000,
#    max_pulse_width=2.5 / 1000
#)

def move_to(pan_angle, tilt_angle, settle_time=0.5):
    """
    Move both servos to the given angles (-90 to 90) and wait briefly
    """

    servo_pan.angle = pan_angle
    #servo_tilt.angle = tilt_angle
    time.sleep(settle_time)


def sweep_demo():
    print("Centering...")
    move_to(0,0)

    print("Sweeping pan...")
    for angle in range(-120, 120, 10):
        move_to(angle, 0, settle_time=0.1)

    print("Returning to center...")
    move_to(0,0)

if __name__ == "__main__":
    try:
        sweep_demo()
    finally:
        servo_pan.detach()
        #servo_tilt.detach()
        print("Done. Servos detached.")
