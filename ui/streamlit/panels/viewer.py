"""viewer.py — Phrase Selector panel.

The Phrase Selector gives a full-width, scrollable/zoomable view of the
funscript with each phrase drawn as a labelled, bordered box.

Interaction
-----------
* Drag left/right  — pan (scroll) the visible window.
* Scroll wheel     — zoom in/out (Plotly native).
* Click a point    — selects the enclosing phrase; shows phrase info below.
* Phrase buttons   — P1, P2, … below the chart jump directly to a phrase.
* Zoom controls    — manual timestamp entry + scroll-step buttons.

Selected phrase info (start, end, duration, BPM, pattern, cycle count) is
displayed below.  A phrase editor will appear here in the next version.
"""

from __future__ import annotations

from typing import List, Optional

from utils import ms_to_timestamp, parse_timestamp


def render(project, view_state, proposed_actions: Optional[List[dict]] = None) -> None:
    """Render the Phrase Selector.

    Parameters
    ----------
    project:
        Loaded :class:`~ui.common.project.Project`.
    view_state:
        Shared :class:`~ui.common.view_state.ViewState`.
    proposed_actions:
        Reserved for future editing workflow.
    """
    import streamlit as st

    if not project or not project.is_loaded:
        st.info("Load a funscript to use the Phrase Selector.")
        return

    from visualizations.chart_data import compute_chart_data, compute_annotation_bands
    from visualizations.funscript_chart import FunscriptChart, HAS_PLOTLY

    if not HAS_PLOTLY:
        st.error("plotly is required.  Run: pip install plotly")
        return

    import json
    with open(project.funscript_path) as f:
        _raw = json.load(f)
    original_actions = _raw["actions"]

    assessment_dict = project.assessment.to_dict()
    phrases         = assessment_dict.get("phrases", [])
    bands           = compute_annotation_bands(assessment_dict)
    duration_ms     = project.assessment.duration_ms

    # Ensure phrases are always shown even if view_state has them toggled off.
    view_state.show_phrases = True

    # ------------------------------------------------------------------
    # Colour mode + scroll/zoom controls (compact, above the chart)
    # ------------------------------------------------------------------
    _render_controls(view_state, duration_ms)

    # ------------------------------------------------------------------
    # Phrase Selector chart — full width, pan mode
    # ------------------------------------------------------------------
    series = compute_chart_data(original_actions)
    chart  = FunscriptChart(series, bands, "", duration_ms)
    ev     = chart.render_streamlit(view_state, key="chart_phrase_sel", height=380)
    _handle_chart_event(ev, view_state, phrases)

    # ------------------------------------------------------------------
    # Phrase quick-jump buttons
    # ------------------------------------------------------------------
    _render_phrase_bar(phrases, view_state)

    # ------------------------------------------------------------------
    # Selected phrase info / editor placeholder
    # ------------------------------------------------------------------
    if view_state.has_selection():
        st.divider()
        _render_phrase_info(view_state, phrases)


# ------------------------------------------------------------------
# Controls bar
# ------------------------------------------------------------------

def _render_controls(view_state, duration_ms: int) -> None:
    """Colour-mode toggle + zoom/scroll controls in a single compact row."""
    import streamlit as st

    col_mode, col_start, col_end, col_apply, col_reset, col_left, col_right = st.columns(
        [2, 2, 2, 1, 1, 1, 1]
    )

    with col_mode:
        view_state.color_mode = st.radio(
            "Color",
            ["velocity", "amplitude"],
            index=0 if view_state.color_mode == "velocity" else 1,
            horizontal=True,
            key="viewer_color_mode",
            label_visibility="collapsed",
        )

    zoom_start = view_state.zoom_start_ms or 0
    zoom_end   = view_state.zoom_end_ms   or duration_ms
    span       = zoom_end - zoom_start

    with col_start:
        z_start = st.text_input(
            "Start",
            value=ms_to_timestamp(zoom_start),
            key="zoom_start_input",
            placeholder="M:SS",
        )

    with col_end:
        z_end = st.text_input(
            "End",
            value=ms_to_timestamp(zoom_end),
            key="zoom_end_input",
            placeholder="M:SS",
        )

    with col_apply:
        st.write("")  # vertical spacer
        if st.button("Apply", key="apply_zoom"):
            try:
                s = parse_timestamp(z_start)
                e = parse_timestamp(z_end)
                view_state.set_zoom(s, e)
                st.rerun()
            except Exception:
                st.error("Bad timestamp.")

    with col_reset:
        st.write("")
        if st.button("All", key="reset_zoom", help="Show full funscript"):
            view_state.reset_zoom()
            view_state.clear_selection()
            st.rerun()

    scroll_step = max(span // 3, 1_000)  # scroll by 1/3 of current window

    with col_left:
        st.write("")
        if st.button("◀", key="scroll_left", help="Scroll left"):
            new_start = max(0, zoom_start - scroll_step)
            new_end   = new_start + span
            view_state.set_zoom(new_start, min(new_end, duration_ms))
            st.rerun()

    with col_right:
        st.write("")
        if st.button("▶", key="scroll_right", help="Scroll right"):
            new_end   = min(duration_ms, zoom_end + scroll_step)
            new_start = max(0, new_end - span)
            view_state.set_zoom(new_start, new_end)
            st.rerun()


# ------------------------------------------------------------------
# Chart event handling
# ------------------------------------------------------------------

def _handle_chart_event(event, view_state, phrases: list) -> None:
    """Map a Plotly point-click or box-select event to a ViewState update."""
    import streamlit as st

    if not event:
        return
    sel = getattr(event, "selection", None)
    if not sel:
        return

    # Single-point click → select enclosing phrase
    points = getattr(sel, "points", [])
    if points:
        x = points[0].get("x")
        if x is not None:
            phrase = _find_phrase_at(int(x), phrases)
            if phrase:
                _select_phrase(phrase, view_state)
                st.rerun()
        return

    # Box drag → manual time range selection
    box = getattr(sel, "box", None) or []
    if box:
        try:
            x_range = box[0].get("x", [])
            if len(x_range) == 2:
                view_state.set_selection(int(x_range[0]), int(x_range[1]))
                st.rerun()
        except Exception:
            pass


# ------------------------------------------------------------------
# Phrase quick-jump bar
# ------------------------------------------------------------------

def _render_phrase_bar(phrases: list, view_state) -> None:
    """A numbered button for each phrase; clicking selects it."""
    import streamlit as st

    if not phrases:
        return

    st.caption(
        f"{len(phrases)} phrase{'s' if len(phrases) != 1 else ''} — "
        "click a phrase on the chart or use the buttons below"
    )

    chunk_size = 10
    chunks = [phrases[i:i + chunk_size] for i in range(0, len(phrases), chunk_size)]
    for row_idx, chunk in enumerate(chunks):
        cols = st.columns(len(chunk))
        for col_idx, ph in enumerate(chunk):
            idx   = row_idx * chunk_size + col_idx
            start = ph["start_ms"]
            end   = ph["end_ms"]
            is_sel = (
                view_state.has_selection()
                and view_state.selection_start_ms == start
                and view_state.selection_end_ms   == end
            )
            label = f"◆ P{idx + 1}" if is_sel else f"P{idx + 1}"
            tip   = (
                f"{ms_to_timestamp(start)} — {ms_to_timestamp(end)}\n"
                f"{ph.get('bpm', 0):.0f} BPM  ·  {ph.get('pattern_label', '')}"
            )
            with cols[col_idx]:
                if st.button(label, key=f"phrase_btn_{idx}", help=tip):
                    _select_phrase(ph, view_state)
                    st.rerun()


# ------------------------------------------------------------------
# Selected phrase info panel
# ------------------------------------------------------------------

def _render_phrase_info(view_state, phrases: list) -> None:
    """Show metadata for the selected phrase and a placeholder editor."""
    import streamlit as st

    start = view_state.selection_start_ms
    end   = view_state.selection_end_ms

    phrase = next(
        (ph for ph in phrases
         if ph["start_ms"] == start and ph["end_ms"] == end),
        None,
    )

    if phrase:
        duration_ms = end - start
        bpm         = phrase.get("bpm", 0)
        pattern     = phrase.get("pattern_label", "—")
        cycles      = phrase.get("cycle_count", "—")

        st.subheader("Selected Phrase")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Start",    ms_to_timestamp(start))
        m2.metric("End",      ms_to_timestamp(end))
        m3.metric("Duration", f"{duration_ms / 1000:.1f} s")
        m4.metric("BPM",      f"{bpm:.1f}")
        m5.metric("Pattern",  pattern)
        m6.metric("Cycles",   cycles)

        st.info(
            "Phrase editor coming in the next version — "
            "will show a zoomed chart of this phrase with transformation controls."
        )
    else:
        st.subheader("Selection")
        c1, c2, c3 = st.columns(3)
        c1.metric("Start",    ms_to_timestamp(start))
        c2.metric("End",      ms_to_timestamp(end))
        c3.metric("Duration", f"{(end - start) / 1000:.1f} s")

    if st.button("Clear selection", key="clear_sel"):
        view_state.clear_selection()
        st.rerun()


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _find_phrase_at(time_ms: int, phrases: list):
    for ph in phrases:
        if ph["start_ms"] <= time_ms <= ph["end_ms"]:
            return ph
    return None


def _select_phrase(phrase: dict, view_state) -> None:
    start, end = phrase["start_ms"], phrase["end_ms"]
    padding = min(2_000, (end - start) // 8)
    view_state.set_selection(start, end)
    view_state.set_zoom(max(0, start - padding), end + padding)
