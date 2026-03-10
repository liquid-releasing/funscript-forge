# Funscript Forge — Single-User Production Backlog

Priority-ordered work items to make Funscript Forge production-ready for a single local user.
Items are drawn from the main backlog, open GitHub issues, and fresh assessment.

---

## Priority 1 — Core Workflow (Blockers)

These items must be complete before the product is usable end-to-end.

### 1.1 Validate position boundaries after transforms · [#9](https://github.com/liquid-releasing/funscript-forge/issues/9) `bug`

Transforms can push `pos` values outside 0–100. Add a post-transform clamp pass and surface a
warning in the Export panel when any action was clamped.

### 1.2 Validate timestamp ordering and deduplicate before export · [#10](https://github.com/liquid-releasing/funscript-forge/issues/10) `bug`

After stitching transformed slices back into the timeline, the result may contain duplicate `at`
values or out-of-order entries. Validate and fix before writing the download file.

### 1.3 Record exact transform parameters in export log · [#12](https://github.com/liquid-releasing/funscript-forge/issues/12) `enhancement`

The downloaded funscript should include (or accompany) a log of exactly which transforms were
applied with which parameters so the user can reproduce or adjust a previous session.

### 1.4 Wire transformer and customizer into the Streamlit UI · [#4](https://github.com/liquid-releasing/funscript-forge/issues/4) `enhancement ui`

The backend `FunscriptTransformer` (suggested_updates/) and `WindowCustomizer`
(user_customization/) are not yet exposed in the UI. Expose a "Run pipeline" flow that lets the
user apply the full assess → transform → customize chain from the browser.

---

## Priority 2 — Friction Reduction (High Value for Solo Use)

### 2.1 Upload funscripts via browser · [#5](https://github.com/liquid-releasing/funscript-forge/issues/5)

Add `st.file_uploader` to the sidebar. Save uploaded file to `output/uploads/`. Removes the
requirement to manually copy files to `test_funscript/`.

### 2.2 Automated quality gate · [#13](https://github.com/liquid-releasing/funscript-forge/issues/13) `enhancement`

After export, run a velocity-limits and device-safety-range check on the result and show a
pass/fail badge with specific warnings (e.g. "3 actions exceed 200 pos/s").

### 2.3 Progress indicator for long assessments · [#14](https://github.com/liquid-releasing/funscript-forge/issues/14) `enhancement`

Long funscripts (60+ min) can take several seconds to assess. Show a progress spinner / bar and
allow cancellation.

---

## Priority 3 — Usability Polish

### 3.1 Clean up UI tabs · [#7](https://github.com/liquid-releasing/funscript-forge/issues/7)

Current tab bar has 6 tabs. Remove or merge stale tabs. Target order:

1. Phrase Selector (viewer)
2. Pattern Editor
3. Transform Catalog (reference only)
4. Export

### 3.2 Undo / redo for accepted phrase transforms · [#15](https://github.com/liquid-releasing/funscript-forge/issues/15) `enhancement`

Let the user undo the last accepted transform (or redo after undo) from the Export panel.

### 3.3 Onboarding flow and guided first-run experience · [#16](https://github.com/liquid-releasing/funscript-forge/issues/16) `enhancement`

When no project is loaded, show a welcome screen with step-by-step instructions.

---

## Priority 4 — Documentation & Support

### 4.1 MkDocs user documentation site · [#17](https://github.com/liquid-releasing/funscript-forge/issues/17) `enhancement documentation`

MkDocs + Material theme covering: Getting Started, Assessment, Behavioral Tags (all 8), Transforms
reference, Pattern Editor, Export, CLI reference.

### 4.2 In-app AI assistant · [#18](https://github.com/liquid-releasing/funscript-forge/issues/18) `enhancement ui`

Claude API-backed assistant in the sidebar. Context-aware (current phrase tags/BPM/span sent as
system context). Explains tags, recommends transforms, answers parameter questions.
Gracefully disabled when no API key is configured.

---

## Priority 5 — Quality & Reliability

### 5.1 Smoke-test Streamlit app against all three test funscripts · [#1](https://github.com/liquid-releasing/funscript-forge/issues/1) `testing ui`

Formal smoke test: load each of the three test funscripts, verify assessment completes without
error, verify export produces a valid JSON funscript.

### 5.2 Fix uniform-tempo funscript segmentation · [#2](https://github.com/liquid-releasing/funscript-forge/issues/2) `assessment improvement`

VictoriaOaks (1:33:12) produces a single phrase because the uniform BPM never triggers a
transition. Add duration-based phrase splitting as a fallback.

### 5.3 Fix Streamlit `use_container_width` deprecation warnings

Minor: suppress deprecation warnings in the sidebar layout.

---

## Out of Scope for Single-User Phase

These items are explicitly deferred until the SaaS / multi-user phase:

- **REST API** ([#8](https://github.com/liquid-releasing/funscript-forge/issues/8)) — needed for SaaS, not local use
- **FastAPI + frontend scaffold** ([#3](https://github.com/liquid-releasing/funscript-forge/issues/3)) — SaaS only
- **Upload and sync media/audio** ([#6](https://github.com/liquid-releasing/funscript-forge/issues/6)) — nice-to-have, not blocking

---

## Assessment: Current State of the Tag → Transform → Export Loop

*Assessed 2026-03-10 against branch `main` (v0.5.0).*

### What works ✅

- Assessment pipeline fully produces behavioral tags on every phrase
- Phrase Editor: single-phrase transform selection with live preview chart
- Pattern Editor: batch-apply a transform to all phrases sharing a behavioral tag; split phrases at cycle boundaries; save patterns to catalog
- Export panel: auto-suggests transforms for unhandled phrases (via `suggest_transform()`); accept/reject UI; download button applies all accepted transforms and returns a modified funscript JSON
- Tab cross-navigation: Assessment "Focus" button → Phrase Editor; Pattern Editor "Edit" button → Phrase detail

### Gaps identified ⚠️

| Gap | Severity | Linked issue |
|-----|----------|--------------|
| No post-transform position clamp (pos can exceed 0–100) | High — corrupts output | #9 |
| No timestamp dedup/sort after slice stitching | High — invalid funscript output | #10 |
| No export log — applied params not recorded | Medium — reproducibility | #12 |
| Backend FunscriptTransformer and WindowCustomizer not wired to UI | Medium — users can't use the full pipeline from the browser | #4 |
| No error recovery if `TRANSFORM_CATALOG[key]` lookup fails | Medium — silent crash in export | — |
| `suggest_transform()` result not validated against `TRANSFORM_CATALOG` | Low | — |
| Pattern catalog assumes saved files exist — no graceful missing-file handling | Low | — |

### Recommended first fix

**#9 + #10** are the highest-risk bugs — they can silently produce corrupted output files. Fix both as a single PR before any other work.

---

*© 2026 [Liquid Releasing](https://github.com/liquid-releasing). Licensed under the [MIT License](LICENSE).  Written by human and Claude AI (Claude Sonnet).*
