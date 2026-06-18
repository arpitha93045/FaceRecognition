from __future__ import annotations

import numpy as np


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def extract_embedding(face) -> np.ndarray:
    """Extract and normalize ArcFace embedding from an insightface Face object."""
    return normalize(face.embedding.astype(np.float32))
