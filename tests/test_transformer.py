"""Unit tests for suggested_updates/transformer.py"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import tempfile
import unittest

from assessment.analyzer import FunscriptAnalyzer
from suggested_updates.transformer import FunscriptTransformer
from suggested_updates.config import TransformerConfig

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.funscript")


def _make_transformer_with_assessment():
    """Helper: return a transformer pre-loaded with fixture + assessment."""
    analyzer = FunscriptAnalyzer()
    analyzer.load(FIXTURE)
    assessment = analyzer.analyze()

    transformer = FunscriptTransformer()
    transformer.load_funscript(FIXTURE)
    transformer.load_assessment(assessment)
    return transformer


class TestFunscriptTransformer(unittest.TestCase):
    def test_load_funscript(self):
        t = FunscriptTransformer()
        t.load_funscript(FIXTURE)
        self.assertGreater(len(t._actions), 0)

    def test_load_assessment_populates_windows(self):
        t = _make_transformer_with_assessment()
        total = len(t._auto_perf) + len(t._auto_break) + len(t._auto_default)
        self.assertGreater(total, 0)

    def test_merge_windows_returns_dict(self):
        t = _make_transformer_with_assessment()
        merged = t.merge_windows()
        self.assertIn("performance", merged)
        self.assertIn("break", merged)
        self.assertIn("default", merged)
        self.assertIn("raw", merged)

    def test_transform_returns_actions(self):
        t = _make_transformer_with_assessment()
        t.merge_windows()
        actions = t.transform()
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)

    def test_transform_output_positions_in_range(self):
        t = _make_transformer_with_assessment()
        t.merge_windows()
        actions = t.transform()
        for a in actions:
            self.assertGreaterEqual(a["pos"], 0)
            self.assertLessEqual(a["pos"], 100)

    def test_transform_timestamps_non_negative(self):
        t = _make_transformer_with_assessment()
        t.merge_windows()
        actions = t.transform()
        for a in actions:
            self.assertGreaterEqual(a["at"], 0)

    def test_save_produces_valid_funscript(self):
        t = _make_transformer_with_assessment()
        t.merge_windows()
        t.transform()

        with tempfile.NamedTemporaryFile(suffix=".funscript", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            t.save(tmp_path)
            with open(tmp_path) as f:
                data = json.load(f)
            self.assertIn("actions", data)
            self.assertGreater(len(data["actions"]), 0)
        finally:
            os.unlink(tmp_path)

    def test_get_log_returns_list(self):
        t = _make_transformer_with_assessment()
        t.merge_windows()
        t.transform()
        log = t.get_log()
        self.assertIsInstance(log, list)
        self.assertGreater(len(log), 0)


class TestManualOverrides(unittest.TestCase):
    def test_manual_override_removes_overlapping_auto(self):
        t = _make_transformer_with_assessment()

        # Inject a synthetic auto performance window
        t._auto_perf = [(1000, 3000)]

        # Create a manual window overlapping the auto one
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump([{"start": "00:00:01.500", "end": "00:00:02.500", "label": "manual"}], f)
            tmp_path = f.name

        try:
            t.load_manual_overrides(perf_path=tmp_path)
            merged = t.merge_windows()
            # Auto window overlapping manual should be removed
            # Final perf windows should only contain the manual one
            self.assertEqual(len(merged["performance"]), 1)
            self.assertEqual(merged["performance"][0]["start_ms"], 1500)
        finally:
            os.unlink(tmp_path)

    def test_non_overlapping_auto_windows_preserved(self):
        t = _make_transformer_with_assessment()

        # Two auto windows, one overlapping manual, one not
        t._auto_perf = [(0, 500), (5000, 6000)]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump([{"start": "00:00:00.100", "end": "00:00:00.400", "label": "manual"}], f)
            tmp_path = f.name

        try:
            t.load_manual_overrides(perf_path=tmp_path)
            merged = t.merge_windows()
            # manual (1) + non-overlapping auto (1) = 2 total
            self.assertEqual(len(merged["performance"]), 2)
        finally:
            os.unlink(tmp_path)


class TestTransformerConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = TransformerConfig()
        self.assertEqual(cfg.time_scale, 2.0)
        self.assertEqual(cfg.amplitude_scale, 2.0)
        self.assertEqual(cfg.beat_accent_radius_ms, 40)

    def test_config_round_trip(self):
        cfg = TransformerConfig(time_scale=1.5, beat_accent_amount=6)
        d = cfg.to_dict()
        restored = TransformerConfig.from_dict(d)
        self.assertEqual(restored.time_scale, 1.5)
        self.assertEqual(restored.beat_accent_amount, 6)

    def test_config_save_load(self):
        cfg = TransformerConfig(lpf_default=0.25)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            cfg.save(tmp_path)
            loaded = TransformerConfig.load(tmp_path)
            self.assertEqual(loaded.lpf_default, 0.25)
        finally:
            os.unlink(tmp_path)

    def test_from_dict_ignores_unknown_keys(self):
        cfg = TransformerConfig.from_dict({"time_scale": 3.0, "unknown_key": "ignored"})
        self.assertEqual(cfg.time_scale, 3.0)


if __name__ == "__main__":
    unittest.main()
