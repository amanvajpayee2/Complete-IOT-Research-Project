README.md (copy-paste this into your repo root)
# Face Recognition + MQTT Servo Control + Gmail Alerts

A project that runs face recognition on a Raspberry Pi using a USB webcam, sends MQTT commands to an ESP32 to control a servo (or blink an LED), and sends Gmail alerts with snapshot attachments when an authorized face is detected.

## Features

- Multi-user face recognition (train faces using `image_capture.py` and `model_training.py`).
- Per-user actions: different users can trigger different hardware behaviors (e.g. 180° servo, 360° spin approximation).
- MQTT-based command relay via a broker (tested with `test.mosquitto.org`).
- ESP32 sketch supports JSON payloads: `{"token": "...", "angle":180}`, `{"token":"...","spin":true}`, `{"token":"...","led":true}`.
- Email alerts with JPEG attachment using Gmail (SMTP SSL + App Password).
- Uses `paho-mqtt`, `face-recognition`, and `opencv-python`.

---

## Repo structure



face-recognition-esp-mqtt/
├── esp32/
│ └── esp_unified.ino
├── raspberry-pi/
│ ├── facial_recognition_hardware.py
│ ├── facial_recognition.py
│ ├── model_training.py
│ ├── image_capture.py
│ └── requirements.txt
├── docs/
│ └── project-report.md
├── dataset_template/
├── .gitignore
├── LICENSE
├── README.md
└── CONTRIBUTING.md


---

## Quick start (Raspberry Pi)

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv ~/face_rec
   source ~/face_rec/bin/activate
   

Install packages:

pip install --upgrade pip
pip install -r raspberry-pi/requirements.txt


Prepare dataset:

Use raspberry-pi/image_capture.py to capture images for each person.

Place images in raspberry-pi/dataset/<person_name>/.

Train encodings:

source ~/face_rec/bin/activate
python3 raspberry-pi/model_training.py


This produces encodings.pickle in the working directory (do not commit it to git).

Upload the ESP32 sketch (esp32/esp_unified.ino) to your ESP32 via Arduino IDE.

Configure raspberry-pi/facial_recognition_hardware.py:

Set the ENCODINGS_PATH to your encodings.pickle absolute path.

Set MQTT broker, token, and Gmail credentials as environment variables or in a .env (recommended).

Run the main script:

source ~/face_rec/bin/activate
python3 raspberry-pi/facial_recognition_hardware.py

ESP32

Libraries required: PubSubClient, ArduinoJson, ESP32Servo

The sketch subscribes to face_control/esp32/rotate and checks for a shared token.

Supported JSON:

{"token":"<token>","angle":180} → rotate servo to angle

{"token":"<token>","spin":true} → perform two 180° sweeps (SG90 approximation)

{"token":"<token>","led":true,"times":3,"ms":200} → blink LED

Security & privacy

Do not commit encodings.pickle or real face images. They are personal data.

Use Gmail App Passwords for SMTP and store secrets in environment variables.

Use a secure MQTT broker (TLS + auth) for production.

What to include in the repo and what not to include

Include:

Source code (ESP & Pi scripts)

docs/project-report.md

Example dataset structure (no images)

requirements.txt, README.md, LICENSE

Do not include:

encodings.pickle (models containing user faces)

Any real CCTV footage, raw images of people, or private credentials

License

This repository is released under the MIT License. See LICENSE for details.


---

# 3 — Supporting files

### `.gitignore` (paste at repo root)

Python

pycache/
*.pyc
*.pyo
*.pyd
env/
venv/
face_rec/
*.egg-info/
dist/
build/

Virtual envs

.env
.envrc
.venv
face_rec/

OS

.DS_Store
thumbs.db

Jupyter

.ipynb_checkpoints

VSCode

.vscode/

Python dependencies

pip-log.txt
pip-delete-this-directory.txt

Large / sensitive

encodings.pickle
dataset/
*.db
*.sqlite

Arduino / build

*.bin
*.elf
*.hex


### `CONTRIBUTING.md`
```markdown
# Contributing

Thanks for your interest. If you want to contribute:

- Fork the repository and create feature branches.
- Run `black` (or your formatting tool) and ensure code passes basic linting.
- Do not add any images with faces to the repo.
- Use PRs with descriptive titles and link to issues.

requirements.txt (put under raspberry-pi/)
opencv-python
face-recognition
imutils
paho-mqtt
numpy


Note: face-recognition may require system packages (build-essential, cmake, libjpeg-dev, etc.) on Raspberry Pi.

LICENSE (MIT)
MIT License

Copyright (c) 2025 Aman Vajpayee

Permission is hereby granted, free of charge, to any person obtaining a copy...
[full MIT license text here]


(Use standard MIT text; replace copyright.)
