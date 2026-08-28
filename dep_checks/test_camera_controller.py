import cv2

from ptz_camera_track.camera.camera_controller import CameraController

def main():
    with CameraController(device_index=0, resolution=(640, 480), framerate=30) as camera:

        width, height = camera.get_frame_size()

        print(f"Camera opened at {width}x{height}")

        while True:
            frame = camera.read_frame()
            cv2.imshow("Camera Test", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
