import argparse

def get_cli_parser():
    parser = argparse.ArgumentParser(
        description="Track an object with a DIY PTZ camera",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Tracking 
    tracking_group = parser.add_argument_group("Tracking Settings")
    tracking_group.add_argument("-m", "--model", type=str, default="yolo11n_fish_ncnn_model", help="Path to model. If not found, will try to download from Ultralytics")
    tracking_group.add_argument("-c", "--confidence", default=0.5)
    tracking_group.add_argument("-tc", "--track-config", choices=["bytetrack", "botsort"], default="botsort")
    tracking_group.add_argument("-t", "--target", type=str, help="Select a category to track", default="person")
    tracking_group.add_argument("--threshold", type=float, help="The minimum threshold the delta angle must be before servos move", default=7.0)

    # Camera-related
    camera_group = parser.add_argument_group("Camera Settings")
    camera_group.add_argument('-f', "--file", help="Designate file to use")
    camera_group.add_argument("-z", "--zoom", help="Set the zoom scale", default=1.5, type=float)
    camera_group.add_argument("-zt", "--zoom-threshold", help="Only zoom in while the locked target's bounding box covers less than this fraction of the frame area", default=0.30, type=float)
    camera_group.add_argument("-ts", "--track-strategy", choices=["manual", "highest_confidence"], help="Choose a tracking strategy for targeting.", default="highest_confidence")

    camera_group.add_argument("-ci", "--camera-index", help="Change camera index", default=0, type=int)
    camera_group.add_argument("-zs", "--zoom-strategy", choices=["affine"], default="affine", type=str, help="Choose zoom strategies for different performance and look")

    # Movement-related
    movement_group = parser.add_argument_group("Movement Settings", "Change GPIO Servo settings")
    movement_group.add_argument("-pp", "--pan-pin", help="Set the GPIO panning pin", type=int, default=13)
    movement_group.add_argument("--pan-min-angle", help="Set the panning minimum angle in degrees", default=-60.0, type=float)
    movement_group.add_argument("--pan-max_angle", help="Set the panning maximum angle in degrees", default=60.0, type=float)
    movement_group.add_argument("--pan-min-pulse", help="Set the panning minimum pulse width", default=0.6/1000, type=float)
    movement_group.add_argument("--pan-max-pulse", help="Set the panning maximum pulse width", default= 2.3/1000, type=float)
    
    movement_group.add_argument("-tp", "--tilt-pin", help="Set the GPIO tilting pin", type=int, default=12)
    movement_group.add_argument("--tilt-min-angle", help="Set the tilting minimum angle in degrees", default=-60.0, type=float)
    movement_group.add_argument("--tilt-max-angle", help="Set the tilting maximum angle in degrees", default=60.0, type=float)
    movement_group.add_argument("--tilt-min-pulse", help="Set the tilting minimum pulse width", default=0.6/1000, type=float)
    movement_group.add_argument("--tilt-max-pulse", help="Set the tilting maximum pulse width", default=2.3/1000, type=float)
    
    logging_group = parser.add_argument_group("Logging Settings")
    logging_group.add_argument("-l", "--logging", choices=["ERROR", "WARN", "INFO", "DEBUG"], default="INFO")

    return parser.parse_args()

