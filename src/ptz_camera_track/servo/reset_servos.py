from gpiozero import AngularServo

try:
    print("Reseting panning servo")
    pan_servo = AngularServo(12)
    pan_servo.mid()
except:
    print("an error occurred reseting pan servo!")
    pass
finally:
    print("Closing Pan servo connection")
    pan_servo.detach()
    pan_servo.close()

try:
    print("Resetting tilt servo")
    tilt_servo = AngularServo(19)
    tilt_servo.mid()

except:
    print("An error occured resetting tilt servo!")
    pass
finally:
    print("Closing tilt servo")
    tilt_servo.detach()
    tilt_servo.close()
