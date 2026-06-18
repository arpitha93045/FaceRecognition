from __future__ import annotations

import base64
import os
from pathlib import Path

import numpy as np
from cryptography.fernet import Fernet

from utils.config_loader import Config

_fernet: Fernet | None = None


def _load_or_create_key() -> bytes:
    env_key = Config.fernet_key_env
    if env_key:
        return env_key.encode() if isinstance(env_key, str) else env_key

    key_path = Config.fernet_key_file
    if key_path.exists():
        return key_path.read_bytes().strip()

    key_path.parent.mkdir(parents=True, exist_ok=True)
    new_key = Fernet.generate_key()
    key_path.write_bytes(new_key)
    os.chmod(key_path, 0o600)
    print(f"[SECURITY] New encryption key generated: {key_path}")
    print("[SECURITY] BACK UP THIS FILE — losing it makes all stored embeddings unrecoverable.")
    return new_key


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def encrypt_embedding(vec: np.ndarray) -> bytes:
    raw = vec.astype(np.float32).tobytes()
    return get_fernet().encrypt(raw)


def decrypt_embedding(data: bytes) -> np.ndarray:
    raw = get_fernet().decrypt(data)
    return np.frombuffer(raw, dtype=np.float32)
