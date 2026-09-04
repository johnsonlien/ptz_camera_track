#!/usr/bin/env python3
"""Manual hardware check: sweeps pan (GPIO 12) and tilt (GPIO 19) together
using the Pi's hardware PWM directly, bypassing gpiozero entirely.

GPIO 12 is hardware PWM channel 0, GPIO 19 is hardware PWM channel 1.

The bare `dtoverlay=pwm-2chan` line maps to GPIO18/GPIO19 by default, NOT
GPIO12 -- to actually get PWM0 on GPIO12 the overlay needs explicit pin
params. In /boot/firmware/config.txt (or /boot/config.txt on older
Raspberry Pi OS):
    dtoverlay=pwm-2chan,pin=12,func=4,pin2=19,func2=2
then reboot. Verify with `pinctrl get 12,19` -- both should show an alt
function (e.g. a0/a4 and a5), not `ip` (plain input).

Also requires write access to /sys/class/pwm/pwmchip0 (run as root, or
with the pwm group set up).

Note: running a gpiozero/lgpio-based servo script (e.g. test_servo_sweep.py,
reset_servos.py, TSServoController) against pins 12/19 claims them as plain
GPIO and knocks them out of PWM alt-function mode until the next reboot --
avoid mixing the two approaches on the same pins within one boot session.

Run directly on the Pi:
    python dep_checks/hardware_pwm_sweep.py
"""

import logging
import time

from rpi_hardware_pwm import HardwarePWM

PAN_CHANNEL = 0   # GPIO 12
TILT_CHANNEL = 1  # GPIO 19

PWM_HZ = 50.0
PERIOD_S = 1.0 / PWM_HZ

MIN_PULSE_WIDTH_S = 0.0009  # 0.9ms
MAX_PULSE_WIDTH_S = 0.0023  # 2.3ms

PAN_MIN_ANGLE, PAN_MAX_ANGLE = -60.0, 60.0
TILT_MIN_ANGLE, TILT_MAX_ANGLE = -10.0, 40.0

STEPS_PER_LEG = 60  # resolution of one min->max (or max->min) sweep leg
STEP_DELAY = 0.02
CYCLES = 3


def angle_to_duty_cycle(angle: float, min_angle: float, max_angle: float) -> float:
    """Map an angle within [min_angle, max_angle] to a 0-100 PWM duty cycle."""
    angle = max(min_angle, min(max_angle, angle))
    fraction = (angle - min_angle) / (max_angle - min_angle)
    pulse_width_s = MIN_PULSE_WIDTH_S + fraction * (MAX_PULSE_WIDTH_S - MIN_PULSE_WIDTH_S)
    return (pulse_width_s / PERIOD_S) * 100.0


class HardwarePWMServo:
    """Maps angles to hardware PWM duty cycles for a single servo."""

    def __init__(self, channel: int, min_angle: float, max_angle: float):
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.pwm = HardwarePWM(pwm_channel=channel, hz=PWM_HZ, chip=0)
        self.pwm.start(angle_to_duty_cycle(0.0, min_angle, max_angle))

    def set_angle(self, angle: float) -> None:
        self.pwm.change_duty_cycle(angle_to_duty_cycle(angle, self.min_angle, self.max_angle))

    def stop(self) -> None:
        self.pwm.stop()


def _leg(start_fraction: float, end_fraction: float, steps: int):
    """Yield `steps` fractions from start_fraction to end_fraction inclusive."""
    for i in range(steps + 1):
        yield start_fraction + (end_fraction - start_fraction) * (i / steps)


def sweep(pan: HardwarePWMServo, tilt: HardwarePWMServo, cycles: int = CYCLES) -> None:
    for cycle in range(cycles):
        logging.info(f"Sweep cycle {cycle + 1}/{cycles}: min -> max")
        for fraction in _leg(0.0, 1.0, STEPS_PER_LEG):
            pan.set_angle(PAN_MIN_ANGLE + fraction * (PAN_MAX_ANGLE - PAN_MIN_ANGLE))
            tilt.set_angle(TILT_MIN_ANGLE + fraction * (TILT_MAX_ANGLE - TILT_MIN_ANGLE))
            time.sleep(STEP_DELAY)

        logging.info(f"Sweep cycle {cycle + 1}/{cycles}: max -> min")
        for fraction in _leg(1.0, 0.0, STEPS_PER_LEG):
            pan.set_angle(PAN_MIN_ANGLE + fraction * (PAN_MAX_ANGLE - PAN_MIN_ANGLE))
            tilt.set_angle(TILT_MIN_ANGLE + fraction * (TILT_MAX_ANGLE - TILT_MIN_ANGLE))
            time.sleep(STEP_DELAY)


def main():
    logging.basicConfig(level=logging.INFO)

    pan = HardwarePWMServo(PAN_CHANNEL, PAN_MIN_ANGLE, PAN_MAX_ANGLE)
    tilt = HardwarePWMServo(TILT_CHANNEL, TILT_MIN_ANGLE, TILT_MAX_ANGLE)

    try:
        sweep(pan, tilt)
    finally:
        logging.info("Centering and stopping PWM...")
        pan.set_angle((PAN_MIN_ANGLE + PAN_MAX_ANGLE) / 2)
        tilt.set_angle((TILT_MIN_ANGLE + TILT_MAX_ANGLE) / 2)
        time.sleep(0.5)
        pan.stop()
        tilt.stop()


if __name__ == "__main__":
    main()
