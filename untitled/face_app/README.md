# FaceGuard — Face Recognition Application

A secure AI-based desktop application for personnel identification and access monitoring. Detects and recognizes authorized personnel in real time using a webcam, IP camera, or CCTV/RTSP feed. Built with Python, PyQt6, insightface (RetinaFace + ArcFace), and PostgreSQL.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Running the App](#running-the-app)
- [Default Credentials](#default-credentials)
- [Usage Guide](#usage-guide)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)

---

## Features

| Feature | Description |
|---|---|
| **Personnel Database** | Add, edit, delete personnel with multiple face photos per person |
| **Real-time Recognition** | Webcam / IP camera / RTSP stream with live bounding boxes, name, and confidence score |
| **Unknown Detection** | Captures snapshot, logs, and alerts on unregistered faces |
| **Attendance Logs** | Entry/exit events with timestamp, camera location, and confidence |
| **Search by Image** | Upload a photo and find the top-5 matching personnel records |
| **Dashboard** | Live stats — total registered, today's entries, unknown detections, active cameras |
| **Role-based Access** | Admin (full access) and Operator (read-only) roles |
| **Encrypted Embeddings** | AES/Fernet-encrypted face vectors stored in PostgreSQL |
| **Audit Logs** | Every login, logout, and data change is logged |
| **Fully Offline** | Works on a local network with no internet required after first model download |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| UI | PyQt6 |
| Face Detection | RetinaFace (via insightface `buffalo_l`) |
| Face Recognition | ArcFace (via insightface `buffalo_l`) |
| Inference | ONNX Runtime (CPU) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x |
| DB Driver | psycopg2-binary |
| Encryption | cryptography (Fernet / AES-128-CBC) |
| Password Hashing | bcrypt (cost 12) |
| Video Capture | OpenCV |

---

## Project Structure

```
face_app/
├── main.py                        # Entry point
├── config.ini                     # DB URL, model settings, paths
├── requirements.txt
├── schema.sql                     # PostgreSQL DDL + seed data
├── .env.example                   # Environment variable template
│
├── db/
│   ├── connection.py              # SQLAlchemy engine + session_scope()
│   └── models.py                  # ORM models (9 tables)
│
├── face_engine/
│   ├── detector.py                # FaceDetector — RetinaFace wrapper
│   ├── embedder.py                # ArcFace embedding + L2 normalize
│   ├── matcher.py                 # EmbeddingMatcher — in-RAM cosine similarity
│   └── encryption.py             # Fernet encrypt/decrypt embeddings
│
├── camera/
│   ├── source.py                  # CameraSource ABC
│   ├── webcam.py                  # WebcamSource(device_index)
│   └── ip_camera.py               # IPCameraSource(rtsp_url) with auto-reconnect
│
├── security/
│   ├── auth.py                    # AuthSession singleton — bcrypt login
│   ├── rbac.py                    # @requires_role decorator
│   └── audit.py                   # write_audit_log() helper
│
├── ui/
│   ├── app.py                     # QApplication + dark stylesheet
│   ├── styles/main.qss            # Catppuccin dark theme
│   ├── windows/                   # All main pages
│   ├── dialogs/                   # Add/edit person, photo upload, unknown alert
│   └── workers/                   # QThread workers for camera loop + image search
│
├── utils/
│   ├── config_loader.py           # Config singleton
│   └── image_utils.py             # numpy↔QPixmap, draw bounding boxes
│
└── data/
    ├── photos/                    # Stored personnel photos
    └── snapshots/                 # Unknown detection snapshots
```

---

## Prerequisites

- **macOS / Windows / Linux**
- **Python 3.10 or later** (3.14 confirmed working)
- **PostgreSQL 16**
- ~1 GB disk space for the insightface `buffalo_l` model (downloads once on first launch)

### macOS (Homebrew)

```bash
brew install python@3.12 postgresql@16
brew services start postgresql@16
```

---

## Installation

```bash
# 1. Clone / navigate to the project root
cd /path/to/untitled

# 2. Create a virtual environment
python3 -m venv face_app/.venv

# 3. Install dependencies
face_app/.venv/bin/pip install -r face_app/requirements.txt
```

---

## Database Setup

```bash
# Create the database user and database (run once)
psql -U $USER -d postgres -c "CREATE USER face_user WITH PASSWORD 'password';"
psql -U $USER -d postgres -c "CREATE DATABASE facerecog_db OWNER face_user;"

# Load the schema and seed data
psql -U $USER -d facerecog_db -f face_app/schema.sql

# Grant permissions
psql -U $USER -d facerecog_db -c "
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO face_user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO face_user;
  GRANT USAGE ON SCHEMA public TO face_user;
"
```

### Custom DB credentials

Edit `face_app/config.ini`:

```ini
[database]
url = postgresql://face_user:password@localhost:5432/facerecog_db
```

Or set the environment variable:

```bash
export DATABASE_URL=postgresql://face_user:password@localhost:5432/facerecog_db
```

---

## Running the App

```bash
# From the project root (untitled/)
face_app/.venv/bin/python face_app/main.py
```

> **First launch:** The `buffalo_l` model pack (~500 MB) auto-downloads to `~/.insightface/models/` — the splash screen shows "Loading AI models… Please wait." This only happens once.

---

## Default Credentials

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `ChangeMe123!` |

**Change this password immediately** after first login via Settings → User Management → Change Password.

---

## Usage Guide

### 1. Add Personnel

1. Go to **Personnel** in the sidebar
2. Click **+ Add Personnel**
3. Fill in Service Number, Full Name, Rank, Department
4. Switch to the **Photos / Face Data** tab
5. Click **Browse Photos…** and select one or more clear face photos
6. Each photo is validated for a detected face before saving
7. Click **Save** — face embeddings are extracted, encrypted, and stored

### 2. Live Recognition

1. Go to **Live Recognition**
2. Select camera from the dropdown (default: Webcam #0)
3. Click **Start**
4. Recognized personnel appear with green bounding boxes (Name + Confidence)
5. Unknown faces appear with red boxes and trigger an alert dialog + snapshot

> **macOS camera permission:** On first use, grant Terminal camera access in  
> System Settings → Privacy & Security → Camera

### 3. Search by Image

1. Go to **Search by Image**
2. Click **Upload Image** and select a photo
3. Click **Search** — top 5 matching personnel are shown with similarity percentages

### 4. View Logs

- **Attendance Logs** — filter by date range, export to CSV
- **Unknown Detections** — review and resolve unknown snapshots

### 5. Add Cameras (Admin)

1. Go to **Settings → Camera Management**
2. Click **+ Add Camera**
3. For RTSP/IP cameras enter the stream URL (e.g. `rtsp://user:pass@192.168.1.100:554/stream`)

---

## Security Notes

- **Face embeddings** are encrypted with Fernet (AES-128-CBC) before storage. The key is auto-generated at `~/.faceapp/fernet.key` on first run — **back this file up**. If lost, all stored embeddings become unrecoverable.
- **Passwords** are hashed with bcrypt (cost 12) — never stored in plain text.
- **Audit logs** record every login, logout, and data modification.
- **Role separation** — Operators can view but cannot add/edit/delete personnel, manage users, or change settings.
- The app is designed for **local network use only** — no data is sent externally.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `pip: command not found` | Use `pip3` or `python3 -m pip` |
| `externally-managed-environment` | Use a venv: `python3 -m venv face_app/.venv` |
| `psycopg2-binary` build error | Install PostgreSQL dev headers or use Python ≥ 3.10 |
| `password is wrong` on login | Re-run: `psql -U $USER -d facerecog_db -f face_app/schema.sql` |
| App closes after login | Ensure PostgreSQL is running: `brew services start postgresql@16` |
| Camera not working (macOS) | Grant Terminal camera access in System Settings → Privacy & Security → Camera |
| `buffalo_l` model slow to load | Normal on first launch — ~500 MB downloads once to `~/.insightface/models/` |
| `pg_config not found` | Install PostgreSQL: `brew install postgresql@16` |
