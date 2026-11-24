# Platform and medium profiles

Read the section for each target. The project's own platform rules and design
system win over these defaults. Combine with the
[quality standard](design-quality.md) and, for product changes, the
[workflow](workflow.md) gate.

## Choose the build medium

- Prototype in the platform's native stack when the project already uses it and
  the toolchain is present (SwiftUI or Compose previews, Flutter, WinUI/XAML,
  the app's own web stack or Storybook). Native previews show real controls,
  type scaling and system behavior.
- Otherwise build an HTML prototype: `pfui.py init app --platform
  web|desktop|ios|android`. Treat it as an approximation and list what it
  cannot show: gestures, system sheets and pickers, haptics, Dynamic Type and
  font-scale reflow, keyboard avoidance, window management.
- One brand, many platforms: share tokens and identity; let navigation,
  controls, back behavior, typography and capitalization follow each platform.
  `pfui.py tokens build designs/system/tokens.json --out build/tokens --format
  css,ios,android,flutter` keeps colors and metrics in sync from one DTCG
  source; copy each platform's output into its project and compile it there.

| Target | Prototype | Verify with | Non-negotiables |
|---|---|---|---|
| Web app or site | Project stack or HTML | Browser at 360-1920px, 200% zoom, keyboard, screen reader | WCAG 2.2 AA, reflow at 320px, prefers-* media |
| iOS / iPadOS | SwiftUI previews or HTML at 390x844 / 820x1180 | Simulator, Accessibility Inspector, VoiceOver | Human Interface Guidelines, 44pt targets, safe areas, Dynamic Type |
| Android | Compose previews or HTML at 412x915 / 360x800 | Emulator, TalkBack, font scale 200% | Material 3, 48dp targets, edge-to-edge, predictive back |
| macOS | SwiftUI/AppKit or HTML (`--platform desktop`) | Running app, VoiceOver, keyboard only | Menu bar, toolbar, shortcuts, resizable windows |
| Windows | WinUI/WPF/Electron/Tauri or HTML (`--platform desktop`) | Running app, Narrator, contrast themes | Fluent 2, access keys, forced colors |
| Linux desktop | GTK/libadwaita or Qt/KDE | Running app, Orca | GNOME or KDE guidelines for the toolkit |
| Browser extension | HTML popup, options page, side panel | Load unpacked; test on varied host pages | Small popup, isolated injected UI, minimal permissions |
| CLI / TUI | Text transcripts, then the real binary | 80x24 terminal, NO_COLOR, piped output, screen reader | Readable without color, machine output, exit codes |
| Email | Table-based HTML, inline CSS | Major clients when a preview service is available; images-off; dark mode | 600px, no scripts, hosted images |
| Print / PDF | HTML with @page (`pfui.py init doc`) or native tools | Every rendered page of the PDF | Page geometry, breaks, resolution |
| Slides | HTML deck (`pfui.py init deck`) or a real PPTX exporter | Rendered slides and the exported file | Projection sizes, one idea per slide |
| Watch, TV, spatial, car | Native stack and simulator only | Device or simulator | Glanceability, focus navigation, distance, safety |

## Web

- Breakpoints follow content; components adapt with container queries where
  supported. Fluid `clamp()` type belongs on marketing pages, not dense tools.
- Respect `prefers-color-scheme`, `prefers-reduced-motion`, `prefers-contrast`
  and `forced-colors`.
- Performance is design: size the largest image, reserve media dimensions to
  avoid layout shift, prefer system fonts or self-hosted fonts with
  `font-display: swap`, keep the critical path small.
- Standalone and installed web apps: `viewport-fit=cover` plus
  `env(safe-area-inset-*)` padding.
- Support the browsers the project names; feature-detect instead of sniffing.

## iOS and iPadOS

- Navigation: a tab bar for top-level sections (at most five on iPhone), a
  navigation stack with swipe-back, sheets for focused subtasks, large titles on
  top-level screens.
- Use system controls and behaviors first: pickers, menus, swipe actions,
  share sheets, alerts and action sheets with Cancel.
- Targets at least 44x44pt. Layouts must survive the largest accessibility text
  sizes (Dynamic Type) without truncating essential text.
- Respect safe areas (sensor housing, home indicator) and keep content clear of
  the keyboard.
- Follow Apple's capitalization and wording conventions for buttons, alerts and
  menus. Use symbol-style icons consistent with the system set.
- iPad: sidebars and split views, multitasking widths, pointer hover, hardware
  keyboard shortcuts.
- Verify: VoiceOver labels, traits and order; Dynamic Type; dark mode;
  landscape; Reduce Motion and Reduce Transparency.
- Tokens: `--format ios` writes an asset catalog (light and dark appearances)
  and Swift constants.

## Android

- Adapt by window size class: compact (under 600dp) uses a navigation bar;
  medium (600-839dp) a navigation rail; expanded (840dp and up) a rail or drawer
  with list-detail panes.
- Targets at least 48x48dp; 8dp layout grid; text in sp; layouts survive font
  scale 200%.
- Apps targeting Android 15 (API 35) draw edge-to-edge: handle system bar and
  keyboard insets. Support the predictive back gesture; never trap Back.
- Top app bar for context; a floating action button only for the single primary
  creation action.
- Dynamic color is optional; brand palettes must still pass contrast in light
  and dark schemes.
- Verify: TalkBack order and labels, font scale, dark theme, landscape, large
  screens and foldables when supported.
- Tokens: `--format android` writes `values/colors.xml`,
  `values-night/colors.xml`, `dimens.xml` and `integers.xml`.

## Desktop: macOS, Windows, Linux

- Pointer and keyboard first: denser controls (24-32px), hover states,
  tooltips, context menus, multi-select with Shift and Ctrl/Cmd, drag and drop,
  complete keyboard operation, shortcuts shown in menus.
- Windows resize: set a minimum size, collapse panes gracefully, remember size
  and position. No mobile hamburger patterns in a wide desktop window.
- macOS: every command reachable from the menu bar; toolbar for frequent
  actions; sidebar source lists; Command-key shortcuts; title-style
  capitalization in menus and buttons; respect the system accent and
  appearance.
- Windows: Fluent 2 patterns (navigation view, command bar, Segoe UI Variable),
  access keys via Alt, contrast themes rendered through `forced-colors`.
- Linux: follow the toolkit in use (GTK/libadwaita header bars and adaptive
  layouts, or KDE Breeze conventions).
- Electron and Tauri: per-OS title bar, menus and shortcuts rather than one
  web-styled chrome everywhere.
- `--platform desktop` in init and lint: 32px controls, native cursor, desktop
  target sizes.

## Browser extensions

- The popup is small (Chrome caps it at 800x600), must open instantly and closes
  when focus leaves, so keep state in storage. Longer tasks belong in an
  options page or side panel.
- Injected UI isolates its styles (shadow DOM), never breaks the host layout,
  respects host dark mode and is easy to dismiss.
- Ask for permissions at the moment of need and explain the benefit.

## CLI and TUI

- Human-readable output by default; `--json` (or similar) for machines. Results
  to stdout, progress and logs to stderr; meaningful exit codes.
- Color is semantic and redundant: pair it with words or symbols; honor
  `NO_COLOR` and non-TTY output; work in 16-color terminals; avoid depending on
  emoji or patched fonts; provide ASCII fallbacks for box drawing.
- Wrap to the terminal width (assume 80 columns); align tables; truncate long
  paths in the middle.
- Confirm destructive actions, with a flag such as `--yes` for scripts; show
  progress bars only on a TTY.
- Prototype with realistic plain-text transcripts of sessions, including help
  output, errors, partial failure, empty results and the `--json` form.

## Email

- Single column, about 600px wide; tables for structural layout; critical CSS
  inlined; no scripts or forms; buttons built from HTML and CSS, not images.
- Images are hosted and may be blocked: every image has alt text and the
  message reads without them. Lint with `pfui.py lint --medium email`.
- Clients may invert colors in dark mode: avoid transparent logos that vanish on
  dark backgrounds; check both schemes.
- Legal footer content (address, unsubscribe) comes from an authoritative
  source, never invented.

## Print and PDF

- Geometry through `@page`: size, margins (wider binding edge for bound
  documents), running headers or footers, page numbers.
- Body 9-11pt, 60-75 characters per line; headings keep with the following
  text; avoid widows and orphans; do not split table rows or figures.
- Raster images at least 300 dpi at printed size; charts as vectors.
- Commercial press needs CMYK conversion, bleed and crop marks, which HTML
  rendering does not guarantee: state that limitation or use a press-capable
  tool.
- Verify by exporting the PDF and inspecting every page.

## Slides

See [visual communication](visual-communication.md). The deck scaffold uses a
1920x1080 canvas, a 24/32/40/72/96/132px projection scale, `?slide=N` URLs,
speaker notes and print-to-PDF at slide size. PPTX requires a real exporter;
never rename HTML or PDF output as PPTX.

## Watch, TV, spatial and automotive

- Watch: glanceable, one task at a time, large type, the platform's complications
  or tiles.
- TV (10-foot): focus-driven navigation with a strong focus state, margins safe
  from overscan, larger type, no hover.
- Spatial (for example visionOS): interactive targets of at least 60pt, the
  platform's materials and depth, comfortable placement at a distance.
- Automotive: driver-distraction limits and the platform's templates only.
- Use the native toolchain and simulator. HTML mockups cannot verify these
  platforms; label any such mockup as a sketch.

## Cross-platform frameworks

React Native and Expo, Flutter, Compose Multiplatform, .NET MAUI, Capacitor,
Electron and Tauri: decide per component whether it is "same everywhere"
(brand content, illustrations, data views) or "native per platform"
(navigation, back, pickers, menus, sheets, system dialogs, text input). Share
tokens; test each platform separately; report untested platforms as unverified.
