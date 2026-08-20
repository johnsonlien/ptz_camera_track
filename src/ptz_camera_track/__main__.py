from ptz_camera_track.cli.parse import get_cli_parser

from ptz_camera_track.camera.camera_controller import CameraController



if __name__ == "__main__":
    parser = get_cli_parser()
    parser.parse_args()
