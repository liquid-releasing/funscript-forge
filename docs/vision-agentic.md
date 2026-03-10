# Funscript Forge — Visionary Agentic AI Roadmap

## The vision

An autonomous AI pipeline that takes raw video as input and produces
a professionally crafted, multi-sensory haptic experience — with no human
scripting required. Funscript Forge is the quality engine at the centre of
that pipeline.

---

## The ecosystem

### Open-source components available today

| Project | Role |
| --- | --- |
| **Funscript Forge** | Motion structure analysis, behavioral classification, transform pipeline |
| **PythonDancer** | Video analysis → raw funscript generation (motion detection from video frames) |
| **Restim** | Multi-axis estim pattern generation + funscript-to-estim conversion |
| **MultiFunPlayer** | Multi-device playback, funscript routing, device sync |
| **OpenFunscripter** | Manual scripting + existing community tooling |
| **Whisper / Wav2Vec** | Audio beat detection, scene cut detection, speech timing |
| **CLIP / BLIP** | Video scene classification (genre, intensity, mood tagging) |
| **SceneDetect** | Fast scene boundary detection |
| **ffmpeg** | Video preprocessing, frame extraction, audio separation |

---

## Proposed agentic architecture

```
                    ┌────────────────────────────────┐
                    │         Orchestrator Agent      │
                    │   (Claude / GPT-4 function API) │
                    │   Plans, delegates, validates   │
                    └──────┬─────────┬────────────────┘
                           │         │
          ┌────────────────▼──┐   ┌──▼──────────────────┐
          │  Analysis Agent   │   │  Transform Agent     │
          │  PythonDancer     │   │  Funscript Forge     │
          │  SceneDetect      │   │  assess → classify   │
          │  CLIP / BLIP      │   │  → auto-transform    │
          │  Whisper          │   │  → export            │
          └────────┬──────────┘   └──────────┬──────────┘
                   │                         │
          ┌────────▼──────────┐   ┌──────────▼──────────┐
          │  Beat/Audio Agent │   │  Multi-Device Agent  │
          │  Librosa / BeatNet│   │  Restim pattern gen  │
          │  Scene-to-beat    │   │  MultiFunPlayer sync │
          │  alignment        │   │  Device profile mgr  │
          └───────────────────┘   └─────────────────────┘
                   │                         │
                   └──────────┬──────────────┘
                              │
                   ┌──────────▼──────────────┐
                   │   Quality Agent          │
                   │   Funscript Forge        │
                   │   (validate, score,      │
                   │    reject / re-run)      │
                   └──────────────────────────┘
```

---

## What the pipeline could do

### Fully automated mode

```
Input: raw video file
   │
   ▼
1. Scene analysis (CLIP + SceneDetect)
   Detect: cuts, genre tags, intensity curve, mood arc
   │
   ▼
2. Audio analysis (Whisper + Librosa)
   Detect: beat grid, BPM transitions, bass events, vocal peaks
   │
   ▼
3. Motion generation (PythonDancer)
   Produce raw funscript from optical flow + audio cues
   │
   ▼
4. Quality assessment (Funscript Forge — assess)
   Classify phrases: stingy, frantic, drone, giggle, etc.
   │
   ▼
5. Auto-transform (Funscript Forge — export-plan --apply)
   Apply recommended transforms per behavioral tag
   │
   ▼
6. Multi-device routing (Restim + MultiFunPlayer config)
   Map stroke axis to L/R estim channels
   Generate estim pattern variants (edge, buildup, release)
   │
   ▼
7. Quality gate (Funscript Forge — validate)
   Score output: smoothness, range use, device safety limits
   If score < threshold → re-run with adjusted parameters
   │
   ▼
Output: .funscript + .restim + .mfp config
```

### Human-in-the-loop mode

Same pipeline, but the Orchestrator pauses at steps 4–5 and opens the
Funscript Forge UI for review. Human accepts, rejects, or edits transforms.
Pipeline resumes on confirmation.

---

## Agentic AI layer — what Claude adds

| Capability | How Claude contributes |
| --- | --- |
| Intent understanding | Parse natural language requests: "make the climax more intense but keep the buildup slow" |
| Parameter reasoning | Translate intent to transform parameters: `amplitude_scale factor=1.4`, `beat_accent strength=0.6` |
| Multi-step planning | Orchestrate the full pipeline; retry failed steps with adjusted params |
| Quality evaluation | Read assessment JSON, reason about behavioral tags, decide if output is good enough |
| Explanation | Generate human-readable notes on what was changed and why |
| Style learning | Learn user's preferences from accepted/rejected transforms; adapt future runs |

---

## Monetisation potential

### Pricing models

| Model | Target | Price point | Rationale |
| --- | --- | --- | --- |
| **Per-video processing** | Casual creators | $1–3 per video | Low friction, usage-based |
| **Creator subscription** | Regular scripters | $15–25/month | Unlimited processing, history |
| **Studio API** | Platforms, agencies | $99–299/month | Bulk volume, priority queue |
| **White-label pipeline** | Device manufacturers | $500–2,000/month | Embedded in firmware OTA |
| **Enterprise licence** | Large studios | Custom ($5k+/year) | On-prem, SLA, support |

### Revenue scenarios

| Scenario | Users | MRR | ARR |
| --- | --- | --- | --- |
| MVP (creators only) | 200 × $15 | $3,000 | $36,000 |
| Growth (mixed) | 500 × $15 + 30 × $150 | $12,000 | $144,000 |
| Scale (API + studios) | 1,000 × $20 + 20 × $200 | $24,000 | $288,000 |
| White-label (2 OEM deals) | — + 2 × $1,500 | $3,000 add-on | $36,000 add-on |

### What justifies premium pricing
1. **Time savings** — manual scripting of a 30-min video takes 4–8 hours; automated pipeline takes < 2 minutes
2. **Quality uplift** — behavioral classification catches issues a human would miss on pass-one
3. **Device safety** — quality gate enforces velocity limits and range constraints automatically
4. **Multi-device** — one upload → outputs for linear, rotational, and estim devices simultaneously
5. **Learning** — system improves per-user over time; cold-start problem solved by shared catalog

---

## Near-term integration opportunities

### Funscript Forge + PythonDancer (3–4 months)

PythonDancer generates a raw script from video. Funscript Forge cleans it up.
A simple CLI pipe:

```bash
python dancer.py input.mp4 | python cli.py assess - | python cli.py export-plan - --apply
```

### Funscript Forge + Restim (2–3 months)

Restim needs a clean motion signal. Funscript Forge post-processed scripts
produce better estim patterns because behavioral noise is removed.

Integration: `cli.py export` → `restim convert --input edited.funscript`

### Full agentic loop (6–12 months)

Claude as orchestrator, calling Funscript Forge and PythonDancer as tool-use
functions. The LLM reasons about quality, retries failed transformations, and
generates a session report for the user.

---

## What makes this defensible

- **Domain-specific behavioral taxonomy** — the 8-tag classification system is
  unique to Funscript Forge; competitors use raw waveform processing only
- **Cross-script pattern catalog** — accumulates institutional knowledge with
  every script processed; a moat that grows with usage
- **Pipeline composability** — each stage is independently callable and
  testable; easy to slot into any agentic framework
- **Community trust** — open-source core builds trust with script authors who
  are protective of their work
