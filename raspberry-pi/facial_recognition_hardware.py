import cv2
import face_recognition
import pickle
import time
import threading
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime
import paho.mqtt.client as mqtt
import os
import sys

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "face_control/esp32/rotate"
MQTT_TOKEN = os.getenv("MQTT_TOKEN", "change_me_in_env")

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
GMAIL_TO  = os.getenv("GMAIL_TO")

CAM_INDEX = 0
CAM_WIDTH = 640
CAM_HEIGHT = 480

COOLDOWN = 30

ENCODINGS_PATH = "add exact path of your folder"

authorized_actions = {
    "Aman Vajpayee": "servo180",
    "jake paul": "spin360"
}

if not os.path.exists(ENCODINGS_PATH):
    print(f"[ERROR] Encodings file not found: {ENCODINGS_PATH}")
    sys.exit(1)

with open(ENCODINGS_PATH, "rb") as f:
    data = pickle.load(f)
print("[INFO] Loaded encodings.")

def send_email_alert(name, frame):
    try:
        success, im_buf = cv2.imencode(".jpg", frame)
        if not success:
            print("[EMAIL] Failed to encode frame to JPEG")
            return False
        image_bytes = im_buf.tobytes()
        msg = EmailMessage()
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_TO
        msg["Subject"] = f"Face Detected: {name}"
        body = f"{name} detected at {datetime.now().isoformat()}."
        msg.set_content(body)
        msg.add_attachment(image_bytes, maintype="image", subtype="jpeg",
                           filename=f"{name}_{int(time.time())}.jpg")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        print("[EMAIL] Sent.")
        return True
    except Exception as e:
        print("[EMAIL ERROR]", e)
        return False

_mqtt_client = None
_mqtt_lock = threading.Lock()

def _ensure_mqtt_client():
    global _mqtt_client
    with _mqtt_lock:
        if _mqtt_client is not None:
            return _mqtt_client
        try:
            client = mqtt.Client()
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_start()
            _mqtt_client = client
            print("[MQTT] Connected to broker:", MQTT_BROKER)
            return _mqtt_client
        except Exception as e:
            print("[MQTT ERROR] Could not connect to broker:", e)
            _mqtt_client = None
            return None

def trigger_motor_mqtt(angle=180, qos=1, wait_for_ack=True):
    client = _ensure_mqtt_client()
    payload = {"token": MQTT_TOKEN, "angle": int(angle)}
    if not client:
        try:
            tmp = mqtt.Client()
            tmp.connect(MQTT_BROKER, MQTT_PORT, 60)
            tmp.loop_start()
            info = tmp.publish(MQTT_TOPIC, json.dumps(payload), qos=qos)
            if wait_for_ack:
                info.wait_for_publish()
            tmp.loop_stop()
            tmp.disconnect()
            print("[MQTT] Temporary publish done", payload)
            return True
        except Exception as e:
            print("[MQTT ERROR] Temporary publish failed:", e)
            return False
    try:
        info = client.publish(MQTT_TOPIC, json.dumps(payload), qos=qos)
        print("[MQTT] Published:", payload, " rc:", getattr(info, "rc", None))
        if wait_for_ack:
            info.wait_for_publish()
        return True
    except Exception as e:
        print("[MQTT ERROR] publish failed:", e)
        try:
            client.reconnect()
            info = client.publish(MQTT_TOPIC, json.dumps(payload), qos=qos)
            if wait_for_ack:
                info.wait_for_publish()
            return True
        except Exception as e2:
            print("[MQTT ERROR] retry publish failed:", e2)
            return False

def trigger_motor_spin_command(qos=1):
    client = _ensure_mqtt_client()
    payload = {"token": MQTT_TOKEN, "spin": True}
    if not client:
        try:
            tmp = mqtt.Client()
            tmp.connect(MQTT_BROKER, MQTT_PORT, 60)
            tmp.loop_start()
            info = tmp.publish(MQTT_TOPIC, json.dumps(payload), qos=qos)
            info.wait_for_publish()
            tmp.loop_stop()
            tmp.disconnect()
            print("[MQTT] Temporary spin publish done", payload)
            return True
        except Exception as e:
            print("[MQTT ERROR] Temporary spin publish failed:", e)
            return False
    try:
        info = client.publish(MQTT_TOPIC, json.dumps(payload), qos=qos)
        print("[MQTT] Published spin:", payload, " rc:", getattr(info, "rc", None))
        info.wait_for_publish()
        return True
    except Exception as e:
        print("[MQTT ERROR] spin publish failed:", e)
        try:
            client.reconnect()
            info = client.publish(MQTT_TOPIC, json.dumps(payload), qos=qos)
            info.wait_for_publish()
            return True
        except Exception as e2:
            print("[MQTT ERROR] spin retry failed:", e2)
            return False

cooldowns = {}

cam = cv2.VideoCapture(CAM_INDEX)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

if not cam.isOpened():
    print("[ERROR] Could not open camera index:", CAM_INDEX)
    sys.exit(1)

print("[INFO] Camera opened. System ready.")

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            time.sleep(0.1)
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []
        for encoding in encodings:
            matches = face_recognition.compare_faces(data["encodings"], encoding)
            name = "Unknown"
            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                for i in matchedIdxs:
                    matched_name = data["names"][i]
                    counts[matched_name] = counts.get(matched_name, 0) + 1
                name = max(counts, key=counts.get)
            names.append(name)
        for ((top, right, bottom, left), name) in zip(boxes, names):
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if name != "Unknown":
                last = cooldowns.get(name, 0)
                now = time.time()
                if now - last >= COOLDOWN:
                    cooldowns[name] = now
                    print(f"[ACTION] Authorized face detected: {name}")
                    action = authorized_actions.get(name, "servo180")
                    if action == "servo180":
                        t1 = threading.Thread(target=trigger_motor_mqtt, args=(180,))
                        t1.daemon = True
                        t1.start()
                    elif action == "spin360":
                        t1 = threading.Thread(target=trigger_motor_spin_command)
                        t1.daemon = True
                        t1.start()
                    try:
                        frame_copy = frame.copy()
                        t2 = threading.Thread(target=send_email_alert, args=(name, frame_copy))
                        t2.daemon = True
                        t2.start()
                    except Exception as e:
                        print("[EMAIL THREAD ERROR]", e)
                else:
                    remaining = int(COOLDOWN - (now - last))
                    print(f"[INFO] Cooldown active for {name}: {remaining}s remaining")
        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
except KeyboardInterrupt:
    print("[INFO] Interrupted by user")
finally:
    try:
        if _mqtt_client:
            _mqtt_client.loop_stop()
            _mqtt_client.disconnect()
    except Exception:
        pass
    cam.release()
    cv2.destroyAllWindows()
    print("[INFO] Shutdown complete")
