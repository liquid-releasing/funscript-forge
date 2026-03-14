# Copyright (c) 2026 Liquid Releasing. Licensed under the MIT License.
# Written by human and Claude AI (Claude Sonnet).

"""ReTransform Global — catalog UI for selecting estim character.

Five character cards displayed simultaneously. Browse and compare.
Pick one — selected card gets highlighted border + "Selected" state.
Banner confirms the active selection and offers "Proceed to Phrases →".

Two levels:
  ReTransform Global  — applies chosen character to the whole funscript
  ReTransform Phrases — per-phrase refinement (next milestone)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Character definitions
# ---------------------------------------------------------------------------

_GREEN_DOT = "#2ecc71"
_RED_DOT   = "#e74c3c"
_BG        = "rgba(14,14,18,1)"

_CHARACTERS: List[Dict[str, Any]] = [
    {
        "name": "Gentle",
        "emoji": "🌊",
        "tagline": "Soft, slow-building.",
        "description": "Good for intimate or slow content. Sensation stays close to center and builds gradually — no sharp onset.",
        "what_youll_feel": "Subtle movement close to center. Pulses build slowly. Good for warming up or winding down.",
        "sliders": [
            {"key": "min_dist",  "label": "Softness",     "hint": "How far sensation moves from center. Low = very subtle.", "min": 0.05, "max": 0.4,  "default": 0.15, "step": 0.01, "format": "%.2f"},
            {"key": "pr_max",    "label": "Pulse onset",  "hint": "How gently pulses start. Higher = softer attack.",        "min": 0.0,  "max": 1.0,  "default": 0.8,  "step": 0.05, "format": "%.2f"},
        ],
        "path_shape": "semi_circle",
        "color": "#4a90d9",
        "border": "2px solid #4a90d9",
        "selected_border": "3px solid #4a90d9",
    },
    {
        "name": "Reactive",
        "emoji": "⚡",
        "tagline": "Sharp, tracks every stroke.",
        "description": "Good for fast, intense content. Sensation follows the action instantly — no lag, wide sweep.",
        "what_youll_feel": "Wide sweep, instant response to every stroke. Pulse rate spikes with fast action.",
        "sliders": [
            {"key": "freq_ramp", "label": "Reactivity",      "hint": "How tightly sensation follows each stroke. Low = instant.", "min": 0.5, "max": 5.0, "default": 1.2, "step": 0.1,  "format": "%.1f"},
            {"key": "pf_max",    "label": "Peak intensity",  "hint": "Maximum pulse rate during peak action.",                    "min": 0.5, "max": 1.0, "default": 0.9, "step": 0.05, "format": "%.2f"},
        ],
        "path_shape": "three_quarter",
        "color": "#e74c3c",
        "border": "2px solid #e74c3c",
        "selected_border": "3px solid #e74c3c",
    },
    {
        "name": "Scene Builder",
        "emoji": "🏗️",
        "tagline": "Builds gradually over the scene.",
        "description": "Works well for longer content with a slow arc. Sensation expands as the scene develops.",
        "what_youll_feel": "Sensation expands slowly over time. The arc widens as the scene develops. Rewards patience.",
        "sliders": [
            {"key": "freq_ramp", "label": "Build speed", "hint": "How gradually sensation builds. High = very slow build.", "min": 3.0, "max": 10.0, "default": 7.0, "step": 0.5,  "format": "%.1f"},
            {"key": "min_dist",  "label": "Arc width",   "hint": "How far the sensation sweeps across.",                   "min": 0.1, "max": 0.6,  "default": 0.35, "step": 0.01, "format": "%.2f"},
        ],
        "path_shape": "circle",
        "color": "#2ecc71",
        "border": "2px solid #2ecc71",
        "selected_border": "3px solid #2ecc71",
    },
    {
        "name": "Unpredictable",
        "emoji": "🎲",
        "tagline": "Random direction changes.",
        "description": "Good for surprise content. Direction and pulse rate vary without pattern.",
        "what_youll_feel": "Direction changes without warning. Pulse rate varies widely. Keeps you guessing.",
        "sliders": [
            {"key": "min_dist",        "label": "Wildness", "hint": "How wide the random movement ranges. High = very wild.", "min": 0.1, "max": 0.6, "default": 0.4, "step": 0.01, "format": "%.2f"},
            {"key": "pulse_freq_ratio","label": "Variety",  "hint": "How varied the pulse rate is.",                         "min": 1.0, "max": 8.0, "default": 5.0, "step": 0.5,  "format": "%.1f"},
        ],
        "path_shape": "zigzag",
        "color": "#f39c12",
        "border": "2px solid #f39c12",
        "selected_border": "3px solid #f39c12",
    },
    {
        "name": "Balanced",
        "emoji": "⚖️",
        "tagline": "Middle of everything.",
        "description": "A good starting point for any content. Moderate sweep, steady build.",
        "what_youll_feel": "Moderate sweep, steady build, neither too sharp nor too soft. Works with most content.",
        "sliders": [
            {"key": "min_dist",  "label": "Sweep width",          "hint": "Width of the sensation sweep.",                            "min": 0.05, "max": 0.6, "default": 0.3, "step": 0.01, "format": "%.2f"},
            {"key": "freq_ramp", "label": "Speed / build balance", "hint": "More reactive (low) vs. more gradual (high).",             "min": 1.0,  "max": 8.0, "default": 4.0, "step": 0.5,  "format": "%.1f"},
        ],
        "path_shape": "circle",
        "color": "#9b59b6",
        "border": "2px solid #9b59b6",
        "selected_border": "3px solid #9b59b6",
    },
]

# ---------------------------------------------------------------------------
# Geometric path chart
# ---------------------------------------------------------------------------

def _path_points(shape: str) -> tuple[list[float], list[float]]:
    n = 120
    if shape == "semi_circle":
        angles = [math.pi * i / (n - 1) for i in range(n)]
        return [0.5 + 0.4 * math.cos(t) for t in angles], [0.5 + 0.4 * math.sin(t) for t in angles]
    elif shape == "three_quarter":
        angles = [1.5 * math.pi * i / (n - 1) + math.pi * 0.75 for i in range(n)]
        return [0.5 + 0.4 * math.cos(t) for t in angles], [0.5 + 0.4 * math.sin(t) for t in angles]
    elif shape == "circle":
        angles = [2 * math.pi * i / (n - 1) for i in range(n)]
        return [0.5 + 0.4 * math.cos(t) for t in angles], [0.5 + 0.4 * math.sin(t) for t in angles]
    else:  # zigzag
        xs = [i / (n - 1) for i in range(n)]
        ys = [0.5 + 0.4 * math.sin(8 * math.pi * x) * (1 - x * 0.3) for x in xs]
        return xs, ys


def _path_chart(shape: str, color: str, height: int = 160) -> go.Figure:
    a, b = _path_points(shape)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a, y=b, mode="lines",
                             line=dict(color=color, width=2.5),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[a[0]], y=[b[0]], mode="markers",
                             marker=dict(color=_GREEN_DOT, size=9),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[a[-1]], y=[b[-1]], mode="markers",
                             marker=dict(color=_RED_DOT, size=9),
                             showlegend=False, hoverinfo="skip"))
    fig.update_layout(
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(l=2, r=2, t=2, b=2),
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[-0.05, 1.05], scaleanchor="x"),
        height=height,
    )
    return fig

# ---------------------------------------------------------------------------
# Card CSS
# ---------------------------------------------------------------------------

_CSS = """
<style>
.retransform-card {
    background: #0e0e12;
    border-radius: 10px;
    padding: 16px 14px 12px 14px;
    margin-bottom: 8px;
    transition: border 0.15s;
    min-height: 420px;
    display: flex;
    flex-direction: column;
}
.retransform-card.unselected {
    border: 2px solid #333;
    opacity: 0.72;
}
.retransform-card.selected {
    border: 3px solid var(--card-color);
    opacity: 1.0;
    box-shadow: 0 0 18px -4px var(--card-color);
}
.card-header {
    font-size: 1.1em;
    font-weight: 700;
    margin-bottom: 2px;
}
.card-tagline {
    font-size: 0.85em;
    color: #aaa;
    margin-bottom: 8px;
}
.card-feel {
    font-size: 0.8em;
    color: #bbb;
    border-left: 3px solid var(--card-color);
    padding-left: 8px;
    margin: 10px 0 12px 0;
    line-height: 1.5;
}
.selected-badge {
    display: inline-block;
    background: var(--card-color);
    color: #000;
    font-weight: 700;
    font-size: 0.78em;
    padding: 2px 8px;
    border-radius: 12px;
    margin-left: 8px;
}
</style>
"""

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _render_banner(selected: str | None, color: str | None):
    if not selected:
        st.info("Browse the characters below and select one to apply.")
        return

    emoji = next((c["emoji"] for c in _CHARACTERS if c["name"] == selected), "")
    st.markdown(
        f"""<div style='background:#0e0e12;border:2px solid {color};border-radius:8px;
        padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:16px;'>
        <span style='font-size:1.4em'>{emoji}</span>
        <div>
            <span style='font-weight:700;font-size:1.1em;color:{color}'>
                Currently applying: {selected}
            </span><br>
            <span style='color:#aaa;font-size:0.88em'>
                {next((c["description"] for c in _CHARACTERS if c["name"] == selected), "")}
            </span>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Single card
# ---------------------------------------------------------------------------

def _render_card(char: dict, is_selected: bool, col):
    with col:
        color = char["color"]
        card_class = "selected" if is_selected else "unselected"
        selected_badge = '<span class="selected-badge">✓ Selected</span>' if is_selected else ""

        st.markdown(
            f"""<div class="retransform-card {card_class}" style="--card-color:{color}">
            <div class="card-header">{char['emoji']} {char['name']}{selected_badge}</div>
            <div class="card-tagline">{char['tagline']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Path chart
        st.plotly_chart(
            _path_chart(char["path_shape"], color, height=140),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"rt_chart_{char['name']}",
        )

        # Sliders
        slider_vals = {}
        for spec in char["sliders"]:
            key = f"rt_{char['name']}_{spec['key']}"
            val = st.slider(
                spec["label"],
                min_value=spec["min"],
                max_value=spec["max"],
                value=st.session_state.get(key, spec["default"]),
                step=spec["step"],
                format=spec["format"],
                help=spec["hint"],
                key=key,
            )
            slider_vals[spec["key"]] = val

        # What you'll feel
        st.markdown(
            f'<div class="card-feel" style="--card-color:{color}">{char["what_youll_feel"]}</div>',
            unsafe_allow_html=True,
        )

        # Select button
        if is_selected:
            st.button(
                f"✓ Selected",
                key=f"rt_select_{char['name']}",
                use_container_width=True,
                disabled=True,
                type="primary",
            )
        else:
            if st.button(
                f"Use {char['name']}",
                key=f"rt_select_{char['name']}",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state["retransform_selected"] = char["name"]
                st.session_state["retransform_config"] = {
                    "name": char["name"],
                    "sliders": slider_vals,
                }
                st.rerun()

# ---------------------------------------------------------------------------
# ReTransform Phrases
# ---------------------------------------------------------------------------

def _render_phrases(global_selected: str, global_color: str, project) -> None:
    st.markdown("---")
    st.markdown("## ReTransform Phrases")
    st.markdown(
        f"Global character: **{global_selected}** — applied to all phrases by default. "
        "Override individual phrases here, or leave them as None to inherit Global."
    )

    # Get phrases from project, or show placeholder
    phrases = []
    if project is not None and hasattr(project, "work_items") and project.work_items:
        phrases = project.work_items
    else:
        # Placeholder phrases for when no project is loaded
        phrases = [type("P", (), {"item_id": f"phrase_{i}", "start_ms": i*10000, "end_ms": (i+1)*10000, "bpm": 90.0})()
                   for i in range(5)]
        st.caption("No funscript loaded — showing placeholder phrases.")

    n = len(phrases)

    # Phrase navigator
    if "rt_phrase_idx" not in st.session_state:
        st.session_state["rt_phrase_idx"] = 0
    idx = st.session_state["rt_phrase_idx"]
    idx = max(0, min(idx, n - 1))

    nav_left, nav_mid, nav_right = st.columns([1, 3, 1])
    with nav_left:
        if st.button("← Previous", disabled=(idx == 0), use_container_width=True):
            st.session_state["rt_phrase_idx"] = idx - 1
            st.rerun()
    with nav_mid:
        phrase = phrases[idx]
        start_s = getattr(phrase, "start_ms", 0) / 1000
        end_s   = getattr(phrase, "end_ms", 0) / 1000
        st.markdown(
            f"<div style='text-align:center;padding:6px 0'>"
            f"<strong>Phrase {idx+1} of {n}</strong> &nbsp;·&nbsp; "
            f"{start_s:.1f}s – {end_s:.1f}s"
            f"</div>",
            unsafe_allow_html=True,
        )
    with nav_right:
        if st.button("Next →", disabled=(idx == n - 1), use_container_width=True):
            st.session_state["rt_phrase_idx"] = idx + 1
            st.rerun()

    st.markdown("")

    # Phrase override selector
    phrase_key = getattr(phrase, "item_id", f"phrase_{idx}")
    overrides = st.session_state.get("rt_phrase_overrides", {})
    current_override = overrides.get(phrase_key, None)

    char_names = ["None — use Global"] + [c["name"] for c in _CHARACTERS]
    current_label = current_override if current_override else "None — use Global"
    default_idx = char_names.index(current_label) if current_label in char_names else 0

    left_col, right_col = st.columns([1, 2])

    with left_col:
        chosen_label = st.selectbox(
            f"Character for phrase {idx+1}",
            options=char_names,
            index=default_idx,
            key=f"rt_phrase_select_{phrase_key}",
            help="None = inherit the Global character. Pick a character to override this phrase only.",
        )
        chosen = None if chosen_label.startswith("None") else chosen_label
        char_data = next((c for c in _CHARACTERS if c["name"] == chosen), None)

        # Sliders for chosen override
        slider_vals = {}
        if char_data:
            st.markdown(f"**{char_data['emoji']} {char_data['name']}** — {char_data['tagline']}")
            for spec in char_data["sliders"]:
                key = f"rt_phrase_{phrase_key}_{spec['key']}"
                val = st.slider(
                    spec["label"],
                    min_value=spec["min"],
                    max_value=spec["max"],
                    value=st.session_state.get(key, spec["default"]),
                    step=spec["step"],
                    format=spec["format"],
                    help=spec["hint"],
                    key=key,
                )
                slider_vals[spec["key"]] = val
        else:
            effective = next((c for c in _CHARACTERS if c["name"] == global_selected), None)
            if effective:
                eff_color = effective["color"]
                eff_emoji = effective["emoji"]
                eff_name  = effective["name"]
                st.markdown(
                    f"<div style='color:#aaa;font-size:0.88em;padding:8px 0'>"
                    f"Inheriting Global: <strong style='color:{eff_color}'>"
                    f"{eff_emoji} {eff_name}</strong></div>",
                    unsafe_allow_html=True,
                )

        # Accept button
        st.markdown("")
        accept_col, clear_col = st.columns(2)
        with accept_col:
            if st.button("✓ Accept", type="primary", use_container_width=True, key=f"rt_accept_{phrase_key}"):
                overrides = st.session_state.get("rt_phrase_overrides", {})
                if chosen:
                    overrides[phrase_key] = chosen
                else:
                    overrides.pop(phrase_key, None)
                st.session_state["rt_phrase_overrides"] = overrides
                # Auto-advance to next phrase
                if idx < n - 1:
                    st.session_state["rt_phrase_idx"] = idx + 1
                st.rerun()
        with clear_col:
            if st.button("Clear override", use_container_width=True, key=f"rt_clear_{phrase_key}"):
                overrides = st.session_state.get("rt_phrase_overrides", {})
                overrides.pop(phrase_key, None)
                st.session_state["rt_phrase_overrides"] = overrides
                st.rerun()

    with right_col:
        # Summary of all overrides so far
        overrides = st.session_state.get("rt_phrase_overrides", {})
        if overrides:
            st.markdown("**Phrase overrides**")
            for i, p in enumerate(phrases):
                pid = getattr(p, "item_id", f"phrase_{i}")
                if pid in overrides:
                    c = next((ch for ch in _CHARACTERS if ch["name"] == overrides[pid]), None)
                    color = c["color"] if c else "#aaa"
                    st.markdown(
                        f"<span style='color:{color}'>● Phrase {i+1}: {overrides[pid]}</span>",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                f"<div style='color:#aaa;font-size:0.88em;padding:8px 0'>"
                f"No overrides yet — all phrases will use Global: "
                f"<strong>{global_selected}</strong></div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(project=None) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    selected = st.session_state.get("retransform_selected", None)
    selected_color = next((c["color"] for c in _CHARACTERS if c["name"] == selected), None)

    st.markdown("## ReTransform Global")
    st.markdown(
        "Pick a character for the estim output. All five are shown — browse, compare, then select one. "
        "Each card shows the electrode path, the 1–2 sliders that matter most, and what you'll feel."
    )

    # Banner — confirms selection, offers next step
    _render_banner(selected, selected_color)

    if selected:
        proceed_col, _ = st.columns([1, 3])
        with proceed_col:
            if st.button("Proceed to ReTransform Phrases →", type="primary", use_container_width=True):
                st.session_state["retransform_show_phrases"] = True
                st.rerun()

    st.divider()

    # Five cards in one row
    cols = st.columns(5, gap="small")
    for char, col in zip(_CHARACTERS, cols):
        is_selected = selected == char["name"]
        _render_card(char, is_selected, col)

    # Advanced expander at the bottom
    st.divider()
    with st.expander("Advanced — full parameter control"):
        st.info(
            "Full parameter control coming soon. "
            "These will expose all alpha/beta generation, frequency, and pulse settings "
            "for the selected character."
        )

    # ReTransform Phrases — only shown after Global selection
    if selected and st.session_state.get("retransform_show_phrases", False):
        _render_phrases(selected, selected_color, project)
