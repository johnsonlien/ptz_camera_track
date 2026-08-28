from gpiozero import AngularServo
import time

class Controller:
    def __init__(self):
        self.servos = {}

    def add_servo(self, pin):
        self.servos[pin] = None #AngularServo(pin, min_angle=-180, max_angle=180, min_pulse_width=0.5/1000, max_pulse_width=2.4/1000)

    def run(self):

        for angle in range(-100, 100, 20):
            for key, servo in self.servos.items():
                servo = AngularServo(key, min_angle=-180, max_angle=180, min_pulse_width=0.5/1000, max_pulse_width=2.4/1000)
                print(f"Changing angle to {angle}")
                servo.angle = angle
                time.sleep(1)

                servo.detach()
                servo = None

    def cleanup(self):
        print("Deatching servos")
        for k, servo in self.servos.items():
            if servo.is_active:
                servo.detach()
                servo = None

if __name__ == "__main__":
    controller = Controller()

    controller.add_servo(23)
    controller.add_servo(24)

    controller.run()
    #controller.cleanup()
