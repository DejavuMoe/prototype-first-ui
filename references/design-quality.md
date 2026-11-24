# Design quality standard

Use while building any visual deliverable and whenever you critique one. These
are defaults for when nobody has set a stronger rule: the user's explicit
direction, an approved brand, the design system and platform guidelines win.
Nothing overrides accessibility minimums or the content contract.

Rule ids in brackets are checked by `pfui.py check` / `pfui.py lint`;
everything else needs rendered review by eye. The lint's thresholds are
deliberately looser than the targets here (for example it flags more than ten
font sizes or three families) so every finding is a clear violation. Passing
the lint is the floor, not the standard.

## Set a direction before pixels

Write a short direction in notes, foundations or the handoff. Never put it in
the product.

1. **Audience and task**: who, in what context, doing what, how often.
2. **Medium and platform**: screen sizes, input (touch, pointer, keyboard,
   remote), viewing distance, light/dark, print.
3. **Three attributes** that describe the intended feel, each translated into
   decisions. Adjectives without decisions are not a direction.

| Attribute (example) | Type | Color | Density and space | Shape and depth | Motion | Imagery |
|---|---|---|---|---|---|---|
| Calm | system sans, regular weights | neutral canvas, one muted accent | generous gaps between groups | soft 8px radii, low shadows | 150-200ms fades | none or product-only |
| Precise | tabular numerals, tight scale | high-contrast text, status colors only for status | compact 32-36px rows | crisp 1px borders, 4-6px radii | instant feedback, no flourish | diagrams over photos |
| Editorial | serif display + sans UI | near-monochrome, ink accent | wide margins, strong vertical rhythm | rules and whitespace, few boxes | minimal | large, cropped with intent |

Derive the attributes from the audience, content and brand, not from trends.
A named style ("glassmorphism", "bento", "brutalist") is not a direction until
it is justified by the task and translated into the table above.

## Hierarchy and layout

- One focal point per region and one primary action per view. Squint test: the
  most important thing must stand out when the screenshot is blurred.
- Build hierarchy with size, weight, color contrast and space, in that order,
  before reaching for boxes, borders or color fills.
- Align to few edges. Use a 4px spacing grid and a spacing scale; padding inside
  a group is smaller than the gap between groups (proximity) [spacing-grid].
- Reading text: 45-75 characters per line (about 68ch). Forms: one column,
  labels above fields, related fields grouped.
- Density follows the task: expert and data tools 32-40px rows; consumer and
  touch 44-56px. Offer a density setting only when both audiences are real.
- Responsive by content, not by device names. Check 360, 390-412, 768, 1024,
  1280 and 1440+ widths. Content reflows at 320 CSS px without horizontal
  scrolling (WCAG 1.4.10); only data tables, code and diagrams may scroll inside
  their own container.
- Empty space is structure. Remove decoration that does not group, separate or
  emphasize something.

## Typography

- One or two text families, plus a monospace for code where needed. Prefer the
  platform's system stack unless a licensed brand font is available locally
  [font-family-count].
- One modular scale; at most 6-8 sizes per surface [font-size-scale]. Ratios of
  1.125-1.2 suit dense UI; 1.25-1.333 suit editorial and marketing.
- UI body 14-16px (iOS 17pt, Android 16sp); long reading 16-18px; never below
  12px on screen [font-size-min]. Use rem so text follows user settings
  [font-size-px].
- Line height 1.4-1.6 for body, 1.1-1.3 for headings. Large display text gets
  slight negative tracking (-1% to -3%); all-caps labels get +4% to +8%.
- Weights: regular for body, 500-600 for emphasis and headings. Avoid light
  weights for small text and synthetic bold/italic.
- Numbers: tabular figures in tables and metrics, right-aligned, consistent
  decimals, units in the header or label, locale-aware separators.
- `text-wrap: balance` for headings and `pretty` for paragraphs; avoid one-word
  last lines in headlines.
- CJK: no faux italics or uppercase; slightly larger line height (1.6-1.8 for
  reading); fallback stacks that cover both Latin and CJK glyphs.

## Color

- Build neutrals first, then one accent, then status hues. Tint neutrals very
  slightly toward the accent hue so the palette feels related.
- Components use semantic roles (canvas, surface, text, border, accent, status),
  never raw ramp steps or literal colors [raw-color].
- Contrast, WCAG 2.2 AA in every supported theme: 4.5:1 for text; 3:1 for large
  text (24px, or 18.66px bold), UI component boundaries, focus indicators and
  meaningful graphics [low-contrast]. Declare pairs and let
  `pfui.py tokens check` verify them per mode.
- Color is never the only signal: pair it with text, icon, shape or position.
- Mostly neutral surfaces; the accent marks action and selection only. Status
  colors mean status and nothing else.
- Generate ramps in a perceptual space (OKLCH) so steps look even:
  `pfui.py tokens ramp --name brand --hue 160`.
- Dark mode is a separate palette, not an inversion: near-black canvas (not
  #000), elevation shown by lighter surfaces, slightly desaturated accents, body
  text below pure white, contrast re-checked. Where a platform defines its own
  dark palette (iOS uses pure black base backgrounds with lighter elevated
  levels), follow the platform. Set `color-scheme` so native controls follow
  [color-scheme].
- A brand color that fails contrast becomes a fill or accent paired with a
  compliant text color; it does not become small text.

## Shape, depth, icons and imagery

- A short radius scale (4-5 values) used consistently; nested corners use the
  outer radius minus the padding [radius-scale].
- At most four elevation levels with soft, tinted shadows [shadow-scale]. Do not
  stack a heavy border, a shadow and a fill on the same element. In dark themes,
  lighter surfaces and borders carry depth.
- One icon family, one stroke weight, 16/20/24px sizes, optically centered.
  Unfamiliar actions get text labels; icon-only buttons get accessible names
  [control-name]. No emoji as interface icons [emoji-icon].
- Every image has a job: show the product, explain, or ground the context. No
  generic stock smiles or decorative blobs. Crop per breakpoint, give alt text
  or alt="" [img-alt], keep a local copy with provenance [remote-asset].

## Interaction and states

- Every interactive element defines default, hover (pointer), pressed,
  focus-visible, disabled and busy states, plus selected or current where it
  applies. The same state looks the same across components.
- Focus is always visible: at least a 2px ring with 3:1 contrast against what
  surrounds it. Never remove the outline without a replacement
  [outline-removed].
- Targets: at least 24x24 CSS px everywhere (WCAG 2.5.8); 44x44pt on iOS;
  48x48dp on Android [touch-target].
- Timing: under 100ms feels instant; show progress after about 1s; skeletons
  for content whose layout is known; spinners only for short indeterminate
  waits; optimistic updates with undo for reversible actions.
- Errors say what happened, why when known, and how to fix it; they sit next to
  the cause, keep the user's input and are announced to assistive technology.
- Destructive actions name the object and the consequence and offer undo or a
  confirmation whose button repeats the action ("Delete 3 files").
- Empty states say what is missing and offer the next action; never leave a
  table with headers and no rows.
- Forms: validate on blur or submit, not on every keystroke; do not disable
  submit without saying why; use correct input types and autocomplete.
- Content revealed on hover needs a keyboard and touch equivalent [hover-only].

## Motion

- Motion explains: entering and leaving, cause and effect, where things went.
  It is never decoration on a loop.
- Durations: 100-150ms for hover and press, 200-300ms for component
  transitions, 300-500ms for large layout changes; exits a little faster than
  entrances.
- Easing: ease-out to enter, ease-in to exit, a standard curve to move; linear
  only for progress and spinners; no bounce in productivity tools.
- Animate transform and opacity, not layout properties [transition-all].
- Honor `prefers-reduced-motion` by removing or replacing large motion with a
  fade [reduced-motion]. Nothing flashes more than three times per second.

## Words in the interface

The [content contract](content-contract.md) decides which words may appear.
This section decides how they read.

- Buttons use specific verbs that name the result ("Save changes", "Export
  CSV"), not "OK", "Submit" or "Yes".
- One term per concept everywhere, taken from the user's domain.
- Sentence case by default; follow platform capitalization where it differs
  (Apple uses title-style capitalization for many control labels).
- Front-load the important words; digits for numbers; localized dates, times,
  currency and units.
- No filler, slogans or fake data [filler-copy]; no "click here" links
  [ambiguous-link]; no unresolved slots or lorem ipsum [placeholder-text].
- Errors without blame, jokes or exclamation marks.

## Accessibility floor

WCAG 2.2 AA unless the project sets a higher bar.

- Native semantics first (button, a, label, input, table, dialog, landmarks);
  ARIA only to fill gaps.
- Names and structure: every control, field and informative image is named
  [control-name] [field-label] [img-alt]; the page has a language, title, main
  landmark and ordered headings [html-lang] [doc-title] [missing-main]
  [heading-skip]; ids are unique and references resolve [duplicate-id]
  [aria-reference].
- Keyboard: everything operable, logical order, no traps, visible focus, no
  positive tabindex [positive-tabindex], skip link on content sites.
- Zoom and reflow: 200% text and 320px width without loss; never block pinch
  zoom [viewport-zoom].
- Test with a keyboard and, when available, a screen reader (VoiceOver,
  TalkBack, NVDA, Narrator, Orca). If you could not, say so.

## Internationalization and resilience

- Leave room for 30-40% longer strings; test the longest realistic value, an
  empty value and a huge number in every slot.
- Use logical properties (`margin-inline`, `inset-inline-start`) so RTL works.
- Localize number, date and currency formats; respect plural rules; never bake
  text into images.

## Anti-patterns: the generic "AI default" look

Flag each in critique. Keep one only when the user asked for it or the brief
justifies it, and then make it accessible (contrast, names, reduced motion).

1. Purple-to-blue gradients, gradient-clipped headlines, glowing blobs, glass on
   everything [gradient-text].
2. Emoji as icons, bullets or status indicators in product UI [emoji-icon].
3. Everything centered; the reflexive hero of giant headline, subtitle and two
   buttons.
4. Card soup: every block boxed, cards inside cards, border plus shadow plus
   fill on one element.
5. Pill-shaped everything or inconsistent radii [radius-scale].
6. A rainbow of accents; badges on everything; status colors used decoratively.
7. Low-contrast gray-on-gray "minimal" text [low-contrast].
8. Fake data that looks fake: John Doe, Acme, lorem ipsum, 99.9%, round numbers,
   five-star testimonials [filler-copy] [placeholder-text].
9. Vanity dashboards: KPI tiles without definitions, baselines or a question.
10. Decorative motion: everything slides in on scroll; infinite pulsing.
11. Marketing slogans inside tools ("Supercharge your workflow").
12. Placeholder-as-label inputs, nameless icon buttons, disabled buttons with no
    explanation.
13. Modals for everything; toasts for errors that need action.
14. Desktop layouts squeezed onto phones; hover-only affordances on touch.
15. Dark mode by inversion; pure white text on pure black where the platform's
    own dark palette does not call for it.

## Critique protocol

Run all five steps before every review request and hand-off. In `critique`
mode for an existing interface, run steps 1-3 only and report the findings
ranked by user impact; fixes then go through a normal prototype.

1. Render every affected state at the target sizes and themes. `pfui.py serve`
   (it runs until stopped, so start it in the background) then **Sheet** shows
   all states at mobile and desktop widths in one view.
2. Run `pfui.py check` (or `pfui.py lint` on an existing interface) and fix
   errors first when building. It is a floor, not a verdict.
3. Score each dimension 0-2 with evidence (state, size, selector or
   screenshot):

| Dimension | 2: ship | 1: fix soon | 0: blocker |
|---|---|---|---|
| Task clarity | Purpose and primary action obvious at a glance | Findable with effort | Unclear what to do |
| Hierarchy | One focal point per region; squint test passes | Competing emphasis | Flat or chaotic |
| Layout and rhythm | Aligned, spacing scale, fitting density | Minor misalignment | Broken grid or overflow |
| Typography | Disciplined scale, measure, numerals | Too many sizes or long lines | Illegible or clipped |
| Color and contrast | Roles correct, every theme passes | Weak secondary contrast | Text or focus below minimum |
| States and feedback | All affected states designed and reachable | Some states generic | Happy path only |
| Interaction and access | Keyboard, focus, names, targets correct | Minor gaps | Unusable without a mouse or screen |
| Content | Purposeful, consistent, evidenced | Wordy or inconsistent | Filler, fake claims or brief leakage |
| Platform fit | Conventions of the target respected | Minor deviations | Wrong navigation or controls for the platform |
| Craft and consistency | Tokens, icons, radii, details coherent | A few strays | Visibly inconsistent or generic |
| Resilience | Narrow/wide, long text, empty and huge data, zoom | One case breaks | Breaks under ordinary data |

4. Fix every 0 and the top three 1s, re-render and re-score.
5. Ship bar: no 0s, average at least 1.6, no lint or contract errors, and every
   unverified item listed. Report scores and evidence in the handoff, never in
   the product.
