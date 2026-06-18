import configparser
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class _Config:
    def __init__(self):
        self._parser = configparser.ConfigParser()
        cfg_path = Path(__file__).parent.parent / "config.ini"
        self._parser.read(str(cfg_path))

    # ── Database ──────────────────────────────────────────────────────────────
    @property
    def db_url(self) -> str:
        return os.environ.get("DATABASE_URL") or self._parser.get("database", "url")

    # ── Encryption ────────────────────────────────────────────────────────────
    @property
    def fernet_key_file(self) -> Path:
        raw = self._parser.get("encryption", "key_file", fallback="~/.faceapp/fernet.key")
        return Path(raw).expanduser()

    @property
    def fernet_key_env(self) -> str | None:
        return os.environ.get("FERNET_KEY") or None

    # ── Recognition ───────────────────────────────────────────────────────────
    @property
    def model_name(self) -> str:
        return self._parser.get("recognition", "model_name", fallback="buffalo_l")

    @property
    def similarity_threshold(self) -> float:
        return float(self._parser.get("recognition", "similarity_threshold", fallback="0.45"))

    @property
    def unknown_threshold(self) -> float:
        return float(self._parser.get("recognition", "unknown_threshold", fallback="0.40"))

    @property
    def top_k(self) -> int:
        return int(self._parser.get("recognition", "top_k", fallback="5"))

    @property
    def det_size(self) -> tuple[int, int]:
        w = int(self._parser.get("recognition", "det_size_w", fallback="640"))
        h = int(self._parser.get("recognition", "det_size_h", fallback="640"))
        return w, h

    # ── Camera ────────────────────────────────────────────────────────────────
    @property
    def default_device_index(self) -> int:
        return int(self._parser.get("camera", "default_device_index", fallback="0"))

    @property
    def frame_skip(self) -> int:
        return int(self._parser.get("camera", "frame_skip", fallback="2"))

    @property
    def reconnect_delay(self) -> float:
        return float(self._parser.get("camera", "reconnect_delay_sec", fallback="3"))

    # ── App paths ─────────────────────────────────────────────────────────────
    @property
    def photo_storage_dir(self) -> Path:
        raw = self._parser.get("app", "photo_storage_dir", fallback="./data/photos")
        p = Path(raw)
        if not p.is_absolute():
            p = Path(__file__).parent.parent / raw.lstrip("./")
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def snapshot_dir(self) -> Path:
        raw = self._parser.get("app", "snapshot_dir", fallback="./data/snapshots")
        p = Path(raw)
        if not p.is_absolute():
            p = Path(__file__).parent.parent / raw.lstrip("./")
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def log_level(self) -> str:
        return self._parser.get("app", "log_level", fallback="INFO")


Config = _Config()
