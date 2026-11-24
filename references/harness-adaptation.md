# Harness adaptation

This skill is written for any Agent Skills-compatible, file-capable AI agent. Do
not invent unavailable tools or claim capabilities based on another product.

## Find out what is available

Run `python <skill>/scripts/pfui.py doctor` (or `--json`) once per session. It
reports Git and repository state, browser executables, automation (Playwright,
adb, xcrun), exporters (LibreOffice, pandoc, typst, python-pptx, Pillow and
others), the detected stack and platforms, token sources and existing design
deliverables. It cannot see tools that live inside the agent itself, such as a
built-in browser or screenshot tool; those count too.

## Capability levels

### Level 1: files and repository

Required for the scripted product UI workflow and optional bootstrap: read,
search and write files; run local commands; use Git; read command output.

Without Git or a shell, the UI commit gate cannot run. File-capable agents can
still author systems, decks, diagrams and static prototypes; report the missing
checks and never claim gated implementation. Read-only agents can provide a
specification but must not claim to have created files.

### Level 2: rendered review

Required for normal prototype approval: serve locally (`pfui.py serve`), open
the URL in a browser or preview surface, interact, read console errors and
capture screenshots or use native vision.

Without these, produce a draft, keep it `needs-review` and label visual
verification incomplete. Never mark it approved from source inspection.

### Level 3: high-confidence verification

Preferred for completion: DOM evaluation, accessibility-tree inspection,
viewport and zoom control, native simulators and emulators, automated
end-to-end tests, image comparison or human review. Use the strongest
combination available; a missing optional tool never justifies a fabricated
result.

## Tool-neutral mapping

| Abstract action | Acceptable implementation |
|---|---|
| Ask a focused question | Native question tool or one concise chat question |
| Read, write, search | Filesystem tools, IDE tools or shell |
| Preview | `pfui.py serve`, the project's dev server, a built-in browser, IDE preview |
| Every state at once | `pfui.py serve` review harness, Sheet view; or one screenshot per state URL |
| Screenshot | Browser screenshot, OS capture, simulator capture or native vision |
| DOM capture | Evaluate `scripts/collect_dom_content.js` on each state URL |
| Accessibility check | Accessibility tree, Playwright with axe, platform inspectors, VoiceOver, TalkBack, NVDA, Narrator |
| Real runtime | Project dev command, simulator, emulator, desktop shell or device |
| Static checks | `pfui.py check`, `pfui.py lint`, `pfui.py tokens check` |
| Deliver files | Attached artifact, exact local path or repository commit, as the harness supports |

Do not hard-code client-specific tool names (a particular browser connector,
question tool or file-sending tool) into generated project instructions unless
that repository is intentionally tied to that client.

## Installation and invocation across hosts

- Install only at project scope: `.agents/skills/prototype-first-ui/` or the
  host's project-scoped skills folder (for example `.claude/skills/` for Claude
  Code). Never write global or home-directory skill folders or global agent
  configuration.
- Hosts without skill discovery: add one line to the project's instruction file
  (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` or
  the host's rules file) telling the agent to read
  `<skill path>/SKILL.md` for UI, design and visual work.
- `$prototype-first-ui <mode>` in examples is notation, not a portable command.
  Use the host's skill selector or slash invocation, or ask the agent to read
  the installed `SKILL.md`.
- Paths in the skill are relative to its folder. Use `python3` where `python`
  is not Python 3; on Windows, `py -3` also works.

Image generation, native document export and chart rendering are optional.
Reuse available tools or project libraries; HTML, CSS and SVG are the portable
editable fallback. A missing PPTX, PDF or native renderer is reported as a
missing deliverable or check, never silently replaced. Do not impose a model
family, hosted artifact API, custom editor or Node runtime on every agent
because one adapter uses it.

## Questions and ambiguity

Ask only when the answer changes product scope, content authority, source role,
destructive Git behavior or approval. Do not ask for anything that reading or
running the repository can answer.

When the harness cannot ask during execution:

- choose the safest reversible default and record it as an assumption;
- record unknowns as `unknown` or non-goals;
- stop at approval and destructive boundaries;
- never infer authorization for Git reset, production implementation, remote
  publication, credential use or third-party upload.

## Browserless fallback

1. Run `pfui.py check` and other static checks.
2. Use `pfui.py content static-scan`, `seed` and `check --allow-static` as a
   provisional copy review (never final sign-off).
3. Validate files, links, local assets and JSON records.
4. Keep the deliverable `needs-review`.
5. Report that hierarchy, clipping, runtime interaction, computed accessibility
   and final DOM content remain unverified.

## Multimodal-input fallback

When an attachment or referenced media cannot be accessed, do not guess its
contents or rely on a filename, opaque id, alt text or claim as though it were
inspected. Continue only with available evidence and state which decisions are
blocked or provisional.

## Multi-agent use

Subagents can run independent read-only audits, accessibility review, platform
checks or visual comparison; they are never required. When used:

- give them the exact mode, paths, source roles and read-only scope;
- prohibit production writes during design review;
- merge findings through the structured records (rubric scores, lint JSON,
  content inventory) rather than free-form prompt chains;
- never let a subagent approve, reset history, publish or override the user's
  content authority.
