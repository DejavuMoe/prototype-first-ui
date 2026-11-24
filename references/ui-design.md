# Interfaces and prototypes

Use for app screens, flows, websites and interactive mockups on any platform.
Apply the [workflow](workflow.md) gate when the work changes a product; a
standalone mockup follows the same craft without inventing a backend. Read
[platforms](platforms.md) for non-web targets and
[design quality](design-quality.md) for the standard you will be scored on.

## Shape the experience

Read the existing system through [design system](design-system.md) as needed.
Audit affected routes, domain objects, actions, permissions and real
interfaces; make unknown behavior explicit. Find the primary task, the
information needed before it and the decision it ends in, then organize
navigation, grouping and density around that path.

For an exploration, compare two or three materially different structures with
the same content and fixtures: navigation model, workspace organization, task
sequence, density, pane and table relationships, platform interaction model.
Color or font swaps are not different directions. Explain tradeoffs in task
steps, discoverability, space use and platform fit. For a revision, extend the
selected design; do not restart exploration or change unrelated visual
language.

## Choose the build medium

- The project's own stack when it can render the affected states cheaply
  (Storybook, SwiftUI or Compose previews, Flutter, an isolated route) and the
  change is component-level.
- Otherwise HTML/CSS/JS in the design folder. `pfui.py init app --name N
  --platform web|desktop|ios|android [--product]` (or `site`) gives a shell on
  the project's tokens and components, a state mechanism and copy slots. Add no
  build system for a static screen.
- HTML imitating native apps is an approximation; list what it cannot show.

## Profiles by deliverable type

| Type | Lead with | Watch for |
|---|---|---|
| Operational app, admin, developer tool | The object list or detail and its primary action | Density, keyboard paths, bulk actions, permission and error states |
| Dashboard | The question it answers ([data visualization](data-visualization.md)) | Metric definitions, baselines, freshness, empty data |
| Form, settings, wizard | Grouping, defaults, the save model | Inline errors, unsaved changes, progress, recovery |
| Onboarding and empty product | The first useful action | No marketing inside operational surfaces |
| Website, landing page | Message hierarchy from approved copy | Content profile, performance, reading measure |
| Docs and content site | Navigation, reading measure, search | Code blocks, anchors, long headings |
| Commerce and checkout | Totals and policies from real sources | Payment, address and error states are simulated, never real |
| Mobile app | Thumb reach, tab structure, back behavior | Safe areas, Dynamic Type or font scale, keyboard |

## States and fixtures

- Build a state matrix for each affected surface: ready, loading, empty,
  partial, error, permission, offline, disabled, in progress, success, long or
  overflowing content, first run. Include only states the product can reach.
- Make each state reachable directly. In HTML prototypes wrap states in
  `[data-state-view="<id>"]`; `params.js` shows the one named by `?state=`.
  Native previews get one preview per state.
- Fixtures are synthetic but realistic: varied lengths, zero, one and many
  items, very large numbers, missing optional fields, non-Latin and RTL text.
  Use reserved domains (example.com) and invented identifiers. Never use real
  accounts, keys, private URLs or local paths.
- Simulated behavior (sending, paying, deleting, syncing) is described as
  simulated in the handoff. The product UI never claims effects it does not
  have.
- Keep review controls out of the product surface; `pfui.py serve` provides
  them outside the page.

## Build quality

- Semantic controls with visible labels, focus styles and a predictable tab
  order; tokens and system components instead of literal values.
- Content-driven layout and breakpoints. Check narrow and wide viewports, long
  content, 200% zoom, light and dark themes, and the platform variants in scope.
- A device frame is presentation chrome; test the real viewport and scrolling
  inside it.
- Every visible string fills a slot from evidence or approved copy. Product UI
  follows the [content contract](content-contract.md).

## Critique, review and handoff

1. Serve the prototype (`pfui.py serve designs/<name>`, started in the
   background because it runs until stopped) and render every affected state at
   the target sizes and themes; the Sheet view shows them together.
2. Run `pfui.py check designs/<name>` and fix its errors.
3. Score the [critique rubric](design-quality.md#critique-protocol), fix
   blockers and the top issues, and render again.
4. For product UI, capture DOM copy per state URL with
   `scripts/collect_dom_content.js`, classify it in `content-inventory.json`,
   and list every local dependency (HTML, CSS, scripts, images, fonts,
   fixtures, copied system styles) in the matching `ui-contract.json` surface's
   `prototype.files`. Shared system styles are snapshotted inside the design
   folder so the reviewed result can be reproduced; production never imports
   the design folder.
5. Present the preview URL, the exact file, the scope and the checks that did
   not run. Keep `needs-review` until the user approves this version; a polished
   screenshot or a request for more changes is not approval.
