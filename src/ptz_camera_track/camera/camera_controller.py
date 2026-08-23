import cv2

class CameraController:

    def __init__(self, device_index=0, resolution=(640, 480), framerate=30, file=None):
        self.resolution = resolution
        self.framerate = framerate
        self.camera_index = device_index 
        self._cam = None
        self.file = None
    
    def start(self):
        if self.file is not None:
            self._cam = cv2.VideoCapture(self.file) # Camera should be at index 0
        else:
            self._cam = cv2.VideoCapture(self.camera_index) # Camera should be at index 0
        
        if not self._cam.isOpened():
            print("Error: Could not open video. Check if video file exists, webcam is plugged in, or if the correct index is used for live video")
            return
        
        width, height = self.resolution
        self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cam.set(cv2.CAP_PROP_FPS, self.framerate)
        
        # Small buffer to reduce latency between capture and read
        self._cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read_frame(self):

        if self._cam is None:
            raise RuntimeError("Camera has not started. Call start() first.")

        ret, frame = self._cam.read()
        if not ret:
            print("Error: Could not grab frame!")
            raise RuntimeError("Could not read from camera!")
        
        return frame
    
    def get_frame_size(self):
        if self._cam is None:
            raise RuntimeError("Camera is not started. Cannot get frame size")

        width = int(self._cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return width, height
    
    def stop(self):
        if self._cam is not None:
            self._cam.release()
            self._cam = None
    
    def __enter__(self):
        self.start()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
