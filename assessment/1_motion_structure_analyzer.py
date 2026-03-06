import json
import math
import os

'''
What this script gives you
1. Phase segmentation
Fine‑grained direction‑based segments.

2. Cycle clustering
Each cycle is a full oscillation.

3. Pattern detection
Cycles grouped into repeating types.

4. Phrase boundaries
Long‑form structural sections where the pattern stays consistent.

This is the complete structural analysis pipeline. 

You can use the outputs to create beat‑aware transformations, or just to understand the structure of the original performance.
'''
# ------------------------------------------------------------
# INPUT / OUTPUT PATHS
# ------------------------------------------------------------
INPUT = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\VictoriaOaks - Wet Dreams.stingy.funscript"
OUT_PHASES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\phase_segments.json"
OUT_CYCLES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\cycle_segments.json"
OUT_PATTERNS = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\cycle_patterns.json"
OUT_PHRASES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\phrase_boundaries.json"

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
MIN_VELOCITY = 0.02
MIN_PHASE_DURATION = 80
DURATION_TOLERANCE = 0.20
VELOCITY_TOLERANCE = 0.25

# ------------------------------------------------------------
# LOAD FUNSCRIPT
# ------------------------------------------------------------
with open(INPUT) as f:
    data = json.load(f)

actions = data["actions"]

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def velocity(p0, p1, t0, t1):
    dt = max(1, t1 - t0)
    return (p1 - p0) / dt

def describe_phase(avg_vel):
    if avg_vel > MIN_VELOCITY:
        return "steady upward motion"
    elif avg_vel < -MIN_VELOCITY:
        return "steady downward motion"
    else:
        return "low-motion plateau"

def phase_direction(label):
    label = label.lower()
    if "upward" in label:
        return "up"
    if "downward" in label:
        return "down"
    return "flat"

def cycle_duration(cycle):
    return cycle["end"] - cycle["start"]

def cycle_avg_velocity(cycle):
    dur = cycle_duration(cycle)
    return 1.0 / max(1, dur)

def cycles_are_similar(a, b):
    dur_a = cycle_duration(a)
    dur_b = cycle_duration(b)
    if abs(dur_a - dur_b) > DURATION_TOLERANCE * max(dur_a, dur_b):
        return False
    if a["label"] != b["label"]:
        return False
    vel_a = cycle_avg_velocity(a)
    vel_b = cycle_avg_velocity(b)
    if abs(vel_a - vel_b) > VELOCITY_TOLERANCE * max(vel_a, vel_b):
        return False
    return True

def ms_to_timestamp(ms):
    """
    Convert milliseconds → HH:MM:SS.mmm
    Always returns zero‑padded, human‑readable timestamps.
    """
    if ms < 0:
        ms = 0

    hours = ms // 3_600_000
    ms %= 3_600_000

    minutes = ms // 60_000
    ms %= 60_000

    seconds = ms // 1_000
    milliseconds = ms % 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

# ------------------------------------------------------------
# STEP 1 — PHASE DETECTION
# ------------------------------------------------------------
phases = []
phase_start_index = 0
phase_velocities = []

for i in range(1, len(actions)):
    t_prev = actions[i-1]["at"]
    t_curr = actions[i]["at"]
    p_prev = actions[i-1]["pos"]
    p_curr = actions[i]["pos"]

    v = velocity(p_prev, p_curr, t_prev, t_curr)
    phase_velocities.append(v)

    current_dir = 1 if v > MIN_VELOCITY else -1 if v < -MIN_VELOCITY else 0

    if len(phase_velocities) > 1:
        prev_v = phase_velocities[-2]
        prev_dir = 1 if prev_v > MIN_VELOCITY else -1 if prev_v < -MIN_VELOCITY else 0
    else:
        prev_dir = current_dir

    if current_dir != prev_dir:
        start_t = actions[phase_start_index]["at"]
        end_t = actions[i-1]["at"]

        if end_t - start_t >= MIN_PHASE_DURATION:
            avg_vel = sum(phase_velocities[:-1]) / max(1, len(phase_velocities[:-1]))
            phases.append({
                "start": start_t,
                "end": end_t,
                "label": describe_phase(avg_vel),
            })

        phase_start_index = i - 1
        phase_velocities = [v]

if phase_velocities:
    start_t = actions[phase_start_index]["at"]
    end_t = actions[-1]["at"]
    if end_t - start_t >= MIN_PHASE_DURATION:
        avg_vel = sum(phase_velocities) / max(1, len(phase_velocities))
        phases.append({
            "start": start_t,
            "end": end_t,
            "label": describe_phase(avg_vel)
        })

with open(OUT_PHASES, "w") as f:
    json.dump(phases, f, indent=2)

print(f"Saved {len(phases)} phases → {OUT_PHASES}")

# ------------------------------------------------------------
# STEP 2 — CYCLE DETECTION
# ------------------------------------------------------------
cycles = []
current_cycle = []
current_dir = None

for ph in phases:
    ph_dir = phase_direction(ph["label"])

    if not current_cycle:
        current_cycle.append(ph)
        current_dir = ph_dir
        continue

    if ph_dir != current_dir:
        current_cycle.append(ph)
        current_dir = ph_dir
    else:
        cycle_start = current_cycle[0]["start"]
        cycle_end = current_cycle[-1]["end"]
        desc = " → ".join(phase_direction(p["label"]) for p in current_cycle)

        cycles.append({
            "start": cycle_start,
            "end": cycle_end,
            "label": desc
        })

        current_cycle = [ph]
        current_dir = ph_dir

if current_cycle:
    cycle_start = current_cycle[0]["start"]
    cycle_end = current_cycle[-1]["end"]
    desc = " → ".join(phase_direction(p["label"]) for p in current_cycle)
    cycles.append({
        "start": cycle_start,
        "end": cycle_end,
        "label": desc,
    })

with open(OUT_CYCLES, "w") as f:
    json.dump(cycles, f, indent=2)

print(f"Saved {len(cycles)} cycles → {OUT_CYCLES}")

# ------------------------------------------------------------
# STEP 3 — REPEATING PATTERN DETECTION
# ------------------------------------------------------------
patterns = []
assigned = [False] * len(cycles)

for i, base_cycle in enumerate(cycles):
    if assigned[i]:
        continue

    group = [base_cycle]
    assigned[i] = True

    for j in range(i + 1, len(cycles)):
        if assigned[j]:
            continue
        if cycles_are_similar(base_cycle, cycles[j]):
            group.append(cycles[j])
            assigned[j] = True

    pattern_label = base_cycle["label"]
    avg_duration = sum(cycle_duration(c) for c in group) / len(group)

    patterns.append({
        "pattern_label": pattern_label,
        "avg_duration": avg_duration,
        "count": len(group),
        "cycles": group
    })

with open(OUT_PATTERNS, "w") as f:
    json.dump(patterns, f, indent=2)

print(f"Saved {len(patterns)} patterns → {OUT_PATTERNS}")

# ------------------------------------------------------------
# STEP 4 — PHRASE BOUNDARY DETECTION
# ------------------------------------------------------------
all_cycles = []
for pattern in patterns:
    for c in pattern["cycles"]:
        all_cycles.append({
            "start": c["start"],
            "end": c["end"],
            "pattern_label": pattern["pattern_label"]
        })

all_cycles.sort(key=lambda x: x["start"])

phrases = []
current_phrase = []
current_label = None

for cycle in all_cycles:
    label = cycle["pattern_label"]

    if not current_phrase:
        current_phrase.append(cycle)
        current_label = label
        continue

    if label == current_label:
        current_phrase.append(cycle)
    else:
        phrase_start = current_phrase[0]["start"]
        phrase_end = current_phrase[-1]["end"]
        phrases.append({
            "start": phrase_start,
            "end": phrase_end,
            "pattern_label": current_label,
            "cycle_count": len(current_phrase),
            "description": f"{len(current_phrase)} cycles of pattern '{current_label}'"
        })

        current_phrase = [cycle]
        current_label = label

if current_phrase:
    phrase_start = current_phrase[0]["start"]
    phrase_end = current_phrase[-1]["end"]
    phrases.append({
        "start": phrase_start,
        "end": phrase_end,
        "pattern_label": current_label,
        "cycle_count": len(current_phrase),
        "description": f"{len(current_phrase)} cycles of pattern '{current_label}'"
    })

with open(OUT_PHRASES, "w") as f:
    json.dump(phrases, f, indent=2)

print(f"Saved {len(phrases)} phrases → {OUT_PHRASES}")
