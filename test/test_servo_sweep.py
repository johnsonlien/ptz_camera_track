"""Manual hardware check: sweeps pan (GPIO 12) and tilt (GPIO 19) at the same time.

Run directly on the Pi:
    python test/test_servo_sweep.py
"""

import logging
import time

from ptz_camera_track.servo.thread_safe_servo_controller import (
    ServoConfig,
    TSServoController,
)

PAN_PIN = 12
TILT_PIN = 19

STEP_DEGREE = 3.0
STEP_DELAY = 0.05
SETTLE_TIME = 0.5
CYCLES = 3


def sweep(servo_controller: TSServoController, cycles: int = CYCLES) -> None:
    pan_min = servo_controller._servos[servo_controller.PAN_SERVO].config.min_angle
    pan_max = servo_controller._servos[servo_controller.PAN_SERVO].config.max_angle
    tilt_min = servo_controller._servos[servo_controller.TILT_SERVO].config.min_angle
    tilt_max = servo_controller._servos[servo_controller.TILT_SERVO].config.max_angle

    for cycle in range(cycles):
        logging.info(f"Sweep cycle {cycle + 1}/{cycles}: moving to max")
        servo_controller.move_to_async(
            servo_controller.PAN_SERVO, pan_max, step_degree=STEP_DEGREE, step_delay=STEP_DELAY
        )
        servo_controller.move_to_async(
            servo_controller.TILT_SERVO, tilt_max, step_degree=STEP_DEGREE, step_delay=STEP_DELAY
        )
        servo_controller.wait_all()

        logging.info(f"Sweep cycle {cycle + 1}/{cycles}: moving to min")
        servo_controller.move_to_async(
            servo_controller.PAN_SERVO, pan_min, step_degree=STEP_DEGREE, step_delay=STEP_DELAY
        )
        servo_controller.move_to_async(
            servo_controller.TILT_SERVO, tilt_min, step_degree=STEP_DEGREE, step_delay=STEP_DELAY
        )
        servo_controller.wait_all()


def main():
    logging.basicConfig(level=logging.INFO)

    pan_config = ServoConfig(
        PAN_PIN,
        min_angle=-60.0,
        max_angle=60.0,
        min_pulse_width=0.0009,
        max_pulse_width=0.0023,
        initial_angle=0,
    )
    tilt_config = ServoConfig(
        TILT_PIN,
        min_angle=-60.0,
        max_angle=60.0,
        min_pulse_width=0.0009,
        max_pulse_width=0.0023,
        initial_angle=0,
    )

    servo_controller = TSServoController(pan_config, tilt_config)
    try:
        sweep(servo_controller)
    finally:
        logging.info("Shutting down servo controller...")
        servo_controller.shutdown()


if __name__ == "__main__":
    main()
