from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from face_engine.embedder import normalize
from face_engine.encryption import decrypt_embedding
from utils.config_loader import Config


@dataclass
class MatchResult:
    personnel_id: int
    service_number: str
    full_name: str
    score: float


class EmbeddingMatcher:
    def __init__(self):
        self._matrix: np.ndarray | None = None   # shape (N, 512)
        self._ids: list[int] = []
        self._service_numbers: list[str] = []
        self._names: list[str] = []
        self.last_best_score: float = 0.0

    def load(self, session) -> None:
        from db.models import FaceEmbedding, Personnel

        rows = (
            session.query(FaceEmbedding, Personnel)
            .join(Personnel, FaceEmbedding.personnel_id == Personnel.id)
            .filter(Personnel.is_active.is_(True))
            .all()
        )

        if not rows:
            self._matrix = None
            self._ids = []
            self._service_numbers = []
            self._names = []
            return

        vecs = []
        ids, snums, names = [], [], []
        for emb_row, person in rows:
            try:
                vec = decrypt_embedding(bytes(emb_row.embedding_enc))
                vecs.append(normalize(vec))
                ids.append(person.id)
                snums.append(person.service_number)
                names.append(person.full_name)
            except Exception:
                continue

        if vecs:
            self._matrix = np.vstack(vecs).astype(np.float32)
            self._ids = ids
            self._service_numbers = snums
            self._names = names
        else:
            self._matrix = None

    def match(self, query_vec: np.ndarray) -> Optional[MatchResult]:
        if self._matrix is None or len(self._ids) == 0:
            self.last_best_score = 0.0
            return None

        scores = self._matrix @ query_vec.astype(np.float32)
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])
        self.last_best_score = best_score

        if best_score >= Config.unknown_threshold:
            return MatchResult(
                personnel_id=self._ids[best_idx],
                service_number=self._service_numbers[best_idx],
                full_name=self._names[best_idx],
                score=best_score,
            )
        return None

    def search_top_k(self, query_vec: np.ndarray, k: int = 5) -> list[MatchResult]:
        if self._matrix is None or len(self._ids) == 0:
            return []

        scores = self._matrix @ query_vec.astype(np.float32)
        k = min(k, len(scores))
        top_indices = np.argsort(scores)[::-1][:k]

        return [
            MatchResult(
                personnel_id=self._ids[i],
                service_number=self._service_numbers[i],
                full_name=self._names[i],
                score=float(scores[i]),
            )
            for i in top_indices
        ]

    def reload(self, session) -> None:
        self.load(session)

    @property
    def count(self) -> int:
        return len(self._ids)
