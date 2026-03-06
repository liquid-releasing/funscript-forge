"""FunscriptVisualizer: plots motion structure from an AssessmentResult.

Requires matplotlib. Install with: pip install matplotlib
"""

from models import AssessmentResult

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class FunscriptVisualizer:
    """Renders a motion + structure plot from a loaded funscript and its assessment.

    Usage::

        viz = FunscriptVisualizer(assessment, actions)
        viz.plot("output.png")
    """

    def __init__(self, assessment: AssessmentResult, actions: list):
        self.assessment = assessment
        self.actions = actions

    def plot(self, output_path: str) -> None:
        """Save a visualization PNG to output_path."""
        if not HAS_MATPLOTLIB:
            raise RuntimeError(
                "matplotlib is required for visualization. "
                "Install it with: pip install matplotlib"
            )

        times = [a["at"] for a in self.actions]
        positions = [a["pos"] for a in self.actions]
        a = self.assessment

        fig, ax = plt.subplots(figsize=(16, 5))
        ax.plot(times, positions, color="steelblue", linewidth=0.8, label="motion")

        for phase in a.phases:
            ax.axvline(phase.start_ms, color="gray", linewidth=0.4, alpha=0.4)

        for cycle in a.cycles:
            ax.axvspan(cycle.start_ms, cycle.end_ms, alpha=0.05, color="green")

        for phrase in a.phrases:
            ax.axvspan(phrase.start_ms, phrase.end_ms, alpha=0.08, color="orange")
            ax.text(
                (phrase.start_ms + phrase.end_ms) / 2, 96,
                phrase.pattern_label[:14],
                ha="center", fontsize=6, color="darkorange",
            )

        perf = a.auto_mode_windows.get("performance", [])
        brk = a.auto_mode_windows.get("break", [])
        for w in perf:
            ax.axvspan(w.start_ms, w.end_ms, alpha=0.12, color="red")
        for w in brk:
            ax.axvspan(w.start_ms, w.end_ms, alpha=0.12, color="blue")

        ax.set_title(f"Funscript Analysis — {a.source_file}")
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Position (0-100)")
        ax.set_ylim(-5, 110)

        from matplotlib.patches import Patch
        legend_items = [
            Patch(color="steelblue", label="motion"),
            Patch(color="green", alpha=0.3, label="cycles"),
            Patch(color="orange", alpha=0.4, label="phrases"),
            Patch(color="red", alpha=0.5, label="performance"),
            Patch(color="blue", alpha=0.5, label="break"),
        ]
        ax.legend(handles=legend_items, loc="upper right", fontsize=7)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
