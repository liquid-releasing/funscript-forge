"""pattern_catalog.py — Persistent cross-funscript pattern catalog.

Each time a funscript is assessed, its tagged phrases (with metrics) are
appended to a JSON catalog file.  Over time this builds a dataset of what
behavioral patterns exist across your library, their typical metric ranges,
and which funscripts exhibit each issue.

Catalog file schema (output/pattern_catalog.json)
--------------------------------------------------
{
  "version": "1.0",
  "entries": [
    {
      "funscript":   "Timeline1.original.funscript",
      "assessed_at": "2026-03-09T10:00:00",
      "duration_ms": 193000,
      "phrases": [
        {
          "start_ms":     5000,
          "end_ms":       45000,
          "bpm":          145.0,
          "pattern_label":"up -> down",
          "tags":         ["stingy"],
          "metrics": {
            "mean_pos": 50.2, "span": 82.0,
            "mean_velocity": 0.42, "peak_velocity": 0.55,
            "cv_bpm": 0.08, "duration_ms": 40000
          }
        }
      ]
    }
  ]
}
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


_SCHEMA_VERSION = "1.0"


class PatternCatalog:
    """Load, update, and query the cross-funscript pattern catalog.

    Parameters
    ----------
    path : str
        Path to the catalog JSON file.  Created if it does not exist.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._data: dict = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"version": _SCHEMA_VERSION, "entries": []}

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_assessment(
        self,
        funscript_name: str,
        phrases: List[dict],
        duration_ms: int = 0,
    ) -> int:
        """Add or replace the entry for *funscript_name*.

        Only phrases that have at least one behavioral tag are stored
        (untagged phrases carry no pattern information).

        Parameters
        ----------
        funscript_name : str
            Bare filename (no directory), e.g. ``"Timeline1.original.funscript"``.
        phrases : list[dict]
            Phrase dicts from ``AssessmentResult.to_dict()["phrases"]``.
            Each must already contain ``"tags"`` and ``"metrics"`` keys
            (i.e. ``annotate_phrases`` must have been called first).
        duration_ms : int
            Total funscript duration in milliseconds.

        Returns
        -------
        int
            Number of tagged phrases stored.
        """
        tagged = [
            {
                "start_ms":      ph["start_ms"],
                "end_ms":        ph["end_ms"],
                "bpm":           ph.get("bpm", 0.0),
                "pattern_label": ph.get("pattern_label", ""),
                "tags":          ph.get("tags", []),
                "metrics":       ph.get("metrics", {}),
            }
            for ph in phrases
            if ph.get("tags")
        ]

        # Replace existing entry for this funscript (re-run overwrites)
        self._data["entries"] = [
            e for e in self._data["entries"]
            if e.get("funscript") != funscript_name
        ]
        self._data["entries"].append({
            "funscript":   funscript_name,
            "assessed_at": datetime.now().isoformat(timespec="seconds"),
            "duration_ms": duration_ms,
            "phrases":     tagged,
        })
        return len(tagged)

    def remove(self, funscript_name: str) -> bool:
        """Remove the entry for *funscript_name*.  Returns True if found."""
        before = len(self._data["entries"])
        self._data["entries"] = [
            e for e in self._data["entries"]
            if e.get("funscript") != funscript_name
        ]
        return len(self._data["entries"]) < before

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def entries(self) -> List[dict]:
        return self._data.get("entries", [])

    @property
    def funscript_names(self) -> List[str]:
        return [e["funscript"] for e in self.entries]

    def get_tag_stats(self) -> Dict[str, dict]:
        """Return per-tag aggregate statistics across all catalog entries.

        Returns
        -------
        dict
            ``{tag_key: {"count": int, "funscripts": int,
                         "bpm_mean": float, "bpm_min": float, "bpm_max": float,
                         "span_mean": float, "span_min": float, "span_max": float,
                         "mean_vel_mean": float, "duration_mean_ms": float}}``
        """
        from collections import defaultdict

        tag_data: Dict[str, dict] = defaultdict(lambda: {
            "phrases": [], "funscripts": set(),
        })

        for entry in self.entries:
            fname = entry["funscript"]
            for ph in entry.get("phrases", []):
                for tag in ph.get("tags", []):
                    tag_data[tag]["phrases"].append(ph)
                    tag_data[tag]["funscripts"].add(fname)

        stats: Dict[str, dict] = {}
        for tag, d in tag_data.items():
            phrases = d["phrases"]
            bpms    = [p["bpm"] for p in phrases if p.get("bpm", 0) > 0]
            spans   = [p["metrics"].get("span", 0) for p in phrases if p.get("metrics")]
            vels    = [p["metrics"].get("mean_velocity", 0) for p in phrases if p.get("metrics")]
            durs    = [p["metrics"].get("duration_ms", 0) for p in phrases if p.get("metrics")]

            def _mean(lst): return round(sum(lst) / len(lst), 2) if lst else 0.0
            def _min(lst):  return round(min(lst), 2) if lst else 0.0
            def _max(lst):  return round(max(lst), 2) if lst else 0.0

            stats[tag] = {
                "count":            len(phrases),
                "funscripts":       len(d["funscripts"]),
                "bpm_mean":         _mean(bpms),
                "bpm_min":          _min(bpms),
                "bpm_max":          _max(bpms),
                "span_mean":        _mean(spans),
                "span_min":         _min(spans),
                "span_max":         _max(spans),
                "mean_vel_mean":    _mean(vels),
                "duration_mean_ms": int(_mean(durs)),
            }

        return stats

    def get_phrases_for_tag(self, tag: str) -> List[dict]:
        """Return all stored phrase records that carry *tag*."""
        result = []
        for entry in self.entries:
            for ph in entry.get("phrases", []):
                if tag in ph.get("tags", []):
                    result.append({**ph, "_funscript": entry["funscript"]})
        return result

    def summary(self) -> dict:
        """Return a high-level summary dict."""
        stats = self.get_tag_stats()
        return {
            "funscripts_indexed": len(self.entries),
            "total_tagged_phrases": sum(
                len(e.get("phrases", [])) for e in self.entries
            ),
            "tags_found": sorted(stats.keys()),
            "tag_counts": {t: s["count"] for t, s in stats.items()},
        }
