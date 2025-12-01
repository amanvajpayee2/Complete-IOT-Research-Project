# Face Recognition + ESP32 MQTT Servo Control + Gmail Alerts

This project integrates **Computer Vision**, **IoT**, and **Cloud Email Alerts** into a complete end‑to‑end system. A Raspberry Pi performs face recognition using an attached USB webcam, and upon detecting known users, triggers different hardware actions through an ESP32 over MQTT. The Pi also sends Gmail alerts with an attached snapshot for every authorized detection.

This README corresponds to your current repository structure:

```
Complete-IOT-Research-Project/
├── esp32/
│   └── esp_unified.ino
├── project_growth_documentation/
│   └── (PDFs, reports, documentation)
├── raspberry-pi/
│   ├── facial_recognition_hardware.py
│   ├── facial_recognition.py
│   ├── image_capture.py
│   ├── model_training.py
│   ├── requirements.txt
│   └── dataset_template/ (if added later)
├── README.md
```

---

##  Project Summary

This system:

* Detects faces using the **face_recognition** library on a Raspberry Pi.
* Uses an LG USB webcam for live video feed.
* Recognizes multiple users (e.g., *Aman Vajpayee*, *Jake Paul*).
* Triggers different ESP32 motor actions depending on who was detected:

  * **Aman Vajpayee → Servo rotates 180°**
  * **Jake Paul → 360° spin (two 180° sweeps)**
* Sends **MQTT messages** to an ESP32 subscribed to: `face_control/esp32/rotate`.
* ESP32 receives JSON payloads and controls a **SG90 servo motor**.
* Sends **Gmail alerts with snapshot attachments** whenever an authorized face appears.
* Implements cooldown to avoid repeated triggers.

---

##  Face Recognition Overview

The Pi runs:

* `image_capture.py` → Captures face images and organizes them into dataset folders.
* `model_training.py` → Converts captured images into `encodings.pickle` using face_recognition.
* `facial_recognition_hardware.py` → Main script:

  * Reads frames from webcam
  * Detects & identifies users
  * Sends MQTT commands to ESP
  * Sends Gmail alerts

### Supported Users and Actions

Defined inside `facial_recognition_hardware.py`:

```python
authorized_actions = {
    "Aman Vajpayee": "servo180",
    "jake paul": "spin360"
}
```

Each action maps to:

* `servo180` → Publish `{ "angle": 180 }`
* `spin360` → Publish `{ "spin": true }`

---

## 📡 MQTT Communication

The Pi publishes JSON messages:

```json
{"token": "aman_face_access", "angle": 180}
```

```json
{"token": "aman_face_access", "spin": true}
```

The ESP32 subscribes to:

```
face_control/esp32/rotate
```

The ESP32 code handles:

* Angle rotations
* 360° spin simulation
* LED blinking (optional)

MQTT broker used:

```
test.mosquitto.org:1883
```

---

## ESP32 Functionality (esp32/esp_unified.ino)

The ESP script:

* Connects to WiFi
* Connects to MQTT broker
* Subscribes to the project topic
* Parses JSON payloads using ArduinoJson
* Confirms security token
* Controls:

  * **Servo on GPIO 13**
  * Optional: **LED on GPIO 2**

Supported payload fields:

* `angle` → Servo rotation
* `spin` → Perform two 180° sweeps
* `led` → Blink LED

---

##  Email Alerts

The Pi uses Gmail SMTP to send:

* Authorized user name
* Timestamp
* Snapshot attachment (JPEG)

Requires a **Gmail App Password**.

---

##  Running the Raspberry Pi System

1. Activate the virtual environment:

```bash
source ~/face_rec/bin/activate
```

2. Install dependencies:

```bash
pip install -r raspberry-pi/requirements.txt
```

3. Train encodings:

```bash
python3 raspberry-pi/model_training.py
```

4. Run face recognition system:

```bash
python3 raspberry-pi/facial_recognition_hardware.py
```

---

##  Webcam Notes (LG Smart Cam)

If the webcam produces:

```
select() timeout
```

Fixes:

* Replug into USB 3.0 port (blue)
* Reboot Raspberry Pi
* Force MJPG mode if needed
* Ensure correct device `/dev/video0`

---

##  Dataset Structure (Do NOT upload real images)

```
dataset/
 ├── aman vajpayee/
 └── jake paul/
```

Each folder contains multiple images captured from the webcam.

This folder should remain **private**.

---

##  Security & Privacy

Do NOT commit:

* Gmail password
* `encodings.pickle` (contains facial embeddings)
* Real face images
* `.env` or secret tokens

Use `.gitignore` to prevent accidental uploads.

---

##  What This Project Demonstrates

This is a full integrated IOT + AI system showing:

* Edge AI (face detection)
* MQTT communication
* Microcontroller motor control
* Cloud email alerts
* Multi-user behavior mapping
* Secure token verification

It is suitable for:

* Academic submissions
* IoT research work
* Practical robotics demonstrations
* Home automation

---

##  Author

**Aman Vajpayee**
B.Tech CSE – NIIT University

---

# End of README.md
