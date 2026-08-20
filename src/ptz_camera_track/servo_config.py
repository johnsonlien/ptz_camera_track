pan_config = dict(
    min_angle = -60.0,
    max_angle = 60.0,
    pin = 23,
    start_angle = 10,
    step_count = 10
)

tilt_config = dict(
    min_angle = -30.0,
    max_angle = 30.0,
    pin = 24,
    start_angle = 110,
    step_count = 10
)

common_config = dict(
    min_pulse_width = 0.9 / 1000
    max_pulse_width = 2.1 / 1000
)

zoom_config = dict(
    scale = 1.25,

    # smooth - Uses rotation matrix for smoother zooming (slower)
    # crop - Uses bounding box of target and resizes the screen (faster but more abrupt)
    strategy = "smooth"
)
