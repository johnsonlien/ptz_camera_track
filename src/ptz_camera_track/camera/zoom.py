import cv2

class ZoomStrategy:
    def __init__(self):
        self.zoom_strategies = {
            'affine': self.zoom_affine,
            #'crop': self.zoom_crop
        }

    def zoom(self, frame, zoom_scale=1.5, center=None, strategy="affine"):
        if strategy in self.zoom_strategies:
            kwargs = {'zoom_scale': zoom_scale, 'center': center}
            return self.zoom_strategies[strategy](frame, **kwargs)

        print(f"Warning: Zoom strategy '{strategy}' was not found.")
        return 
    
    @staticmethod
    def zoom_affine(frame, zoom_scale=1.5, center=None):
        height, width = frame.shape[:2]

        if center is None:
            cx, cy = width / 2.0, height / 2.0
        else:
            cx, cy = map(float, center)

        matrix = cv2.getRotationMatrix2D((cx, cy), 0, zoom_scale)

        return cv2.warpAffine(frame, matrix, (width, height), flags=cv2.INTER_LINEAR)

    def zoom_crop(frame, zoom_scale=1.5, center=None):
        print("zoom cropping")
        pass
