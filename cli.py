import argparse

def cli():
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--model", 
        default="yolo11n_ncnn_model", 
        help="Path to model"
    )
    parser.add_argument(
        "--target",
        default="fish",
        help="Class name to zoom in on"
    )
    parser.add_argument(
        "--source",
        default=0,
        help="Camera index or video file path"
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=0.6,
        help="Extra margin around the box, as a fraction of box size"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.4,
        help="Minimum confidence to count as a detection"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=320,
        help="Inference resolution (lower = faster on Pi)"
    )

    args = parser.parse_args()
    
    return parser
