from ultralytics import YOLO

class Tracker:
    def __init__(self, model_path="yolo11n.pt", tracker_config="bytetrack.yaml", conf=0.5, classes=None):
        
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config
        self.conf = conf
        self.classes = classes

    def track_frame(self, frame):

        results = self.model.track(
            source=frame,
            tracker=self.tracker_config,
            conf=self.conf,
            classes=self.classes,
            persist=True,
            verbose=False,
        )
        return results[0]
