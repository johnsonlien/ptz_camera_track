from __future__ import annotations

import logging
from typing import Dict, Optional

from rpi_hardware_pwm import HardwarePWM

# Which hardware PWM channel each GPIO pin is wired to. This mapping is only
# valid when /boot/firmware/config.txt has the matching dtoverlay, e.g.:
#   dtoverlay=pwm-2chan,pin=12,func=4,pin2=19,func2=2
# See dep_checks/hardware_pwm_sweep.py for the raw sweep this was derived from.
PIN_TO_CHANNEL: Dict[int, int] = {
    12: 0,
    18: 1,
    19: 1,
}

DEFAULT_FREQUENCY_HZ = 50.0


def _angle_to_duty_cycle(
    angle: float,
    min_angle: float,
    max_angle: float,
    min_pulse_width: float,
    max_pulse_width: float,
    period_s: float,
) -> float:
    lo, hi = sorted((min_angle, max_angle))
    angle = max(lo, min(hi, angle))
    fraction = (angle - min_angle) / (max_angle - min_angle)
    pulse_width_s = min_pulse_width + fraction * (max_pulse_width - min_pulse_width)
    return (pulse_width_s / period_s) * 100.0


class HardwareServo:
    """Drives a servo using the Pi's hardware PWM, bypassing gpiozero/lgpio.

    Mimics the subset of gpiozero.AngularServo's interface that TSServo
    relies on (angle get/set, is_active, detach, close) so it can be used
    as a drop-in replacement.
    """

    def __init__(
        self,
        pin: int,
        initial_angle: Optional[float] = 0.0,
        min_angle: float = -90.0,
        max_angle: float = 90.0,
        min_pulse_width: float = 0.5 / 1000,
        max_pulse_width: float = 2.5 / 1000,
        frequency: float = DEFAULT_FREQUENCY_HZ,
        chip: int = 0,
    ):
        if pin not in PIN_TO_CHANNEL:
            raise ValueError(
                f"No hardware PWM channel known for pin {pin}. "
                f"Known pins: {sorted(PIN_TO_CHANNEL)}"
            )

        self.pin = pin
        self.channel = PIN_TO_CHANNEL[pin]
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width
        self.frequency = frequency
        self._period_s = 1.0 / frequency

        self._pwm = HardwarePWM(pwm_channel=self.channel, hz=frequency, chip=chip)
        self._angle = initial_angle if initial_angle is not None else 0.0
        self.is_active = True
        self._attached = True

        self._pwm.start(self._angle_to_duty_cycle(self._angle))
        logging.debug(f"HardwareServo on pin {pin} (channel {self.channel}) started at {self._angle} degrees")

    def _angle_to_duty_cycle(self, angle: float) -> float:
        return _angle_to_duty_cycle(
            angle,
            self.min_angle,
            self.max_angle,
            self.min_pulse_width,
            self.max_pulse_width,
            self._period_s,
        )

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._angle = value
        duty_cycle = self._angle_to_duty_cycle(value)
        if self._attached:
            self._pwm.change_duty_cycle(duty_cycle)
        else:
            # start() re-enables the channel, which stop() (detach) disabled.
            self._pwm.start(duty_cycle)
            self._attached = True

    def min(self) -> None:
        self.angle = self.min_angle

    def max(self) -> None:
        self.angle = self.max_angle

    def mid(self) -> None:
        self.angle = (self.min_angle + self.max_angle) / 2

    def detach(self) -> None:
        """Stop pulsing without releasing the PWM channel."""
        self._pwm.stop()
        self._attached = False

    def close(self) -> None:
        if not self.is_active:
            return
        self._pwm.stop()
        self._attached = False
        self.is_active = False
