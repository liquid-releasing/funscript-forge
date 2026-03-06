import json

'''
Automatic Mode‑Window Creation Script

This script uses:

- phrases
- patterns
- cycles

to automatically generate:

- performance windows
- break windows
- default windows

The logic is simple and adjustable:

- long phrases → performance windows
- short phrases → break windows
- everything else → default

'''

# ------------------------------------------------------------
# INPUT / OUTPUT
# ------------------------------------------------------------
PHRASES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\phrase_boundaries.json"
PATTERNS = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\cycle_patterns.json"
OUTPUT = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\auto_mode_windows.json"

# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------
with open(PHRASES) as f:
    phrases = json.load(f)

with open(PATTERNS) as f:
    patterns = json.load(f)

# ------------------------------------------------------------
# MODE WINDOW GENERATION
# ------------------------------------------------------------
mode_windows = {
    "performance": [],
    "break": [],
    "default": []
}

for ph in phrases:
    dur = ph["end"] - ph["start"]

    if ph["cycle_count"] >= 5:
        mode_windows["performance"].append({
            "start": ph["start"],
            "end": ph["end"],
            "label": ph["description"]
        })
    elif ph["cycle_count"] <= 2:
        mode_windows["break"].append({
            "start": ph["start"],
            "end": ph["end"],
            "label": ph["description"]
        })
    else:
        mode_windows["default"].append({
            "start": ph["start"],
            "end": ph["end"],
            "label": ph["description"]
        })

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------
with open(OUTPUT, "w") as f:
    json.dump(mode_windows, f, indent=2)

print("Saved:", OUTPUT)
