from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from gpiozero import AngularServo

@dataclass
class ServoConfig:
    pin: int
    min_angle: float = 0.0
    max_angle: float = 0.0
    min_pulse_width: float = 0.0005
    max_pulse_width: float = 0.0025
    initial_angle: Optional[float] = None

class TSServo:
    def __init__(self, name: str, config: ServoConfig):
        self.name = name
        self.config = config
        self.lock = threading.RLock()
        self.current_angle: Optional[float] = config.initial_angle

        self._stop_flag = threading.Event()
        self._servo = AngularServo(
            config.pin,
            initial_angle = config.initial_angle,
            min_angle = config.min_angle,
            max_angle = config.max_angle,
            min_pulse_width = config.min_pulse_width,
            max_pulse_width = config.max_pulse_width,
        )

    def _clamp(self, angle: float) -> float:
        lo, hi = sorted((self.config.min_angle, self.config.max_angle))

        return max(lo, min(hi, angle))
    
    def set_angle(self, angle: float, settle_time: float = 0.5, detach_after: bool = True) -> None:
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

    def move_to(self, target_angle: float, step_degree: float = 1.0, step_delay: float = 0.02, detach_after: bool = True) -> None:
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

            if detach_after:
                self._servo.detach()

            self.current_angle = angle
    def stop(self) -> None:
        self._stop_flag.set()

    def cleanup(self) -> None:
        logging.info(f"Cleaning up {self.name}...")
        with self.lock:
            if self._servo.is_active():
                logging.debug(f"{self.name} is now closing...")
                self._servo.close()
            else:
                logging.debug(f"{self.name} is already closed! Continuing...")

class TSServoController:
    def __init__(self, pan_servo_config : ServoConfig, tilt_servo_config: ServoConfig):
        try:
            self._servos: Dict[str, TSServo] = {
                "pan_servo": TSServo('pan_servo', pan_servo_config),
                "tilt_servo": TSServo('tilt_servo', tilt_servo_config),
            }
        except Exception as e:
            logging.error("Could not instatiate Thread-Safe Servos")
            raise

        self._controller_lock = threading.Lock()
        self._threads: List[threading.Thread] = []



    def _get_servo(self, name: str) -> TSServo:
        try:
            return self._servos[name]
        except KeyError:
            raise ValueError(f"Unknown servo by name '{name}'. Available servos: {list(self._servos)}")

    def _run_async(self, target: Callable[[], None]) -> thread.Thread:
        t = threading.Thread(target=target, daemon=True)
        with self._controller_lock:
            self._threads.append(t)
        t.start()
        return t


    def set_angle(self, name: str, angle: float, settle_time: float = 0.3) -> None:
        """Blocking call to move servos"""
        self._get_servo(name).set_angle(angle, settle_time=settle_time)

    def move_to(self, name: str, angle: float, step_degree: float = 1.0, step_delay: float = 0.5) -> None:
        """Blocking call to smoothly move servos"""
        self._get_servo(name).move_to(angle, step_degree=step_degree, step_delay=step_delay)

    def get_angle(self, name: str) -> Optional[float]:
        return self._get_servo(name).current_angle

    def stop(self, name: str) -> None:
        self._get_servo(name).stop()


    def set_angle_async(
        self,
        name: str, 
        angle: float, 
        settle_time: float = 0.5
    ) -> threading.Thread:
    
        return self._run_async(lambda: self.set_angle(name, angle, settle_time=settle_time))

    def move_to_async(
        self,
        name: str,
        angle: float,
        settle_time: float = 0.5,
        step_degree: float = 1.0,
        step_delay: float = 0.5
    ) -> threading.Thread:
        return self._run_async(lambda: self.move_to(name, angle, step_degree=step_degree, step_delay=step_delay))

    def move_both_async(
        self, 
        pan_angle: float,
        tilt_angle: float,
        step_degree: float = 1.0,
        step_delay: float = 0.5
    ) -> None:
        
        names = list(self._servos.keys())
        logging.debug(f"Servo names: {names}")
        # names will always be 'pan_servo' and then 'tilt_servo'

        self.move_to_async("pan_servo", pan_angle, step_degree=step_degree, step_delay=step_delay)
        self.move_to_async("tilt_servo", tilt_angle, step_degree=step_degree, step_delay=step_delay)

    def wait_all(self, timeout: Optional[float] = None) -> None:
        with self._controller_lock:
            threads = list(self._threads)
        for t in threads:
            t.join(timeout=timeout)

    def shutdown(self) -> None:
        """Stop and cleanup all servos"""

        for name in list(self._servos.keys()):
            self.stop(name)
        self.wait_all(timeout=2.0)
        for servo in self._servos.values():
            servo.cleanup()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.basicConfig(level="debug")
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

    servo_controller = TSServoController(pan_config, tilt_config)

    logger.debug(f"Panning the camera!") 
    for angle in range(int(pan_config.min_angle), int(pan_config.max_angle), 20):
        logger.info(f"Panning to {angle}")
        servo_controller.set_angle("pan_servo", float(angle), settle_time=1)
    
    logger.debug(f"Tilting the camera!")    
    for angle in range(int(tilt_config.min_angle), int(pan_config.max_angle), 20):
        logger.info(f"Tilting servo to {angle}")
        servo_controller.set_angle("tilt_servo", angle, settle_time=1)
   
    logger.info("Returning servos to initial angles")
    servo_controller.move_both_async(pan_config.initial_angle, tilt_config.initial_angle)
    

    logger.info(f"Waiting for all servos to complete their movement...")
    servo_controller.wait_all()
    
    logger.info(f"Pan Servo is now at angle: ", servo_controller.get_angle("pan_servo"))
    logger.info(f"Tilt Servo is now at angle: ", servo_controller.get_angle("tilt_servo"))
