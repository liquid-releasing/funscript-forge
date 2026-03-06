import json
import matplotlib.pyplot as plt

'''
This script plots:

the raw funscript motion curve

phase boundaries

cycle boundaries

phrase boundaries

'''

# ------------------------------------------------------------
# INPUT FILES
# ------------------------------------------------------------

FUNSCRIPT = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\VictoriaOaks - Wet Dreams.stingy.funscript"
PHASES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\phase_segments.json"
CYCLES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\cycle_segments.json"
PHRASES = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\phrase_boundaries.json"
OUTPUT = r"C:\Users\bruce\projects-lqr\VictoriaOaks_-_Wet_Dreams\working_gen\motion_visualization.png"

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
with open(FUNSCRIPT) as f:
    fs = json.load(f)["actions"]

with open(PHASES) as f:
    phases = json.load(f)

with open(CYCLES) as f:
    cycles = json.load(f)

with open(PHRASES) as f:
    phrases = json.load(f)

# ------------------------------------------------------------
# PLOT
# ------------------------------------------------------------
times = [a["at"] for a in fs]
positions = [a["pos"] for a in fs]

plt.figure(figsize=(16, 8))
plt.plot(times, positions, label="Motion Curve", color="black", linewidth=1)

# Phase boundaries
for ph in phases:
    plt.axvline(ph["start"], color="blue", alpha=0.3)
    plt.axvline(ph["end"], color="blue", alpha=0.3)

# Cycle boundaries
for cy in cycles:
    plt.axvline(cy["start"], color="green", alpha=0.3)
    plt.axvline(cy["end"], color="green", alpha=0.3)

# Phrase boundaries
for pr in phrases:
    plt.axvline(pr["start"], color="red", alpha=0.4, linewidth=2)
    plt.axvline(pr["end"], color="red", alpha=0.4, linewidth=2)

plt.title("Motion Structure Visualization")
plt.xlabel("Time (ms)")
plt.ylabel("Position")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(OUTPUT)
plt.show()