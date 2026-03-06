import json

'''
This script uses:

- detected cycles
- detected phrases

to generate windows aligned to the beat structure.
A “beat” here is the start of each cycle.

It outputs:

`beat_windows.json`
'''

# ------------------------------------------------------------
# INPUT / OUTPUT
# ------------------------------------------------------------
CYCLES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\cycle_segments.json"
PHRASES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\phrase_boundaries.json"
OUTPUT = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\beat_windows.json"

# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------
with open(CYCLES) as f:
    cycles = json.load(f)

with open(PHRASES) as f:
    phrases = json.load(f)

# ------------------------------------------------------------
# BEAT WINDOWS
# ------------------------------------------------------------
beat_windows = []

for cy in cycles:
    beat_windows.append({
        "start": cy["start"],
        "end": cy["end"],
        "label": f"cycle beat ({cy['label']})"
    })

# Phrase-level windows
for ph in phrases:
    beat_windows.append({
        "start": ph["start"],
        "end": ph["end"],
        "label": f"phrase ({ph['pattern_label']})"
    })

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------
with open(OUTPUT, "w") as f:
    json.dump(beat_windows, f, indent=2)

print("Saved:", OUTPUT)
