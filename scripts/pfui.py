#!/usr/bin/env python3
"""prototype-first-ui command line: one entry point for agents and people.

  doctor    What this machine and project can do (browsers, exporters, stack).
  status    Design deliverables, review states and the next step for each.
  init      Scaffold a design system, app, site, deck or document.
  serve     Localhost preview plus a review harness (states x widths x themes).
  check     Run every applicable check under a path: review records, contracts,
            sources, content inventory, tokens (with contrast) and design lint.
  lint      Design lint (see design_lint.py --help).
  tokens    Design tokens: check | build | ramp | contrast (design_tokens.py).
  content   Content inventory: seed | static-scan | check (content_audit.py).
  gate      Workflow gates: review | approval | contract | sources | structure |
            design-scope | implementation-gate (validate_workflow.py).

Standard library only (Python 3.9+). Nothing here uploads, installs or
publishes; serve binds to 127.0.0.1 only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import functools
import http.server
import importlib.util
import json
import os
from pathlib import Path
import platform as platform_module
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import unquote, urlsplit

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
STARTER = SKILL_ROOT / "assets" / "starter"
sys.path.insert(0, str(SCRIPTS))

import design_lint  # noqa: E402
import design_tokens  # noqa: E402

IGNORED_DIRS = {".git", "node_modules", "dist", "build", "coverage", "__pycache__", ".cache", ".venv", "venv", "target", ".next", ".nuxt"}
KINDS = ("system", "app", "site", "deck", "doc")
KIND_MEDIUM = {"system": "ui", "app": "ui", "site": "site", "deck": "deck", "doc": "doc"}
KIND_ENTRY = {"system": "components.html", "app": "index.html", "site": "index.html", "deck": "index.html", "doc": "index.html"}
PAGE_SIZES = {"A4": ("A4", "210mm", "297mm"), "Letter": ("letter", "8.5in", "11in")}
SHARED_STYLES = ("tokens.css", "base.css", "params.js")
PASSTHROUGH = {"lint": "design_lint", "tokens": "design_tokens", "content": "content_audit", "gate": "validate_workflow"}


def safe_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def skill_version() -> str:
    try:
        from validate_skill import parse_frontmatter

        frontmatter, _ = parse_frontmatter((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"))
        metadata = frontmatter.get("metadata")
        if isinstance(metadata, dict):
            return str(metadata.get("version", "unknown"))
    except (OSError, ValueError, ImportError):
        pass
    return "unknown"


def run_quiet(command: Sequence[str], cwd: Optional[Path] = None, timeout: int = 10) -> Optional[str]:
    try:
        result = subprocess.run(list(command), cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or result.stderr).strip()


def walk_files(root: Path, max_depth: int = 6) -> List[Path]:
    found: List[Path] = []
    root = root.resolve()
    for directory, dirs, files in os.walk(root):
        current = Path(directory)
        depth = len(current.relative_to(root).parts)
        dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS and not name.startswith(".") and depth < max_depth)
        found.extend(current / name for name in sorted(files))
    return found


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    design_tokens.write_text_lf(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_json(path: Path) -> Optional[object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def default_root() -> Path:
    designs = Path("designs")
    return designs if designs.is_dir() else Path(".")


# --------------------------------------------------------------------------
# doctor
# --------------------------------------------------------------------------

BROWSER_COMMANDS = {
    "chrome": ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser"),
    "edge": ("msedge", "microsoft-edge", "microsoft-edge-stable"),
    "firefox": ("firefox",),
}
BROWSER_PATHS = (
    ("chrome", "%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
    ("chrome", "%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
    ("chrome", "%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"),
    ("edge", "%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe"),
    ("edge", "%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe"),
    ("firefox", "%ProgramFiles%\\Mozilla Firefox\\firefox.exe"),
    ("chrome", "/Applications/Google Chrome.app"),
    ("edge", "/Applications/Microsoft Edge.app"),
    ("firefox", "/Applications/Firefox.app"),
    ("safari", "/Applications/Safari.app"),
)
TOOLS = {
    "render-and-automation": ("playwright", "adb", "emulator", "xcrun", "xcodebuild", "flutter"),
    "exporters": ("soffice", "libreoffice", "pandoc", "typst", "magick", "inkscape", "rsvg-convert", "wkhtmltopdf"),
    "toolchains": ("swift", "dotnet", "cargo", "java", "gradle", "pnpm", "npm", "bun", "deno"),
}
PY_MODULES = {"playwright": "Playwright (Python)", "PIL": "Pillow", "pptx": "python-pptx", "docx": "python-docx", "reportlab": "ReportLab", "matplotlib": "Matplotlib", "openpyxl": "openpyxl"}
JS_PACKAGES = {
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt", "svelte": "Svelte", "@sveltejs/kit": "SvelteKit",
    "solid-js": "Solid", "@angular/core": "Angular", "astro": "Astro", "vite": "Vite", "tailwindcss": "Tailwind CSS",
    "@mui/material": "MUI", "@chakra-ui/react": "Chakra UI", "@mantine/core": "Mantine", "antd": "Ant Design",
    "element-plus": "Element Plus", "electron": "Electron", "@tauri-apps/api": "Tauri", "react-native": "React Native",
    "expo": "Expo", "@playwright/test": "Playwright", "playwright": "Playwright", "puppeteer": "Puppeteer",
    "style-dictionary": "Style Dictionary", "@terrazzo/cli": "Terrazzo", "recharts": "Recharts", "d3": "D3",
    "echarts": "ECharts", "chart.js": "Chart.js", "@vitejs/plugin-react": "Vite React", "pptxgenjs": "PptxGenJS",
}
JS_PREFIXES = {"@radix-ui/": "Radix UI", "@storybook/": "Storybook", "@headlessui/": "Headless UI", "@ark-ui/": "Ark UI"}


def detect_browsers() -> Dict[str, str]:
    found: Dict[str, str] = {}
    for name, commands in BROWSER_COMMANDS.items():
        for command in commands:
            path = shutil.which(command)
            if path:
                found.setdefault(name, path)
                break
    for name, raw in BROWSER_PATHS:
        path = Path(os.path.expandvars(raw))
        if "%" not in str(path) and path.exists():
            found.setdefault(name, str(path))
    return found


def detect_project(root: Path) -> Dict[str, object]:
    result: Dict[str, object] = {"root": str(root.resolve()), "stack": [], "platforms": [], "tokenSources": [], "designProjects": []}
    stack: List[str] = []
    platforms: Set[str] = set()
    token_sources: List[str] = []
    files = walk_files(root, max_depth=4)

    def add(label: str) -> None:
        if label not in stack:
            stack.append(label)

    for path in files:
        relative = path.relative_to(root.resolve()).as_posix() if path.is_absolute() else path.as_posix()
        name = path.name
        if name == "package.json":
            data = load_json(path)
            if isinstance(data, dict):
                deps: Dict[str, object] = {}
                for key in ("dependencies", "devDependencies", "peerDependencies"):
                    value = data.get(key)
                    if isinstance(value, dict):
                        deps.update(value)
                for dep in deps:
                    label = JS_PACKAGES.get(dep) or next((label for prefix, label in JS_PREFIXES.items() if dep.startswith(prefix)), None)
                    if label:
                        add(label)
                if any(dep in deps for dep in ("react-native", "expo")):
                    platforms.update({"ios", "android"})
                elif any(dep in deps for dep in ("electron", "@tauri-apps/api")):
                    platforms.add("desktop")
                elif deps:
                    platforms.add("web")
        elif name == "pubspec.yaml":
            add("Flutter")
            platforms.update({"ios", "android"})
        elif name == "Package.swift" or path.parent.name.endswith((".xcodeproj", ".xcworkspace")):
            # Xcode projects are directory bundles; match the files inside them.
            add("Swift/Xcode")
            platforms.add("ios")
        elif name == "AndroidManifest.xml" or name in {"build.gradle.kts", "build.gradle"} and "android" in path.read_text(encoding="utf-8", errors="ignore")[:4000].lower():
            add("Android")
            platforms.add("android")
        elif name.endswith(".csproj"):
            text = path.read_text(encoding="utf-8", errors="ignore")[:6000]
            for marker, label in (("UseWPF", "WPF"), ("UseWinUI", "WinUI"), ("Microsoft.Maui", ".NET MAUI"), ("UseWindowsForms", "WinForms")):
                if marker in text:
                    add(label)
                    platforms.add("desktop")
        elif name == "Cargo.toml" and "tauri" in path.read_text(encoding="utf-8", errors="ignore").lower():
            add("Tauri")
            platforms.add("desktop")
        elif name == "manifest.json":
            data = load_json(path)
            if isinstance(data, dict) and "manifest_version" in data:
                add("Browser extension")
                platforms.add("extension")
        if re.search(r"(?:^|[./-])tokens?(?:\.[a-z]+)?\.json$|design-tokens|tailwind\.config\.|theme\.(?:ts|js|json)$", name, re.IGNORECASE) and "resolved" not in name:
            token_sources.append(relative)
        elif name in {"tokens.css", "variables.css", "colors.xml"} or relative.endswith(".colorset/Contents.json"):
            token_sources.append(relative)
        if name == "design-review.json":
            result["designProjects"].append(path.parent.relative_to(root.resolve()).as_posix() or ".")  # type: ignore[union-attr]
    for directory in (".storybook",):
        if (root / directory).is_dir():
            add("Storybook")
    result["stack"] = stack
    result["platforms"] = sorted(platforms)
    result["tokenSources"] = token_sources[:20]
    return result


def doctor_report(root: Path) -> Dict[str, object]:
    git_version = run_quiet(["git", "--version"])
    in_repo = run_quiet(["git", "rev-parse", "--show-toplevel"], cwd=root) if git_version else None
    dirty = run_quiet(["git", "status", "--porcelain"], cwd=root) if in_repo else None
    browsers = detect_browsers()
    tools = {group: {name: bool(shutil.which(name)) for name in names} for group, names in TOOLS.items()}
    modules = {label: importlib.util.find_spec(module) is not None for module, label in PY_MODULES.items()}
    automation = bool(modules.get("Playwright (Python)") or tools["render-and-automation"].get("playwright") or tools["render-and-automation"].get("adb") or tools["render-and-automation"].get("xcrun"))
    project = detect_project(root)
    exporters = [name for name, present in tools["exporters"].items() if present] + [label for label in ("python-pptx", "python-docx", "ReportLab", "Pillow") if modules.get(label)]
    return {
        "schemaVersion": 1,
        "skill": {"version": skill_version(), "path": str(SKILL_ROOT)},
        "host": {"os": platform_module.system(), "release": platform_module.release(), "python": platform_module.python_version()},
        "levels": {
            "files": True,
            "shell": True,
            "git": bool(git_version),
            "renderedReview": bool(browsers),
            "automation": automation,
        },
        "git": {"version": git_version, "repository": in_repo, "uncommittedPaths": len(dirty.splitlines()) if dirty else 0},
        "node": run_quiet(["node", "--version"]),
        "browsers": browsers,
        "tools": tools,
        "pythonModules": modules,
        "exporters": exporters,
        "project": project,
        "notes": [
            "Your agent may have its own browser or preview tool; that also satisfies rendered review.",
            "Report missing capabilities as unverified checks or undelivered formats; never claim them.",
        ],
    }


def print_doctor(report: Dict[str, object]) -> None:
    levels = report["levels"]
    yes = lambda flag: "yes" if flag else "no"  # noqa: E731
    print("prototype-first-ui %s on %s, Python %s" % (report["skill"]["version"], report["host"]["os"], report["host"]["python"]))  # type: ignore[index]
    print("Files + shell: yes   Git: %s   Rendered review: %s   Automation: %s" % (yes(levels["git"]), yes(levels["renderedReview"]), yes(levels["automation"])))  # type: ignore[index]
    git = report["git"]
    if git["repository"]:  # type: ignore[index]
        print("Repository: %s (%d uncommitted path(s))" % (git["repository"], git["uncommittedPaths"]))  # type: ignore[index]
    elif levels["git"]:  # type: ignore[index]
        print("Repository: not inside a Git work tree (product UI commit gates unavailable here)")
    browsers = report["browsers"]
    print("Browsers: %s" % (", ".join(sorted(browsers)) if browsers else "none found on PATH or standard locations"))  # type: ignore[arg-type]
    print("Node: %s" % (report["node"] or "not found (optional)"))
    present = [name for group in report["tools"].values() for name, ok in group.items() if ok]  # type: ignore[union-attr]
    print("Tools: %s" % (", ".join(present) if present else "none of the optional tools"))
    modules = [label for label, ok in report["pythonModules"].items() if ok]  # type: ignore[union-attr]
    print("Python modules: %s" % (", ".join(modules) if modules else "standard library only"))
    print("Export paths: %s" % (", ".join(report["exporters"]) if report["exporters"] else "HTML/CSS/SVG source and browser print-to-PDF only"))  # type: ignore[arg-type]
    project = report["project"]
    print("Project stack: %s" % (", ".join(project["stack"]) or "no framework detected"))  # type: ignore[index]
    print("Platforms: %s" % (", ".join(project["platforms"]) or "unknown"))  # type: ignore[index]
    if project["tokenSources"]:  # type: ignore[index]
        print("Token sources: %s" % ", ".join(project["tokenSources"][:8]))  # type: ignore[index]
    if project["designProjects"]:  # type: ignore[index]
        print("Design deliverables: %s (run `pfui.py status`)" % ", ".join(project["designProjects"]))  # type: ignore[index]
    print("Verification path: %s" % (
        "render with a browser, then `pfui.py check`" if levels["renderedReview"]  # type: ignore[index]
        else "no browser found: use the agent's preview tool if it has one; otherwise deliver a draft and list visual checks as unverified"
    ))


# --------------------------------------------------------------------------
# status
# --------------------------------------------------------------------------

NEXT_STEP = {
    "draft": "Finish the draft: render every state, run `pfui.py check`, then mark needs-review and present it.",
    "needs-review": "Waiting for the user's explicit approval of this exact file (praise or change requests are not approval).",
    "changes-requested": "Revise, re-render and re-check, then return it to needs-review.",
    "approved": "Approved. Product UI: commit design-only, then `pfui.py gate implementation-gate` before production edits.",
}


def find_projects(root: Path) -> List[Path]:
    markers = {"design-review.json", "ui-contract.json", "pfui.json"}
    projects: Set[Path] = set()
    for path in walk_files(root, max_depth=5):
        if path.name in markers:
            projects.add(path.parent)
    return sorted(projects)


def git_info(project: Path) -> Dict[str, object]:
    top = run_quiet(["git", "rev-parse", "--show-toplevel"], cwd=project)
    if not top:
        return {}
    last = run_quiet(["git", "log", "-1", "--format=%h %cs %s", "--", "."], cwd=project)
    dirty = run_quiet(["git", "status", "--porcelain", "--", "."], cwd=project)
    return {"lastCommit": last or None, "uncommitted": len(dirty.splitlines()) if dirty else 0}


def status_report(root: Path) -> Dict[str, object]:
    entries = []
    for project in find_projects(root):
        config = load_json(project / "pfui.json")
        review = load_json(project / "design-review.json")
        contract = load_json(project / "ui-contract.json")
        assets = []
        if isinstance(review, dict) and isinstance(review.get("assets"), list):
            for asset in review["assets"]:
                if isinstance(asset, dict):
                    status = str(asset.get("status"))
                    assets.append({"path": asset.get("path"), "status": status, "next": NEXT_STEP.get(status, "Unknown status; fix design-review.json.")})
        surfaces = []
        if isinstance(contract, dict) and isinstance(contract.get("surfaces"), list):
            for surface in contract["surfaces"]:
                if isinstance(surface, dict):
                    surfaces.append({"id": surface.get("id"), "status": surface.get("status")})
        entry: Dict[str, object] = {
            "path": project.resolve().relative_to(root.resolve()).as_posix() if project.resolve() != root.resolve() else ".",
            "kind": config.get("kind") if isinstance(config, dict) else None,
            "platform": config.get("platform") if isinstance(config, dict) else None,
            "assets": assets,
            "surfaces": surfaces,
            "records": sorted(name for name in ("design-review.json", "ui-contract.json", "content-inventory.json", "design-sources.json", "pfui.json", "tokens.json") if (project / name).exists()),
        }
        entry.update(git_info(project))
        entries.append(entry)
    return {"schemaVersion": 1, "root": str(root.resolve()), "projects": entries}


def print_status(report: Dict[str, object]) -> None:
    projects = report["projects"]
    if not projects:
        print("No design deliverables under %s. Start with `pfui.py init <kind>`." % report["root"])
        return
    for entry in projects:  # type: ignore[union-attr]
        detail = ", ".join(str(item) for item in (entry.get("kind"), entry.get("platform")) if item)
        print("%s%s" % (entry["path"], " (%s)" % detail if detail else ""))
        for asset in entry["assets"]:
            print("  %-18s %s" % (asset["status"], asset["path"]))
            print("  %-18s -> %s" % ("", asset["next"]))
        for surface in entry["surfaces"]:
            print("  surface %-10s %s" % (surface["status"], surface["id"]))
        if entry.get("lastCommit"):
            print("  last commit: %s" % entry["lastCommit"])
        if entry.get("uncommitted"):
            print("  uncommitted changes: %d path(s)" % entry["uncommitted"])
        print("  records: %s" % ", ".join(entry["records"]))


# --------------------------------------------------------------------------
# init
# --------------------------------------------------------------------------


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "design"


def render(text: str, values: Dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def system_source(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit)
    project_system = Path("designs") / "system"
    if all((project_system / name).is_file() for name in SHARED_STYLES):
        return project_system
    return STARTER / "system"


def cmd_init(args: argparse.Namespace) -> int:
    kind = args.kind
    name = args.name or ("Design system" if kind == "system" else "Untitled")
    slug = args.slug or ("system" if kind == "system" else slugify(name))
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        print("ERROR: --slug must be lowercase letters, digits and hyphens", file=sys.stderr)
        return 2
    dest = Path(args.dest) if args.dest else Path("designs") / slug
    if dest.exists() and any(dest.iterdir()) and not args.force:
        existing = [path.name for path in dest.iterdir()][:8]
        print("ERROR: %s already contains files (%s). Choose another --dest or pass --force to add missing files only." % (dest, ", ".join(existing)), file=sys.stderr)
        return 1
    page = PAGE_SIZES[args.page]
    values = {
        "NAME": name,
        "PROJECT_NAME": name,
        "SLUG": slug,
        "LANG": args.lang,
        "PLATFORM": args.platform,
        "PLATFORM_ATTR": "" if args.platform == "web" else ' data-platform="%s"' % args.platform,
        "PAGE_SIZE": page[0],
        "PAGE_WIDTH": page[1],
        "PAGE_HEIGHT": page[2],
        "DATE": dt.date.today().isoformat(),
    }
    written: List[str] = []
    skipped: List[str] = []

    def place(source: Path, target: Path, templated: bool = True) -> None:
        if target.exists():
            skipped.append(target.as_posix())
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        if templated and source.suffix.lower() in {".html", ".css", ".js", ".json", ".md"}:
            design_tokens.write_text_lf(target, render(source.read_text(encoding="utf-8"), values))
        elif source.suffix.lower() in {".css", ".js"}:
            design_tokens.write_text_lf(target, source.read_text(encoding="utf-8"))
        else:
            shutil.copyfile(source, target)
        written.append(target.as_posix())

    kind_dir = STARTER / kind
    for source in sorted(path for path in kind_dir.rglob("*") if path.is_file()):
        place(source, dest / source.relative_to(kind_dir))
    origin = None
    if kind != "system":
        origin = system_source(args.system)
        for filename in SHARED_STYLES:
            source = origin / filename
            if not source.is_file():
                print("ERROR: design system file missing: %s" % source, file=sys.stderr)
                return 1
            place(source, dest / "styles" / filename, templated=False)
    else:
        foundations = SKILL_ROOT / "assets" / "foundations.template.md"
        place(foundations, dest / "foundations.md")

    entry = KIND_ENTRY[kind]
    config: Dict[str, object] = {"schemaVersion": 1, "kind": kind, "platform": args.platform, "medium": KIND_MEDIUM[kind], "lint": {"disable": [], "ignore": []}}
    if kind == "system":
        config["tokens"] = "tokens.json"
    elif origin is not None:
        origin_label = origin.resolve().as_posix()
        try:
            origin_label = origin.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            if origin.resolve() == (STARTER / "system").resolve():
                origin_label = "prototype-first-ui starter %s" % skill_version()
        config["system"] = {"source": origin_label, "copiedOn": values["DATE"], "files": ["styles/%s" % name for name in SHARED_STYLES]}
    if not (dest / "pfui.json").exists():
        write_json(dest / "pfui.json", config)
        written.append((dest / "pfui.json").as_posix())
    if not (dest / "design-review.json").exists():
        write_json(dest / "design-review.json", {"schemaVersion": 1, "assets": [{"path": entry, "status": "draft", "approvalEvidence": None}]})
        written.append((dest / "design-review.json").as_posix())
    if args.product and kind in {"app", "site"} and not (dest / "ui-contract.json").exists():
        profile = args.profile or ("operational-strict" if kind == "app" else "marketing-approved")
        files = sorted(Path(path).resolve().relative_to(dest.resolve()).as_posix() for path in written + skipped if Path(path).suffix in {".html", ".css", ".js"})
        contract = {
            "schemaVersion": 2,
            "project": {"name": name, "slug": slug, "surfaceType": "operational" if kind == "app" else "marketing"},
            "content": {"defaultProfile": profile, "inventory": "content-inventory.json", "approvedCopySources": []},
            "designSources": None,
            "surfaces": [{
                "id": slug,
                "contentProfile": profile,
                "prototype": {"entry": entry, "assetPath": entry, "files": sorted(set(files)), "states": ["ready", "loading", "empty", "error"] if kind == "app" else ["default"], "stableIds": [slug]},
                "production": {"routeOrWindow": None, "files": [], "interfaces": [], "tests": []},
                "status": "prototype",
            }],
        }
        write_json(dest / "ui-contract.json", contract)
        written.append((dest / "ui-contract.json").as_posix())

    for path in written:
        print("created  %s" % path)
    for path in skipped:
        print("kept     %s (already existed)" % path)
    if kind == "system":
        print("\nNext: re-brand tokens.json, then `pfui.py tokens build %s --out %s` and open %s." % ((dest / "tokens.json").as_posix(), dest.as_posix(), (dest / "components.html").as_posix()))
    else:
        print("\nStyles copied from: %s" % (origin.as_posix() if origin else "-"))
        print("Next: replace every {{slot}} with evidenced or approved content, design the ready state,")
        print("      preview with `pfui.py serve %s`, then run `pfui.py check %s`." % (dest.as_posix(), dest.as_posix()))
    return 0


# --------------------------------------------------------------------------
# serve
# --------------------------------------------------------------------------

STATE_VIEW = re.compile(r"data-state-view\s*=\s*[\"']([a-z0-9][a-z0-9-]{0,39})[\"']")
SLIDE = re.compile(r"<section\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bslide\b", re.IGNORECASE)


def build_manifest(root: Path) -> Dict[str, object]:
    pages = []
    contract = load_json(root / "ui-contract.json")
    contract_states: Dict[str, List[str]] = {}
    if isinstance(contract, dict):
        for surface in contract.get("surfaces", []) or []:
            if isinstance(surface, dict) and isinstance(surface.get("prototype"), dict):
                prototype = surface["prototype"]
                if isinstance(prototype.get("entry"), str) and isinstance(prototype.get("states"), list):
                    contract_states[prototype["entry"]] = [str(state) for state in prototype["states"]]
    for path in walk_files(root, max_depth=4):
        if path.suffix.lower() not in {".html", ".htm"} or "screenshots" in path.parts or "exports" in path.parts:
            continue
        relative = path.relative_to(root.resolve()).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        states: List[str] = []
        for state in STATE_VIEW.findall(text):
            if state not in states:
                states.append(state)
        slides = len(SLIDE.findall(text))
        pages.append({
            "path": relative,
            "kind": "deck" if slides else "page",
            "slides": slides,
            "states": states or contract_states.get(relative, []),
        })
    pages.sort(key=lambda page: (page["path"] not in {"index.html", "components.html"}, page["path"]))
    return {"schemaVersion": 1, "root": str(root.resolve()), "pages": pages}


class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    internal = {
        "/__pfui/": SKILL_ROOT / "assets" / "review" / "review.html",
        "/__pfui/review.html": SKILL_ROOT / "assets" / "review" / "review.html",
        "/__pfui/system/tokens.css": STARTER / "system" / "tokens.css",
        "/__pfui/system/base.css": STARTER / "system" / "base.css",
        "/__pfui/system/params.js": STARTER / "system" / "params.js",
    }
    verbose = False

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - signature from base class
        if self.verbose:
            super().log_message(format, *args)

    def translate_path(self, path: str) -> str:
        translated = Path(super().translate_path(path)).resolve()
        root = Path(self.directory).resolve()
        if translated != root and root not in translated.parents:
            return str(root / "__outside_root__")
        return str(translated)

    def _internal(self, head: bool) -> bool:
        route = unquote(urlsplit(self.path).path)
        if not route.startswith("/__pfui"):
            return False
        if route == "/__pfui/manifest.json":
            body = json.dumps(build_manifest(Path(self.directory)), ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif route in self.internal and self.internal[route].is_file():
            target = self.internal[route]
            body = target.read_bytes()
            content_type = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}[target.suffix]
        else:
            self.send_error(404, "Unknown review resource")
            return True
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)
        return True

    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        if not self._internal(False):
            super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._internal(True):
            super().do_HEAD()


def cmd_serve(args: argparse.Namespace) -> int:
    root = Path(args.path or default_root()).resolve()
    if not root.is_dir():
        print("ERROR: not a directory: %s" % root, file=sys.stderr)
        return 2
    ReviewHandler.verbose = args.verbose
    handler = functools.partial(ReviewHandler, directory=str(root))
    server: Optional[http.server.ThreadingHTTPServer] = None
    for port in (args.port, 0):
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            continue
    if server is None:
        print("ERROR: could not bind 127.0.0.1", file=sys.stderr)
        return 1
    port = server.server_address[1]
    manifest = build_manifest(root)
    print("Serving %s (localhost only)" % root)
    print("  Preview: http://127.0.0.1:%d/" % port)
    print("  Review:  http://127.0.0.1:%d/__pfui/review.html" % port)
    for page in manifest["pages"][:12]:  # type: ignore[index]
        detail = ("%d slides" % page["slides"]) if page["kind"] == "deck" else (", ".join(page["states"]) or "no state views")
        print("  %-28s %s" % (page["path"], detail))
    print("State URLs: <page>?state=<id>&theme=dark&platform=ios. Stop with Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------


class CheckResult:
    def __init__(self) -> None:
        self.sections: List[Dict[str, object]] = []

    def add(self, kind: str, target: str, errors: Sequence[str] = (), warnings: Sequence[str] = (), notes: Sequence[str] = ()) -> None:
        self.sections.append({"kind": kind, "target": target, "errors": list(errors), "warnings": list(warnings), "notes": list(notes)})


def stale_css(tokens_path: Path) -> Optional[str]:
    css_path = tokens_path.with_name("tokens.css")
    if not css_path.is_file():
        return None
    current = css_path.read_text(encoding="utf-8")
    first_line = current.splitlines()[0] if current else ""
    if "Generated by prototype-first-ui design_tokens.py" not in first_line:
        return None
    token_set = design_tokens.load_token_set(tokens_path, [])
    if token_set.errors:
        return None
    prefix = re.search(r"--prefix (\S+)", first_line)
    fresh = design_tokens.build_css(token_set, tokens_path.name, prefix.group(1) if prefix else "", "--resolve" in first_line)
    if fresh != current:
        return "tokens.css is out of date with %s; run `pfui.py tokens build %s --out %s`" % (tokens_path.name, tokens_path.as_posix(), tokens_path.parent.as_posix())
    return None


def review_consistency(contract: object, review: object) -> Tuple[List[str], List[str]]:
    """Approval lives in design-review.json; each mapped ui-contract surface must agree with it."""
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(contract, dict) or not isinstance(review, dict):
        return errors, warnings
    statuses = {
        asset.get("path"): asset.get("status")
        for asset in review.get("assets", []) or []
        if isinstance(asset, dict)
    }
    for surface in contract.get("surfaces", []) or []:
        if not isinstance(surface, dict) or not isinstance(surface.get("prototype"), dict):
            continue
        asset = surface["prototype"].get("assetPath")
        surface_status = surface.get("status")
        review_status = statuses.get(asset)
        if surface_status in {"approved", "implemented"} and review_status != "approved":
            errors.append("surface %s is %s but design-review.json records %s as %s; approval must be recorded first" % (surface.get("id"), surface_status, asset, review_status or "missing"))
        elif review_status == "approved" and surface_status not in {"approved", "implemented"}:
            warnings.append("%s is approved but surface %s is still %s; set it to approved (implementation-gate requires it)" % (asset, surface.get("id"), surface_status))
    return errors, warnings


def run_check(root: Path, final: bool, strict: bool, platform: Optional[str], medium: Optional[str]) -> Dict[str, object]:
    import validate_workflow
    from content_audit import validate_inventory

    result = CheckResult()
    files = walk_files(root, max_depth=6)
    by_name: Dict[str, List[Path]] = {}
    for path in files:
        by_name.setdefault(path.name, []).append(path)

    def label(path: Path) -> str:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    for path in by_name.get("design-review.json", []):
        data = load_json(path)
        if data is None:
            result.add("review", label(path), ["invalid JSON"])
            continue
        result.add("review", label(path), validate_workflow.validate_review(data, path.parent))
    for path in by_name.get("ui-contract.json", []):
        data = load_json(path)
        if data is None:
            result.add("contract", label(path), ["invalid JSON"])
            continue
        errors = validate_workflow.validate_contract(data, path.parent, "approved" if final else "draft")
        consistency_errors, consistency_warnings = review_consistency(data, load_json(path.parent / "design-review.json"))
        if final:
            consistency_errors, consistency_warnings = consistency_errors + consistency_warnings, []
        result.add("contract", label(path), errors + consistency_errors, consistency_warnings)
    for path in by_name.get("design-sources.json", []):
        data = load_json(path)
        if data is None:
            result.add("sources", label(path), ["invalid JSON"])
            continue
        result.add("sources", label(path), validate_workflow.validate_sources(data, path.parent))
    for path in by_name.get("content-inventory.json", []):
        data = load_json(path)
        if data is None:
            result.add("content", label(path), ["invalid JSON"])
            continue
        errors, warnings = validate_inventory(data, allow_static=not final, fail_on_soft_flags=False)
        if final:
            result.add("content", label(path), errors, warnings)
        else:
            result.add("content", label(path), [], errors + warnings, ["Drafting: inventory gaps are warnings; `check --final` makes them errors."] if errors else [])
    token_files = [path for path in files if (path.name == "tokens.json" or path.name.endswith(".tokens.json")) and "styles" not in path.parts]
    for path in token_files:
        report = design_tokens.check_tokens(path)
        failures = ["%s on %s [%s]: %.2f:1 < %s" % (item["fg"], item["bg"], item["mode"], item["ratio"] or 0, item["min"]) for item in report["contrast"] if item["status"] != "pass"]  # type: ignore[union-attr]
        warnings = list(report["warnings"])  # type: ignore[arg-type]
        stale = stale_css(path)
        if stale:
            warnings.append(stale)
        notes = ["%d tokens, %d contrast checks across %s" % (report["tokens"], len(report["contrast"]), ", ".join(report["modes"]))]  # type: ignore[arg-type]
        result.add("tokens", label(path), list(report["errors"]) + failures, warnings, notes)  # type: ignore[arg-type]

    projects = sorted({path.parent for path in by_name.get("pfui.json", []) + by_name.get("design-review.json", [])}, key=lambda item: len(item.parts))
    lint_targets: List[Tuple[Path, List[str]]] = []
    if not projects:
        lint_targets.append((root, []))
    else:
        for project in projects:
            nested = [other.resolve().relative_to(project.resolve()).as_posix() + "/**" for other in projects if other != project and project.resolve() in other.resolve().parents]
            lint_targets.append((project, nested))
        covered = [project.resolve() for project in projects]
        loose = [path for path in files if path.suffix.lower() in {".html", ".htm", ".css"} and not any(base == path.resolve().parent or base in path.resolve().parents for base in covered)]
        if loose:
            lint_targets.append((root, [project.resolve().relative_to(root.resolve()).as_posix() + "/**" for project in projects if project.resolve() != root.resolve()]))
    lint_summary = {"error": 0, "warn": 0, "info": 0}
    lint_findings: List[Dict[str, object]] = []
    for target, nested in lint_targets:
        config = design_lint.Config()
        design_lint.load_config(target / "pfui.json" if (target / "pfui.json").is_file() else None, config)
        if platform:
            config.platform = platform
        if medium:
            config.medium = medium
        config.strict = strict
        config.ignore.extend(nested)
        report = design_lint.lint_paths([target], config, root=target)
        prefix = label(target)
        for item in report["findings"]:  # type: ignore[union-attr]
            item = dict(item)
            item["file"] = item["file"] if prefix in {"", "."} else "%s/%s" % (prefix, item["file"])
            lint_findings.append(item)
        for key in lint_summary:
            lint_summary[key] += report["summary"][key]  # type: ignore[index]

    errors = sum(len(section["errors"]) for section in result.sections) + lint_summary["error"]  # type: ignore[arg-type]
    warnings = sum(len(section["warnings"]) for section in result.sections) + lint_summary["warn"]  # type: ignore[arg-type]
    if strict:
        errors += warnings - lint_summary["warn"]
    return {
        "schemaVersion": 1,
        "root": str(root.resolve()),
        "final": final,
        "sections": result.sections,
        "lint": {"summary": lint_summary, "findings": lint_findings},
        "summary": {"errors": errors, "warnings": warnings},
        "passed": errors == 0,
        "notVerified": [
            "Rendered appearance, hierarchy, clipping and responsive behavior (inspect in a browser).",
            "Interaction, keyboard order and screen-reader output (exercise the flow).",
            "Truth, necessity and approval of copy (content contract review).",
            "Export fidelity of PDF/PPTX/images (inspect the exported files).",
        ],
    }


def print_check(report: Dict[str, object]) -> None:
    print("Checking %s%s" % (report["root"], " (final sign-off)" if report["final"] else ""))
    for section in report["sections"]:  # type: ignore[union-attr]
        status = "FAIL" if section["errors"] else ("WARN" if section["warnings"] else "ok")
        print("%-4s %-8s %s" % (status, section["kind"], section["target"]))
        for message in section["errors"]:
            print("       error: %s" % message)
        for message in section["warnings"][:12]:
            print("       warn:  %s" % message)
        if len(section["warnings"]) > 12:
            print("       ... %d more warnings" % (len(section["warnings"]) - 12))
        for message in section["notes"]:
            print("       note:  %s" % message)
    lint = report["lint"]
    for item in lint["findings"]:  # type: ignore[index]
        if item["severity"] != "info":
            print("%s:%s  %-5s %-18s %s" % (item["file"], item["line"], item["severity"], item["rule"], item["message"]))
    summary = lint["summary"]  # type: ignore[index]
    print("lint: %d error(s), %d warning(s), %d info" % (summary["error"], summary["warn"], summary["info"]))
    total = report["summary"]
    print("%s: %d error(s), %d warning(s)." % ("Check passed" if report["passed"] else "Check failed", total["errors"], total["warnings"]))  # type: ignore[index]
    print("Not verified by static checks:")
    for item in report["notVerified"]:  # type: ignore[union-attr]
        print("  - %s" % item)


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.path or default_root())
    if not root.exists():
        print("ERROR: path not found: %s" % root, file=sys.stderr)
        return 2
    report = run_check(root, args.final, args.strict, args.platform, args.medium)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print_check(report)
    return 0 if report["passed"] else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    report = doctor_report(Path(args.path or "."))
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print_doctor(report)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.path or default_root())
    if not root.exists():
        print("ERROR: path not found: %s" % root, file=sys.stderr)
        return 2
    report = status_report(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print_status(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfui.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version="prototype-first-ui %s" % skill_version())
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Report environment and project capabilities")
    doctor.add_argument("path", nargs="?", help="Project root (default .)")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    status = sub.add_parser("status", help="List design deliverables and next steps")
    status.add_argument("path", nargs="?", help="Root to scan (default designs/ or .)")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    init = sub.add_parser("init", help="Scaffold a deliverable")
    init.add_argument("kind", choices=KINDS)
    init.add_argument("--name", help="Real product or brand name; it appears in titles and brand areas (never a task label)")
    init.add_argument("--slug", help="Folder/id slug (default from --name)")
    init.add_argument("--dest", help="Target folder (default designs/<slug>)")
    init.add_argument("--platform", choices=design_lint.PLATFORMS, default="web", help="Target platform: control sizes, touch targets, shell layout and lint thresholds")
    init.add_argument("--lang", default="en", help="BCP 47 language tag for <html lang>")
    init.add_argument("--page", choices=sorted(PAGE_SIZES), default="A4", help="Paper size for doc")
    init.add_argument("--system", help="Design system folder to copy styles from (default designs/system, else the starter)")
    init.add_argument("--product", action="store_true", help="Also create ui-contract.json for the product UI gate")
    init.add_argument("--profile", choices=["operational-strict", "marketing-approved", "content-approved", "mixed-approved"], help="Content profile for --product (default: operational-strict for app, marketing-approved for site)")
    init.add_argument("--force", action="store_true", help="Allow a non-empty folder; existing files are never overwritten")
    init.set_defaults(func=cmd_init)

    serve = sub.add_parser("serve", help="Preview on 127.0.0.1 with the review harness")
    serve.add_argument("path", nargs="?", help="Folder to serve (default designs/ or .)")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--verbose", action="store_true")
    serve.set_defaults(func=cmd_serve)

    check = sub.add_parser("check", help="Run all applicable static checks")
    check.add_argument("path", nargs="?", help="Root to check (default designs/ or .)")
    check.add_argument("--final", action="store_true", help="Sign-off mode: approved-phase contracts, rendered content inventory")
    check.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    check.add_argument("--platform", choices=design_lint.PLATFORMS)
    check.add_argument("--medium", choices=design_lint.MEDIA)
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check)

    for name, module in PASSTHROUGH.items():
        sub.add_parser(name, help="Pass-through to %s.py" % module, add_help=False)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    safe_output()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in PASSTHROUGH:
        module = __import__(PASSTHROUGH[arguments[0]])
        return int(module.main(arguments[1:]))
    args = build_parser().parse_args(arguments)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
