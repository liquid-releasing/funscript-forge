# Copyright (c) 2026 Liquid Releasing. Licensed under the MIT License.
# Written by human and Claude AI (Claude Sonnet).

"""eTransforms panel — apply estim character to the funscript.

Five built-in characters:
  Gentle          Soft, slow-building. Good for intimate or slow content.
  Reactive        Sharp, tracks action closely. Good for fast, intense content.
  Scene Builder   Builds gradually over the scene.
  Unpredictable   Random direction changes, varied character.
  Balanced        Middle of everything. A good starting point.

Each character shows:
  • Description card
  • Electrode path preview (alpha/beta geometric shape)
  • 1–2 contextual sliders most relevant to that character
  • "What you'll feel" summary
  • Process button → generates alpha/beta/pulse_frequency outputs
"""

from __future__ import annotations

import math
import sys
import os
from pathlib import Path
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BG   = "rgba(14,14,18,1)"
_GRID = "rgba(80,80,80,0.25)"
_WHITE = "#ffffff"
_BLUE  = "#4a90d9"
_GREEN = "#2ecc71"
_RED   = "#e74c3c"
_DIM   = "rgba(180,180,180,0.5)"

_ETRANSFORMS: List[Dict[str, Any]] = [
    {
        "name": "Gentle",
        "emoji": "🌊",
        "description": "Soft, slow-building. Good for intimate or slow content.",
        "what_youll_feel": "Subtle movement close to center. Pulses build slowly — no sharp onset. Good for warming up or winding down.",
        "sliders": [
            {
                "key": "min_dist",
                "label": "Softness",
                "hint": "How far sensation moves from center. Low = very subtle.",
                "min": 0.05, "max": 0.4, "default": 0.15, "step": 0.01,
                "format": "%.2f",
            },
            {
                "key": "pr_max",
                "label": "Pulse onset",
                "hint": "How gently pulses start. Higher = softer attack.",
                "min": 0.0, "max": 1.0, "default": 0.8, "step": 0.05,
                "format": "%.2f",
            },
        ],
        "path_shape": "semi_circle",
        "color": "#4a90d9",
    },
    {
        "name": "Reactive",
        "emoji": "⚡",
        "description": "Sharp, tracks action closely. Good for fast, intense content.",
        "what_youll_feel": "Wide sweep, instant response to every stroke. Pulse rate spikes with fast action. No lag.",
        "sliders": [
            {
                "key": "freq_ramp",
                "label": "Reactivity",
                "hint": "How tightly sensation follows each stroke. Low = instant.",
                "min": 0.5, "max": 5.0, "default": 1.2, "step": 0.1,
                "format": "%.1f",
            },
            {
                "key": "pf_max",
                "label": "Peak intensity",
                "hint": "Maximum pulse rate during peak action.",
                "min": 0.5, "max": 1.0, "default": 0.9, "step": 0.05,
                "format": "%.2f",
            },
        ],
        "path_shape": "three_quarter",
        "color": "#e74c3c",
    },
    {
        "name": "Scene Builder",
        "emoji": "🏗️",
        "description": "Builds gradually over the scene. Works well for longer content.",
        "what_youll_feel": "Sensation expands slowly over time. The arc widens as the scene develops. Rewards patience.",
        "sliders": [
            {
                "key": "freq_ramp",
                "label": "Build speed",
                "hint": "How gradually sensation builds. High = very slow build.",
                "min": 3.0, "max": 10.0, "default": 7.0, "step": 0.5,
                "format": "%.1f",
            },
            {
                "key": "min_dist",
                "label": "Arc width",
                "hint": "How far the sensation sweeps across.",
                "min": 0.1, "max": 0.6, "default": 0.35, "step": 0.01,
                "format": "%.2f",
            },
        ],
        "path_shape": "circle",
        "color": "#2ecc71",
    },
    {
        "name": "Unpredictable",
        "emoji": "🎲",
        "description": "Random direction changes, varied character. Good for surprise content.",
        "what_youll_feel": "Direction changes without warning. Pulse rate varies widely. Keeps you guessing.",
        "sliders": [
            {
                "key": "min_dist",
                "label": "Wildness",
                "hint": "How wide the random movement ranges. High = very wild.",
                "min": 0.1, "max": 0.6, "default": 0.4, "step": 0.01,
                "format": "%.2f",
            },
            {
                "key": "pulse_freq_ratio",
                "label": "Variety",
                "hint": "How varied the pulse rate is.",
                "min": 1.0, "max": 8.0, "default": 5.0, "step": 0.5,
                "format": "%.1f",
            },
        ],
        "path_shape": "zigzag",
        "color": "#f39c12",
    },
    {
        "name": "Balanced",
        "emoji": "⚖️",
        "description": "Middle of everything. A good starting point for any content.",
        "what_youll_feel": "Moderate sweep, steady build, neither too sharp nor too soft. Works with most content.",
        "sliders": [
            {
                "key": "min_dist",
                "label": "Sweep width",
                "hint": "Width of the sensation sweep.",
                "min": 0.05, "max": 0.6, "default": 0.3, "step": 0.01,
                "format": "%.2f",
            },
            {
                "key": "freq_ramp",
                "label": "Speed / build balance",
                "hint": "More reactive (low) vs. more gradual (high).",
                "min": 1.0, "max": 8.0, "default": 4.0, "step": 0.5,
                "format": "%.1f",
            },
        ],
        "path_shape": "circle",
        "color": "#9b59b6",
    },
]

# ---------------------------------------------------------------------------
# Geometric path preview
# ---------------------------------------------------------------------------

def _path_points(shape: str) -> tuple[list[float], list[float]]:
    """Return (alpha, beta) lists for a geometric path preview."""
    n = 120
    if shape == "semi_circle":
        angles = [math.pi * i / (n - 1) for i in range(n)]
        a = [0.5 + 0.4 * math.cos(t) for t in angles]
        b = [0.5 + 0.4 * math.sin(t) for t in angles]
    elif shape == "three_quarter":
        angles = [1.5 * math.pi * i / (n - 1) + math.pi * 0.75 for i in range(n)]
        a = [0.5 + 0.4 * math.cos(t) for t in angles]
        b = [0.5 + 0.4 * math.sin(t) for t in angles]
    elif shape == "circle":
        angles = [2 * math.pi * i / (n - 1) for i in range(n)]
        a = [0.5 + 0.4 * math.cos(t) for t in angles]
        b = [0.5 + 0.4 * math.sin(t) for t in angles]
    else:  # zigzag
        rng = [i for i in range(n)]
        a, b = [], []
        for i in rng:
            t = i / (n - 1)
            a.append(t)
            b.append(0.5 + 0.4 * math.sin(8 * math.pi * t) * (1 - t * 0.3))
    return a, b


def _path_chart(shape: str, color: str) -> go.Figure:
    a, b = _path_points(shape)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=a, y=b,
        mode="lines",
        line=dict(color=color, width=2),
        showlegend=False,
        hoverinfo="skip",
    ))
    # Start dot (green) and end dot (red)
    fig.add_trace(go.Scatter(x=[a[0]], y=[b[0]], mode="markers",
                             marker=dict(color=_GREEN, size=8), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[a[-1]], y=[b[-1]], mode="markers",
                             marker=dict(color=_RED, size=8), showlegend=False, hoverinfo="skip"))

    fig.update_layout(
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(l=4, r=4, t=4, b=4),
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[-0.05, 1.05], scaleanchor="x"),
        height=140,
    )
    return fig


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(project=None) -> None:
    st.markdown("## eTransforms")
    st.markdown(
        "Pick a character for the estim output. Each one controls how sensation moves and builds. "
        "Tune the 1–2 sliders that matter most, or expand **Advanced** for full control."
    )

    selected = st.session_state.get("etransform_selected", "Balanced")

    # --- Character buttons ---
    cols = st.columns(len(_ETRANSFORMS))
    for col, et in zip(cols, _ETRANSFORMS):
        with col:
            is_selected = selected == et["name"]
            label = f"{'✓ ' if is_selected else ''}{et['emoji']} {et['name']}"
            if st.button(label, key=f"etransform_btn_{et['name']}",
                         use_container_width=True,
                         type="primary" if is_selected else "secondary"):
                st.session_state["etransform_selected"] = et["name"]
                st.rerun()

    # Find selected eTransform data
    et_data = next((e for e in _ETRANSFORMS if e["name"] == selected), _ETRANSFORMS[4])

    st.divider()

    # --- Two-column layout: path + controls ---
    left, right = st.columns([1, 2])

    with left:
        st.markdown(f"#### {et_data['emoji']} {et_data['name']}")
        st.caption(et_data["description"])
        st.plotly_chart(
            _path_chart(et_data["path_shape"], et_data["color"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with right:
        st.markdown("**Tune it**")
        slider_vals = {}
        for spec in et_data["sliders"]:
            key = f"etransform_{et_data['name']}_{spec['key']}"
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

        st.markdown(
            f"<div style='background:#1a1a2e;border-left:3px solid {et_data['color']};"
            f"padding:10px 14px;border-radius:4px;margin-top:12px;font-size:0.9em;"
            f"color:#ccc'>"
            f"<strong>What you'll feel</strong><br>{et_data['what_youll_feel']}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # --- Advanced expander ---
    with st.expander("Advanced — full control"):
        st.info(
            "Full parameter control coming soon. "
            "These will expose all alpha/beta generation, frequency, and pulse settings."
        )

    # --- Apply / Process ---
    st.divider()
    apply_col, info_col = st.columns([1, 3])
    with apply_col:
        if st.button("Apply eTransform →", type="primary", use_container_width=True):
            if project is None:
                st.warning("Load a funscript first (use the Phrases tab).")
            else:
                st.session_state["etransform_config"] = {
                    "name": et_data["name"],
                    "sliders": slider_vals,
                }
                st.success(
                    f"✓ {et_data['name']} applied. "
                    "Go to Export to generate alpha / beta / pulse_frequency outputs."
                )
    with info_col:
        st.caption(
            "Applies globally to the full funscript. "
            "Per-section support (phrase-level character) coming in the next release."
        )
