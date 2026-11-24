# Ablation study, 2026-11-24 (v3.0.0)

Which layers of the skill change agent behavior, measured blind on the cases in
[evals.json](evals.json). Re-run it after large changes to `SKILL.md` or the
references.

## Method

- **Variants.** Full skill; `SKILL.md` with scripts and assets but no
  `references/`; full minus `design-quality.md`; full minus `platforms.md`; no
  skill at all.
- **Runs.** One mid-tier agent (Claude Sonnet) per variant answered all 39
  requests in one session, reading the skill as it normally would. Each answer
  is the plan it would act on: approach, first files and commands, what it
  refuses or asks, and what it reports as verified. Requests carried anonymous
  ids (`C01`-`C39`); the variant folders contained no `evals/` or `tests/`.
- **Grading.** Three graders (Claude Opus) each scored 13 cases, seeing the five
  answers per case under labels shuffled per case and the case's
  `expected_output`. Scores: 2 pass, 1 partial, 0 fail; fatal failures from the
  [rubric](rubric.md). Graders were told to judge behavior, not vocabulary, so
  naming this skill's tools earns nothing.

## Results

| Variant | Mean (0-2) | Pass | Fail | Fatal |
|---|---|---|---|---|
| Full skill | 1.90 | 35 | 0 | 0 |
| `SKILL.md` only | 1.56 | 23 | 1 | 0 |
| No `design-quality.md` | 1.90 | 35 | 0 | 0 |
| No `platforms.md` | 1.69 | 27 | 0 | 0 |
| No skill | 0.79 | 6 | 14 | 10 |

- **The skill as a whole** removes every fatal failure. Without it, agents
  edited production before approval, put audience pitches into ARIA and JSON,
  inferred a history reset and treated static checks as sign-off.
- **`SKILL.md`** carries about 70% of the gain (0.79 to 1.56); it holds the
  gates and the firewall, which decide most cases.
- **References** add the rest, mainly on system extraction (converting existing
  CSS tokens into a second store without them), approval edge cases, content
  classification, native prototypes and scaffold slots.
- **`platforms.md`**: its removal cost 0.21, mostly on cases unrelated to
  platforms, which points to run-to-run variance rather than the file.
- **`design-quality.md`**: no difference at this level. It governs the craft of
  the rendered result, which plan-level answers cannot show.

## What changed because of it

Even with the full skill, the email, CLI, backend-only, landing-page and
system-extraction cases scored partial: the runner read few references, so
medium rules and edge cases stated only there were missed. `SKILL.md` now routes
each non-web target to its `platforms.md` section in the triage table, adds a
backend-only row with the rule to stop when a visible effect appears, states
that an existing token format stays the only source, asks the direction note to
name the generic defaults to avoid, and spells out slot filling and that
approval never carries over to a later edit, restored version or revoked
status.

A blind A/B rerun of ten affected cases (previous full skill against the
revised one) moved the five targeted cases from partial to pass; three
unrelated cases dropped by one point. The two that pointed at missing wording
(approval carry-over, unsupported slots) were tightened afterwards. The total
went from 13 to 15 of 20.

## Limits

- One run per variant: differences under about 0.2 are within noise. When the
  previous full-skill answers were scored again by another grader, 3 of 10
  scores differed by one point.
- Plans, not artifacts: rendered craft, real tool use and platform fidelity
  were not exercised. Judge `design-quality.md` with built and rendered
  deliverables, scored against its critique rubric.
- Graders and runners are language models; treat the result as directional
  evidence, not a benchmark.
