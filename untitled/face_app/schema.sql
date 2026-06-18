-- ============================================================
--  Face Recognition Application -- PostgreSQL Schema
-- ============================================================

-- ─────────────────────────────── ROLES & USERS ───────────────────────────────

CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255),
    role_id       INTEGER NOT NULL REFERENCES roles(id),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);

-- ─────────────────────────────── PERSONNEL ───────────────────────────────────

CREATE TABLE IF NOT EXISTS departments (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS personnel (
    id               SERIAL PRIMARY KEY,
    service_number   VARCHAR(100) UNIQUE NOT NULL,
    full_name        VARCHAR(255) NOT NULL,
    rank_designation VARCHAR(100),
    department_id    INTEGER REFERENCES departments(id),
    email            VARCHAR(255),
    phone            VARCHAR(50),
    notes            TEXT,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_personnel_service_number ON personnel(service_number);
CREATE INDEX IF NOT EXISTS idx_personnel_full_name      ON personnel(full_name);

-- ─────────────────────────────── PHOTOS ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS photos (
    id           SERIAL PRIMARY KEY,
    personnel_id INTEGER NOT NULL REFERENCES personnel(id) ON DELETE CASCADE,
    filename     VARCHAR(500) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    is_primary   BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_by  INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_photos_personnel ON photos(personnel_id);

-- ─────────────────────────────── FACE EMBEDDINGS ─────────────────────────────

CREATE TABLE IF NOT EXISTS face_embeddings (
    id             SERIAL PRIMARY KEY,
    personnel_id   INTEGER NOT NULL REFERENCES personnel(id) ON DELETE CASCADE,
    photo_id       INTEGER REFERENCES photos(id) ON DELETE SET NULL,
    embedding_enc  BYTEA NOT NULL,
    model_version  VARCHAR(100) NOT NULL DEFAULT 'buffalo_l',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_personnel ON face_embeddings(personnel_id);

-- ─────────────────────────────── CAMERAS ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS cameras (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    location     VARCHAR(500),
    source_type  VARCHAR(20) NOT NULL DEFAULT 'webcam',
    source_uri   VARCHAR(1000),
    device_index INTEGER,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    added_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────── ATTENDANCE / ENTRY LOGS ─────────────────────

CREATE TABLE IF NOT EXISTS attendance_logs (
    id            BIGSERIAL PRIMARY KEY,
    personnel_id  INTEGER NOT NULL REFERENCES personnel(id),
    camera_id     INTEGER REFERENCES cameras(id),
    event_type    VARCHAR(20) NOT NULL DEFAULT 'entry',
    confidence    NUMERIC(5,4),
    snapshot_path VARCHAR(1000),
    logged_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attendance_personnel ON attendance_logs(personnel_id);
CREATE INDEX IF NOT EXISTS idx_attendance_logged_at ON attendance_logs(logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_attendance_date      ON attendance_logs(logged_at);

-- ─────────────────────────────── UNKNOWN DETECTIONS ─────────────────────────

CREATE TABLE IF NOT EXISTS unknown_detections (
    id            BIGSERIAL PRIMARY KEY,
    camera_id     INTEGER REFERENCES cameras(id),
    snapshot_path VARCHAR(1000),
    best_score    NUMERIC(5,4),
    resolved      BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by   INTEGER REFERENCES users(id),
    resolved_at   TIMESTAMPTZ,
    notes         TEXT,
    detected_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_unknown_detected_at ON unknown_detections(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_unknown_resolved    ON unknown_detections(resolved);

-- ─────────────────────────────── AUDIT LOGS ──────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    username    VARCHAR(100),
    action      VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id   INTEGER,
    detail      JSONB,
    ip_address  INET,
    logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user      ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logged_at ON audit_logs(logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action    ON audit_logs(action);

-- ─────────────────────────────── SEED DATA ───────────────────────────────────

INSERT INTO roles (name, description)
VALUES
    ('admin',    'Full access: CRUD personnel, manage users, view all logs'),
    ('operator', 'View personnel, live feed, logs only')
ON CONFLICT (name) DO NOTHING;

-- Default admin password: ChangeMe123!  (bcrypt cost 12)
INSERT INTO users (username, password_hash, full_name, role_id)
SELECT 'admin',
       '$2b$12$8iI0pc0ZwZD0VXgbS0AzEe2pqyelALJOcCmXCChBSsBLEvMEdAfJy',
       'System Administrator',
       id
FROM roles WHERE name = 'admin'
ON CONFLICT (username) DO NOTHING;
