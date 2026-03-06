"""Unit tests for assessment/analyzer.py"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import tempfile
import unittest

from assessment.analyzer import FunscriptAnalyzer, AnalyzerConfig
from models import AssessmentResult, Phase, Cycle, Phrase, Window

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.funscript")


class TestFunscriptAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = FunscriptAnalyzer()
        self.analyzer.load(FIXTURE)
        self.result = self.analyzer.analyze()

    def test_load_sets_actions(self):
        self.assertGreater(len(self.analyzer._actions), 0)

    def test_analyze_returns_assessment_result(self):
        self.assertIsInstance(self.result, AssessmentResult)

    def test_phases_detected(self):
        self.assertGreater(len(self.result.phases), 0)

    def test_cycles_detected(self):
        self.assertGreater(len(self.result.cycles), 0)

    def test_patterns_detected(self):
        self.assertGreater(len(self.result.patterns), 0)

    def test_phrases_detected(self):
        self.assertGreater(len(self.result.phrases), 0)

    def test_beat_windows_detected(self):
        self.assertGreater(len(self.result.beat_windows), 0)

    def test_auto_mode_windows_has_all_keys(self):
        keys = set(self.result.auto_mode_windows.keys())
        self.assertEqual(keys, {"performance", "break", "default"})

    def test_duration_ms_matches_last_action(self):
        with open(FIXTURE) as f:
            data = json.load(f)
        last_at = data["actions"][-1]["at"]
        self.assertEqual(self.result.duration_ms, last_at)

    def test_action_count(self):
        with open(FIXTURE) as f:
            data = json.load(f)
        self.assertEqual(self.result.action_count, len(data["actions"]))

    def test_phase_timestamps_match_ms(self):
        for phase in self.result.phases:
            # start_ts must be consistent with start_ms
            from utils import ms_to_timestamp
            self.assertEqual(phase.start_ts, ms_to_timestamp(phase.start_ms))
            self.assertEqual(phase.end_ts, ms_to_timestamp(phase.end_ms))

    def test_cycle_timestamps_match_ms(self):
        for cycle in self.result.cycles:
            from utils import ms_to_timestamp
            self.assertEqual(cycle.start_ts, ms_to_timestamp(cycle.start_ms))
            self.assertEqual(cycle.end_ts, ms_to_timestamp(cycle.end_ms))

    def test_no_analyze_without_load(self):
        fresh = FunscriptAnalyzer()
        with self.assertRaises(RuntimeError):
            fresh.analyze()


class TestAssessmentResultSerialization(unittest.TestCase):
    def setUp(self):
        analyzer = FunscriptAnalyzer()
        analyzer.load(FIXTURE)
        self.result = analyzer.analyze()

    def test_to_dict_has_meta(self):
        d = self.result.to_dict()
        self.assertIn("meta", d)
        self.assertIn("duration_ms", d["meta"])
        self.assertIn("duration_ts", d["meta"])
        self.assertIn("action_count", d["meta"])

    def test_to_dict_has_all_sections(self):
        d = self.result.to_dict()
        for key in ("phases", "cycles", "patterns", "phrases", "beat_windows", "auto_mode_windows"):
            self.assertIn(key, d)

    def test_window_dicts_have_both_ms_and_ts(self):
        d = self.result.to_dict()
        for phase in d["phases"]:
            self.assertIn("start_ms", phase)
            self.assertIn("start_ts", phase)
            self.assertIn("end_ms", phase)
            self.assertIn("end_ts", phase)

    def test_save_and_load_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name

        try:
            self.result.save(tmp_path)
            loaded = AssessmentResult.load(tmp_path)

            self.assertEqual(loaded.duration_ms, self.result.duration_ms)
            self.assertEqual(loaded.action_count, self.result.action_count)
            self.assertEqual(len(loaded.phases), len(self.result.phases))
            self.assertEqual(len(loaded.cycles), len(self.result.cycles))
            self.assertEqual(len(loaded.patterns), len(self.result.patterns))
            self.assertEqual(len(loaded.phrases), len(self.result.phrases))
        finally:
            os.unlink(tmp_path)

    def test_from_dict_reconstructs_windows(self):
        d = self.result.to_dict()
        loaded = AssessmentResult.from_dict(d)
        for mode in ("performance", "break", "default"):
            self.assertEqual(
                len(loaded.auto_mode_windows[mode]),
                len(self.result.auto_mode_windows[mode]),
            )


class TestAnalyzerConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = AnalyzerConfig()
        self.assertEqual(cfg.min_velocity, 0.02)
        self.assertEqual(cfg.performance_cycle_threshold, 5)
        self.assertEqual(cfg.break_cycle_threshold, 2)

    def test_custom_config_applied(self):
        # With a very high performance threshold, nothing should be performance
        cfg = AnalyzerConfig(performance_cycle_threshold=999)
        analyzer = FunscriptAnalyzer(config=cfg)
        analyzer.load(FIXTURE)
        result = analyzer.analyze()
        self.assertEqual(len(result.auto_mode_windows["performance"]), 0)


if __name__ == "__main__":
    unittest.main()
