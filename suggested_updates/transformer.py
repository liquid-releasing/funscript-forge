"""FunscriptTransformer: applies the six-task transformation pipeline.

Replaces the procedural six_task_transformer.py with a class that can be
driven from a CLI or a UI.

Typical usage::

    transformer = FunscriptTransformer()
    transformer.load_funscript("input.funscript")
    transformer.load_assessment_from_file("assessment.json")
    transformer.load_manual_overrides(
        perf_path="manual_performance.json",
        break_path="manual_break.json",
        raw_path="raw_windows.json",
    )
    transformer.merge_windows()
    transformer.transform()
    transformer.save("output.funscript")
"""

import bisect
import copy
import json
import math
import os
from typing import List, Optional, Tuple

from models import AssessmentResult
from utils import low_pass_filter, overlaps, parse_timestamp
from .config import TransformerConfig

# Type alias for a window stored as (start_ms, end_ms)
_WindowPair = Tuple[int, int]
# With optional label: (start_ms, end_ms, label)
_WindowTriple = Tuple[int, int, str]


class FunscriptTransformer:
    """Applies the six-task transformation pipeline to a funscript.

    Tasks
    -----
    1. Default mode  — half-speed timing + double amplitude outside performance windows
    2. Performance   — velocity limiting, reversal softening, compression
    3. Break         — pull positions toward center, reduce amplitude
    4. Raw preserve  — copy original actions verbatim inside raw windows
    5. Cycle dynamics — cosine-shaped push/pull aligned to cycle midpoints
    6. Beat accents  — small nudges near beat times
    """

    def __init__(self, config: Optional[TransformerConfig] = None):
        self.config = config or TransformerConfig()

        self._data: dict = {}
        self._actions: list = []
        self._original_actions: list = []
        self._log_lines: List[str] = []

        # Auto windows (from assessment)
        self._auto_perf: List[_WindowPair] = []
        self._auto_break: List[_WindowPair] = []
        self._auto_default: List[_WindowPair] = []

        # Manual overrides (from JSON files with HH:MM:SS.mmm timestamps)
        self._manual_perf: List[_WindowTriple] = []
        self._manual_break: List[_WindowTriple] = []
        self._raw_windows: List[_WindowTriple] = []

        # Merged final windows (populated by merge_windows)
        self._perf_windows: List[_WindowPair] = []
        self._break_windows: List[_WindowPair] = []
        self._default_windows: List[_WindowPair] = []

        self._cycles: list = []   # [{"start": ms, "end": ms}, ...]
        self._beats: list = []    # [{"time": ms}, ...]

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_funscript(self, path: str) -> None:
        """Load the source funscript to be transformed."""
        with open(path) as f:
            self._data = json.load(f)
        self._actions = self._data["actions"]
        self._original_actions = copy.deepcopy(self._actions)
        self._log(f"Loaded funscript: {path} ({len(self._actions)} actions)")

    def load_assessment(self, assessment: AssessmentResult) -> None:
        """Load auto windows and cycles from an AssessmentResult object."""
        aw = assessment.auto_mode_windows
        self._auto_perf = [(w.start_ms, w.end_ms) for w in aw.get("performance", [])]
        self._auto_break = [(w.start_ms, w.end_ms) for w in aw.get("break", [])]
        self._auto_default = [(w.start_ms, w.end_ms) for w in aw.get("default", [])]
        self._cycles = [{"start": c.start_ms, "end": c.end_ms} for c in assessment.cycles]
        self._log(
            f"Loaded assessment: {len(self._auto_perf)} perf, "
            f"{len(self._auto_break)} break, "
            f"{len(self._auto_default)} default windows, "
            f"{len(self._cycles)} cycles"
        )

    def load_assessment_from_file(self, path: str) -> None:
        """Load auto windows and cycles from a saved assessment JSON file."""
        with open(path) as f:
            d = json.load(f)
        aw = d.get("auto_mode_windows", {})
        self._auto_perf = [(w["start_ms"], w["end_ms"]) for w in aw.get("performance", [])]
        self._auto_break = [(w["start_ms"], w["end_ms"]) for w in aw.get("break", [])]
        self._auto_default = [(w["start_ms"], w["end_ms"]) for w in aw.get("default", [])]
        self._cycles = [
            {"start": c["start_ms"], "end": c["end_ms"]} for c in d.get("cycles", [])
        ]
        self._log(f"Loaded assessment from {path}")

    def load_beats_from_file(self, path: str) -> None:
        """Load beat times from a JSON file (optional — enables Task 6)."""
        if not os.path.exists(path):
            self._log(f"Beats file not found: {path}. Task 6 inactive.")
            return
        with open(path) as f:
            self._beats = json.load(f)
        self._log(f"Loaded {len(self._beats)} beats from {path}")

    def load_manual_overrides(
        self,
        perf_path: Optional[str] = None,
        break_path: Optional[str] = None,
        raw_path: Optional[str] = None,
    ) -> None:
        """Load manual override windows from JSON files with HH:MM:SS timestamps."""
        if perf_path:
            self._manual_perf = self._load_ts_file(perf_path, "Manual performance")
        if break_path:
            self._manual_break = self._load_ts_file(break_path, "Manual break")
        if raw_path:
            self._raw_windows = self._load_ts_file(raw_path, "Raw windows")

    # ------------------------------------------------------------------
    # Window merging
    # ------------------------------------------------------------------

    def merge_windows(self) -> dict:
        """Merge manual + auto windows (manual overrides auto on overlap).

        Returns a snapshot dict suitable for saving or inspection.
        """
        auto_perf_f, removed_p = self._filter_auto(
            self._auto_perf, self._manual_perf, "Performance"
        )
        auto_break_f, removed_b = self._filter_auto(
            self._auto_break, self._manual_break, "Break"
        )

        self._perf_windows = [(s, e) for s, e, _ in self._manual_perf] + auto_perf_f
        self._break_windows = [(s, e) for s, e, _ in self._manual_break] + auto_break_f
        self._default_windows = list(self._auto_default)

        self._log(
            f"Final windows — performance: {len(self._perf_windows)}, "
            f"break: {len(self._break_windows)}, "
            f"default: {len(self._default_windows)}, "
            f"raw: {len(self._raw_windows)}"
        )

        return {
            "performance": [{"start_ms": s, "end_ms": e} for s, e in self._perf_windows],
            "break": [{"start_ms": s, "end_ms": e} for s, e in self._break_windows],
            "default": [{"start_ms": s, "end_ms": e} for s, e in self._default_windows],
            "raw": [{"start_ms": s, "end_ms": e} for s, e, _ in self._raw_windows],
        }

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def transform(self) -> list:
        """Run all six tasks and return the transformed actions list."""
        if not self._perf_windows and not self._break_windows and not self._default_windows:
            self.merge_windows()

        cfg = self.config
        actions = self._actions
        raw_ms: List[_WindowPair] = [(s, e) for s, e, _ in self._raw_windows]

        cycle_ranges = [(c["start"], c["end"]) for c in self._cycles]
        cycle_midpoints = [(c["start"] + c["end"]) / 2 for c in self._cycles]
        beat_times = sorted(b["time"] for b in self._beats)

        # --- Task 1: half-speed timing (outside performance windows) ---
        for a in actions:
            if not self._in(a["at"], self._perf_windows):
                a["at"] = int(a["at"] * cfg.time_scale)

        # --- Task 1: double amplitude ---
        for a in actions:
            centered = a["pos"] - 50
            a["pos"] = max(0, min(100, int(50 + centered * cfg.amplitude_scale)))

        # --- Tasks 2–6: main per-action loop ---
        for i in range(2, len(actions)):
            t = actions[i]["at"]

            # Task 4 — raw preserve (highest priority)
            if self._in(t, raw_ms):
                actions[i]["at"] = self._original_actions[i]["at"]
                actions[i]["pos"] = self._original_actions[i]["pos"]
                continue

            # Task 2 — performance mode
            if self._in(t, self._perf_windows):
                dt = actions[i]["at"] - actions[i - 1]["at"]
                if abs(dt) < cfg.timing_jitter_ms:
                    actions[i]["at"] = actions[i - 1]["at"] + cfg.timing_jitter_ms

                p0 = actions[i - 1]["pos"]
                p1 = actions[i]["pos"]
                dt = max(1, actions[i]["at"] - actions[i - 1]["at"])
                vel = (p1 - p0) / dt

                if abs(vel) > cfg.max_velocity:
                    p1 = p0 + math.copysign(cfg.max_velocity * dt, vel)
                    actions[i]["pos"] = int(p1)

                dir1 = actions[i - 1]["pos"] - actions[i - 2]["pos"]
                dir2 = actions[i]["pos"] - actions[i - 1]["pos"]
                if dir1 * dir2 < 0:
                    softened = actions[i - 1]["pos"] + dir2 * (1 - cfg.reversal_soften)
                    blended = softened * (1 - cfg.height_blend) + actions[i]["pos"] * cfg.height_blend
                    blended = max(cfg.compress_bottom, min(cfg.compress_top, blended))
                    actions[i]["pos"] = int(blended)

            # Task 3 — break mode
            elif self._in(t, self._break_windows):
                p = actions[i]["pos"]
                actions[i]["pos"] = int(p + (50 - p) * cfg.break_amplitude_reduce)

            # Task 5 — cycle-aware dynamics
            factor = self._cycle_factor(t, cycle_ranges, cycle_midpoints)
            if factor > 0:
                p = actions[i]["pos"]
                delta = (p - cfg.cycle_dynamics_center) * cfg.cycle_dynamics_strength * factor
                actions[i]["pos"] = max(0, min(100, int(p + delta)))

            # Task 6 — beat-synced accents
            if self._near_beat(t, beat_times, cfg.beat_accent_radius_ms):
                p = actions[i]["pos"]
                nudge = cfg.beat_accent_amount if p >= 50 else -cfg.beat_accent_amount
                actions[i]["pos"] = max(0, min(100, p + nudge))

        # --- Final smoothing pass ---
        positions = [a["pos"] for a in actions]
        strengths = []
        for a in actions:
            t = a["at"]
            if self._in(t, raw_ms):
                strengths.append(0.0)
            elif self._in(t, self._perf_windows):
                strengths.append(cfg.lpf_performance)
            elif self._in(t, self._break_windows):
                strengths.append(cfg.lpf_break)
            else:
                strengths.append(cfg.lpf_default)

        smoothed = low_pass_filter(positions, strengths)
        for i, p in enumerate(smoothed):
            actions[i]["pos"] = int(p)

        self._log("Transform complete.")
        return actions

    def save(self, path: str) -> None:
        """Write the transformed funscript to disk."""
        self._data["actions"] = self._actions
        with open(path, "w") as f:
            json.dump(self._data, f, indent=2)
        self._log(f"Saved output: {path}")

    def get_log(self) -> List[str]:
        """Return all log messages produced during this session."""
        return list(self._log_lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_ts_file(self, path: str, label: str) -> List[_WindowTriple]:
        if not os.path.exists(path):
            self._log(f"{label}: file not found, treating as empty.")
            return []
        with open(path) as f:
            data = json.load(f)
        out = [
            (parse_timestamp(w["start"]), parse_timestamp(w["end"]), w.get("label", ""))
            for w in data
        ]
        self._log(f"{label}: loaded {len(out)} windows.")
        return out

    def _filter_auto(
        self,
        auto: List[_WindowPair],
        manual: List[_WindowTriple],
        label: str,
    ) -> Tuple[List[_WindowPair], List[_WindowPair]]:
        filtered, removed = [], []
        for a_start, a_end in auto:
            if any(overlaps(a_start, a_end, m_start, m_end) for m_start, m_end, _ in manual):
                removed.append((a_start, a_end))
            else:
                filtered.append((a_start, a_end))
        self._log(
            f"{label}: auto before={len(auto)}, after={len(filtered)}, removed={len(removed)}"
        )
        return filtered, removed

    def _log(self, msg: str) -> None:
        self._log_lines.append(msg)

    @staticmethod
    def _in(t: int, windows: List[_WindowPair]) -> bool:
        return any(s <= t <= e for s, e in windows)

    @staticmethod
    def _cycle_factor(t: int, ranges: list, midpoints: list) -> float:
        for (start, end), mid in zip(ranges, midpoints):
            if start <= t <= end:
                span = end - start
                if span <= 0:
                    return 0.0
                x = (t - start) / span
                return 0.5 * (1 - math.cos(2 * math.pi * x))
        return 0.0

    @staticmethod
    def _near_beat(t: int, beat_times: list, radius_ms: int) -> bool:
        if not beat_times:
            return False
        idx = bisect.bisect_left(beat_times, t)
        candidates = []
        if idx < len(beat_times):
            candidates.append(beat_times[idx])
        if idx > 0:
            candidates.append(beat_times[idx - 1])
        nearest = min(candidates, key=lambda bt: abs(bt - t))
        return abs(nearest - t) <= radius_ms
