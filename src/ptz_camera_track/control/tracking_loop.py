from ptz_camera_track.tracker.tracking import Tracker
from ptz_camera_track.control.target_selector import TargetSelector
from ptz_camera_track.servo.servo_controller import PanTiltController

class TrackingLoop:
    def __init__(self, 
        camera, 
        tracker: Tracker, 
        selector: TargetSelector,
        servo_controller: PanTiltController,
        zoom,
        kp_pan=0.02,
        kp_tilt=0.02,
    ):
        self.camera = camera
        self.tracker = tracker
        self.selector = selector 
        self.servo_controller = servo_controller 
        self.zoom = zoom 
        self.kp_pan = kp_pan
        self.kp_tilt = kp_tilt

    def step(self) -> bool:
        frame = self.camera.read_frame()
        results = self.tracker.track_frame(frame)

        target_id = self.selector.select(results)

        if targetid is None:
            return False
        
        idx = results.boxes.id.tolist().index(target_id)
        x_center, y_center, w, h = results.boxes.xywh[idx].tolist()

        frame_h, frame_w = frame.shape[:2]

        error_x = (x_center - frame_w / 2) / (frame_w / 2)
        error_y = (y_center - frame_h / 2) / (frame_h / 2)

        pan_delta = -self.kp_pan * error_x * 100
        tilt_delta = self.kp_tilt * error_y * 100

        self.servo_controller.nudge(pan_delta, tilt_delta)
        self.zoom.zoom_to(bbox_size=(w,h), frame_size=(frame_w, frame_h))
        
        return True

    def run(self):
        try:
            while True:
                self.step()
        except KeyboardInterrupt:
            self.pan_tilt.reset()

