# Changelog

## 3.0.0 — 2026-11-24

- Self-contained, project-local design skill for any file-capable agent; no other skill, editor or runtime has to be installed.
- One operating loop (orient, triage, direct, build, render and critique, deliver) with a fixed report separating verified from unverified work.
- Design quality standard: direction-setting, hierarchy, type, color and contrast, states, motion, accessibility, internationalization, anti-patterns of the generic AI look, and a scored critique rubric; new `critique` mode.
- Platform and medium profiles for web, iOS/iPadOS, Android, macOS, Windows, Linux, browser extensions, CLI/TUI, email, print, slides, TV, watch and spatial targets.
- `pfui.py` front door: `doctor`, `status`, `init` (system, app, site, deck, doc), `serve` with a localhost review harness and per-state URLs, and a one-command `check`.
- DTCG token pipeline with per-mode contrast checks, OKLCH ramp generation and builds to CSS, iOS asset catalogs and Swift, Android resources and Flutter.
- 46-rule static design lint covering names, focus, contrast, target sizes, type/color/radius/shadow discipline, motion, placeholders, assets and email.
- Accessible starter design system (203 tokens, 116 passing contrast checks across light and dark), components in cascade layers with platform and density adaptation, and scaffolds whose copy is left as explicit `{{slot}}` decisions.
- Project-owned design-review.json is the only approval record, with a whole-file `review` gate and upgrade guidance for 2.x projects.
- UI implementation gate checks all declared prototype files and current mappings, including binary assets.
- Revised behavior evaluations, rubric dimensions for craft and platform fit, and isolated self-tests for the new tools.
- Blind ablation of the skill's layers ([evals/ablation.md](evals/ablation.md)); its findings tightened triage routing to platform rules, the backend-only exit, token-source ownership, slot filling and approval carry-over.

## 2.1.0 — 2026-09-29

- UI audit, prototype, approval, implementation, and verification workflows.
- Versioned prototype approval through an external design skill.
- DOM content auditing and multimodal source tracking.
- Repository cleanup with verified recovery snapshots.
- English and Chinese usage guides.
- Validated ZIP releases through GitHub Actions.
