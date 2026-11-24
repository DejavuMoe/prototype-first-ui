#!/usr/bin/env python3
"""Static design-quality lint for HTML/CSS prototypes, pages and design systems.

Checks constraints a machine can verify without rendering: accessible names and
labels, focus styles, zoom, contrast of resolvable color pairs, motion
preferences, target sizes, token discipline (raw colors, type/radius/shadow/z
scales), unresolved placeholders, broken or remote assets, and medium-specific
rules for email. Standard library only.

A clean lint is a floor, not a verdict. It does not render the page, so it
cannot judge hierarchy, layout, clipping, real focus order, image contrast or
whether copy is truthful and necessary. Configure with ``pfui.json``:

    {"platform": "web", "medium": "ui",
     "lint": {"disable": ["emoji-icon"], "severity": {"raw-color": "error"},
              "ignore": ["vendor/**"]}}
"""

from __future__ import annotations

import argparse
import bisect
from collections import Counter
import fnmatch
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_tokens import NAMED_COLORS, composite, contrast_ratio, parse_css_color  # noqa: E402

SEVERITIES = ("error", "warn", "info")
MEDIA = ("ui", "site", "deck", "doc", "email")
PLATFORMS = ("web", "desktop", "ios", "android")
TARGET_MIN = {"web": 24, "desktop": 24, "ios": 44, "android": 48}

RULES: Dict[str, Tuple[str, str]] = {
    # HTML structure and accessibility
    "html-lang": ("error", "Set lang on <html> so assistive tech and hyphenation use the right language."),
    "doc-title": ("warn", "Give every page a specific <title>."),
    "viewport-zoom": ("error", "Do not disable zoom (user-scalable=no or maximum-scale < 2)."),
    "viewport-missing": ("warn", "Add <meta name=viewport content='width=device-width, initial-scale=1'>."),
    "img-alt": ("error", "Every <img> needs alt; use alt='' for decoration."),
    "control-name": ("error", "Buttons, links and widget roles need an accessible name."),
    "field-label": ("error", "Form fields need a <label>, aria-label or aria-labelledby; placeholder is not a label."),
    "duplicate-id": ("error", "Element ids must be unique."),
    "aria-reference": ("error", "for / aria-labelledby / aria-describedby must reference existing ids."),
    "heading-skip": ("warn", "Do not skip heading levels."),
    "positive-tabindex": ("warn", "Positive tabindex breaks the natural focus order."),
    "static-click": ("warn", "Click handlers belong on buttons or links, not static elements."),
    "autoplay-media": ("warn", "Autoplaying media must be muted and pausable."),
    "table-header": ("warn", "Data tables need <th> headers (role=presentation for layout tables)."),
    "remote-asset": ("warn", "Remote assets cannot be frozen for review, break offline and leak requests; copy locally with provenance."),
    "missing-asset": ("error", "Referenced local file does not exist."),
    "placeholder-text": ("error", "Unresolved placeholder ({{...}}, TODO, lorem ipsum) in the deliverable."),
    "filler-copy": ("warn", "Generic filler names/copy; use sanitized, domain-realistic fixtures or approved copy."),
    "ambiguous-link": ("warn", "Link text such as 'click here' or 'learn more' does not say where it goes."),
    "emoji-icon": ("info", "Emoji used as interface icons look generic and render inconsistently; use one icon set."),
    "inline-style": ("info", "Many inline style attributes; move repeated styling into classes or tokens."),
    "missing-main": ("info", "Mark the primary content with <main>."),
    # CSS quality and accessibility
    "outline-removed": ("error", "Focus outline removed without a visible :focus-visible replacement."),
    "no-focus-style": ("info", "No :focus-visible styles; check the default ring is visible on your colors."),
    "reduced-motion": ("warn", "Motion without a prefers-reduced-motion alternative."),
    "transition-all": ("info", "transition: all animates layout properties and causes jank; list properties."),
    "important-overuse": ("warn", "Many !important declarations; fix specificity or use cascade layers."),
    "font-size-scale": ("warn", "Too many distinct font sizes; use a type scale."),
    "font-size-min": ("warn", "Text smaller than the medium's legible minimum."),
    "font-family-count": ("warn", "More than three type families."),
    "raw-color": ("warn", "Literal colors bypass the token system; use semantic color tokens."),
    "z-index-scale": ("warn", "Unbounded z-index values; use a small layer scale."),
    "radius-scale": ("info", "Many distinct corner radii; use the radius scale."),
    "shadow-scale": ("info", "Many distinct shadows; use the elevation scale."),
    "spacing-grid": ("info", "Odd pixel spacing values fall off the 4px grid."),
    "low-contrast": ("warn", "Resolvable text/background pair is below WCAG 2 contrast minimums."),
    "touch-target": ("warn", "Interactive control is smaller than the platform's minimum target."),
    "hover-only": ("info", "Content revealed on :hover needs a :focus-visible/:focus-within equivalent."),
    "gradient-text": ("info", "Gradient-clipped text is a common generic flourish; confirm it is a deliberate brand choice and readable."),
    "font-size-px": ("info", "Most font sizes use px; rem respects the reader's font-size setting."),
    "color-scheme": ("info", "Dark theme without color-scheme; native controls and scrollbars stay light."),
    # Email medium
    "email-script": ("error", "Email clients strip scripts."),
    "email-external-css": ("warn", "Many email clients ignore linked stylesheets; inline critical CSS."),
    "email-layout": ("warn", "Flexbox/grid are unreliable in email clients; use tables for structure."),
    "email-position": ("warn", "Positioned elements break in many email clients."),
    "email-width": ("warn", "Fixed widths above 640px overflow common email panes."),
}
EMAIL_DISABLED = {"remote-asset", "reduced-motion", "missing-main", "no-focus-style", "raw-color", "font-size-px", "inline-style"}
EMAIL_ONLY = {rule for rule in RULES if rule.startswith("email-")}

IGNORED_DIRS = {".git", "node_modules", "dist", "build", "coverage", "__pycache__", ".cache", "screenshots", "exports"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
WIDGET_ROLES = {"button", "link", "tab", "menuitem", "menuitemcheckbox", "menuitemradio", "switch", "checkbox", "radio", "option", "treeitem"}
ASSET_ATTRS = {
    "link": ("href",),
    "script": ("src",),
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
    "track": ("src",),
    "iframe": ("src",),
    "embed": ("src",),
    "object": ("data",),
}
PLACEHOLDER = re.compile(r"\{\{[^{}]{1,80}\}\}|\[\[[^\[\]]{1,80}\]\]|\b(?:TODO|TBD|FIXME|XXX)\b|lorem ipsum|dolor sit amet", re.IGNORECASE)
SLOT = re.compile(r"\{\{[^{}\s]{1,80}\}\}")
FILLER = re.compile(
    r"\b(?:john|jane) (?:doe|smith)\b|\bacme(?: (?:corp|inc|co))?\b|\bfoo ?bar\b|\byour (?:text|title|headline|company) here\b|"
    r"\bsample (?:text|title)\b|\bplaceholder (?:text|copy)\b|\btest user\b|\b(?:company|product) name\b|张三|李四|示例文本|此处填写",
    re.IGNORECASE,
)
AMBIGUOUS_LINKS = {"click here", "here", "more", "read more", "learn more", "this link", "link", "details", "点击这里", "这里", "更多", "了解更多", "查看更多", "点此"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF]")
COLOR_FUNCTION = re.compile(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\(", re.IGNORECASE)
HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
COLOR_PROPERTIES = re.compile(
    r"^(?:color|background(?:-color|-image)?|border(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?(?:-color)?|"
    r"outline(?:-color)?|fill|stroke|text-decoration(?:-color)?|caret-color|accent-color|column-rule(?:-color)?|box-shadow|text-shadow)$"
)
INTERACTIVE_SELECTOR = re.compile(r"(?:^|[\s>+~,(])(?:button|\[role=\"?button\"?\])|\.(?:btn|button|icon-button|chip|tab|close)\b", re.IGNORECASE)
MOTION_TRANSITION = re.compile(r"\b(?:all|transform|translate|scale|rotate|top|left|right|bottom|margin|width|height|inset)\b")


class Finding:
    __slots__ = ("rule", "severity", "file", "line", "message")

    def __init__(self, rule: str, severity: str, file: str, line: int, message: str) -> None:
        self.rule = rule
        self.severity = severity
        self.file = file
        self.line = line
        self.message = message

    def as_dict(self) -> Dict[str, object]:
        return {"rule": self.rule, "severity": self.severity, "file": self.file, "line": self.line, "message": self.message, "hint": RULES[self.rule][1]}


class Config:
    def __init__(self) -> None:
        self.platform = "web"
        self.medium = "ui"
        self.disabled: Set[str] = set()
        self.severity: Dict[str, str] = {}
        self.ignore: List[str] = []
        self.strict = False
        self.source: Optional[str] = None


# --------------------------------------------------------------------------
# HTML model.
# --------------------------------------------------------------------------


class Node:
    __slots__ = ("tag", "attrs", "parent", "children", "line")

    def __init__(self, tag: str, attrs: Dict[str, str], parent: Optional["Node"], line: int) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List[object] = []
        self.line = line

    def ancestors(self) -> Iterable["Node"]:
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def elements(self) -> Iterable["Node"]:
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.elements()


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None, 1)
        self.stack: List[Node] = [self.root]
        self.styles: List[Tuple[str, int]] = []
        self.inline_styles: List[Tuple[str, int]] = []
        self.comments: List[Tuple[str, int]] = []
        self.scripts = 0
        self._raw_tag: Optional[str] = None
        self._raw_line = 0
        self._raw: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        values = {name.lower(): (value if value is not None else "") for name, value in attrs}
        line = self.getpos()[0]
        node = Node(tag, values, self.stack[-1], line)
        self.stack[-1].children.append(node)
        if "style" in values and values["style"].strip():
            self.inline_styles.append((values["style"], line))
        if tag in {"style", "script"}:
            self._raw_tag, self._raw_line, self._raw = tag, line, []
            if tag == "script":
                self.scripts += 1
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID and self.stack[-1].tag == tag.lower():
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._raw_tag == tag:
            if tag == "style":
                self.styles.append(("".join(self._raw), self._raw_line))
            self._raw_tag = None
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self._raw_tag:
            self._raw.append(data)
            return
        self.stack[-1].children.append(data)

    def handle_comment(self, data: str) -> None:
        self.comments.append((data, self.getpos()[0]))


def is_hidden(node: Node) -> bool:
    return "hidden" in node.attrs or node.attrs.get("aria-hidden") == "true"


def text_content(node: Node, *, accessible: bool = True) -> str:
    parts: List[str] = []

    def visit(current: Node) -> None:
        for child in current.children:
            if isinstance(child, Node):
                if accessible and is_hidden(child):
                    continue
                if child.tag in {"script", "style", "template"}:
                    continue
                if child.tag == "img" and child.attrs.get("alt"):
                    parts.append(child.attrs["alt"])
                elif child.tag == "title" and current.tag == "svg":
                    parts.append(" ".join(text for text in child.children if isinstance(text, str)))
                else:
                    visit(child)
            else:
                parts.append(child)

    visit(node)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def accessible_name(node: Node, by_id: Dict[str, Node], labels: Optional[Dict[str, Node]] = None) -> str:
    labelled = node.attrs.get("aria-labelledby", "").split()
    if labelled:
        names = [text_content(by_id[item]) for item in labelled if item in by_id]
        if any(names):
            return " ".join(names)
    if node.attrs.get("aria-label", "").strip():
        return node.attrs["aria-label"].strip()
    if node.tag in {"input", "select", "textarea"}:
        wrapping = next((ancestor for ancestor in node.ancestors() if ancestor.tag == "label"), None)
        explicit = (labels or {}).get(node.attrs.get("id", ""))
        for label in (explicit, wrapping):
            if label is not None and text_content(label):
                return text_content(label)
    if node.tag == "input":
        kind = node.attrs.get("type", "text").lower()
        if kind in {"submit", "reset"}:
            return node.attrs.get("value", kind)
        if kind == "button":
            return node.attrs.get("value", "")
        if kind == "image":
            return node.attrs.get("alt", "")
    text = text_content(node)
    if text:
        return text
    return node.attrs.get("title", "").strip()


class HtmlDocument:
    def __init__(self, path: Path, text: str) -> None:
        self.path = path
        self.text = text
        builder = TreeBuilder()
        builder.feed(text)
        builder.close()
        self.root = builder.root
        self.styles = builder.styles
        self.inline_styles = builder.inline_styles
        self.comments = builder.comments
        self.scripts = builder.scripts
        self.elements = list(self.root.elements())
        self.by_id: Dict[str, Node] = {}
        for element in self.elements:
            if "id" in element.attrs and element.attrs["id"] not in self.by_id:
                self.by_id[element.attrs["id"]] = element


# --------------------------------------------------------------------------
# CSS model.
# --------------------------------------------------------------------------


class Declaration:
    __slots__ = ("prop", "value", "important", "line", "selector", "media", "file")

    def __init__(self, prop: str, value: str, important: bool, line: int, selector: str, media: Tuple[str, ...], file: str) -> None:
        self.prop = prop
        self.value = value
        self.important = important
        self.line = line
        self.selector = selector
        self.media = media
        self.file = file


class Rule:
    __slots__ = ("selector", "media", "decls", "line", "file")

    def __init__(self, selector: str, media: Tuple[str, ...], line: int, file: str) -> None:
        self.selector = selector
        self.media = media
        self.decls: List[Declaration] = []
        self.line = line
        self.file = file


class Stylesheet:
    def __init__(self, file: str, text: str, line_offset: int = 0) -> None:
        self.file = file
        self.rules: List[Rule] = []
        self.keyframes = 0
        self.imports: List[Tuple[str, int]] = []
        self.urls: List[Tuple[str, int]] = []
        self.media_preludes: List[str] = []
        cleaned = re.sub(r"/\*.*?\*/", lambda match: re.sub(r"[^\n]", " ", match.group(0)), text, flags=re.DOTALL)
        self._newlines = [index for index, character in enumerate(cleaned) if character == "\n"]
        self._offset = line_offset
        self._text = cleaned
        for match in re.finditer(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", cleaned):
            self.urls.append((match.group(2).strip(), self.line_at(match.start())))
        self._parse(0, len(cleaned), ())

    def line_at(self, offset: int) -> int:
        return bisect.bisect_left(self._newlines, offset) + 1 + self._offset

    def _find(self, start: int, end: int, targets: str) -> int:
        depth = 0
        quote = ""
        index = start
        text = self._text
        while index < end:
            character = text[index]
            if quote:
                if character == "\\":
                    index += 2
                    continue
                if character == quote:
                    quote = ""
            elif character in "'\"":
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth = max(0, depth - 1)
            elif depth == 0 and character in targets:
                return index
            index += 1
        return -1

    def _matching(self, open_index: int, end: int) -> int:
        depth = 0
        quote = ""
        index = open_index
        text = self._text
        while index < end:
            character = text[index]
            if quote:
                if character == "\\":
                    index += 2
                    continue
                if character == quote:
                    quote = ""
            elif character in "'\"":
                quote = character
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return index
            index += 1
        return end

    def _parse(self, start: int, end: int, media: Tuple[str, ...], parent_selector: str = "") -> None:
        position = start
        text = self._text
        while position < end:
            while position < end and text[position] in " \t\r\n;":
                position += 1
            if position >= end:
                break
            stop = self._find(position, end, "{;}")
            if stop == -1:
                break
            if text[stop] == "}":
                position = stop + 1
                continue
            prelude = text[position:stop].strip()
            if text[stop] == ";":
                if prelude.lower().startswith("@import"):
                    self.imports.append((prelude, self.line_at(position)))
                elif parent_selector and ":" in prelude:
                    self._declaration(prelude, position, parent_selector, media)
                position = stop + 1
                continue
            close = self._matching(stop, end)
            body_start, body_end = stop + 1, close
            lowered = prelude.lower()
            if lowered.startswith("@"):
                name = lowered.split(None, 1)[0]
                if name in {"@media", "@supports", "@layer", "@container", "@scope", "@document", "@starting-style"}:
                    if name == "@media":
                        self.media_preludes.append(lowered)
                    self._parse(body_start, body_end, media + (lowered,), parent_selector)
                elif name.endswith("keyframes"):
                    self.keyframes += 1
                elif name in {"@page", "@font-face"}:
                    self._rule(name, body_start, body_end, media, position)
            else:
                selector = prelude if not parent_selector else self._nest(parent_selector, prelude)
                self._rule(selector, body_start, body_end, media, position)
            position = close + 1

    @staticmethod
    def _nest(parent: str, child: str) -> str:
        if "&" in child:
            return child.replace("&", parent)
        return "%s %s" % (parent, child)

    def _rule(self, selector: str, start: int, end: int, media: Tuple[str, ...], position: int) -> None:
        rule = Rule(re.sub(r"\s+", " ", selector), media, self.line_at(position), self.file)
        self.rules.append(rule)
        cursor = start
        text = self._text
        while cursor < end:
            stop = self._find(cursor, end, ";{")
            if stop == -1:
                segment_end = end
            else:
                segment_end = stop
            if stop != -1 and text[stop] == "{":
                nested_close = self._matching(stop, end)
                nested_prelude = text[cursor:stop].strip()
                if nested_prelude.startswith("@"):
                    self._parse(stop + 1, nested_close, media + (nested_prelude.lower(),), rule.selector)
                elif nested_prelude:
                    self._rule(self._nest(rule.selector, nested_prelude), stop + 1, nested_close, media, cursor)
                cursor = nested_close + 1
                continue
            segment = text[cursor:segment_end]
            if segment.strip():
                declaration = self._declaration(segment, cursor, rule.selector, media)
                if declaration is not None:
                    rule.decls.append(declaration)
            if stop == -1:
                break
            cursor = stop + 1

    def _declaration(self, segment: str, position: int, selector: str, media: Tuple[str, ...]) -> Optional[Declaration]:
        if ":" not in segment:
            return None
        prop, value = segment.split(":", 1)
        prop = prop.strip().lower() if not prop.strip().startswith("--") else prop.strip()
        value = value.strip()
        important = bool(re.search(r"!\s*important\s*$", value, re.IGNORECASE))
        if important:
            value = re.sub(r"!\s*important\s*$", "", value, flags=re.IGNORECASE).strip()
        offset = position + len(segment) - len(segment.lstrip())
        return Declaration(prop, value, important, self.line_at(offset), selector, media, self.file)

    def declarations(self) -> Iterable[Declaration]:
        for rule in self.rules:
            yield from rule.decls


def strip_functions(value: str) -> str:
    value = re.sub(r"url\([^)]*\)", " ", value, flags=re.IGNORECASE)
    return re.sub(r"(['\"]).*?\1", " ", value)


def literal_colors(value: str) -> List[str]:
    cleaned = strip_functions(value)
    found = HEX_COLOR.findall(cleaned)
    found += [match.group(0) for match in COLOR_FUNCTION.finditer(cleaned) if not match.group(0).lower().startswith("color-mix")]
    in_mix = "color-mix(" in cleaned.lower()
    without_vars = re.sub(r"var\([^)]*\)", " ", cleaned)
    for word in re.findall(r"(?<![-\w#])([a-zA-Z]+)(?![-\w(])", without_vars):
        lowered = word.lower()
        if lowered in NAMED_COLORS and not (in_mix and lowered in {"black", "white"}):
            found.append(word)
    return found


def to_px(value: str) -> Optional[float]:
    match = re.fullmatch(r"\s*(-?\d*\.?\d+)\s*(px|rem|em|pt)?\s*", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2) or ("px" if number == 0 else None)
    if unit is None:
        return None
    return number * {"px": 1.0, "rem": 16.0, "em": 16.0, "pt": 4 / 3}[unit]


def root_like(selector: str) -> bool:
    return all(re.match(r"^(?::root|html|body)(?:[\[:.(]|$)", part.strip()) for part in selector.split(",") if part.strip())


def theme_of(selector: str, media: Sequence[str]) -> Optional[str]:
    text = selector.lower()
    if re.search(r"data-theme=['\"]?dark", text) or re.search(r"(?:^|[\s.])\.dark\b", text):
        return "dark"
    if any("prefers-color-scheme: dark" in prelude.replace("  ", " ") or "prefers-color-scheme:dark" in prelude for prelude in media):
        return "dark"
    if re.search(r"data-theme=['\"]?light", text):
        return "light"
    return None


# --------------------------------------------------------------------------
# Linting.
# --------------------------------------------------------------------------


class Linter:
    def __init__(self, root: Path, config: Config) -> None:
        self.root = root
        self.config = config
        self.findings: List[Finding] = []
        self.files: List[str] = []
        self._seen: Set[Tuple[str, str, int, str]] = set()

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    def active(self, rule: str) -> bool:
        if rule in self.config.disabled:
            return False
        if self.config.medium == "email":
            return rule not in EMAIL_DISABLED
        return rule not in EMAIL_ONLY

    def add(self, rule: str, file: str, line: int, message: str, severity: Optional[str] = None) -> None:
        if not self.active(rule):
            return
        key = (rule, file, line, message)
        if key in self._seen:
            return
        self._seen.add(key)
        level = self.config.severity.get(rule) or severity or RULES[rule][0]
        if self.config.strict and level == "warn":
            level = "error"
        self.findings.append(Finding(rule, level, file, line, message))

    # -- discovery ---------------------------------------------------------

    def collect(self, targets: Sequence[Path]) -> Tuple[List[Path], List[Path], List[Path]]:
        html: List[Path] = []
        css: List[Path] = []
        scripts: List[Path] = []
        for target in targets:
            candidates = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
            for path in candidates:
                relative = self.rel(path)
                if any(part in IGNORED_DIRS for part in Path(relative).parts):
                    continue
                if any(fnmatch.fnmatch(relative, pattern) for pattern in self.config.ignore):
                    continue
                suffix = path.suffix.lower()
                if suffix in {".html", ".htm"}:
                    html.append(path)
                elif suffix == ".css":
                    css.append(path)
                elif suffix in {".js", ".mjs"}:
                    scripts.append(path)
        return sorted(set(html)), sorted(set(css)), sorted(set(scripts))

    # -- entry -------------------------------------------------------------

    def run(self, targets: Sequence[Path]) -> None:
        html_paths, css_paths, script_paths = self.collect(targets)
        for path in script_paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), 1):
                match = SLOT.search(line)
                if match:
                    self.add("placeholder-text", self.rel(path), number, "Unresolved slot %r in script" % match.group(0))
        sheets: List[Stylesheet] = []
        documents: List[HtmlDocument] = []
        for path in css_paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            sheets.append(Stylesheet(self.rel(path), text))
            self.files.append(self.rel(path))
            for url, line in sheets[-1].urls:
                self.check_reference(url, path, self.rel(path), line, "url()")
            for prelude, line in sheets[-1].imports:
                match = re.search(r"(?:url\()?\s*['\"]?([^'\")\s;]+)", prelude[len("@import"):])
                if match:
                    self.check_reference(match.group(1), path, self.rel(path), line, "@import")
        for path in html_paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            document = HtmlDocument(path, text)
            documents.append(document)
            self.files.append(self.rel(path))
            for style, line in document.styles:
                sheets.append(Stylesheet(self.rel(path), style, line - 1))
            for style, line in document.inline_styles:
                sheets.append(Stylesheet(self.rel(path), "x{%s}" % style, line - 1))
            self.lint_html(document)
        self.lint_css(sheets, documents)

    # -- references --------------------------------------------------------

    def check_reference(self, raw: str, source: Path, label: str, line: int, context: str) -> None:
        value = raw.strip()
        if not value or value.startswith(("#", "data:", "blob:", "mailto:", "tel:", "javascript:", "about:")):
            return
        if re.match(r"^(?:https?:)?//", value, re.IGNORECASE):
            self.add("remote-asset", label, line, "%s references remote %s" % (context, value[:120]))
            return
        if re.match(r"^[a-z][a-z0-9+.-]*:", value, re.IGNORECASE):
            return
        clean = unquote(value.split("#", 1)[0].split("?", 1)[0])
        if not clean or "{{" in clean or "${" in clean:
            return
        if clean.startswith("/"):
            candidate = self.root / clean.lstrip("/")
            if not candidate.exists():
                self.add("missing-asset", label, line, "%s %s not found under the lint root (root-relative path)" % (context, value), "warn")
            return
        if not (source.parent / clean).exists():
            self.add("missing-asset", label, line, "%s %s does not exist" % (context, value))

    # -- HTML --------------------------------------------------------------

    def lint_html(self, document: HtmlDocument) -> None:
        label = self.rel(document.path)
        elements = document.elements
        html = next((element for element in elements if element.tag == "html"), None)
        is_page = html is not None or any(element.tag == "body" for element in elements)
        if is_page:
            if html is None or not html.attrs.get("lang", "").strip():
                self.add("html-lang", label, html.line if html else 1, "<html> has no lang attribute")
            title = next((element for element in elements if element.tag == "title"), None)
            if title is None or not text_content(title, accessible=False):
                self.add("doc-title", label, title.line if title else 1, "Missing or empty <title>")
            viewport = next((element for element in elements if element.tag == "meta" and element.attrs.get("name", "").lower() == "viewport"), None)
            if viewport is None:
                self.add("viewport-missing", label, 1, "No viewport meta tag")
            else:
                content = viewport.attrs.get("content", "").lower().replace(" ", "")
                scale = re.search(r"maximum-scale=([\d.]+)", content)
                if "user-scalable=no" in content or "user-scalable=0" in content or (scale and float(scale.group(1)) < 2):
                    self.add("viewport-zoom", label, viewport.line, "Viewport blocks pinch zoom: %s" % viewport.attrs.get("content"))
            if not any(element.tag == "main" or element.attrs.get("role") == "main" for element in elements):
                self.add("missing-main", label, 1, "No <main> landmark")

        counts = Counter(element.attrs["id"] for element in elements if element.attrs.get("id"))
        reported: Set[str] = set()
        for element in elements:
            element_id = element.attrs.get("id")
            if element_id and counts[element_id] > 1 and element_id not in reported:
                reported.add(element_id)
                self.add("duplicate-id", label, element.line, "id %r is used %d times" % (element_id, counts[element_id]))

        label_for = {element.attrs["for"]: element for element in elements if element.tag == "label" and element.attrs.get("for")}
        labelled_ids = set(label_for)
        previous_heading = 0
        emoji_hits = 0
        for element in elements:
            attrs = element.attrs
            tag = element.tag
            role = attrs.get("role", "").lower()
            for attribute in ("aria-labelledby", "aria-describedby", "aria-errormessage", "aria-controls", "aria-owns", "aria-activedescendant", "for"):
                if attribute == "for" and tag not in {"label", "output"}:
                    continue
                for reference in attrs.get(attribute, "").split():
                    if reference not in document.by_id:
                        severity = "warn" if attribute in {"aria-controls", "aria-owns", "aria-activedescendant"} else None
                        self.add("aria-reference", label, element.line, "%s references missing id %r" % (attribute, reference), severity)
            if tag == "img" and "alt" not in attrs:
                self.add("img-alt", label, element.line, "<img src=%r> has no alt" % attrs.get("src", "")[:80])
            interactive = tag == "button" or (tag == "a" and "href" in attrs) or role in WIDGET_ROLES or (tag == "input" and attrs.get("type", "").lower() in {"button", "submit", "reset", "image"})
            if interactive and not is_hidden(element):
                name = accessible_name(element, document.by_id, label_for)
                if not name:
                    self.add("control-name", label, element.line, "<%s%s> has no accessible name" % (tag, (" role=%s" % role) if role else ""))
                elif tag == "a" and name.strip().lower().rstrip(".…") in AMBIGUOUS_LINKS:
                    self.add("ambiguous-link", label, element.line, "Link text %r does not describe its destination" % name)
            field = (tag == "input" and attrs.get("type", "text").lower() not in {"hidden", "submit", "button", "reset", "image"}) or tag in {"select", "textarea"}
            if field and not is_hidden(element):
                has_label = bool(attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip() or attrs.get("title", "").strip())
                has_label = has_label or (attrs.get("id") in labelled_ids) or any(ancestor.tag == "label" for ancestor in element.ancestors())
                if not has_label:
                    hint = " (placeholder is not a label)" if attrs.get("placeholder") else ""
                    self.add("field-label", label, element.line, "<%s> has no label%s" % (tag, hint))
            match = re.fullmatch(r"h([1-6])", tag)
            if match:
                level = int(match.group(1))
                if previous_heading and level > previous_heading + 1:
                    self.add("heading-skip", label, element.line, "<%s> follows <h%d>" % (tag, previous_heading))
                previous_heading = level
            tabindex = attrs.get("tabindex", "").strip()
            if re.fullmatch(r"[1-9]\d*", tabindex):
                self.add("positive-tabindex", label, element.line, "tabindex=%s" % tabindex)
            if "onclick" in attrs and tag not in {"button", "a", "input", "select", "summary", "label", "option"} and not (role in WIDGET_ROLES and "tabindex" in attrs):
                self.add("static-click", label, element.line, "<%s onclick> is not keyboard operable; use <button>" % tag)
            if tag in {"video", "audio"} and "autoplay" in attrs and "muted" not in attrs:
                self.add("autoplay-media", label, element.line, "<%s autoplay> without muted" % tag)
            if tag == "table" and role not in {"presentation", "none"}:
                cells = [child for child in element.elements() if child.tag in {"td", "th"}]
                if cells and not any(child.tag == "th" for child in cells):
                    self.add("table-header", label, element.line, "<table> has data cells but no <th>")
            for attribute in ASSET_ATTRS.get(tag, ()):
                value = attrs.get(attribute, "")
                if not value:
                    continue
                if tag == "link" and not re.search(r"stylesheet|icon|preload|manifest|modulepreload", attrs.get("rel", ""), re.IGNORECASE):
                    continue
                urls = [part.strip().split()[0] for part in value.split(",") if part.strip()] if attribute == "srcset" else [value]
                for url in urls:
                    self.check_reference(url, document.path, label, element.line, "<%s %s>" % (tag, attribute))
            if tag == "input" and attrs.get("type", "").lower() == "image" and attrs.get("src"):
                self.check_reference(attrs["src"], document.path, label, element.line, "<input src>")
            if tag in {"button", "a", "label", "th", "h1", "h2", "h3", "h4", "summary"} or role in WIDGET_ROLES or (tag == "li" and any(a.tag == "nav" for a in element.ancestors())):
                own = "".join(child for child in element.children if isinstance(child, str))
                if EMOJI.search(own):
                    emoji_hits += 1
                    if emoji_hits <= 5:
                        self.add("emoji-icon", label, element.line, "Emoji in <%s> text: %r" % (tag, own.strip()[:40]))
            if self.config.medium == "email" and tag == "link" and "stylesheet" in attrs.get("rel", "").lower():
                self.add("email-external-css", label, element.line, "Linked stylesheet in email")

        if self.config.medium == "email" and document.scripts:
            self.add("email-script", label, 1, "%d <script> element(s) in email HTML" % document.scripts)
        if len(document.inline_styles) > 12:
            self.add("inline-style", label, document.inline_styles[0][1], "%d inline style attributes" % len(document.inline_styles))
        self.scan_text(document, label)

    def scan_text(self, document: HtmlDocument, label: str) -> None:
        placeholder_lines: Set[int] = set()
        filler_lines: Set[int] = set()
        for element in document.elements:
            if element.tag in {"script", "style"}:
                continue
            own = " ".join(child for child in element.children if isinstance(child, str))
            values = [own] + [value for name, value in element.attrs.items() if name in {"alt", "title", "placeholder", "aria-label", "aria-description", "value", "content", "label"}]
            for value in values:
                if not value.strip():
                    continue
                match = PLACEHOLDER.search(value)
                if match and element.line not in placeholder_lines:
                    placeholder_lines.add(element.line)
                    self.add("placeholder-text", label, element.line, "Unresolved placeholder %r in <%s>" % (match.group(0), element.tag))
                filler = FILLER.search(value)
                if filler and element.line not in filler_lines:
                    filler_lines.add(element.line)
                    self.add("filler-copy", label, element.line, "Generic filler %r in <%s>" % (filler.group(0), element.tag))
        for comment, line in document.comments:
            match = PLACEHOLDER.search(comment)
            if match:
                self.add("placeholder-text", label, line, "Unresolved placeholder %r in an HTML comment" % match.group(0))

    # -- CSS ---------------------------------------------------------------

    def lint_css(self, sheets: Sequence[Stylesheet], documents: Sequence[HtmlDocument]) -> None:
        declarations = [declaration for sheet in sheets for declaration in sheet.declarations()]
        rules = [rule for sheet in sheets for rule in sheet.rules]
        if not declarations:
            return
        all_media = [prelude for sheet in sheets for prelude in sheet.media_preludes]
        has_reduced_motion = any("prefers-reduced-motion" in prelude for prelude in all_media)
        focus_visible_rules = [rule for rule in rules if ":focus-visible" in rule.selector or ":focus" in rule.selector]
        focus_replacement = any(
            ":focus-visible" in rule.selector and any(
                decl.prop in {"outline", "outline-style", "outline-color", "box-shadow", "border", "border-color"} and not re.fullmatch(r"none|0(?:px)?", decl.value.strip(), re.IGNORECASE)
                for decl in rule.decls
            )
            for rule in rules
        )
        token_files = {sheet.file for sheet in sheets if "token" in Path(sheet.file).name.lower()}
        for sheet in sheets:
            decls = list(sheet.declarations())
            if decls and sum(1 for decl in decls if decl.prop.startswith("--")) >= 0.9 * len(decls) and len(decls) >= 8:
                token_files.add(sheet.file)
        color_properties_defined = sum(1 for decl in declarations if decl.prop.startswith("--") and literal_colors(decl.value))
        has_tokens = color_properties_defined >= 8

        # Focus.
        for decl in declarations:
            if decl.prop in {"outline", "outline-style", "outline-width"} and re.fullmatch(r"none|0(?:px)?", decl.value.strip(), re.IGNORECASE):
                if ":focus-visible" in decl.selector:
                    replaced = False
                    for rule in rules:
                        if rule.selector == decl.selector and any(item.prop in {"box-shadow", "border", "border-color"} for item in rule.decls):
                            replaced = True
                    if not replaced:
                        self.add("outline-removed", decl.file, decl.line, "%s removes the focus-visible outline" % decl.selector)
                elif not focus_replacement:
                    self.add("outline-removed", decl.file, decl.line, "%s sets outline:%s and no :focus-visible style replaces it" % (decl.selector, decl.value))
        interactive_html = any(element.tag in {"button", "a", "input", "select", "textarea"} for document in documents for element in document.elements)
        if interactive_html and not focus_visible_rules:
            self.add("no-focus-style", sheets[0].file, 1, "No :focus or :focus-visible rules in the stylesheets")

        # Motion.
        motion = [
            decl for decl in declarations
            if (decl.prop in {"animation", "animation-name"} and decl.value.strip().lower() not in {"none", "unset", "initial", "inherit"})
            or (decl.prop in {"transition", "transition-property"} and MOTION_TRANSITION.search(decl.value.lower()))
        ]
        if (motion or any(sheet.keyframes for sheet in sheets)) and not has_reduced_motion:
            first = motion[0] if motion else None
            self.add("reduced-motion", first.file if first else sheets[0].file, first.line if first else 1, "Animations/transitions found but no @media (prefers-reduced-motion) block")
        for decl in declarations:
            if decl.prop in {"transition", "transition-property"} and re.search(r"(?:^|[\s,])all(?:[\s,]|$)", decl.value.lower()):
                self.add("transition-all", decl.file, decl.line, "%s { %s: %s }" % (decl.selector, decl.prop, decl.value))

        important = [
            decl for decl in declarations
            if decl.important and not any("prefers-reduced-motion" in prelude or "forced-colors" in prelude for prelude in decl.media) and "[hidden]" not in decl.selector
        ]
        if len(important) > 8:
            self.add("important-overuse", important[0].file, important[0].line, "%d !important declarations" % len(important))

        # Type.
        sizes: Dict[float, Declaration] = {}
        px_sizes = 0
        literal_sizes = 0
        minimum = {"deck": 24.0, "doc": 10.0}.get(self.config.medium, 12.0)
        for decl in declarations:
            if decl.prop != "font-size" or decl.file in token_files or "var(" in decl.value or "calc(" in decl.value:
                continue
            if re.search(r"(?:em|%)\s*$", decl.value.strip()) and not decl.value.strip().endswith("rem"):
                continue
            px = to_px(decl.value)
            if px is None:
                continue
            literal_sizes += 1
            if decl.value.strip().lower().endswith("px"):
                px_sizes += 1
            sizes.setdefault(round(px, 2), decl)
            if 0 < px < minimum and not any("print" in prelude for prelude in decl.media):
                self.add("font-size-min", decl.file, decl.line, "font-size %s (%.1fpx) is below %gpx for %s" % (decl.value, px, minimum, self.config.medium))
        if len(sizes) > 10:
            first = min(sizes.values(), key=lambda decl: decl.line)
            self.add("font-size-scale", first.file, first.line, "%d distinct font sizes: %s" % (len(sizes), ", ".join("%gpx" % size for size in sorted(sizes))))
        if literal_sizes >= 5 and px_sizes / literal_sizes > 0.6:
            self.add("font-size-px", sheets[0].file, 1, "%d of %d font sizes use px" % (px_sizes, literal_sizes))
        families: Dict[str, Declaration] = {}
        for decl in declarations:
            if decl.prop != "font-family" or "var(" in decl.value or decl.file in token_files:
                continue
            first_family = decl.value.split(",")[0].strip().strip("'\"").lower()
            if first_family and first_family not in {"inherit", "initial", "unset", "revert"}:
                families.setdefault(first_family, decl)
        if len(families) > 3:
            first = min(families.values(), key=lambda decl: decl.line)
            self.add("font-family-count", first.file, first.line, "%d primary families: %s" % (len(families), ", ".join(sorted(families))))

        # Token discipline.
        raw_by_file: Dict[str, List[Declaration]] = {}
        for decl in declarations:
            if decl.prop.startswith("--") or decl.file in token_files or not COLOR_PROPERTIES.match(decl.prop):
                continue
            if any("forced-colors" in prelude for prelude in decl.media):
                continue
            if literal_colors(decl.value):
                raw_by_file.setdefault(decl.file, []).append(decl)
        for file, items in raw_by_file.items():
            sample = ", ".join("%s:%d" % (item.prop, item.line) for item in items[:4])
            message = "%d literal color(s) outside tokens (%s%s)" % (len(items), sample, ", ..." if len(items) > 4 else "")
            self.add("raw-color", file, items[0].line, message, None if has_tokens else "info")

        z_values: Dict[int, Declaration] = {}
        for decl in declarations:
            if decl.prop == "z-index" and re.fullmatch(r"-?\d+", decl.value.strip()):
                value = int(decl.value)
                z_values.setdefault(value, decl)
                if value > 1000:
                    self.add("z-index-scale", decl.file, decl.line, "z-index %d; use the layer scale" % value)
        if len(z_values) > 8:
            first = min(z_values.values(), key=lambda decl: decl.line)
            self.add("z-index-scale", first.file, first.line, "%d distinct z-index values" % len(z_values))

        def distinct(prop_names: Set[str], skip: Set[str]) -> Dict[str, Declaration]:
            values: Dict[str, Declaration] = {}
            for decl in declarations:
                if decl.prop in prop_names and "var(" not in decl.value and decl.file not in token_files:
                    normalized = re.sub(r"\s+", " ", decl.value.strip().lower())
                    if normalized not in skip:
                        values.setdefault(normalized, decl)
            return values

        radii = distinct({"border-radius"}, {"0", "50%", "9999px", "999px", "inherit", "100%"})
        if len(radii) > 6:
            first = min(radii.values(), key=lambda decl: decl.line)
            self.add("radius-scale", first.file, first.line, "%d distinct radii: %s" % (len(radii), ", ".join(sorted(radii))))
        shadows = distinct({"box-shadow"}, {"none", "inherit"})
        if len(shadows) > 5:
            first = min(shadows.values(), key=lambda decl: decl.line)
            self.add("shadow-scale", first.file, first.line, "%d distinct box-shadows" % len(shadows))

        odd: List[Declaration] = []
        for decl in declarations:
            if re.match(r"^(?:margin|padding|gap|row-gap|column-gap|inset)(?:-|$)", decl.prop) and decl.file not in token_files:
                for number in re.findall(r"(?<![\w.-])(\d+)px", decl.value):
                    if int(number) > 1 and int(number) % 2 == 1:
                        odd.append(decl)
                        break
        if odd:
            self.add("spacing-grid", odd[0].file, odd[0].line, "%d declaration(s) use odd px spacing (first: %s { %s: %s })" % (len(odd), odd[0].selector, odd[0].prop, odd[0].value))

        # Contrast and targets.
        self.check_contrast(rules)
        threshold = TARGET_MIN[self.config.platform]
        for rule in rules:
            if not INTERACTIVE_SELECTOR.search(rule.selector) or "::" in rule.selector:
                continue
            values = {decl.prop: decl for decl in rule.decls}
            minimum_height = values.get("min-height")
            if minimum_height is not None and (to_px(minimum_height.value) or 0) >= threshold:
                continue
            for prop in ("height", "min-height"):
                decl = values.get(prop)
                if decl is not None:
                    px = to_px(decl.value)
                    if px is not None and 0 < px < threshold:
                        self.add("touch-target", decl.file, decl.line, "%s { %s: %s } is below %dpx for %s" % (rule.selector, prop, decl.value, threshold, self.config.platform))

        # Hover-only reveals.
        selectors = {rule.selector for rule in rules}
        for rule in rules:
            if ":hover" not in rule.selector:
                continue
            reveals = any(
                (decl.prop == "opacity" and decl.value.strip() in {"1", "1.0"})
                or (decl.prop == "visibility" and decl.value.strip() == "visible")
                for decl in rule.decls
            )
            if reveals:
                alternatives = {rule.selector.replace(":hover", pseudo) for pseudo in (":focus-visible", ":focus-within", ":focus")}
                if not any(alternative in selectors or alternative in rule.selector for alternative in alternatives) and ":focus" not in rule.selector:
                    self.add("hover-only", rule.file, rule.line, "%s reveals content only on hover" % rule.selector)

        for decl in declarations:
            if decl.prop in {"background-clip", "-webkit-background-clip"} and decl.value.strip().lower() == "text":
                self.add("gradient-text", decl.file, decl.line, "%s clips a background to text" % decl.selector)

        has_dark = any(theme_of(rule.selector, rule.media) == "dark" for rule in rules)
        if has_dark and not any(decl.prop == "color-scheme" for decl in declarations):
            self.add("color-scheme", sheets[0].file, 1, "Dark theme rules found but color-scheme is never set")

        if self.config.medium == "email":
            for decl in declarations:
                if decl.prop == "display" and decl.value.strip().lower() in {"flex", "inline-flex", "grid", "inline-grid"}:
                    self.add("email-layout", decl.file, decl.line, "display:%s in email CSS" % decl.value)
                if decl.prop == "position" and decl.value.strip().lower() in {"absolute", "fixed", "sticky"}:
                    self.add("email-position", decl.file, decl.line, "position:%s in email CSS" % decl.value)
                if decl.prop in {"width", "min-width"}:
                    px = to_px(decl.value)
                    if px is not None and px > 640:
                        self.add("email-width", decl.file, decl.line, "%s:%s exceeds 640px" % (decl.prop, decl.value))

    # -- contrast ----------------------------------------------------------

    def check_contrast(self, rules: Sequence[Rule]) -> None:
        base: Dict[str, str] = {}
        dark: Dict[str, str] = {}
        for rule in rules:
            if not root_like(rule.selector) or re.search(r"\[data-(?!theme)", rule.selector):
                continue
            theme = theme_of(rule.selector, rule.media)
            target = dark if theme == "dark" else base
            for decl in rule.decls:
                if decl.prop.startswith("--"):
                    target[decl.prop] = decl.value
        contexts = [("default", base)]
        if dark:
            merged = dict(base)
            merged.update(dark)
            contexts.append(("dark", merged))

        def resolve(value: str, local: Dict[str, str], props: Dict[str, str], depth: int = 0) -> Optional[str]:
            if depth > 12:
                return None
            match = re.search(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\))?[^()]*))?\)", value)
            if not match:
                return value
            name, fallback = match.group(1), match.group(2)
            replacement = local.get(name, props.get(name))
            if replacement is None:
                replacement = fallback
            if replacement is None:
                return None
            resolved = resolve(replacement.strip(), local, props, depth + 1)
            if resolved is None:
                return None
            return resolve(value[: match.start()] + resolved + value[match.end():], local, props, depth + 1)

        for rule in rules:
            if re.search(r":disabled|\[disabled\]|aria-disabled=['\"]?true|::placeholder", rule.selector):
                continue
            values = {decl.prop: decl for decl in rule.decls}
            color_decl = values.get("color")
            background_decl = values.get("background-color") or values.get("background")
            if color_decl is None or background_decl is None:
                continue
            local = {decl.prop: decl.value for decl in rule.decls if decl.prop.startswith("--")}
            rule_theme = theme_of(rule.selector, rule.media)
            size = to_px(values["font-size"].value) if "font-size" in values else None
            weight = values.get("font-weight")
            bold = bool(weight and re.fullmatch(r"(?:bold|[6-9]00)", weight.value.strip()))
            large = size is not None and (size >= 24 or (bold and size >= 18.66))
            for context_name, props in contexts:
                if rule_theme == "dark" and context_name != "dark":
                    continue
                if rule_theme == "light" and context_name == "dark":
                    continue
                fg_text = resolve(color_decl.value, local, props)
                bg_text = resolve(background_decl.value, local, props)
                if not fg_text or not bg_text:
                    continue
                foreground = parse_css_color(fg_text.strip())
                background = parse_css_color(bg_text.strip())
                if foreground is None or background is None or background[3] < 1 or foreground[3] == 0:
                    continue
                ratio = contrast_ratio(composite(foreground, background) if foreground[3] < 1 else foreground, background)
                minimum = 3.0 if large else 4.5
                if ratio + 1e-9 < minimum:
                    severity = "error" if ratio < 3 else None
                    self.add("low-contrast", color_decl.file, color_decl.line, "%s: %.2f:1 in %s theme (needs %.1f:1)" % (rule.selector, ratio, context_name, minimum), severity)


# --------------------------------------------------------------------------
# Config, reporting and CLI.
# --------------------------------------------------------------------------


def find_config(start: Path) -> Optional[Path]:
    current = start if start.is_dir() else start.parent
    for _ in range(8):
        candidate = current / "pfui.json"
        if candidate.is_file():
            return candidate
        if (current / ".git").exists() or current.parent == current:
            break
        current = current.parent
    return None


def load_config(path: Optional[Path], config: Config) -> List[str]:
    problems: List[str] = []
    if path is None:
        return problems
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ["Cannot read %s: %s" % (path, exc)]
    if not isinstance(data, dict):
        return ["%s must contain an object" % path]
    config.source = str(path)
    if data.get("platform") in PLATFORMS:
        config.platform = data["platform"]
    if data.get("medium") in MEDIA:
        config.medium = data["medium"]
    lint = data.get("lint", {})
    if isinstance(lint, dict):
        for rule in lint.get("disable", []):
            if rule in RULES:
                config.disabled.add(rule)
            else:
                problems.append("%s: unknown rule %r in lint.disable" % (path.name, rule))
        severity = lint.get("severity", {})
        if isinstance(severity, dict):
            for rule, level in severity.items():
                if rule in RULES and level in SEVERITIES:
                    config.severity[rule] = level
                else:
                    problems.append("%s: invalid severity override %r=%r" % (path.name, rule, level))
        ignore = lint.get("ignore", [])
        if isinstance(ignore, list):
            config.ignore.extend(str(item) for item in ignore)
    return problems


def lint_paths(targets: Sequence[Path], config: Config, root: Optional[Path] = None) -> Dict[str, object]:
    base = root or (targets[0] if targets and targets[0].is_dir() else (targets[0].parent if targets else Path.cwd()))
    linter = Linter(base, config)
    linter.run(targets)
    order = {name: index for index, name in enumerate(SEVERITIES)}
    findings = sorted(linter.findings, key=lambda item: (order[item.severity], item.file, item.line, item.rule))
    summary = Counter(item.severity for item in findings)
    return {
        "schemaVersion": 1,
        "root": str(base),
        "config": config.source,
        "platform": config.platform,
        "medium": config.medium,
        "files": sorted(linter.files),
        "findings": [item.as_dict() for item in findings],
        "summary": {level: summary.get(level, 0) for level in SEVERITIES},
        "passed": summary.get("error", 0) == 0,
        "limitations": [
            "Static analysis: layout, clipping, focus order, rendered contrast over images/gradients and copy quality are not verified.",
            "Contrast is checked only where a rule's color and background resolve to solid colors.",
        ],
    }


def print_report(report: Dict[str, object]) -> None:
    for item in report["findings"]:  # type: ignore[union-attr]
        print("%s:%s  %-5s  %-18s %s" % (item["file"], item["line"], item["severity"], item["rule"], item["message"]))
    summary = report["summary"]
    print(
        "Design lint: %d error(s), %d warning(s), %d info in %d file(s) [platform=%s, medium=%s]."
        % (summary["error"], summary["warn"], summary["info"], len(report["files"]), report["platform"], report["medium"])  # type: ignore[index,arg-type]
    )
    if not report["files"]:
        print("No HTML or CSS files found.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", default=["."], help="Files or directories to lint")
    parser.add_argument("--platform", choices=PLATFORMS)
    parser.add_argument("--medium", choices=MEDIA)
    parser.add_argument("--config", help="pfui.json path (default: nearest pfui.json above the first path)")
    parser.add_argument("--disable", default="", help="Comma-separated rule ids")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-rules", action="store_true")
    return parser


def configure(args: argparse.Namespace, targets: Sequence[Path]) -> Tuple[Config, List[str]]:
    config = Config()
    config_path = Path(args.config) if getattr(args, "config", None) else (find_config(targets[0].resolve()) if targets else None)
    problems = load_config(config_path, config)
    if getattr(args, "platform", None):
        config.platform = args.platform
    if getattr(args, "medium", None):
        config.medium = args.medium
    for rule in [item.strip() for item in (getattr(args, "disable", "") or "").split(",") if item.strip()]:
        if rule in RULES:
            config.disabled.add(rule)
        else:
            problems.append("Unknown rule %r in --disable" % rule)
    config.strict = bool(getattr(args, "strict", False))
    return config, problems


def safe_output() -> None:
    """Never crash on characters the console encoding cannot represent."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    safe_output()
    args = build_parser().parse_args(argv)
    if args.list_rules:
        for rule, (severity, description) in RULES.items():
            print("%-20s %-5s %s" % (rule, severity, description))
        return 0
    targets = [Path(item) for item in args.paths]
    missing = [str(path) for path in targets if not path.exists()]
    if missing:
        print("ERROR: path not found: %s" % ", ".join(missing), file=sys.stderr)
        return 2
    config, problems = configure(args, targets)
    for problem in problems:
        print("WARNING: %s" % problem, file=sys.stderr)
    report = lint_paths(targets, config)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print_report(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
