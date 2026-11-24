# Visual communication

Use for slides, designed documents, print pages, posters, social assets,
diagrams, email and brand imagery. These are first-class deliverables: they do
not need a product UI contract or an implementation commit.

## Brief and format

Identify the message, audience, reading context (projected, on a phone, printed,
skimmed in an inbox), source material and requested format. Reuse project
foundations and brand assets. Settle aspect ratio or page size, editable source
needs and destination constraints before layout. Missing evidence for a claim
is a content gap, not permission to invent it; mark drafted copy as draft.

| Medium | Design decisions | Verification |
|---|---|---|
| Slides | One message per slide; sequence that builds an argument; layouts chosen per evidence | Read at presentation size; order, notes, overflow and the actual export |
| Documents and print | Reading order, headings, grid, tables, captions, margins, pagination | Every rendered page: splits, widows, image resolution, page size, links |
| Poster and social | One focal point, short hierarchy, crop-safe zones, a clear call to action | Intended size and thumbnail; destination crops; contrast over imagery |
| Diagram | Explicit nodes, relationships, direction, grouping, legend | Claims and endpoints correct; labels readable without crossings |
| Email | Single column, scannable sections, one primary action | Client rendering, images off, dark mode ([platforms](platforms.md#email)) |
| Brand imagery | Subject, composition, role in the layout, reusable art direction | Identity consistency, rights, crop, resolution, transparency |

## Slides

- Start from `pfui.py init deck --name N` when no deck tooling exists: a
  1920x1080 canvas scaled to the window, `?slide=N` URLs, speaker notes
  (`n` or `?notes=1`) and print-to-PDF at slide size.
- Titles state the takeaway ("On-time pickups rose 6 points"), not the topic
  ("Q3 results"). Put supporting detail in speaker notes, not on the slide.
- Projection sizes: body 32-40px, titles 64-96px, nothing below 24px at
  1920x1080. One idea, at most about five short lines, per slide.
- Vary layouts to fit the evidence (statement, list, split with figure,
  metrics, quote, chart), but keep one grid, margin and type scale throughout.
- Charts on slides: one message, the key value labeled directly, the rest
  muted; cite sources on the slide.
- Export honestly: browser print gives PDF. PPTX needs a real exporter (for
  example python-pptx or LibreOffice, listed by `pfui.py doctor`). A PDF or a
  renamed HTML file is not an editable PPTX; report the gap instead.

## Documents and print

- `pfui.py init doc --name N --page A4|Letter` gives an `@page` layout, serif
  reading text, sans headings, captions and tabular figures, previewed as a
  sheet on screen.
- 9-11pt body at 60-75 characters per line; headings keep with their text; no
  split table rows or figures; captions say what to notice.
- Export to PDF and inspect every page. Press work (CMYK, bleed, crop marks)
  needs a press-capable tool; say so when it is not available.

## Diagrams

- Choose a notation the audience reads (flow, sequence, architecture boxes,
  state machine, swimlane) and keep it consistent: one shape per concept, one
  arrow style per relationship type, a legend for anything non-obvious.
- Flow in one direction (left to right or top to bottom); group related nodes;
  avoid edge crossings; label edges with verbs.
- Author as SVG or the project's diagram tool (Mermaid, PlantUML, draw.io) so
  text stays editable and searchable; use semantic colors and tokens; check the
  diagram at the size it will be read.

## Posters, social and brand imagery

- Design for the thumbnail first: the focal point and headline must read at the
  smallest size it will appear.
- Respect each destination's safe zones and crops; keep text off the edges and
  away from interface overlays.
- Image generation is optional and suits illustration, atmosphere and
  photography-like scenes. Without it, use authorized assets or a disclosed
  substitute. Never claim an image was generated or an attachment inspected when
  that did not happen. Record provenance and rights in `design-sources.json`.

## Authoring

Use the requested native format through available tools when possible;
otherwise HTML/CSS for editable layouts, SVG for diagrams and vector artwork,
and existing project libraries for decks or document export. Do not build a
custom editor or canvas runtime for an ordinary artifact.

Keep text, tables, diagrams and exact numbers editable where it matters.
Motion explains order, change or emphasis; preserve a readable static and
reduced-motion result and check final animation states in exports. Do not add
audio or animation merely because a tool supports it.

## Revision and delivery

Use stable slide, page or element identifiers when feedback targets a part of
the artifact. Re-read the source before editing, preserve untouched pages and
user changes, and report any requested font, effect or export feature that
could not be preserved. Keep review notes outside the artifact unless asked.

Run `pfui.py check` on HTML sources, score the
[critique rubric](design-quality.md#critique-protocol) with the medium's
criteria, and follow [delivery](delivery.md). A deck is verified as a deck, not
through invented UI states or route mappings.
