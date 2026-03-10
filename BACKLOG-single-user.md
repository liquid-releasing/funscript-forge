# Funscript Forge — Single-User Production Backlog

Priority-ordered work items to make Funscript Forge production-ready for a single local user.
Items are drawn from the main backlog, open GitHub issues, and fresh assessment.

---

## Priority 1 — Core Workflow (Blockers) ✅ COMPLETE

All four blockers fixed in commits `db8b335` and `6dbfeb6` on `single_user_implementation`.

### ~~1.1 Validate position boundaries after transforms~~ · [#9](https://github.com/liquid-releasing/funscript-forge/issues/9) ✅

`_clamp_sort_dedup()` in `export_panel.py` clamps every `pos` to [0, 100] and shows a
warning banner if any action was clamped.  15 unit tests added in `tests/test_export_integrity.py`.

### ~~1.2 Validate timestamp ordering and deduplicate before export~~ · [#10](https://github.com/liquid-releasing/funscript-forge/issues/10) ✅

Same `_clamp_sort_dedup()` call sorts by `at` and deduplicates (last-write wins) before
every download.  Covered by the same 15 unit tests.

### ~~1.3 Record exact transform parameters in export log~~ · [#12](https://github.com/liquid-releasing/funscript-forge/issues/12) ✅

`_build_export_log()` constructs a `_forge_log` dict embedded in every downloaded funscript.
Records transform name, parameters, source (Phrase/Pattern Editor or Recommended), and export
timestamp for each change.

### ~~1.4 Wire transformer and customizer into the Streamlit UI~~ · [#4](https://github.com/liquid-releasing/funscript-forge/issues/4) ✅

`run_pipeline_in_memory()` added to `ui/common/pipeline.py`.  `_render_pipeline_section()`
added to `export_panel.py` — collapsible expander with BPM threshold + amplitude scale sliders,
Stage 2 toggle, ▶ Run Pipeline button, and a separate ⬇ Download pipeline result button.
11 integration tests added in `tests/test_integration.py`.  Total test count: 498.

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

## Priority 6 — Distribution (This Sprint)

Items required to ship the single-user packaged executable to an end user.

### 6.1 PyInstaller Windows build pipeline · `packaging`

`launcher.py`, `funscript_forge.spec`, and `build.bat` created.  Remaining work:

- Test the built exe against all three sample funscripts
- Confirm Streamlit static assets are correctly bundled (white-screen risk)
- Confirm pattern catalog and user_transforms paths resolve inside `_MEIPASS`
- Add `media/funscriptforge.ico` icon (convert existing PNG with Pillow or ImageMagick)
- Measure cold-start time; optimize if > 15 s

### 6.2 Output and user-data directory for frozen exe · `packaging`

When running frozen, `output/` must be placed next to the exe (not inside `_MEIPASS`
which is read-only on each launch).  Patch `cli.py`, `project.py`, and `pattern_catalog.py`
to resolve writable directories relative to `sys.executable` (frozen) or `__file__` (dev).

### 6.3 Windows installer (NSIS or Inno Setup) · `packaging`

Wrap `dist/FunscriptForge/` in a one-click installer:

- Install to `%LOCALAPPDATA%\FunscriptForge\`
- Create Start Menu shortcut and optional Desktop shortcut
- Add uninstaller

### 6.4 Auto-update mechanism · `packaging`

For a single known user, the simplest path is a `check_for_update()` call on startup
that compares a `VERSION` file against a GitHub release tag and shows a banner if a
newer build is available (no silent auto-install required for v1).

### 6.5 GitHub Release and distribution artifact · `packaging`

- Add `VERSION` file (semver, currently `0.5.0`)
- Create a GitHub Actions workflow (`release.yml`) that builds the exe on push to a
  `release/*` tag and uploads `FunscriptForge-win64.zip` as a release asset
- Document the release process in `CONTRIBUTING.md`

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
