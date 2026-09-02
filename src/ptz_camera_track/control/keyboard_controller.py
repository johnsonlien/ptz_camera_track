import logging

from typing import Callable, Dict

from ptz_camera_track.servo.thread_safe_servo_controller import TSServoController


class KeyboardServoController:
    """
    Feed this the return value of cv2.waitKey() each frame to manually jog
    the pan/tilt servos from the keyboard.

    Default bindings (WASD - portable across cv2's backends, unlike arrow
    key codes which vary by platform):
        a / d   -> pan left / right
        w / s   -> tilt up / down
        r       -> reset both servos to their initial angle
        space   -> stop both servos (cancels queued movement)
    """

    def __init__(
        self,
        servo_controller: TSServoController,
        pan_step: float = 2.0,
        tilt_step: float = 2.0,
        step_delay: float = 0.02,
    ):
        self.controller = servo_controller
        self.pan_step = pan_step
        self.tilt_step = tilt_step
        self.step_delay = step_delay

        self._bindings: Dict[int, Callable[[], None]] = {
            ord('a'): lambda: self._pan(-self.pan_step),
            ord('d'): lambda: self._pan(self.pan_step),
            ord('w'): lambda: self._tilt(self.tilt_step),
            ord('s'): lambda: self._tilt(-self.tilt_step),
            ord('r'): self._reset,
            ord(' '): self._stop,
        }

    def _pan(self, delta: float) -> None:
        name = self.controller.PAN_SERVO
        angle = self.controller.get_angle(name)
        logging.debug(f"Keyboard jog: panning to {angle + delta}")
        self.controller.move_to_async(name, angle + delta, step_delay=self.step_delay)

    def _tilt(self, delta: float) -> None:
        name = self.controller.TILT_SERVO
        angle = self.controller.get_angle(name)
        logging.debug(f"Keyboard jog: tilting to {angle + delta}")
        self.controller.move_to_async(name, angle + delta, step_delay=self.step_delay)

    def _stop(self) -> None:
        logging.info("Keyboard jog: stop_both()")
        self.controller.stop_both()

    def _reset(self) -> None:
        # Blocking: reset_angle() steps gradually back to the initial angle,
        # so this pauses the caller for as long as that takes.
        logging.info("Keyboard jog: reset_both()")
        self.controller.reset_both()

    def handle_key(self, key: int) -> bool:
        """
        Pass in the value returned by `cv2.waitKey(delay) & 0xFF` each frame.
        Returns True if the key was bound to a jog action, False otherwise
        (e.g. -1/255 when nothing was pressed, or an unbound key).
        """
        if key == -1:
            return False

        action = self._bindings.get(key & 0xFF)
        if action is None:
            return False

        action()
        return True
