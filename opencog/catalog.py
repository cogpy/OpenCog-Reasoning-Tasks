"""Loss-aware loading and auditing of the Markdown reasoning-task catalog.

Examples are source material, not verified answers. No parser or JSON comparison
promotes their audit status to ground truth.
"""

import json
from pathlib import Path
import re


_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_EXAMPLE = re.compile(r"^\s*(?:#{1,6}\s*|-\s*)?Example\s+\d+\s*:?\s*$", re.I)
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
_KNOWN_AUDITS = {
    "mental-rotation-tasks": (
        "spatial-answer-unverified",
        "Cube opposite faces are unspecified; the letter-F transformation is "
        "also questionable. These examples are not ground truth.",
    ),
    "understanding-time-zones-and-global-time-differences": (
        "timezone-answer-unverified",
        "Dates and seasonal UTC offsets are unspecified; the flight example "
        "also has incorrect arithmetic (Monday 23:00 + 34 hours is Wednesday "
        "09:00, not 17:00). These examples are not ground truth.",
    ),
    "bias-mitigation": (
        "unsupported-bias-correction",
        "Corrections introduce unsupported personal histories, motivations, "
        "or conclusions. They are not established ground truth.",
    ),
}


class CatalogParseError(ValueError):
    """A task definition lacks required data or contains malformed examples."""


def _outside_fences(lines):
    """Yield line/index/visibility, respecting fence character and length."""
    fence = None
    for index, line in enumerate(lines):
        match = _FENCE.match(line)
        outside = fence is None
        if match:
            marker, suffix = match.groups()
            if fence is None:
                fence = marker
            elif (marker[0] == fence[0] and len(marker) >= len(fence)
                  and not suffix.strip()):
                fence = None
            outside = False
        yield index, line, outside


def _has_unclosed_fence(lines):
    fence = None
    for line in lines:
        match = _FENCE.match(line)
        if match:
            marker, suffix = match.groups()
            if fence is None:
                fence = marker
            elif (marker[0] == fence[0] and len(marker) >= len(fence)
                  and not suffix.strip()):
                fence = None
    return fence is not None


def _label(line):
    # The exceptional LaTeX file uses **Input:**, **Input: ** and ** Output**:.
    plain = line.strip()
    if plain.startswith("**"):
        plain = plain.replace("**", "", 2).strip()
    match = re.match(r"^(Input|Output)\s*:\s*(.*)$", plain, re.I)
    return (match[1].lower(), match[2]) if match else None


def _value(lines):
    lines = list(lines)
    while lines and (not lines[-1].strip() or lines[-1].strip() == "---"):
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    # Unwrap only a single enclosing fence, not a response containing several
    # code blocks interspersed with explanatory prose.
    if lines:
        first = _FENCE.match(lines[0])
        if first:
            marker = first[1]
            closing = None
            for index, line in enumerate(lines[1:], 1):
                match = _FENCE.match(line)
                if (match and match[1][0] == marker[0]
                        and len(match[1]) >= len(marker)
                        and not match[2].strip()):
                    closing = index
                    break
            if closing == len(lines) - 1:
                lines = lines[1:-1]
    return "\n".join(lines).strip()


def _parse_example(lines, source, number, tolerant, warnings):
    labels = [(index, _label(line)) for index, line, visible
              in _outside_fences(lines) if visible and _label(line)]
    problems = []
    turns = []
    pending = None
    if not labels:
        problems.append("no Input/Output turn labels")
    elif any(line.strip() for line in lines[:labels[0][0]]):
        problems.append("unparsed text before the first turn")
    if _has_unclosed_fence(lines):
        problems.append("unclosed Markdown fence")
    for position, (start, (kind, inline)) in enumerate(labels):
        end = labels[position + 1][0] if position + 1 < len(labels) else len(lines)
        value = _value(([inline] if inline else []) + lines[start + 1:end])
        if not value:
            problems.append("empty " + kind)
        if kind == "input":
            if pending is not None:
                problems.append("input without a following output")
                turns.append({"input": pending, "output": ""})
            pending = value
        elif pending is None:
            problems.append("output without a preceding input")
            turns.append({"input": "", "output": value})
        else:
            turns.append({"input": pending, "output": value})
            pending = None
    if pending is not None:
        problems.append("input without a following output")
        turns.append({"input": pending, "output": ""})
    if problems:
        message = "Example {}: {}".format(number, "; ".join(problems))
        if not tolerant:
            raise CatalogParseError("{}: {}".format(source, message))
        warnings.append(message)
    first = turns[0] if turns else {"input": "", "output": ""}
    return {
        "turns": turns,
        "input": first["input"],
        "output": first["output"],
        "raw_content": "\n".join(lines),
        "audit_status": "unreviewed",
        "parse_status": "malformed" if problems else "parsed",
        "provenance": {"source": source, "example": number,
                       "origin": "source-task", "verified": False},
    }


def parse_task_file(path):
    """Parse a UTF-8 task; raise CatalogParseError for malformed ordinary files.

    The historical nonstandard LaTeX definition is accepted with explicit
    warnings, inferred modality, and lossless raw source. Malformed turns in
    that definition are retained and marked, never silently counted as parsed.
    """
    path = Path(path)
    source = str(path)
    with path.open(encoding="utf-8", newline="") as handle:
        raw = handle.read()
    lines = raw.splitlines()
    tolerant = path.stem == "multiturn-latex-generation"
    warnings = []
    name = None
    sections = {}
    current = None
    for _, line, visible in _outside_fences(lines):
        heading = _HEADING.match(line) if visible else None
        if heading and len(heading[1]) == 1 and name is None and current is None:
            name = heading[2].strip().rstrip(":")
            continue
        if heading and len(heading[1]) == 2:
            label, colon, inline = heading[2].partition(":")
            current = label.strip().lower()
            if current in sections:
                raise CatalogParseError("{}: duplicate {} section".format(source, current))
            sections[current] = [inline.strip()] if colon and inline.strip() else []
            continue
        if tolerant and current is None and visible:
            plain = line.replace("**", "").strip()
            if plain.lower().startswith("name:"):
                name = plain.split(":", 1)[1].strip()
                continue
            if plain.lower().startswith("description:"):
                current = "description"
                sections[current] = [plain.split(":", 1)[1].strip()]
                continue
        if (tolerant and visible and line.strip().lower() == "example(s):"):
            current = "examples"
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
        elif line.strip():
            warnings.append("Unparsed preamble text: " + line.strip())
    if not name:
        raise CatalogParseError("{}: missing name/title".format(source))
    if _has_unclosed_fence(lines):
        message = "Unclosed Markdown fence"
        if not tolerant:
            raise CatalogParseError("{}: {}".format(source, message))
        warnings.append(message)
    if tolerant:
        warnings.append("Nonstandard LaTeX source format; examples are unreviewed.")
        if not _value(sections.get("modality", [])):
            sections["modality"] = ["Text only"]
            warnings.append("Missing modality; inferred Text only from LaTeX task.")
    for required in ("description", "modality", "examples", "tags"):
        if not _value(sections.get(required, [])):
            raise CatalogParseError("{}: missing or empty {}".format(source, required))
    tags = []
    for line in sections["tags"]:
        if not line.strip():
            continue
        match = re.match(r"^\s*[-*+]\s+(.+?)\s*$", line)
        tag = match[1] if match else line.strip()
        if not any(character.isalnum() for character in tag):
            warnings.append("Ignored garbage tag: " + line.strip())
        else:
            tags.append(tag)
    if not tags:
        raise CatalogParseError("{}: missing valid tags".format(source))
    example_lines = sections["examples"]
    starts = [index for index, line, visible in _outside_fences(example_lines)
              if visible and _EXAMPLE.match(line)]
    if not starts:
        raise CatalogParseError("{}: no numbered examples".format(source))
    if any(line.strip() for line in example_lines[:starts[0]]):
        message = "Unparsed text before first example"
        if not tolerant:
            raise CatalogParseError("{}: {}".format(source, message))
        warnings.append(message)
    examples = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(example_lines)
        examples.append(_parse_example(example_lines[start + 1:end], source,
                                       index + 1, tolerant, warnings))
    audit_issues = []
    if path.stem in _KNOWN_AUDITS:
        code, message = _KNOWN_AUDITS[path.stem]
        audit_issues.append({"code": code, "message": message,
                             "severity": "warning", "source": source})
        warnings.append(message)
    for index, example in enumerate(examples, 1):
        if example["parse_status"] == "malformed":
            audit_issues.append({"code": "malformed-example", "example": index,
                                 "message": "Incomplete or unparsed conversation.",
                                 "severity": "warning", "source": source})
    metadata = {key: _value(value) for key, value in sections.items()
                if key not in ("description", "modality", "tags", "examples")}
    return {
        "id": path.stem, "name": name,
        "description": _value(sections["description"]),
        "modality": _value(sections["modality"]),
        "tags": tags, "examples": examples, "metadata": metadata,
        "raw_content": raw, "source": source, "warnings": warnings,
        "audit_issues": audit_issues, "audit_status": "unreviewed",
    }


def load_catalog(directory):
    """Return (sorted task dictionaries, per-file load/audit report).

    ``loaded`` counts readable definitions, including explicitly warned legacy
    definitions. ``skipped`` contains each failed path and its error.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(str(directory))
    paths = sorted(directory.glob("*.md"))
    tasks = []
    report = {"total_files": len(paths), "loaded": 0, "issues": [], "skipped": []}
    for path in paths:
        try:
            task = parse_task_file(path)
        except (OSError, UnicodeError, CatalogParseError) as error:
            report["skipped"].append({"source": str(path), "error": str(error)})
            continue
        tasks.append(task)
        if task["warnings"] or task["audit_issues"]:
            report["issues"].append({"source": task["source"],
                                     "warnings": task["warnings"],
                                     "audit_issues": task["audit_issues"]})
    report["loaded"] = len(tasks)
    return tasks, report


def _normalize(value):
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _semantic_fields(task):
    examples = []
    for example in task.get("examples", []):
        if isinstance(example, list):
            turns = example
        elif isinstance(example, dict):
            turns = example.get("turns", [example])
        else:
            raise ValueError("examples must contain conversation lists or dictionaries")
        examples.append([{"input": turn["input"], "output": turn["output"]}
                         for turn in turns])
    tags = [tag for tag in task.get("tags", [])
            if any(character.isalnum() for character in tag)]
    fields = {key: task.get(key) for key in ("name", "description", "modality")}
    fields.update(tags=tags, examples=examples)
    return _normalize(fields)


def check_json_consistency(directory, json_directory):
    """Compare normalized semantic fields against the JS nested-turn schema.

    Return ``mismatches`` (per-source differing fields or invalid JSON errors),
    ``missing`` JSON paths, and the underlying Markdown ``catalog_report``.
    Equality is only a format consistency check, not answer verification.
    """
    tasks, catalog_report = load_catalog(directory)
    json_directory = Path(json_directory)
    report = {"checked": 0, "mismatches": [], "missing": [],
              "catalog_report": catalog_report}
    for task in tasks:
        path = json_directory / (task["id"] + ".json")
        if not path.is_file():
            report["missing"].append({"source": task["source"], "json_source": str(path)})
            continue
        report["checked"] += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            actual = _semantic_fields(data)
            expected = _semantic_fields(task)
            differing = [key for key in expected if expected[key] != actual[key]]
            if differing:
                report["mismatches"].append({"source": task["source"],
                                             "json_source": str(path),
                                             "fields": differing})
        except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as error:
            report["mismatches"].append({"source": task["source"],
                                         "json_source": str(path), "error": str(error)})
    return report
