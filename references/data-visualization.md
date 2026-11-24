# Data visualization and dashboards

Use for analytical pages, charts in any medium and data-driven graphics. Read
[UI design](ui-design.md) for interactive product surfaces and
[visual communication](visual-communication.md) for decks and reports that use
charts.

## Establish what the data means

Read the supplied dataset or authorized source. Record provenance, observation
period, refresh time, units, timezone, field definitions and missing values.
Identify aggregation grain, filters and comparison baselines before computing a
metric. A screenshot of a number is not a reproducible dataset.

Keep data and presentation separate. Compute totals, rates and changes from
source rows; record formulas and denominators. Check a small known example or
recompute independently, including empty data, zero denominators and missing or
duplicate observations. Do not treat missing as zero without a domain rule.
Parse dates explicitly and keep calendar dates separate from instants.

When real data is unavailable, label fixtures as illustrative and draw no
business conclusions. Include only the fields the task needs; keep private raw
data out of client assets.

## Start from the question

Every view answers a named question for a named reader ("Are pickups on time
this week, and where are they slipping?"). A chart without a question is
decoration; a sentence or a table often answers better.

| Question | Useful starting point |
|---|---|
| Compare categories | Sorted bar or dot plot |
| Change over time | Line with explicit gaps for missing intervals |
| Distribution | Histogram, box plot or individual points |
| Relationship | Scatter plot with units and context |
| Part-to-whole | Stacked bar, or a small labelled part-to-whole for two or three parts |
| Exact lookup | Table, optionally with an inline bar or sparkline |

## Dashboard composition

- Order by decision: headline status and key metrics, then trend, then
  breakdown, then detail. Group by question, not by chart type.
- Each metric shows its definition (on hover and in a details view), its unit,
  a comparison (target, previous period or baseline) and its freshness. A KPI
  tile without a comparison is a vanity number.
- A shared time range and filter bar at the top drives every chart, metric and
  table consistently; the active filters stay visible.
- Five to nine primary views per screen; move the rest behind tabs or drill-down.
- Design loading, empty, partial, error and stale states. Never show obsolete
  numbers as current after a refresh fails; show the age instead.

## Chart craft

- Bars start at zero. Do not mix incompatible scales on dual axes; split them.
- Sort categories by value unless the order is meaningful (time, ranking).
- Label directly at the end of lines and bars instead of using distant legends;
  keep gridlines light and few; no 3D, shadows or gradients on marks.
- Highlight what matters in the accent or a data color and mute context in a
  neutral; annotate events and thresholds in plain words.
- Pie and donut charts only for two or three parts; never for comparisons
  across groups.
- Explain transformed axes, truncation and uncertainty.

## Color and type in charts

- Use semantic text and surface tokens for chrome and the categorical
  `color.data.1-n` tokens for series; each starter data color clears 3:1 against
  surfaces in light and dark themes. Keep a series' color identical across
  every chart on the page.
- Categorical color identifies entities; sequential lightness shows magnitude;
  diverging color needs a meaningful center; status colors keep their status
  meaning and are never reused for series.
- Never rely on color alone: direct labels, markers, patterns or an accessible
  table must carry the distinction. Check color-vision simulations when
  available; naming a familiar palette is not a validation.
- Tabular figures, locale-aware formatting, consistent precision (more decimals
  never add truth), abbreviations (1.2k) with the full value available.

## Interaction, accessibility and verification

- Tooltips are bounded, keyboard and touch reachable, and never the only place a
  value appears. Hit areas are at least 24px.
- Provide a text summary of the main finding and a data table alternative for
  complex charts; give SVG charts a role and accessible name.
- Filters update charts, metrics and tables together. Verify one filter against
  the expected rows and one metric against its formula.
- Inspect label collisions, legends, axes and overflow at each target size and
  theme. For static exports replace hover-only details with labels, notes or
  tables. Re-render after data changes; a fresh source does not refresh an old
  export.

Deliver the editable view, safe source references, metric definitions and the
checks actually run. Do not add a scheduler, database, connector, chart
framework or live-feed claim unless the task needs it and the environment
supports it.
