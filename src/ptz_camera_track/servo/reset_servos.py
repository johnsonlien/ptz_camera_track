import time

from ptz_camera_track.servo.hardware_servo import HardwareServo

# Mirrors the pan/tilt configs in __main__.py so "mid" here lands on the same
# physical center the app uses.
PAN_CONFIG = dict(min_angle=-60.0, max_angle=60.0, min_pulse_width=0.0009, max_pulse_width=0.0023)
TILT_CONFIG = dict(min_angle=-10.0, max_angle=40.0, min_pulse_width=0.0009, max_pulse_width=0.0023)

pan_servo = None
tilt_servo = None

try:
    print("Reseting panning servo")
    pan_servo = HardwareServo(12, **PAN_CONFIG)
    pan_servo.mid()
    time.sleep(1)

except Exception:
    print("an error occurred reseting pan servo!")
finally:
    if pan_servo is not None:
        print("Closing Pan servo connection")
        pan_servo.detach()
        pan_servo.close()

try:
    print("Resetting tilt servo")
    tilt_servo = HardwareServo(19, **TILT_CONFIG)
    tilt_servo.mid()
    time.sleep(1)
except Exception:
    print("An error occured resetting tilt servo!")
finally:
    if tilt_servo is not None:
        print("Closing tilt servo")
        tilt_servo.detach()
        tilt_servo.close()
