"""
servo_test.py

Sanity-check script for two servos wired to a Raspberry Pi 4.

Hardware assumptions:
    - Servo 1 signal wire -> GPIO 12 (hardware PWM capable)
    - Servo 2 signal wire -> GPIO 13 (hardware PWM capable)
    - Servo power/ground   -> external power supply
    - External power supply ground -> tied to a Pi GND pin (shared ground)

Uses lgpio's hardware PWM (tx_pwm) instead of software-timed PWM to avoid
the jitter that can come from OS scheduling inconsistencies.

Run with:
    python3 servo_test.py
"""

import time
import lgpio


class Servo:
    """
    Represents a single hobby servo driven by hardware PWM through lgpio.

    Handles converting a desired angle (0-180 degrees) into the duty
    cycle percentage the servo expects, and provides simple sweep/center
    helpers for testing that the servo is wired and responding correctly.
    """

    # Standard hobby servo PWM frequency
    PWM_FREQUENCY_HZ = 50

    # Typical pulse width range in milliseconds for 0-180 degree travel.
    # Most hobby servos expect ~1ms (0 deg) to ~2ms (180 deg) pulses,
    # with 1.5ms as center/neutral. Adjust these if your servo's datasheet
    # specifies a different range.
    MIN_PULSE_MS = 1.0
    MAX_PULSE_MS = 2.0

    def __init__(self, gpio_chip_handle: int, gpio_pin: int):
        """
        Initialize the servo on a specific GPIO pin.

        Args:
            gpio_chip_handle: Open lgpio chip handle (from lgpio.gpiochip_open).
            gpio_pin: BCM GPIO pin number the servo signal wire is connected to.
        """
        self._handle = gpio_chip_handle
        self._pin = gpio_pin

        # Claim the pin as an output before we can drive PWM on it
        lgpio.gpio_claim_output(self._handle, self._pin)

    def _angle_to_duty_cycle(self, angle_degrees: float) -> float:
        """
        Convert a target angle (0-180) into a PWM duty cycle percentage.

        Args:
            angle_degrees: Desired servo angle, 0-180.

        Returns:
            Duty cycle as a percentage (0-100) suitable for lgpio.tx_pwm.
        """
        angle_degrees = max(0.0, min(180.0, angle_degrees))

        pulse_ms = self.MIN_PULSE_MS + (
            (angle_degrees / 180.0) * (self.MAX_PULSE_MS - self.MIN_PULSE_MS)
        )

        period_ms = 1000.0 / self.PWM_FREQUENCY_HZ
        duty_cycle_percent = (pulse_ms / period_ms) * 100.0

        return duty_cycle_percent

    def set_angle(self, angle_degrees: float) -> None:
        """
        Move the servo to a specific angle.

        Args:
            angle_degrees: Target angle, 0-180 degrees.
        """
        duty_cycle = self._angle_to_duty_cycle(angle_degrees)
        lgpio.tx_pwm(self._handle, self._pin, self.PWM_FREQUENCY_HZ, duty_cycle)

    def center(self) -> None:
        """Move the servo to its neutral/center position (90 degrees)."""
        self.set_angle(0)

    def stop_signal(self) -> None:
        """
        Fully stop driving this servo's signal pin.

        lgpio.tx_pwm requires a valid (non-zero) frequency -- passing 0
        causes a "bad PWM micros" error internally. So we zero out the
        duty cycle at a valid frequency first (this stops the servo from
        holding torque), then free the GPIO line so nothing continues
        driving the pin after the script exits.
        """
        lgpio.tx_pwm(self._handle, self._pin, self.PWM_FREQUENCY_HZ, 0)
        lgpio.gpio_free(self._handle, self._pin)


def sweep_test(servo: Servo, label: str) -> None:
    """
    Run a simple sweep (center -> min -> max -> center) on a servo so you
    can visually confirm it responds correctly across its full range.

    Args:
        servo: The Servo instance to test.
        label: A human-readable name for this servo, used in print output.
    """
    print(f"[{label}] Centering (90 deg)...")
    servo.center()
    time.sleep(1)

    print(f"[{label}] Moving to 0 deg...")
    servo.set_angle(0)
    time.sleep(1)

    print(f"[{label}] Moving to 180 deg...")
    servo.set_angle(180)
    time.sleep(1)

    print(f"[{label}] Returning to center (90 deg)...")
    servo.center()
    time.sleep(1)


def main() -> None:
    """
    Open the GPIO chip, initialize both servos, and run a sweep test on
    each one to confirm wiring and signal are working correctly.
    """
    GPIO_PIN_SERVO_1 = 23 
    GPIO_PIN_SERVO_2 = 24

    # Open the default GPIO chip (chip 0 on Raspberry Pi 4)
    chip_handle = lgpio.gpiochip_open(0)

    try:
        servo_1 = Servo(chip_handle, GPIO_PIN_SERVO_1)
        servo_2 = Servo(chip_handle, GPIO_PIN_SERVO_2)

        sweep_test(servo_1, f"Servo 1 ({GPIO_PIN_SERVO_1})")
        sweep_test(servo_2, f"Servo 2 ({GPIO_PIN_SERVO_2})")

        print("Sweep test complete. Both servos should have moved "
              "smoothly without shaking at each stop.")

    finally:
        # Always stop PWM output and release the GPIO chip, even if
        # something above raised an exception mid-test.
        servo_1.stop_signal()
        servo_2.stop_signal()
        lgpio.gpiochip_close(chip_handle)
        print("GPIO chip closed cleanly.")


if __name__ == "__main__":
    main()
