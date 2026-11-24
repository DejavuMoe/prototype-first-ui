# Project design system

Use for creating, extracting, extending or maintaining reusable design
decisions. The result must let another agent produce consistent work without
this conversation.

## Establish the source of truth

Inspect existing styles and tokens, component exports, representative screens,
assets, brand guidance and platform constraints (`pfui.py doctor` lists token
sources it can find). Distinguish what the product does now from what the user
wants it to become. Keep an established token format and component API; do not
translate them into a second format just for this skill. Style Dictionary,
Terrazzo, Tailwind themes, Xcode asset catalogs and Android resources are all
valid sources of truth.

When no system exists, start with `pfui.py init system --name "<Brand>"`:

- `tokens.json`: W3C DTCG source with primitives, semantic roles, light and dark
  modes and declared contrast pairs;
- `tokens.css`: generated custom properties (`pfui.py tokens build`);
- `base.css`: components in cascade layers, so project CSS always overrides;
- `params.js`: review parameters for theme, density, platform and state;
- `components.html`: a live gallery with contrast readouts and theme, density
  and platform switches;
- `foundations.md`: intent, direction, consumption recipe and known gaps.

Treat the starter as neutral raw material. Re-brand it before using it for a
real product, and keep only what the project needs.

## Token architecture

1. **Primitives**: ramps by hue (`color.neutral.*`, `color.blue.*`), the type
   scale, spacing, radii, shadows, durations, easing. Generate color ramps in
   OKLCH (`pfui.py tokens ramp`) so steps are perceptually even.
2. **Semantic roles**: what a value is for: `color.bg.canvas|surface|raised|field`,
   `color.text.primary|secondary|tertiary|link|on-accent`,
   `color.border.subtle|default|control`, `color.accent.*`, `color.focus.ring`,
   `color.success|warning|danger|info.*`, `color.data.1-n`, plus `type.*`
   styles. Components use only these.
3. **Component tokens** (optional): `button.primary.bg` aliasing a semantic
   role, added only when a component needs to diverge.

- Modes: dark, high contrast or density values live beside the default in
  `$extensions.mode` (or an overlay file) on semantic tokens; primitives stay
  mode-free. Add only supported themes.
- Declare the color pairs that are actually used together in
  `$extensions.contrast` (text on every background it appears on, controls,
  focus ring, status pairs, data marks). `pfui.py tokens check` verifies them in
  every mode.
- Names describe purpose, not appearance (`text.secondary`, not `gray-600`), and
  never encode a single screen.
- One source, many outputs: `pfui.py tokens build designs/system/tokens.json
  --out build/tokens --format css,json,ios,android,flutter`. Without arguments,
  `tokens check` and `tokens build` use `designs/system/tokens.json` and write
  beside it. Generated files are build output; never edit them by hand, and
  compile platform output in its project before relying on it.

## Build a coherent language

1. Define the direction ([design quality](design-quality.md#set-a-direction-before-pixels)),
   reading order and task emphasis. Choose a small type scale, line lengths,
   spacing rhythm, density, container and grid rules and responsive behavior
   from the content and viewing distance.
2. Bind components to semantic roles so a theme change never requires
   scattered literal edits.
3. Document fallback fonts, missing assets, long labels and localization. Do not
   silently replace a brand font or add dark mode outside scope.
4. Specify each component: anatomy; variants and sizes; states (hover, pressed,
   focus-visible, disabled, busy, selected, invalid); content limits and
   truncation; keyboard and screen-reader behavior; platform differences; use
   and avoid guidance. Point to production exports when they exist and run real
   components in the project's preview environment rather than painting
   look-alike copies.
5. Show composition: how components assemble into a screen, a chart, a slide
   or a print page. Share identity and semantics across media; adapt density,
   type size, units and interaction to each medium rather than scaling a web
   page.

For extraction from an existing library, map documented props and exports and
test representative states. Do not claim full coverage after inspecting a few
examples. When the runtime cannot load the real component, label the visual
approximation with the reason and the missing verification.

## Rebrand or theme recipe

1. Generate or adjust ramps: `pfui.py tokens ramp --name brand --hue <h>
   --chroma <c>` and paste the group into `tokens.json`.
2. Re-point semantic aliases (`color.accent.*`, `color.focus.ring`, links) to
   the new ramp; adjust neutrals' hue tint if needed.
3. `pfui.py tokens check` until every declared pair passes in every mode; move a
   failing role to a different step instead of lowering the minimum.
4. `pfui.py tokens build` and review `components.html` in light, dark, every
   density and every supported platform.
5. Record the decisions and remaining gaps in `foundations.md`.

## Verify and maintain

- Token references resolve, generated CSS is fresh (`pfui.py check` reports a
  stale `tokens.css`), examples consume canonical values, declared contrast
  passes in every theme, focus is visible and state never relies on color
  alone. Exercise interactive examples with keyboard and pointer or touch.
- Measured contrast covers declared pairs only; report what was not measured.
- Before changing shared foundations, find consumers and identify which outputs
  change. Deliverables copy system styles as snapshots and record their source
  in `pfui.json`; never auto-refresh an approved deliverable to newer tokens.
  Inspect the diff and return changed UX to review.
- Commit design-system changes separately from production adoption when the UI
  gate applies.

Deliver the gallery plus a short consumption recipe: which files to use, which
variants exist, how to preview and check, and known gaps. Keep these facts in
foundations, not duplicated across artifacts.
