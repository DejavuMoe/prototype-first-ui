# Usage examples

`$prototype-first-ui <mode>` stands for whatever invocation your agent supports;
plain requests work too because the skill routes by intent.

## Start or resume

```text
$prototype-first-ui
Run doctor and status, tell me what this repository can verify, and continue the
deliverable that is waiting for work.
```

## Design system

```text
$prototype-first-ui system
Build this project's design system from the existing brand and components:
semantic tokens with light and dark modes, contrast checked in both, component
states and a gallery. Keep it in this project; do not install global skills.
```

```text
$prototype-first-ui system
Re-brand the starter system around our teal (#0f766e). Generate the ramps,
re-point the accent roles, keep every declared contrast pair passing, and build
CSS, iOS, Android and Flutter outputs from the one token file.
```

## Critique

```text
$prototype-first-ui critique
Our settings page looks dated. Review it at mobile and desktop widths in light
and dark, score it against the quality rubric with screenshots as evidence, and
rank the fixes. Do not change production code yet.
```

## Prototype

```text
$prototype-first-ui prototype
Prototype bulk rename for this file manager in designs/rename/: preview of the
changes, filename conflicts, progress, cancellation and errors. Present it for
review with state URLs.
```

```text
$prototype-first-ui prototype
Design the same onboarding flow for iOS and Android. Share our tokens, but
follow each platform's navigation, controls and back behavior, and list what an
HTML prototype cannot verify.
```

## Explore

```text
$prototype-first-ui explore
Explore three navigation and workspace structures for <product> using the
existing capabilities and design system.
```

## Visual communication

```text
$prototype-first-ui compose
Use the project system and the approved copy in docs/launch-copy.md for a
six-slide introduction and a one-page handout. Keep the source editable, inspect
both, and tell me which export formats are not available here.
```

```text
$prototype-first-ui compose
Build the monthly status email from content/october.json: single column, table
layout, dark-mode safe, readable with images off. Lint it as email.
```

## Data visualization

```text
$prototype-first-ui visualize
Turn this CSV into a dashboard. Define each metric and its comparison, check
totals and filters against the rows, and design loading, empty and stale states.
```

## Other platforms

```text
$prototype-first-ui prototype
Design the output of our CLI's `deploy` command: progress, success, failure and
--json. It must read without color and in an 80-column terminal.
```

## Product UI lifecycle

```text
$prototype-first-ui audit
Record this product's current screens, actions, states and interfaces in
docs/ui/capabilities.md.
```

```text
$prototype-first-ui approve
I approve the current designs/<project>/index.html. Record its approval and
create the design-only commit.
```

```text
$prototype-first-ui implement
Implement <feature> from the approved designs/<project>/index.html at design
commit <SHA>.
```

```text
$prototype-first-ui sync
Compare the production <surface> with its approved prototype and fix
implementation drift.
```

```text
$prototype-first-ui verify
Check <feature> against its approved prototype: interactions, content,
responsive layout, themes and keyboard accessibility.
```

## Bootstrap

```text
$prototype-first-ui bootstrap
Clean this repository and replace its local Git history on branch <branch>
after creating and verifying an external recovery snapshot. Preserve the
application and leave the remote unchanged.
```
