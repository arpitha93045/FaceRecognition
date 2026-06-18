---
description: Launch and drive the FaceGuard face recognition desktop app (PyQt6 + PostgreSQL + insightface)
---

# run-faceapp skill

## Environment requirements

- Working directory: repo root (`/path/to/untitled`)
- Virtual environment: `face_app/.venv/` (Python 3.10+)
- PostgreSQL 16 must be running: `brew services start postgresql@16`
- Database: `facerecog_db` with user `face_user` / password `password`
- insightface `buffalo_l` model cached at `~/.insightface/models/buffalo_l/` (auto-downloads on first run, ~500 MB)

## Launch command

```bash
face_app/.venv/bin/python face_app/main.py
```

Run from the repo root (`untitled/`). Do NOT cd into `face_app/` first — imports break.

## Startup sequence

1. Splash screen: "Loading AI models… Please wait." (~3–8s with cached models)
2. Login window appears
3. Default credentials: `admin` / `ChangeMe123!`
4. Main window with sidebar opens after successful login

## Key facts for driving the app

- **Login slot** is `LoginWindow._on_login` — triggered by pressing Enter or clicking Login
- **Main window** uses a `QStackedWidget` — pages are: Dashboard (0), Personnel (1), Live Recognition (2), Logs (3), Search by Image (4), Settings (5)
- **Settings page** is hidden for Operator role users
- **Live Recognition**: select camera from dropdown → click Start → camera feed appears with bounding boxes
- **Add Personnel**: Personnel page → "+ Add Personnel" → fill form → Photos tab → Browse Photos → Save
- **Search**: upload an image → click Search → top-5 results with similarity %

## Verifying it works

After login, the Dashboard should show stat cards (Total Registered, Today's Entries, etc.) with values ≥ 0. No error dialogs = healthy startup.

To verify face recognition:
1. Add a person with at least one clear face photo
2. Open Live Recognition → Start
3. Show that face to the webcam → green box with name should appear

## Known warnings (safe to ignore)

```
qt.qpa.fonts: Populating font family aliases took NNN ms. Replace uses of missing font family "Segoe UI"...
```
This is a harmless macOS font substitution warning.

```
OpenCV: not authorized to capture video (status 0), requesting...
```
Normal on first camera use — grant Terminal camera access in  
System Settings → Privacy & Security → Camera, then restart the app.

## If PostgreSQL is not running

```bash
brew services start postgresql@16
```

## If the venv is missing

```bash
python3 -m venv face_app/.venv
face_app/.venv/bin/pip install -r face_app/requirements.txt
```

## If the database is missing

```bash
psql -U $USER -d postgres -c "CREATE USER face_user WITH PASSWORD 'password';"
psql -U $USER -d postgres -c "CREATE DATABASE facerecog_db OWNER face_user;"
psql -U $USER -d facerecog_db -f face_app/schema.sql
psql -U $USER -d facerecog_db -c "
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO face_user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO face_user;
  GRANT USAGE ON SCHEMA public TO face_user;
"
```
