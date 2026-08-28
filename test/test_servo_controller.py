from ptz_camera_track.servo.thread_safe_servo_controller import ServoConfig, MockServo, TSServo, TSServoController

def test_mock_servo():

    mock_servo = MockServo(12, min_angle=-100, max_angle=100, initial_angle=0)

    assert mock_servo.angle == 0

def test_tsservo():
    config = ServoConfig(
        12,
        min_angle = -60,
        max_angle = 120,
        min_pulse_width = 0.5 /1000,
        max_pulse_width = 2.5 / 1000,
        initial_angle = 20
    )


    servo = TSServo("test_servo", config, use_mock=True)

    assert isinstance(servo._servo, MockServo)

def test_tscontroller_movement():
    tilt_config = ServoConfig(
        23,
        min_angle = -90,
        max_angle = 90,
        initial_angle = 0
    )

    pan_config = ServoConfig(
        24,
        min_angle = -100,
        max_angle = 100,
        initial_angle = 20
    )

    controller = TSServoController(pan_config, tilt_config, use_mock=True)

    # Testing normal movement
    controller.set_both_async(-80, 100)
    controller.set_both_async(-14, 10)
    controller.set_both_async(4, 34)
    controller.set_both_async(5, 2)
    controller.wait_all()
    assert controller.get_angle("tilt_servo") == 2
    assert controller.get_angle("pan_servo") == 5 

    # Test going out of bounds
    # Angles should be clamping to either min_angle or max_angle

    controller.set_angle("tilt_servo", -100)
    controller.set_angle("pan_servo", 200)
    controller.wait_all()
    assert controller.get_angle("tilt_servo") == tilt_config.min_angle
    assert controller.get_angle("pan_servo") == pan_config.max_angle

