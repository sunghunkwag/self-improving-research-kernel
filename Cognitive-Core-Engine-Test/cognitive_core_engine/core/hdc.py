"""Pure Python hyperdimensional vector core used by the CCE package.

The integrated OMEGA-THDSE tree still imports ``HyperVector`` from this
module in the Cognitive Core Engine public API.  The FHRR arena-backed vector
implementation lives in ``fhrr.py``; this file preserves the older binary HDC
contract used by the CCE tests and modules.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, List, Optional


class HyperVector:
    """Binary 10,000-bit hypervector with deterministic seed construction."""

    DIM = 10000

    def __init__(self, val: Optional[int] = None) -> None:
        self.val = random.getrandbits(self.DIM) if val is None else val

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HyperVector):
            return NotImplemented
        return self.val == other.val

    def __hash__(self) -> int:
        return hash(self.val)

    @classmethod
    def from_seed(cls, seed_obj: Any) -> "HyperVector":
        digest = hashlib.sha256(str(seed_obj).encode("utf-8")).hexdigest()
        rng = random.Random(int(digest, 16))
        return cls(rng.getrandbits(cls.DIM))

    @classmethod
    def zero(cls) -> "HyperVector":
        return cls(0)

    def bind(self, other: "HyperVector") -> "HyperVector":
        return HyperVector(self.val ^ other.val)

    def fractional_bind(self, other: "HyperVector", role_index: int) -> "HyperVector":
        shifted = other.permute(role_index * 7 + 1)
        return HyperVector(self.val ^ shifted.val)

    def permute(self, shifts: int = 1) -> "HyperVector":
        shifts %= self.DIM
        if shifts == 0:
            return self
        mask = (1 << self.DIM) - 1
        return HyperVector(((self.val << shifts) & mask) | (self.val >> (self.DIM - shifts)))

    def similarity(self, other: "HyperVector") -> float:
        distance = (self.val ^ other.val).bit_count()
        return 1.0 - (distance / self.DIM)

    def cosine_similarity(self, other: "HyperVector") -> float:
        return 2.0 * self.similarity(other) - 1.0

    @staticmethod
    def bundle(vectors: List["HyperVector"]) -> "HyperVector":
        if not vectors:
            return HyperVector.zero()
        if len(vectors) == 1:
            return vectors[0]

        threshold = len(vectors) / 2.0
        counts = [0] * HyperVector.DIM
        for vector in vectors:
            bits = bin(vector.val)[2:].zfill(HyperVector.DIM)[::-1]
            for i, bit in enumerate(bits):
                if bit == "1":
                    counts[i] += 1

        result = 0
        for i, count in enumerate(counts):
            if count > threshold or (count == threshold and i % 2 == 0):
                result |= 1 << i
        return HyperVector(result)
