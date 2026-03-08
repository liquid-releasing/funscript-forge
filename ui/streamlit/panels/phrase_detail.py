"""phrase_detail.py — Detailed view for a selected phrase.

Layout (when a phrase is selected)
------------------------------------
  Divider + "P{N} — Phrase Detail" heading

  Row 1:
    [ Full-colour zoomed chart — original actions   (3/4) ]
    [ Transform selector + param sliders            (1/4) ]

  Row 2 (always visible):
    [ Preview chart — transform applied, not saved (full) ]
    Caption: "Preview — {Transform Name}  (not saved)"
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from utils import ms_to_timestamp


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def render(
    phrases: list,
    original_actions: list,
    view_state,
    duration_ms: int,
    bpm_threshold: float = 120.0,
) -> None:
    import streamlit as st

    if not view_state.has_selection():
        return

    sel_start  = view_state.selection_start_ms
    sel_end    = view_state.selection_end_ms
    phrase_idx = next(
        (i for i, ph in enumerate(phrases)
         if ph["start_ms"] == sel_start and ph["end_ms"] == sel_end),
        None,
    )
    if phrase_idx is None:
        return

    phrase = phrases[phrase_idx]

    st.divider()
    st.subheader(f"P{phrase_idx + 1} — Phrase Detail")

    # ------------------------------------------------------------------
    # Viewport: selected phrase + one neighbour each side + small pad
    # ------------------------------------------------------------------
    prev_phrase = phrases[phrase_idx - 1] if phrase_idx > 0 else None
    next_phrase = phrases[phrase_idx + 1] if phrase_idx < len(phrases) - 1 else None

    win_start = prev_phrase["start_ms"] if prev_phrase else sel_start
    win_end   = next_phrase["end_ms"]   if next_phrase else sel_end
    pad = max((sel_end - sel_start) // 10, 1_000)
    win_start = max(0, win_start - pad)
    win_end   = min(duration_ms, win_end + pad)

    # ------------------------------------------------------------------
    # Row 1: original chart (left) + transform controls (right)
    # ------------------------------------------------------------------
    col_chart, col_controls = st.columns([3, 1])

    with col_chart:
        st.caption("Original")
        _render_chart(
            actions=original_actions,
            phrases=phrases,
            phrase_idx=phrase_idx,
            win_start=win_start,
            win_end=win_end,
            view_state=view_state,
            chart_key=f"detail_orig_{phrase_idx}_{win_start}",
        )

    with col_controls:
        _render_transform_controls(phrase, bpm_threshold, phrase_idx)

    # ------------------------------------------------------------------
    # Row 2: preview chart (transform applied, not saved)
    # ------------------------------------------------------------------
    transform_state = st.session_state.get(f"phrase_transform_{phrase_idx}", {})
    transform_key  = transform_state.get("transform_key", "passthrough")
    param_values   = transform_state.get("param_values", {})

    from suggested_updates.phrase_transforms import TRANSFORM_CATALOG
    spec = TRANSFORM_CATALOG.get(transform_key, TRANSFORM_CATALOG["passthrough"])

    preview_actions = _apply_transform_to_window(
        original_actions=original_actions,
        phrase=phrase,
        spec=spec,
        param_values=param_values,
    )

    st.caption(f"Preview — **{spec.name}** *(not saved)*")
    _render_chart(
        actions=preview_actions,
        phrases=phrases,
        phrase_idx=phrase_idx,
        win_start=win_start,
        win_end=win_end,
        view_state=view_state,
        chart_key=f"detail_prev_{phrase_idx}_{win_start}_{transform_key}",
    )


# ------------------------------------------------------------------
# Shared chart renderer
# ------------------------------------------------------------------

def _render_chart(
    actions: list,
    phrases: list,
    phrase_idx: int,
    win_start: int,
    win_end: int,
    view_state,
    chart_key: str,
) -> None:
    import streamlit as st
    from visualizations.chart_data import (
        compute_chart_data, compute_annotation_bands,
        slice_series, slice_bands,
    )
    from visualizations.funscript_chart import FunscriptChart

    sel_phrase = phrases[phrase_idx]
    s = slice_series(compute_chart_data(actions), win_start, win_end)

    assessment_stub = {
        "phrases": phrases, "phases": [], "cycles": [],
        "patterns": [], "bpm_transitions": [],
    }
    visible_bands = slice_bands(compute_annotation_bands(assessment_stub), win_start, win_end)

    # Always use per-segment coloured lines in the detail view
    chart = FunscriptChart(
        s, visible_bands, "",
        win_end - win_start,
        large_funscript_threshold=10_000_000,
    )

    class _LocalVS:
        zoom_start_ms      = win_start
        zoom_end_ms        = win_end
        color_mode         = view_state.color_mode
        show_phrases       = True
        selection_start_ms = sel_phrase["start_ms"]
        selection_end_ms   = sel_phrase["end_ms"]
        def has_zoom(self):      return True
        def has_selection(self): return True

    chart.render_streamlit(_LocalVS(), key=chart_key, height=260)


# ------------------------------------------------------------------
# Transform application
# ------------------------------------------------------------------

def _apply_transform_to_window(
    original_actions: list,
    phrase: dict,
    spec,
    param_values: dict,
) -> list:
    """Return a deep copy of original_actions with the transform applied
    only to actions that fall within the phrase's time window."""
    phrase_start = phrase["start_ms"]
    phrase_end   = phrase["end_ms"]

    result = copy.deepcopy(original_actions)

    # Extract the phrase slice, apply, write back
    phrase_slice = [a for a in result if phrase_start <= a["at"] <= phrase_end]
    transformed  = spec.apply(phrase_slice, param_values)

    # Map by timestamp for fast lookup
    t_to_pos = {a["at"]: a["pos"] for a in transformed}
    for a in result:
        if a["at"] in t_to_pos:
            a["pos"] = t_to_pos[a["at"]]

    return result


# ------------------------------------------------------------------
# Transform controls
# ------------------------------------------------------------------

def _render_transform_controls(phrase: dict, bpm_threshold: float, phrase_idx: int) -> None:
    import streamlit as st
    from suggested_updates.phrase_transforms import TRANSFORM_CATALOG, suggest_transform

    suggested_key = suggest_transform(phrase, bpm_threshold)
    keys   = list(TRANSFORM_CATALOG.keys())
    labels = [TRANSFORM_CATALOG[k].name for k in keys]
    suggested_idx = keys.index(suggested_key) if suggested_key in keys else 0

    st.markdown("**Transform**")
    st.caption(f"Suggested: **{TRANSFORM_CATALOG[suggested_key].name}**")

    chosen_label = st.selectbox(
        "Select transform",
        options=labels,
        index=suggested_idx,
        key=f"transform_sel_{phrase_idx}",
        label_visibility="collapsed",
    )
    chosen_key = keys[labels.index(chosen_label)]
    spec = TRANSFORM_CATALOG[chosen_key]

    st.caption(spec.description)

    param_values = {}
    for param_key, param in spec.params.items():
        if param.type == "float":
            param_values[param_key] = st.slider(
                param.label,
                min_value=float(param.min_val or 0.0),
                max_value=float(param.max_val or 1.0),
                value=float(param.default),
                step=float(param.step or 0.05),
                help=param.help,
                key=f"param_{phrase_idx}_{param_key}",
            )
        elif param.type == "int":
            param_values[param_key] = st.slider(
                param.label,
                min_value=int(param.min_val or 0),
                max_value=int(param.max_val or 100),
                value=int(param.default),
                step=int(param.step or 1),
                help=param.help,
                key=f"param_{phrase_idx}_{param_key}",
            )

    st.session_state[f"phrase_transform_{phrase_idx}"] = {
        "transform_key": chosen_key,
        "param_values":  param_values,
    }
