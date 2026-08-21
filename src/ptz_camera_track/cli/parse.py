import argparse

def get_cli_parser():
    parser = argparse.ArgumentParser(
        description="Track an object with a DIY PTZ camera",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Models
    model_group = parser.add_argument_group("Models")
    model_group.add_argument("-m", "--model", choice=["yolo11n.pt"])

    # Camera-related
    camera_group = parser.add_argument_group("Camera Settings")
    camera_group.add_argument("-z", "--zoom", help="Set the zoom scale", default=1.5, type=float)
    camera_group.add_argument("-ts", "--track-strategy", choices=["manual", "highest_confidence"], help="Choose a zoom strategy for targeting.", default="manual")

    camera_group.add_argument("-ci", "--camera-index", help="Change camera index", default=0, type=int)
    
    # Movement-related
    movement_group = parser.add_argument_group("Movement Settings", "Change GPIO Servo settings")
    movement_group.add_argument("-pp", "--pan-pin", help="Set the GPIO panning pin", type=int, default=23)
    movement_group.add_argument("--pan-min-angle", help="Set the panning minimum angle in degrees", default=-60.0, type=float)
    movement_group.add_argument("--pan-max_angle", help="Set the panning maximum angle in degrees", default=60.0, type=float)
    movement_group.add_argument("--pan-min-pulse", help="Set the panning minimum pulse width", default=0.6/1000, type=float)
    movement_group.add_argument("--pan-max-pulse", help="Set the panning maximum pulse width", default= 2.3/1000, type=float)
    
    movement_group.add_argument("-tp", "--tilt-pin", help="Set the GPIO tilting pin", type=int, default=24)
    movement_group.add_argument("--tilt-min-angle", help="Set the tilting minimum angle in degrees", default=-60.0, type=float)
    movement_group.add_argument("--tilt-max-angle", help="Set the tilting maximum angle in degrees", default=60.0, type=float)
    movement_group.add_argument("--tilt-min-pulse", help="Set the tilting minimum pulse width", default=0.6/1000, type=float)
    movement_group.add_argument("--tilt-max-pulse", help="Set the tilting maximum pulse width", default=2.3/1000, type=float)
    

    return parser

