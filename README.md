# Prototype-first UI

[中文](README.zh-CN.md)

A design skill for general-purpose AI agents. It makes an agent work like a
senior product designer and a careful engineer: set a direction before pixels,
build on a project-local design system, render and critique the real output,
and keep unreviewed designs out of production. It covers web apps, websites,
dashboards, iOS, Android and desktop apps, browser extensions, CLI/TUI, email,
slides, print documents, diagrams and design systems.

One `SKILL.md` routes each request to the few references it needs. Tools are
optional, standard-library Python; any file-capable agent can follow the skill
without them.

## What an agent gets

- **A loop**: orient, triage, direct, build, render and critique, deliver, with
  a fixed report that separates what was verified from what was not.
- **A quality standard**: direction-setting, hierarchy, type, color and
  contrast, states, motion, accessibility, internationalization, the
  anti-patterns of the generic "AI default" look, and a scored critique rubric.
- **Platform profiles**: web, iOS and iPadOS, Android, macOS, Windows, Linux,
  browser extensions, CLI/TUI, email, print, slides, TV, watch and spatial.
- **A starter design system**: 203 DTCG tokens with light and dark modes, 58
  declared contrast pairs (116 checks) that all pass, components in cascade
  layers, and a live gallery; scaffolds for apps, sites, decks and documents.
- **Tools** (`scripts/pfui.py`): environment doctor, status, scaffolding, a
  localhost review harness, a one-command check, a 46-rule design lint, and a
  token pipeline from one source to CSS, iOS, Android and Flutter.
- **Governance**: content firewall (the brief never becomes UI copy), explicit
  approval gate for product UI, untrusted-media policy, sanitized fixtures and
  verified recovery snapshots for the optional history reset.

## Quick start

From the target project, after installing the skill (see below):

```sh
S=.agents/skills/prototype-first-ui/scripts
python $S/pfui.py doctor                                   # what can this machine verify?
python $S/pfui.py init system --name "Harbor"              # tokens, components, gallery
python $S/pfui.py init app --name "Orders" --platform ios  # prototype shell with state views
python $S/pfui.py serve designs                            # http://127.0.0.1:8765/__pfui/review.html
python $S/pfui.py check                                    # records, tokens, contrast, lint
```

Then ask your agent, for example:

```text
$prototype-first-ui critique
Review our settings page at mobile and desktop widths in light and dark, score it
against the quality rubric with screenshots, and rank the fixes.
```

## Modes

| Mode | Deliverable |
|---|---|
| `system` | Tokens, themes, components, gallery and consumption recipe |
| `critique` | Evidence-backed quality review scored against the rubric |
| `prototype` / `explore` | Screens, flows and alternative structures with every state reachable by URL |
| `compose` | Slides, documents, posters, social images, diagrams, email |
| `visualize` | Charts and dashboards with defined metrics and checked data |
| `audit`, `approve`, `implement`, `verify`, `sync` | The product UI lifecycle |
| `bootstrap` | Optional repository cleanup and local history reset with a recovery snapshot |

Product UI keeps the gate: audit, prototype, review, explicit approval,
design-only commit, implementation gate, one implemented slice, verification.
Standalone artifacts are verified for their medium without fake routes or
approval commits.

## Commands

| Command | Purpose |
|---|---|
| `pfui.py doctor` | Git, browsers, automation, exporters, detected stack, token sources |
| `pfui.py status` | Deliverables, review states and next steps |
| `pfui.py init system\|app\|site\|deck\|doc` | Starter system or scaffold; copy left as `{{slot}}` decisions |
| `pfui.py serve` | Localhost preview plus a review harness: states, themes, platforms, widths, Sheet view |
| `pfui.py check [--final]` | Review records, UI contracts, sources, content inventory, token contrast, lint |
| `pfui.py tokens check\|build\|ramp\|contrast` | DTCG tokens to CSS, iOS asset catalog and Swift, Android resources, Flutter |
| `pfui.py lint` | Names, focus, contrast, targets, type and color discipline, motion, placeholders, assets, email |
| `pfui.py content`, `pfui.py gate` | Rendered-copy inventory and product UI gates |

Full reference: [tooling](references/tooling.md).

## Requirements

- A file-capable AI agent; a shell to run checks.
- Optional: Python 3.9+ (standard library only) for the tools; Git for product
  UI commit gates; a browser, simulator or emulator for rendered review; image
  generation and exporters (LibreOffice, python-pptx, pandoc and others) when a
  format needs them. `pfui.py doctor` reports what is present.

## Installation

Install per project, never globally. From the target project, choose project
scope and your agent:

```sh
npx skills add DejavuMoe/prototype-first-ui --skill prototype-first-ui --copy
```

Or extract the ZIP from
[GitHub Releases](https://github.com/DejavuMoe/prototype-first-ui/releases)
into `<project>/.agents/skills/prototype-first-ui/` or your host's
project-scoped skills folder (for example `.claude/skills/`). Hosts without
skill discovery can be pointed at the installed `SKILL.md` from `AGENTS.md`,
`CLAUDE.md`, `GEMINI.md` or their rules file. The installer needs Node.js;
manual extraction does not.

This repository is the distributable source, not a product workspace.

## Examples

```text
$prototype-first-ui system
Re-brand the starter around our teal, keep every contrast pair passing in light
and dark, and build CSS, iOS, Android and Flutter outputs from one token file.

$prototype-first-ui prototype
Prototype bulk rename for this file manager: preview, conflicts, progress,
cancellation and errors. Present it for review with state URLs.

$prototype-first-ui compose
Make a six-slide introduction from the approved copy; tell me which export
formats are not available here.
```

After review: `$prototype-first-ui implement` with the approved file and its
design commit. More: [English](references/prompts.en.md) ·
[中文](references/prompts.zh-CN.md).

[Skill instructions](SKILL.md) · [Design quality](references/design-quality.md) ·
[Platforms](references/platforms.md) · [Workflow](references/workflow.md) ·
[Release guide](RELEASING.md) · [Changelog](CHANGELOG.md)

## Upgrade from 2.x

Approval now lives only in project-owned `design-review.json`, and the
implementation gate checks every declared prototype dependency, including binary
assets. Follow [the upgrade guide](references/design-review.md#upgrading-a-2x-project);
an old status flag is never converted into approval automatically. Existing UI,
content and source contracts keep working, and no other skill or editor needs to
be installed.

## License

[MIT](LICENSE)
