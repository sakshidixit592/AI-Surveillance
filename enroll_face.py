"""
Face Enrollment Tool
====================
Run this script to register a new authorised person via webcam.
Usage:  python enroll_face.py
"""

import cv2
import face_recognition
import os

KNOWN_FACES_DIR = "known_faces"

def enroll():
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

    name = input("Enter person's name (e.g. John_Smith): ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    cap = cv2.VideoCapture(0)
    print("\n[INFO] Look directly at the camera.")
    print("[INFO] Press SPACE to capture, Q to quit.\n")

    captured = False
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Try to find a face in current frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)

        for (top, right, bottom, left) in locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 100), 2)
            cv2.putText(frame, "Face detected — press SPACE to save",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 100), 2)

        cv2.putText(frame, f"Enrolling: {name}", (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Face Enrollment", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(" ") and locations:
            save_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
            cv2.imwrite(save_path, frame)
            print(f"[SUCCESS] Face saved as: {save_path}")
            print("[INFO] Restart main.py to use the new face.")
            captured = True
            break
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    if not captured:
        print("[INFO] No face captured.")

if __name__ == "__main__":
    enroll()