# FaceGuard — Face Recognition Application

A secure AI-based desktop application for personnel identification and access monitoring. Detects and recognizes authorized personnel in real time using a webcam, IP camera, or CCTV/RTSP feed. Built with Python, PyQt6, insightface (RetinaFace + ArcFace), and PostgreSQL.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation — macOS](#installation--macos)
- [Installation — Windows](#installation--windows)
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
| **Dashboard** | Live stats — total registered, currently detected, today's entries, unknown detections, active cameras |
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
FaceRecognition/face_app/          ← project root (run all commands from here)
├── main.py                        # Entry point
├── config.ini                     # DB URL, model settings, paths
├── requirements.txt
├── schema.sql                     # PostgreSQL DDL + seed data
├── .env.example                   # Environment variable template
├── .venv/                         # Virtual environment (not committed)
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
    ├── photos/                    # Stored personnel photos (git-ignored)
    └── snapshots/                 # Unknown detection snapshots (git-ignored)
```

---

## Prerequisites

The following must be installed before setting up the application.

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or later | 3.12 recommended |
| PostgreSQL | 16 | Must be running before launching the app |
| Git | Any | To clone the repository |
| Disk space | ~1.5 GB | ~500 MB for insightface `buffalo_l` model + dependencies |
| Webcam / IP camera | — | Required for live recognition |

> **Internet access** is only needed once — on first launch to download the `buffalo_l` model (~500 MB). After that the app works fully offline.

---

## Installation — macOS

### Step 1 — Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2 — Install Python and PostgreSQL

```bash
brew install python@3.12 postgresql@16
```

### Step 3 — Start PostgreSQL

```bash
brew services start postgresql@16
```

Verify it is running:

```bash
brew services list | grep postgresql
```

You should see `postgresql@16` with status `started`.

### Step 4 — Add PostgreSQL to PATH (if `psql` is not found)

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Step 5 — Clone the repository

```bash
git clone https://github.com/arpitha93045/FaceRecognition.git
cd FaceRecognition/face_app
```

### Step 6 — Create a virtual environment

```bash
python3 -m venv .venv
```

### Step 7 — Activate the virtual environment

```bash
source .venv/bin/activate
```

Your prompt will change to show `(.venv)` — this means the venv is active.

### Step 8 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 9 — Grant camera permission

On first use, macOS will prompt for camera access. If it does not:

> System Settings → Privacy & Security → Camera → enable Terminal (or your IDE)

---

## Installation — Windows

### Step 1 — Install Python 3.12

Download the installer from [python.org](https://www.python.org/downloads/windows/).

During installation:
- Check **"Add Python to PATH"**
- Check **"Install pip"**

Verify in Command Prompt:

```cmd
python --version
pip --version
```

### Step 2 — Install PostgreSQL 16

Download the installer from [postgresql.org](https://www.postgresql.org/download/windows/).

During installation:
- Set a password for the `postgres` superuser — remember this
- Keep the default port **5432**
- Make sure **pgAdmin** and **Command Line Tools** are selected

After installation, add PostgreSQL `bin` to your system PATH:

> Control Panel → System → Advanced system settings → Environment Variables  
> Edit `Path` under System variables → Add:  
> `C:\Program Files\PostgreSQL\16\bin`

Verify:

```cmd
psql --version
```

### Step 3 — Install Git

Download from [git-scm.com](https://git-scm.com/download/win) and install with default settings.

### Step 4 — Clone the repository

```cmd
git clone https://github.com/arpitha93045/FaceRecognition.git
cd FaceRecognition\face_app
```

### Step 5 — Create a virtual environment

```cmd
python -m venv .venv
```

### Step 6 — Activate the virtual environment

```cmd
.venv\Scripts\activate
```

Your prompt will change to show `(.venv)` — this means the venv is active.

### Step 7 — Install Python dependencies

```cmd
pip install -r requirements.txt
```

> **Note:** If you see a `Microsoft Visual C++ required` error while installing `psycopg2-binary`, install the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and retry.

### Step 8 — Install Visual C++ Redistributable (if needed)

Some ONNX Runtime builds require the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe). Download and install if the app fails to start.

---

## Database Setup

Run these commands from inside `FaceRecognition/face_app/`. On Windows use `postgres` as the superuser instead of `$USER`.

**macOS / Linux:**

```bash
psql -U $USER -d postgres -c "CREATE USER face_user WITH PASSWORD 'password';"
psql -U $USER -d postgres -c "CREATE DATABASE facerecog_db OWNER face_user;"
psql -U $USER -d facerecog_db -f schema.sql
psql -U $USER -d facerecog_db -c "
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO face_user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO face_user;
  GRANT USAGE ON SCHEMA public TO face_user;
"
```

**Windows (Command Prompt):**

```cmd
psql -U postgres -d postgres -c "CREATE USER face_user WITH PASSWORD 'password';"
psql -U postgres -d postgres -c "CREATE DATABASE facerecog_db OWNER face_user;"
psql -U postgres -d facerecog_db -f schema.sql
psql -U postgres -d facerecog_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO face_user; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO face_user; GRANT USAGE ON SCHEMA public TO face_user;"
```

### Custom DB credentials

Edit `config.ini`:

```ini
[database]
url = postgresql://face_user:password@localhost:5432/facerecog_db
```

Or set the environment variable:

```bash
# macOS / Linux
export DATABASE_URL=postgresql://face_user:password@localhost:5432/facerecog_db

# Windows
set DATABASE_URL=postgresql://face_user:password@localhost:5432/facerecog_db
```

---

## Running the App

**macOS / Linux:**

```bash
cd /path/to/FaceRecognition/face_app
source .venv/bin/activate
python3 main.py
```

**Windows:**

```cmd
cd C:\path\to\FaceRecognition\face_app
.venv\Scripts\activate
python main.py
```

> **First launch:** The `buffalo_l` model pack (~500 MB) auto-downloads to `~/.insightface/models/` (macOS/Linux) or `C:\Users\<you>\.insightface\models\` (Windows). The splash screen shows "Loading AI models… Please wait." This only happens once.

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

> **macOS:** Grant Terminal camera access in System Settings → Privacy & Security → Camera  
> **Windows:** Grant camera access in Settings → Privacy & Security → Camera

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

- **Face embeddings** are encrypted with Fernet (AES-128-CBC) before storage. The key is auto-generated at `~/.faceapp/fernet.key` (macOS/Linux) or `C:\Users\<you>\.faceapp\fernet.key` (Windows) on first run — **back this file up**. If lost, all stored embeddings become unrecoverable.
- **Passwords** are hashed with bcrypt (cost 12) — never stored in plain text.
- **Audit logs** record every login, logout, and data modification.
- **Role separation** — Operators can view but cannot add/edit/delete personnel, manage users, or change settings.
- The app is designed for **local network use only** — no data is sent externally.

---

## Troubleshooting

| Problem | Platform | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'PyQt6'` | Both | Activate the venv first: `source .venv/bin/activate` (macOS) or `.venv\Scripts\activate` (Windows) |
| `Must construct a QApplication before a QWidget` | Both | Wrong directory — run `python3 main.py` from `FaceRecognition/face_app/`, not from inside a subdirectory |
| `pip: command not found` | macOS | Use `pip3` or `python3 -m pip` |
| `python: command not found` | macOS | Use `python3` |
| `externally-managed-environment` | macOS | Always use a venv: `python3 -m venv .venv` |
| `psycopg2-binary` build error | Windows | Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |
| `pg_config not found` | macOS | Run `brew install postgresql@16` and add to PATH |
| `psql` not recognized | Windows | Add `C:\Program Files\PostgreSQL\16\bin` to system PATH |
| `password is wrong` on login | Both | Re-run: `psql -U <user> -d facerecog_db -f schema.sql` |
| App closes after login | Both | Ensure PostgreSQL is running |
| PostgreSQL not running | macOS | `brew services start postgresql@16` |
| PostgreSQL not running | Windows | Open Services → find `postgresql-x64-16` → Start |
| Camera not working | macOS | Grant Terminal camera access in System Settings → Privacy & Security → Camera |
| Camera not working | Windows | Settings → Privacy & Security → Camera → allow app access |
| `buffalo_l` model slow to load | Both | Normal on first launch — ~500 MB downloads once |
| ONNX Runtime error | Windows | Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
