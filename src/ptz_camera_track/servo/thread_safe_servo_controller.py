from __future__ import annotations

import logging
import threading
import time
import queue

from dataclasses import dataclass
from typing import Callable, Dict, Optional

from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory

_pin_factory: Optional[LGPIOFactory] = None

def _get_pin_factory() -> LGPIOFactory:
    global _pin_factory
    if _pin_factory is None:
        _pin_factory = LGPIOFactory()
    return _pin_factory

@dataclass
class ServoConfig:
    pin: int
    min_angle: float = -60.0
    max_angle: float = 60.0
    min_pulse_width: float = 0.0005
    max_pulse_width: float = 0.0025
    initial_angle: Optional[float] = None
    alpha: float = 0.1  # Used to help smoothen movement
    detach_when_idle: bool = False

class MockServo:
    """AngularServo Mock for testing"""
    
    def __init__(
        self,
        pin : int,
        initial_angle : float = 0.0,
        min_angle : float = -90.0,
        max_angle : float = 90.0,
        min_pulse_width : float = 0.5 / 1000, # Unused but mimicing the real AngularServo
        max_pulse_width : float = 2.5 / 1000, # Unused
    ):
        self.pin = pin
        self.angle = initial_angle
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width
        self.is_active = True
    
    def is_active(self):
        return self.is_active
    def min(self):
        self.angle = self.min_angle
    def max(self):
        self.angle = self.max_angle
    def detach(self):
        pass
    def close(self):
        self.is_active = False

class TSServo:
    def __init__(self, name: str, config: ServoConfig, use_mock: bool = False):
        """
        Compositive class containing AngularServo to handle angle clamping
        """
        self.name = name
        self.config = config
        self.lock = threading.RLock()
        self.current_angle: Optional[float] = config.initial_angle
        self.start_angle = config.initial_angle
        self.alpha = config.alpha
        self._stop_flag = threading.Event()
        self._queue: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        
        if use_mock:
            self._servo = MockServo(
                config.pin,
                initial_angle = config.initial_angle,
                min_angle = config.min_angle,
                max_angle = config.max_angle,
                min_pulse_width = config.min_pulse_width,
                max_pulse_width = config.max_pulse_width,
            )
        else:
            self._servo = AngularServo(
                config.pin,
                initial_angle = config.initial_angle,
                min_angle = config.min_angle,
                max_angle = config.max_angle,
                min_pulse_width = config.min_pulse_width,
                max_pulse_width = config.max_pulse_width,
                pin_factory = _get_pin_factory(),
            )

            if config.detach_when_idle:
                # Detach immediately to reduce the immediate shaking
                self._servo.detach()
        self._worker.start()
    
    def _process_queue(self):
        while True:
            if self._stop_flag.is_set():
                # If signaled to stop (i.e., in the case of unlocked status) 
                # stop all pending movements
                logging.info(f"{self.name} has stop_flag set! Removing all items in queue...")
                with self._queue.mutex:
                    unfinished = self._queue.unfinished_tasks - len(self._queue.queue)
                    if unfinished <= 0:
                        if unfinished < 0:
                            raise ValueError('task_done() called too many times')
                        self._queue.all_tasks_done.notify_all()
                    logging.info(f"{self.name} had {unfinished} tasks left")
                    self._queue.unfinished_tasks = unfinished
                    self._queue.queue.clear()
                    logging.info(f"{self.name} has removed all items from its queue. Notifying all...")
                    self._queue.not_full.notify_all()
                self._stop_flag.clear()

            func = self._queue.get()
            if func is None:
                logging.info(f"{self.name} was signaled to stop processing its queue.")
                break
            func()
            self._queue.task_done()

    def _submit(self, func):
        self._queue.put(func)

    def _submit_latest(self, func) -> None:
        with self._queue.mutex:
            discarded = len(self._queue.queue)
            if discarded:
                unfinished = self._queue.unfinished_tasks - discarded
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self._queue.unfinished_tasks = unfinished
                self._queue.queue.clear()
                if unfinished == 0:
                    self._queue.all_tasks_done.notify_all()

            self._queue.queue.append(func)
            self._queue.unfinished_tasks += 1
            self._queue.not_empty.notify()

    def _clamp(self, angle: float) -> float:
        lo, hi = sorted((self.config.min_angle, self.config.max_angle))

        return max(lo, min(hi, angle))
    
    def set_angle(self, angle: float, settle_time: float = 0.5, detach_after: bool = False) -> None:
        with self.lock:
            angle = self._clamp(angle)
            logging.debug(f"Setting {self.name} servo to {angle} degrees")
            self._servo.angle = angle 
            
            time.sleep(settle_time)

            if detach_after:
                # Noticed that servos shake while idling but they dont after detaching.
                self._servo.detach()
                
            # Update current angle to keep track of it 
            self.current_angle = angle 
    
    def get_angle(self):
        with self.lock:
            return self.current_angle
    
    def reset_angle(self, step_degree: float = 1.0, step_delay: float = 0.02):
        with self.lock:
            target_angle = self.start_angle
            if target_angle is None:
                logging.warning(f"{self.name} has no initial_angle configured; skipping reset_angle")
                return
            angle = self.current_angle if self.current_angle is not None else target_angle
            direction = 1 if target_angle >= angle else -1

            while direction * (target_angle - angle) > 0:
                angle += direction * step_degree
                if direction * (angle - target_angle) > 0:
                    angle = target_angle
                self._servo.angle = angle
                time.sleep(step_delay)

            self.current_angle = angle

    def move_to(self, 
        target_angle: float,
        step_degree: float = 1.0,
        step_delay: float = 0.02, 
        detach_after: bool = False
    ) -> None:
        """Incrementally move the servos instead of jumping"""

        with self.lock:
            self._stop_flag.clear()
            target_angle = self._clamp(target_angle)
            start = self.current_angle if self.current_angle is not None else target_angle

            direction = 1 if target_angle >= start else -1
            angle = start

            while direction * (target_angle - angle) > 0:
                if self._stop_flag.is_set():
                    logging.info(f"Interrupt detected! Will not move {self.name}")
                    break
                angle += direction * step_degree
                if direction * (angle - target_angle) > 0:
                    angle = target_angle

                self._servo.angle = angle
                time.sleep(step_delay)
            self.current_angle = angle
            
            if detach_after:
                self._servo.detach()

    
    def ease_to(
        self,
        target_angle,
        step_delay: float = 0.02,
        detach_after: bool = False
    ) -> None:
        """Ease into the target angle by going a percentage of the target angle and current angle"""

        with self.lock:
            target_angle = self._clamp(target_angle)
            current = self.current_angle if self.current_angle is not None else target_angle
            smoothed_angle = (self.alpha * target_angle) + ((1.0 - self.alpha) * current)
            logging.info(f"Moving towards {target_angle} by going to angle {smoothed_angle}")
            
            self._servo.angle = smoothed_angle
            self.current_angle = smoothed_angle
        
            time.sleep(step_delay)
        
            if detach_after:
                self._servo.detach()

    def stop(self) -> None:
        self._stop_flag.set()

    def cleanup(self) -> None:
        logging.info(f"Cleaning up {self.name}...")
        with self.lock:
            if self._servo is not None and self._servo.is_active:
                logging.debug(f"{self.name} is now closing...")
                self._servo.close()
            else:
                logging.debug(f"{self.name} is already closed! Continuing...")

class TSServoController:
    def __init__(self, pan_servo_config : ServoConfig, tilt_servo_config: ServoConfig, use_mock : bool = False):
        self.TILT_SERVO = "tilt_servo"
        self.PAN_SERVO = "pan_servo"

        try:
            self._servos: Dict[str, TSServo] = {
                self.PAN_SERVO: TSServo(self.PAN_SERVO, pan_servo_config, use_mock=use_mock),
                self.TILT_SERVO: TSServo(self.TILT_SERVO, tilt_servo_config, use_mock=use_mock),
            }

        except Exception as e:
            logging.error("Could not instatiate Thread-Safe Servos")
            raise

    def _get_servo(self, name: str) -> TSServo:
        try:
            return self._servos[name]
        except KeyError:
            raise ValueError(f"Unknown servo by name '{name}'. Available servos: {list(self._servos)}")

    def set_angle(self, name: str, angle: float, settle_time: float = 0.3) -> None:
        """Blocking call to move servos"""
        self._get_servo(name).set_angle(angle, settle_time=settle_time)

    def move_to(self, name: str, angle: float, step_degree: float = 1.0, step_delay: float = 0.5) -> None:
        """Blocking call to smoothly move servos"""
        self._get_servo(name).move_to(angle, step_degree=step_degree, step_delay=step_delay)

    def ease_to(self, name: str, angle: float, step_delay: float = 0.02) -> None:
        """Blocking call to smoothly ease a servo towards a target angle (EMA smoothing)"""
        self._get_servo(name).ease_to(angle, step_delay=step_delay)

    def get_angle(self, name: str) -> Optional[float]:
        return self._get_servo(name).get_angle()

    def stop(self, name: str) -> None:
        self._get_servo(name).stop()
    
    def stop_both(self) -> None:
        self._servos[self.PAN_SERVO].stop()
        self._servos[self.TILT_SERVO].stop()

    def set_angle_async(
        self,
        name: str, 
        angle: float, 
        settle_time: float = 0.5
    ) -> threading.Thread:
        self._get_servo(name)._submit(lambda: self.set_angle(name, angle, settle_time=settle_time))
    
    def move_to_async(
        self,
        name: str,
        angle: float,
        step_degree: float = 1.0,
        step_delay: float = 0.5
    ) -> threading.Thread:
        self._get_servo(name)._submit(lambda: self.move_to(name, angle, step_degree=step_degree, step_delay=step_delay))

    def ease_to_async(
        self,
        name: str,
        angle: float,
        step_delay: float = 0.02
    ) -> None:
        self._get_servo(name)._submit_latest(lambda: self.ease_to(name, angle, step_delay=step_delay))

    def set_both_async(
        self, 
        pan_angle: float,
        tilt_angle: float,
        settle_time: float = 0.5
    ) -> None:
        """Helper function to set both pan and tilt servos""" 
        self.set_angle_async(self.PAN_SERVO, pan_angle, settle_time=settle_time)
        self.set_angle_async(self.TILT_SERVO, tilt_angle, settle_time=settle_time)
    
    def move_both_async(
        self,
        pan_angle: float,
        tilt_angle: float,
        step_angle: float = 3.0,
        step_delay: float = 0.5,
    ) -> None:
        """Helper function to slide both pan and tilt servos"""
        self.move_to_async(self.PAN_SERVO, pan_angle, step_angle=step_angle, step_delay=step_delay)
        self.move_to_async(self.TILT_SERVO, tilt_angle, step_angle=step_angle, step_delay=step_delay)
   
    def reset_both(self) -> None:
        self._servos[self.PAN_SERVO].reset_angle()
        self._servos[self.TILT_SERVO].reset_angle()

    def wait_all(self) -> None:
        for servo in self._servos.values():
            servo._queue.join()

    def shutdown(self) -> None:
        """Stop and cleanup all servos"""
        logging.info("Thread-safe Servo Controller initiating servo cleanup")
        for name in list(self._servos.keys()):
            self.stop(name)
        logging.info("Servo Controller is waiting for all items in servo queue to finish")
        self.wait_all()
        self.reset_both()
        for servo in self._servos.values():
            servo.cleanup()
        
        
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    # Some initial tests
    pan_config = ServoConfig(
        23,
        min_angle = -80.0,
        max_angle = 80.0,
        initial_angle = 0,
    )
    tilt_config = ServoConfig(
        24,
        min_angle = 40.0,
        max_angle = 120.0,
        initial_angle = 80
    )

    servo_controller = TSServoController(pan_config, tilt_config, use_mock=True)
     
    logger.debug(f"Panning the camera!") 
    for angle in range(int(pan_config.min_angle), int(pan_config.max_angle), 20):
        logger.info(f"Panning to {angle}")
        servo_controller.set_angle(servo_controller.PAN_SERVO, float(angle), settle_time=1)
    
    logger.debug(f"Tilting the camera!")    
    for angle in range(int(tilt_config.min_angle), int(pan_config.max_angle), 20):
        logger.info(f"Tilting servo to {angle}")
        servo_controller.set_angle(servo_controller.TILT_SERVO, float(angle), settle_time=1)
   
    logger.info("Returning servos to initial angles")
    servo_controller.set_both_async(pan_config.initial_angle, tilt_config.initial_angle)

    servo_controller.shutdown()

    logger.info(f"Pan Servo is now at angle: {servo_controller.get_angle(servo_controller.PAN_SERVO)}")
    logger.info(f"Tilt Servo is now at angle: {servo_controller.get_angle(servo_controller.TILT_SERVO)}")


