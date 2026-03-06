"""TransformerConfig: all tunable parameters for the six-task transformer."""

import dataclasses
import json
from dataclasses import dataclass


@dataclass
class TransformerConfig:
    # Task 1 — default mode
    time_scale: float = 2.0
    amplitude_scale: float = 2.0
    lpf_default: float = 0.10

    # Task 2 — performance mode
    max_velocity: float = 0.32
    reversal_soften: float = 0.62
    height_blend: float = 0.75
    compress_bottom: int = 15
    compress_top: int = 92
    lpf_performance: float = 0.16
    timing_jitter_ms: int = 3

    # Task 3 — break mode
    break_amplitude_reduce: float = 0.40
    lpf_break: float = 0.30

    # Task 5 — cycle-aware dynamics
    cycle_dynamics_strength: float = 0.10
    cycle_dynamics_center: int = 50

    # Task 6 — beat-synced accents
    beat_accent_radius_ms: int = 40
    beat_accent_amount: int = 4

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TransformerConfig":
        valid = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "TransformerConfig":
        with open(path) as f:
            return cls.from_dict(json.load(f))
