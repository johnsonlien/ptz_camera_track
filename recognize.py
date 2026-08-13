import os
import cv2
import face_recognition
import numpy as np
import logging 

KNOWN_FACES_DIR = "faces"
CAMERA_INDEX = 0          # change if you have multiple cameras (0, 1, 2...)
FRAME_RESIZE_SCALE = 0.25  # smaller = faster but less accurate
TOLERANCE = 0.6            # lower = stricter match


def load_known_faces(directory):
    """Load and encode all reference face images from a directory."""
    known_encodings = []
    known_names = []

    if not os.path.isdir(directory):
        print(f"Warning: '{directory}' not found. No known faces loaded.")
        return known_encodings, known_names

    for filename in os.listdir(directory):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        path = os.path.join(directory, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)

        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(os.path.splitext(filename)[0])
            print(f"Loaded face: {filename}")
        else:
            print(f"No face found in {filename}, skipping.")

    return known_encodings, known_names


def main():
    known_encodings, known_names = load_known_faces(KNOWN_FACES_DIR)

    video_capture = cv2.VideoCapture(CAMERA_INDEX)
    if not video_capture.isOpened():
        print("Error: could not open webcam. Check CAMERA_INDEX or USB connection.")
        return

    print("Starting webcam feed. Press 'q' to quit.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Error: failed to grab frame.")
            break

        screen_height, screen_width = frame.shape[:2]
        screen_center = (screen_width // 2, screen_height // 2)
        cv2.circle(frame, screen_center, 2, (255,255,255), 2)

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE_SCALE, fy=FRAME_RESIZE_SCALE)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces and compute encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"

            if known_encodings:
                matches = face_recognition.compare_faces(
                    known_encodings, face_encoding, tolerance=TOLERANCE
                )
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances) if len(face_distances) else None

                if best_match_index is not None and matches[best_match_index]:
                    name = known_names[best_match_index]

            # Scale coordinates back up to original frame size
            top = int(top / FRAME_RESIZE_SCALE)
            right = int(right / FRAME_RESIZE_SCALE)
            bottom = int(bottom / FRAME_RESIZE_SCALE)
            left = int(left / FRAME_RESIZE_SCALE)
            print(f"Top: {top} \tRight: {right}\tBottom: {bottom}\tLeft: {left}")
            # Draw bounding box and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(
                frame, name, (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1
            )

            face_center = ( (left + right) // 2, (top + bottom) // 2)
            cv2.circle(frame, face_center, 5, (0, 255,255), -1)
            
            # Draw a line from screen center to face center
            cv2.line(frame, screen_center, face_center, (0, 0, 255), 2)

            # Compute offset 
            offset_x = face_center[0] - screen_center[0]
            offset_y = face_center[1] - screen_center[1]
            distance = int((offset_x ** 2 + offset_y ** 2) ** 0.5)
            
            label = f"dx: {offset_x}  dy: {offset_y}  dist: {distance}px"

            cv2.putText(frame, label, (left, top-10), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.imshow("Face Recognition - press 'q' to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
