import cv2
import logging

class ZoomStrategy:
    def __init__(self):
        self.zoom_strategies = {
            'affine': ZoomStrategy.zoom_affine,
            #'crop': ZoomStrategy.zoom_crop
        }

    def zoom(self, frame, zoom_scale : float = 1.5, center=None, strategy="affine"):
        if strategy in self.zoom_strategies:
            kwargs = {'zoom_scale': zoom_scale, 'center': center}
            return self.zoom_strategies[strategy](frame, **kwargs)

        logging.warning(f"Warning: Zoom strategy '{strategy}' was not found.")
        return frame 
    
    @staticmethod
    def zoom_affine(frame, zoom_scale : float = 1.5, center : tuple[int, int] = None):
        height, width = frame.shape[:2]
        
        if zoom_scale <= 1.0:
            return frame

        if center is None:
            cx, cy = width / 2.0, height / 2.0
        else:
            cx, cy = map(float, center)

        matrix = cv2.getRotationMatrix2D((cx, cy), 0, zoom_scale)

        return cv2.warpAffine(frame, matrix, (width, height), flags=cv2.INTER_LINEAR)
    
#    @staticmethod
#    def zoom_crop(frame, zoom_scale : float = 1.5, center : tuple[int, int] = None):
#        height, width = frame.shape[:2]
#
#        if zoom_scale <= 1.0:
#            return frame
#        
#
#        scaled_width, scaled_height = int(width / zoom_scale), int(height / zoom_scale)
#        
#        if center is None:
#            center = (0, 0)
#
#        if center is None:
#            y1 = int((height - scaled_height) / 2)
#            y2 = y1 + scaled_height
#            x1 = int(( width - scaled_width) / 2)
#            x2 = x1 + scaled_width
#            cropped = frame[y1:y2, x1:x2]
#
#
