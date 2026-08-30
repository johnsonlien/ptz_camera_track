from rpi_hardware_pwm import HardwarePWM
from gpiozero import AngularServo

import time
import threading


pwm = HardwarePWM(pwm_channel=1, hz=50, chip=0)
servo = AngularServo(12, min_pulse_width=0.001, max_pulse_width=0.002)

pwm.start(0)

MIN_PULSE_MS = 1.0
MAX_PULSE_MS = 2.0
PERIOD_MS = 1000 / 50 # 20ms

def angle_to_duty_cycle(angle):
    pulse_ms = MIN_PULSE_MS + (angle +90) * (MAX_PULSE_MS - MIN_PULSE_MS) / 180.0
    return (pulse_ms/PERIOD_MS) * 100.0

try:
    while True:
        for angle in range(-90, 90, 5):
            pwm.change_duty_cycle(angle_to_duty_cycle(angle))
            servo.angle = angle
            time.sleep(0.02)

        for angle in range(90, -90, -5):
            pwm.change_duty_cycle(angle_to_duty_cycle(angle))
            servo.angle = angle
            time.sleep(0.02)
except KeyboardInterrupt:
    pass
finally:
    pwm.stop()
