# Tooling reference

Everything here is optional, standard-library Python 3.9+ under
`<skill>/scripts/`. `pfui.py` is the front door; the other scripts remain
usable directly. Commands print human-readable output; `doctor`, `status`,
`check`, `lint` and `tokens check` also print stable JSON with `--json`. Exit
codes: 0 pass, 1 findings or failure, 2 usage error. Nothing installs
packages, uploads files or binds beyond 127.0.0.1.

## Commands

| Command | Purpose |
|---|---|
| `pfui.py doctor [path] [--json]` | Git and repository state, browsers, automation (Playwright, adb, xcrun), exporters (LibreOffice, pandoc, typst, python-pptx...), detected stack, platforms, token sources and design deliverables |
| `pfui.py status [root] [--json]` | Each deliverable's kind, platform, review status per file, contract surfaces, last commit, uncommitted changes and next step |
| `pfui.py init <kind> [options]` | Scaffold `system`, `app`, `site`, `deck` or `doc` |
| `pfui.py serve [dir] [--port 8765]` | Static preview on 127.0.0.1 plus the review harness at `/__pfui/review.html` |
| `pfui.py check [root] [--final] [--strict] [--json]` | All applicable checks under a root |
| `pfui.py tokens check\|build\|ramp\|contrast ...` | DTCG token validation, contrast, platform builds, OKLCH ramps |
| `pfui.py lint [paths] [--platform P] [--medium M] [--strict] [--json] [--list-rules]` | Static design lint |
| `pfui.py content seed\|static-scan\|check ...` | Content inventory for product UI copy |
| `pfui.py gate review\|approval\|contract\|sources\|structure\|design-scope\|implementation-gate ...` | Product UI gates |

`<root>` defaults to `designs/` when it exists, otherwise the current folder.

## init

```sh
python <skill>/scripts/pfui.py init system --name "Harbor"
python <skill>/scripts/pfui.py init app --name "Harbor" --slug orders --platform ios --product
python <skill>/scripts/pfui.py init site --name "Harbor" --slug launch --lang zh-CN
python <skill>/scripts/pfui.py init deck --name "Harbor" --slug q3-review
python <skill>/scripts/pfui.py init doc --name "Harbor" --slug field-report --page Letter
```

`--name` is the real product or brand name: it appears in page titles and brand
areas, so it is never a task label. `--slug` names the folder
(`designs/<slug>`).

- `system` writes `tokens.json` (source), `tokens.css` (generated),
  `base.css` (components in cascade layers), `params.js`, `components.html`
  (live gallery with contrast readouts, theme, density and platform switches)
  and `foundations.md`.
- Other kinds copy `tokens.css`, `base.css` and `params.js` into `styles/` from
  `--system`, else `designs/system/`, else the starter. The copy is a snapshot
  so an approved prototype stays reproducible; `pfui.json` records its source.
- Every kind writes `pfui.json` and `design-review.json` (status `draft`).
  `--product` adds `ui-contract.json` for the product UI gate.
- User-facing copy is left as `{{slot}}` markers. Each is a content decision to
  fill from evidence or approved copy; `check` fails while any remain.
- Existing files are never overwritten. `--force` only allows a non-empty
  folder and adds missing files.

## serve and state URLs

Prototype pages show one `[data-state-view]` at a time. `styles/params.js`
maps URL parameters to the page, so every state has a stable address for
screenshots and DOM capture:

```text
index.html?state=empty&theme=dark&platform=android&density=compact
index.html?slide=4&notes=1            # decks
```

The harness lists pages, states and slides; switches theme, platform and width
(360-1920 or fit); and **Sheet** tiles every state at 390 and 1280px (decks two
slides per row). Capture DOM content per state URL, never from the harness
page itself. `serve` blocks until stopped: start it as a background process (or
in another terminal), report its URL, and stop it (Ctrl+C or the host's stop
command) when the review ends.

## check

Finds and validates, under the root:

- `design-review.json`: statuses, unique paths, approval evidence only when
  approved, files exist.
- `ui-contract.json`: draft-phase rules, or approved-phase with `--final`.
- `design-sources.json`: roles, trust, permissions, sanitization.
- `content-inventory.json`: gaps are warnings while drafting, errors with
  `--final` (which also requires a rendered-DOM capture).
- `tokens.json` / `*.tokens.json`: structure, aliases, declared contrast pairs
  in every mode, and whether a generated `tokens.css` beside it is stale.
- HTML, CSS and JS: the design lint, per deliverable with its `pfui.json`.

It ends with what static checks cannot verify. A pass is a floor, not
approval or visual sign-off.

## Design tokens (DTCG)

Source files follow the W3C Design Tokens Community Group format: a token is an
object with `$value`; groups may set `$type` for their children; aliases are
`"{group.token}"`. Colors may be hex strings or `{"colorSpace": ..., "components":
[...]}` objects (srgb, hsl, hwb, oklab, oklch, display-p3; others need a `hex`
fallback). Dimensions accept `"16px"`/`"1rem"` or `{"value": 16, "unit": "px"}`.

Conventions this tool adds (other DTCG tools ignore them):

```json
{
  "$extensions": {"contrast": [{"fg": "color.text.primary", "bg": "color.bg.surface", "min": 4.5}]},
  "color": {
    "$type": "color",
    "bg": {"surface": {"$value": "{color.neutral.0}", "$extensions": {"mode": {"dark": "{color.neutral.950}"}}}}
  }
}
```

- `$value` is the default mode. Other modes live in `$extensions.mode`. A mode
  named `axis:value` (for example `density:compact`) targets
  `[data-density="compact"]`; plain names target `[data-theme]`, and `dark`
  also follows the OS setting when no theme is forced.
- `--overlay dark=tokens.dark.json` merges a per-mode file instead.
- Contrast pairs are checked in every theme mode; `over` names the backdrop for
  a translucent background.

```sh
pfui.py tokens check designs/system/tokens.json
pfui.py tokens build designs/system/tokens.json --out designs/system --format css
pfui.py tokens build tokens.json --out build/tokens --format css,json,ios,android,flutter
pfui.py tokens ramp --name brand --hue 160 --chroma 0.14 [--format css]
pfui.py tokens contrast "#6b6f75" "#ffffff"
pfui.py tokens contrast color.text.tertiary color.bg.subtle --tokens tokens.json --mode dark
```

| Format | Output |
|---|---|
| `css` | `tokens.css`: custom properties; aliases stay `var()` references; dark block plus OS media query; `--resolve` inlines values |
| `json` | `tokens.resolved.json`: every token resolved per mode |
| `ios` | `ios/DesignTokens.xcassets` color sets with dark appearances, `ios/DesignTokens.swift` (colors, metrics in pt, durations) |
| `android` | `android/values/colors.xml`, `values-night/colors.xml`, `dimens.xml` (dp; sp for font sizes), `integers.xml` |
| `flutter` | `flutter/design_tokens.dart`: `DesignColors`, `DesignColorsDark`, `DesignMetrics`, `DesignDurations` |

Generated platform files are build output: compile them in the target project
before relying on them, and never edit them by hand.

## pfui.json

Per-deliverable settings read by `lint`, `check`, `status` and `serve`:

```json
{
  "schemaVersion": 1,
  "kind": "app",
  "platform": "ios",
  "medium": "ui",
  "system": {"source": "designs/system", "copiedOn": "2026-11-24", "files": ["styles/tokens.css", "styles/base.css", "styles/params.js"]},
  "lint": {"disable": [], "severity": {"raw-color": "error"}, "ignore": ["vendor/**"]}
}
```

`platform`: web, desktop, ios, android (sets target sizes). `medium`: ui, site,
deck, doc, email (sets type minimums and email rules).

## Design lint rules

`pfui.py lint --list-rules` prints all rules with default severities.

| Area | Rules |
|---|---|
| Document and semantics | html-lang, doc-title, viewport-zoom, viewport-missing, missing-main, heading-skip, duplicate-id, aria-reference |
| Names and labels | control-name, field-label, img-alt, ambiguous-link |
| Keyboard and focus | positive-tabindex, static-click, outline-removed, no-focus-style, hover-only |
| Visual system | raw-color, font-size-scale, font-size-min, font-family-count, font-size-px, radius-scale, shadow-scale, z-index-scale, spacing-grid, important-overuse |
| Contrast and themes | low-contrast, color-scheme |
| Motion | reduced-motion, transition-all, autoplay-media |
| Targets | touch-target (24px web/desktop, 44 iOS, 48 Android) |
| Content hygiene | placeholder-text, filler-copy, emoji-icon, gradient-text, inline-style |
| Assets | missing-asset, remote-asset |
| Data | table-header |
| Email medium | email-script, email-external-css, email-layout, email-position, email-width |

Disable rules or change severities in `pfui.json` rather than suppressing them
inline: HTML comments are part of the rendered content contract.

## Content capture (product UI)

1. Serve the prototype and open each state URL.
2. Evaluate `scripts/collect_dom_content.js` in the page, then call
   `window.__prototypeFirstUICollectDOMContent()`; save the JSON outside the
   repository until reviewed.
3. `pfui.py content seed --capture state-ready.json --capture state-empty.json
   --profile operational-strict --brief-file brief.txt --output
   designs/<name>/content-inventory.json`
4. Classify every string, then `pfui.py content check --inventory ...`.

Without a browser, `pfui.py content static-scan --root designs/<name> --output
static.json` feeds `seed` instead, and `content check --allow-static` accepts
the result as an explicitly provisional review; it is never final sign-off.

## Workflow gates (product UI)

```sh
pfui.py gate design-scope --repo .
pfui.py gate review --project-dir designs/<name>
pfui.py gate approval --project-dir designs/<name> --asset-path index.html
pfui.py gate contract --project-dir designs/<name> --phase approved --asset-path index.html
pfui.py gate implementation-gate --repo . --project-dir designs/<name> --asset-path index.html --design-commit <sha>
```

- `design-scope` allows `designs/**`, `docs/ui/**` and this skill's own
  project-local install folder; add `--allow-constraints` or `--allow-agents`
  only when the user asked to change `docs/product/constraints.md` or
  `AGENTS.md`.
- Approval needs both records: the asset `approved` with evidence in
  `design-review.json`, and the matching `ui-contract.json` surface `status`
  set to `approved` (`implemented` after it ships).
- `python <skill>/scripts/bootstrap.py scaffold ...` writes `AGENTS.md`,
  `README.md` and `docs/product/constraints.md` templates without touching Git
  history and keeps existing files; it is separate from the destructive
  `bootstrap init`.

See [workflow](workflow.md) and [review contract](design-review.md).
