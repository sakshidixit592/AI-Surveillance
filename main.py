"""
AI Surveillance System with Face Recognition & Intruder Alert
=============================================================
Features: Face Recognition, Intruder Alert, Beep Alarm,
          Snapshot Save, Video Recording, Telegram Alert, Email Alert
"""

import cv2
import face_recognition
import numpy as np
import os
import time
import datetime
import threading
import smtplib
import winsound
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import csv

CONFIG = {
    "known_faces_dir":        "known_faces",
    "alert_log_file":         "alert_log.json",
    "snapshot_dir":           "snapshots",
    "recordings_dir":         "recordings",
    "camera_index":           0,
    "detection_confidence":   0.5,
    "alert_cooldown_seconds": 30,
    "send_email_alerts":      True,
    "email_sender":           "sakshidixit592@gmail.com",
    "email_password":         "baus vrum lhxz weqc",
    "email_receiver":         "sakshidixit592@gmail.com",
    "smtp_server":            "smtp.gmail.com",
    "smtp_port":              587,
    "window_title":           "AI Surveillance System",
    "show_fps":               True,
    "save_snapshots":         True,
    "record_duration":        30,
    "attendance_file": "attendance.csv",
    "attendance_cooldown": 1800,
}

TELEGRAM_TOKEN   = "8726124944:AAFopKdQ1Es7f4uMf-5vMaGcwpDWzPa80kk"
TELEGRAM_CHAT_ID = "5639274988"

GREEN = (0, 255, 100)
RED   = (0, 60, 255)
WHITE = (255, 255, 255)
CYAN  = (255, 200, 0)


def load_known_faces(directory):
    known_encodings = []
    known_names = []
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"[INFO] Created '{directory}' folder.")
        return known_encodings, known_names
    for filename in os.listdir(directory):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(directory, filename)
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                name = os.path.splitext(filename)[0].replace("_", " ").title()
                known_names.append(name)
                print(f"[INFO] Loaded face: {name}")
    print(f"[INFO] Total authorised persons loaded: {len(known_names)}")
    return known_encodings, known_names


def send_telegram_alert(snapshot_path):
    try:
        with open(snapshot_path, "rb") as photo:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": "INTRUDER DETECTED!"},
                files={"photo": photo}
            )
        print("[ALERT] Telegram photo sent!")
        threading.Thread(target=send_email_alert, args=(snapshot_path, timestamp), daemon=True).start()
    except Exception as e:
        print(f"[ERROR] Telegram failed: {e}")


def send_email_alert(snapshot_path, timestamp):
    if not CONFIG["send_email_alerts"]:
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = CONFIG["email_sender"]
        msg["To"]      = CONFIG["email_receiver"]
        msg["Subject"] = f"INTRUDER ALERT - {timestamp}"
        msg.attach(MIMEText(f"Intruder detected at {timestamp}.", "plain"))
        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f"attachment; filename={os.path.basename(snapshot_path)}")
            msg.attach(part)
        server = smtplib.SMTP(CONFIG["smtp_server"], CONFIG["smtp_port"])
        server.starttls()
        server.login(CONFIG["email_sender"], CONFIG["email_password"])
        server.send_message(msg)
        server.quit()
        print("[ALERT] Email sent!")
    except Exception as e:
        print(f"[ERROR] Email failed: {e}")

attendance_log = {}

def mark_attendance(name):
    now = time.time()
    if name in attendance_log:
        if now - attendance_log[name] < CONFIG["attendance_cooldown"]:
            return
    attendance_log[name] = now
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(CONFIG["attendance_file"])
    with open(CONFIG["attendance_file"], "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Name", "Date", "Time"])
        writer.writerow([
            name,
            datetime.datetime.now().strftime("%Y-%m-%d"),
            datetime.datetime.now().strftime("%H:%M:%S")
        ])
    print(f"[ATTENDANCE] Marked: {name} at {timestamp}")
def log_alert(name, snapshot_path):
    log = []
    if os.path.exists(CONFIG["alert_log_file"]):
        with open(CONFIG["alert_log_file"], "r") as f:
            try:
                log = json.load(f)
            except:
                log = []
    log.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "person":    name,
        "snapshot":  snapshot_path,
    })
    with open(CONFIG["alert_log_file"], "w") as f:
        json.dump(log, f, indent=2)


def draw_hud(frame, fps, alert_active, person_count, intruder_count):
    h, w = frame.shape[:2]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    cv2.rectangle(frame, (0, 0), (w, 50), (20, 20, 20), -1)
    cv2.putText(frame, "AI SURVEILLANCE SYSTEM", (10, 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, CYAN, 2)
    cv2.putText(frame, timestamp, (w - 280, 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, WHITE, 1)
    cv2.rectangle(frame, (0, h - 45), (w, h), (20, 20, 20), -1)
    status_text  = "STATUS: ALERT - INTRUDER DETECTED" if alert_active else "STATUS: SECURE"
    status_color = RED if alert_active else GREEN
    cv2.putText(frame, status_text, (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
    if CONFIG["show_fps"]:
        cv2.putText(frame, f"FPS: {fps:.1f}", (w - 130, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
    cv2.putText(frame, f"Faces: {person_count}", (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
    cv2.putText(frame, f"Intruders: {intruder_count}", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED if intruder_count > 0 else WHITE, 1)
    if alert_active:
        cv2.rectangle(frame, (0, 0), (w, h), RED, 8)
    return frame


def run_surveillance():
    print("\n" + "=" * 55)
    print("  AI SURVEILLANCE SYSTEM  -  Starting up...")
    print("=" * 55)

    known_encodings, known_names = load_known_faces(CONFIG["known_faces_dir"])

    for folder in [CONFIG["snapshot_dir"], CONFIG["recordings_dir"]]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    cap = cv2.VideoCapture(CONFIG["camera_index"])
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    last_alert_time = 0
    frame_count     = 0
    fps_start       = time.time()
    fps             = 0.0
    process_every_n = 2
    video_writer    = None
    recording       = False
    record_end_time = 0

    print("[INFO] Camera opened. Press 'Q' to quit, 'S' to save snapshot.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % 30 == 0:
            fps       = 30 / (time.time() - fps_start)
            fps_start = time.time()

        alert_active   = False
        intruder_count = 0
        person_count   = 0

        if frame_count % process_every_n == 0:
            small     = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_small, face_locations)
            person_count   = len(face_locations)

            for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                top *= 2; right *= 2; bottom *= 2; left *= 2

                name        = "UNKNOWN"
                color       = RED
                is_intruder = True

                if known_encodings:
                    distances = face_recognition.face_distance(known_encodings, encoding)
                    best_idx  = np.argmin(distances)
                    if distances[best_idx] < CONFIG["detection_confidence"]:
                        name        = known_names[best_idx]
                        color       = GREEN
                        is_intruder = False
                        mark_attendance(name)

                if is_intruder:
                    winsound.Beep(1000, 1000)
                    intruder_count += 1
                    alert_active    = True

                    now = time.time()
                    if now - last_alert_time > CONFIG["alert_cooldown_seconds"]:
                        last_alert_time = now
                        timestamp       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        snap_path       = ""

                        if CONFIG["save_snapshots"]:
                            snap_path = os.path.join(
                                CONFIG["snapshot_dir"], f"intruder_{timestamp}.jpg")
                            cv2.imwrite(snap_path, frame)
                            print(f"[ALERT] INTRUDER DETECTED! Snapshot: {snap_path}")
                        if not recording:
                            rec_path = os.path.join(
                                CONFIG["recordings_dir"], f"intruder_{timestamp}.mp4v")
                            fourcc       = cv2.VideoWriter_fourcc(*'mp4v')
                            video_writer = cv2.VideoWriter(rec_path, fourcc, 20.0, (1280, 720))
                            recording       = True
                            record_end_time = time.time() + CONFIG["record_duration"]
                            print(f"[RECORD] Recording started: {rec_path}")

                        

                        threading.Thread(
                            target=send_telegram_alert,
                            args=(snap_path,),
                            daemon=True
                        ).start()

                        log_alert("UNKNOWN", snap_path)

                        threading.Thread(
                            target=send_email_alert,
                            args=(snap_path, timestamp),
                            daemon=False
                        ).start()

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, -1)
                cv2.putText(frame, name, (left + 6, bottom - 8),
                            cv2.FONT_HERSHEY_DUPLEX, 0.75, WHITE, 1)

                length = 20
                for (x1, y1, dx, dy) in [(left, top, 1, 1), (right, top, -1, 1),
                                          (left, bottom, 1, -1), (right, bottom, -1, -1)]:
                    cv2.line(frame, (x1, y1), (x1 + dx * length, y1), color, 3)
                    cv2.line(frame, (x1, y1), (x1, y1 + dy * length), color, 3)

        if recording:
            video_writer.write(frame)
            if time.time() > record_end_time:
                video_writer.release()
                recording    = False
                video_writer = None
                print("[RECORD] Recording saved.")

        frame = draw_hud(frame, fps, alert_active, person_count, intruder_count)
        cv2.imshow(CONFIG["window_title"], frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q"):
            break
        elif key == ord("s") or key == ord("S"):
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(CONFIG["snapshot_dir"], f"manual_{ts}.jpg")
            cv2.imwrite(path, frame)
            print(f"[INFO] Manual snapshot saved: {path}")

    if video_writer:
        video_writer.release()

    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Surveillance system stopped.")


if __name__ == "__main__":
    run_surveillance()