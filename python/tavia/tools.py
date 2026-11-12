"""The tool checker: the same checks, messages and order as the TypeScript SDK's checkTools.

Errors are what the server refuses at session.update; warnings cost accuracy or safety.
"""

import re
import unicodedata
from typing import Any, TypedDict

from tavia.generated.spec import LIMITS, TOOL_MARKS
from tavia.generated.tool_templates import TOOL_CHECKER

__all__ = ["TOOL_RULES", "ToolIssue", "ToolReport", "check_tools"]

# Every issue code check_tools can report and its severity, "error" or "warning".
TOOL_RULES: dict[str, str] = {k: v for k, v in TOOL_CHECKER["rules"].items() if k != "comment"}
SCHEMA = LIMITS["realtime.toolSchema"]
MAX_TOOLS = LIMITS["limits.tools"]
NAME_RE = re.compile(LIMITS["limits.toolNameRegex"])
EFFECT, EFFECTS, EFFECT_DEFAULT = TOOL_MARKS["effect"], TOOL_MARKS["effects"], TOOL_MARKS["effectDefault"]
ACTION, ACTIONS = TOOL_MARKS["action"], TOOL_MARKS["actions"]
WRITE_HINTS = frozenset(TOOL_CHECKER["writeHints"])
FORMATS = frozenset(TOOL_CHECKER["formats"])
FORMAT_HINTS = list(TOOL_CHECKER["formatHints"].items())
COORDINATE_HINTS = list(TOOL_CHECKER["coordinateHints"].items())
RESERVED = LIMITS["realtime.builtinTools.prefix"]
NUMBER_TYPES = ("number", "integer")
SIMILAR = TOOL_CHECKER["similarity"]
# The server matches patterns in linear time, so it has no lookaround or backreferences.
NOT_LINEAR = re.compile(r"\(\?<?[=!]|\\[1-9]|\\k<")
NOT_WORD = re.compile(r"[\W_]+")  # not a letter or digit, in any script
SPACES = re.compile(r"\s+")
PROPERTIES, PATTERN = "properties", "pattern"
SUBSET = SCHEMA["patternSubset"]
HEX = frozenset("0123456789abcdefABCDEF")
SHORTHAND = (
    "patterns cannot use \\d, \\w, \\s or \\b (they match differently across engines); write the class, such as [0-9]"
)


def _sorted_keys(node: dict) -> list:
    """Keys in JS sort order (UTF-16 code units), so both checkers walk alike."""
    return sorted(node, key=lambda k: k.encode("utf-16-be", "surrogatepass"))


def _subset_problem(p: str) -> str | None:
    """Why a pattern leaves the syntax that means the same in JS, Python and the server, or None."""
    i = 0
    while i < len(p):
        ch, nxt = p[i], p[i + 1 : i + 2]
        if ch == "\\":
            if nxt in SUBSET["shorthand"] and nxt:
                return SHORTHAND
            if nxt == "x" and len(p) > i + 3 and p[i + 2] in HEX and p[i + 3] in HEX:
                i += 4
                continue
            if not nxt or nxt not in SUBSET["escapes"]:
                return f"pattern escape \\{nxt} is not supported"
            i += 2
            continue
        if ch == "(" and nxt == "?" and p[i + 2 : i + 3] != ":":
            return "patterns can only group with ( or (?:"
        if ch == "{" and nxt == ",":
            return "patterns cannot use {,n}; write {0,n}"
        i += 1
    return None


_QUANT = re.compile(r"\{([0-9]+)(?:(,)([0-9]*))?\}")
MAX_REPEAT, MAX_EXPANDED = SUBSET["maxRepeat"], SUBSET["maxExpandedChars"]
REPEAT = f"patterns cannot repeat more than {MAX_REPEAT} times ({{n}}, {{n,}} and {{n,m}} take at most {MAX_REPEAT})"
EXPANDED = f"a pattern is over {MAX_EXPANDED} characters with its repeats written out"


def _units(s: str) -> int:
    return len(s.encode("utf-16-le", "surrogatepass")) // 2


def _class_end(p: str, i: int) -> int:
    """Where a class opening at i ends: after the first unescaped ] (the JS reading, so [] closes at once)."""
    j = i + 2 if p[i + 1 : i + 2] == "^" else i + 1
    while j < len(p):
        if p[j] == "\\":
            j += 2
        elif p[j] == "]":
            return j + 1
        else:
            j += 1
    return len(p)


def _quantifier(p: str, i: int):
    """A quantifier at i: (repeat bound, end) with {n,} as n+1 and {0} as 1, a repeat problem, or None."""
    if p[i] in "*+?":
        return 1, i + 1
    m = _QUANT.match(p, i) if p[i] == "{" else None
    if m is None:
        return None
    lo, comma, hi = m.groups()
    if int(lo) > MAX_REPEAT or (hi and int(hi) > MAX_REPEAT):
        return REPEAT
    return max(1, int(hi) if hi else int(lo) + (1 if comma else 0)), m.end()


def _atom_at(p: str, i: int) -> tuple:
    """The atom at i (a class, an escape or one character): (UTF-16 length, end)."""
    end = i + 1
    if p[i] == "[":
        end = _class_end(p, i)
    elif p[i] == "\\":
        hex2 = p[i + 1 : i + 2] == "x" and len(p) > i + 3 and p[i + 2] in HEX and p[i + 3] in HEX
        end = min(len(p), i + (4 if hex2 else 2))
    return _units(p[i:end]), end


def _repeat_problem(p: str) -> str | None:
    """Counted repeats against the server's pattern limits: maxRepeat per repeat, maxExpandedChars written out."""
    frames = [[0, 0]]  # [written-out total, last atom] per open group
    i = 0
    while i < len(p):
        top = frames[-1]
        q = _quantifier(p, i)
        if isinstance(q, str):
            return q
        if q is not None:
            top[0] += top[1] * (q[0] - 1)
            top[1] *= q[0]
            i = q[1]
        elif p[i] == "(":
            n = 3 if p.startswith("(?:", i) else 1
            frames.append([n, 0])
            i += n
        else:
            if p[i] == ")" and len(frames) > 1:
                frames.pop()
                atom, i = top[0] + 1, i + 1
            else:
                atom, i = _atom_at(p, i)
            frames[-1][0] += atom
            frames[-1][1] = atom
        if sum(f[0] for f in frames) > MAX_EXPANDED:
            return EXPANDED
    return None


class ToolIssue(TypedDict, total=False):
    """One problem check_tools found: its code and severity, the tool and field it is on (if any), and a message."""

    code: str
    severity: str
    tool: str
    path: str
    message: str


class ToolReport(TypedDict):
    """What check_tools found: errors the server would refuse, and warnings that cost accuracy or safety."""

    errors: list[ToolIssue]
    warnings: list[ToolIssue]


def _js_len(s: str) -> int:
    """Length as JavaScript counts it (UTF-16 units), so both SDKs cut at the same place."""
    return len(s.encode("utf-16-le")) // 2


# ---- text similarity (letter n-grams work for spaced and unspaced scripts alike)


def _grams(text: str, n: int) -> set[str]:
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def name_similarity(a: str, b: str) -> float:
    """Dice overlap of letter pairs, ignoring case and separators."""
    x, y = (_grams(NOT_WORD.sub("", s.lower()), 2) for s in (a, b))
    total = len(x) + len(y)
    return 2 * len(x & y) / total if total else 0.0


def text_similarity(a: str, b: str) -> float:
    """Jaccard overlap of three-letter runs, ignoring case and spacing."""
    x, y = (_grams(SPACES.sub(" ", s.lower()).strip(), 3) for s in (a, b))
    union = len(x | y)
    return len(x & y) / union if union else 0.0


def name_words(name: str) -> list[str]:
    """book_slot, bookSlot and book-slot all give [book, slot]."""
    out = []
    for i, ch in enumerate(name):
        prev = unicodedata.category(name[i - 1]) if i else ""
        if unicodedata.category(ch) == "Lu" and (prev == "Ll" or prev.startswith("N")):
            out.append(" ")
        out.append(ch)
    return [w for w in NOT_WORD.split("".join(out).lower()) if w]


# ---- schema walk (the same caps the server applies at session.update; iterative)


def _pattern_problem(pattern: Any) -> str | None:
    if not isinstance(pattern, str):
        return "a pattern must be a string"
    if _js_len(pattern) > SCHEMA["maxPatternChars"]:
        return f"a pattern is over {SCHEMA['maxPatternChars']} characters"
    if NOT_LINEAR.search(pattern):
        return "patterns cannot use lookaround or backreferences"
    subset = _subset_problem(pattern) or _repeat_problem(pattern)
    if subset:
        return subset
    try:
        re.compile(pattern)
    except re.error:
        return f"pattern {pattern} does not compile"
    return None


def _walk(schema: Any) -> tuple[str | None, bool, int]:
    """(problem, the problem is a pattern, patterns seen)."""
    stack: list[tuple[Any, Any, int]] = [(schema, None, 1)]
    nodes = patterns = 0
    while stack:
        node, parent_key, depth = stack.pop()
        nodes += 1
        if nodes > SCHEMA["maxNodes"]:
            return f"over {SCHEMA['maxNodes']} schema nodes", False, patterns
        if depth > SCHEMA["maxDepth"]:
            return f"nested over {SCHEMA['maxDepth']} levels", False, patterns
        if isinstance(node, list):
            stack.extend((v, i, depth + 1) for i, v in enumerate(node))
        if not isinstance(node, dict):
            continue
        if any(_js_len(k) > SCHEMA["maxKeyChars"] for k in node):
            return f"a key is over {SCHEMA['maxKeyChars']} characters", False, patterns
        for k in _sorted_keys(node):
            v = node[k]
            if k == PATTERN and parent_key != PROPERTIES:
                patterns += 1
                why = _pattern_problem(v)
                if why:
                    return why, True, patterns
            else:
                stack.append((v, k, depth + 1))
    return None, False, patterns


def _fields(schema: dict, prefix: str = "") -> list[tuple[str, dict]]:
    """Every named field, depth first in sorted key order; array items keep their parent's name."""
    props = schema.get(PROPERTIES)
    if not isinstance(props, dict):
        return []
    out: list[tuple[str, dict]] = []
    for name in _sorted_keys(props):
        field = props[name]
        if not isinstance(field, dict):
            continue
        path = f"{prefix}.{name}" if prefix else name
        out.append((path, field))
        out.extend(_fields(field, path))
        if isinstance(field.get("items"), dict):
            out.extend(_fields(field["items"], f"{path}[]"))
    return out


# ---- the checks


class _Report:
    def __init__(self) -> None:
        self.out: ToolReport = {"errors": [], "warnings": []}

    def add(self, code: str, message: str, tool: str | None = None, path: str | None = None) -> None:
        issue: ToolIssue = {"code": code, "severity": TOOL_RULES[code], "message": message}
        if tool is not None:
            issue["tool"] = tool
        if path is not None:
            issue["path"] = path
        self.out["errors" if issue["severity"] == "error" else "warnings"].append(issue)


def _check_effect(t: dict, label: str, r: _Report) -> None:
    if EFFECT not in t:
        r.add(
            "effect_missing",
            f"No {EFFECT}, so it runs as {EFFECT_DEFAULT} and is confirmed before every call. "
            "Set read if it only looks things up.",
            label,
        )
    elif t[EFFECT] not in EFFECTS:
        r.add("effect_invalid", f"{EFFECT} must be {' or '.join(EFFECTS)}.", label)
    elif t[EFFECT] == "read" and any(w in WRITE_HINTS for w in name_words(label)):
        r.add(
            "effect_read_looks_like_write",
            "Marked read, but the name sounds like a change. If it changes anything, mark it write.",
            label,
        )


def _check_action(t: dict, label: str, r: _Report) -> None:
    """A write's action says what kind of change it makes, so the agent can say what it did; an unknown one cannot."""
    if ACTION not in t:
        return
    if t[ACTION] not in ACTIONS:
        r.add("action_invalid", f"{ACTION} must be {', '.join(ACTIONS[:-1])} or {ACTIONS[-1]}.", label)
    elif t.get(EFFECT) == "read":
        r.add("action_on_read", f"Marked read, so {ACTION} is ignored: a read only backs 'found'.", label)


def _check_description(t: dict, label: str, r: _Report) -> str | None:
    d = t["description"].strip() if isinstance(t.get("description"), str) else ""
    if not d:
        r.add("description_missing", "Add a description: what it does and when to call it.", label)
        return None
    if len(d.encode("utf-8")) < TOOL_CHECKER["minDescriptionBytes"] or name_words(d) == name_words(label):
        r.add("description_vague", "Say what it does and when to call it, not just its name.", label)
    return d


def _format_for(field_name: str) -> str | None:
    words = set(name_words(field_name))
    hits = [fmt for fmt, hints in FORMAT_HINTS if any(h in words for h in hints)]
    if "date" in hits and "time" in hits:
        return "date-time"
    return hits[0] if hits else None


def _check_coordinate(path: str, schema: dict, label: str, r: _Report) -> None:
    """A number named like a latitude or longitude should carry its range, so a misheard value is refused."""
    if not isinstance(schema.get("type"), str) or schema["type"] not in NUMBER_TYPES:
        return
    if "minimum" in schema and "maximum" in schema:
        return
    words = set(name_words(path.split(".")[-1]))
    for kind, hint in COORDINATE_HINTS:
        if any(w in words for w in hint["words"]):
            r.add(
                "coordinates_unbounded",
                f'Add "minimum": {hint["minimum"]} and "maximum": {hint["maximum"]} '
                f"so an impossible {kind} is refused.",
                label,
                path,
            )
            return


def _check_field(path: str, schema: dict, label: str, r: _Report) -> None:
    desc = schema.get("description")
    if not isinstance(desc, str) or not desc.strip():
        r.add("param_description_missing", f"Describe {path}: what it holds and in what form.", label, path)
    _check_coordinate(path, schema, label, r)
    if "format" in schema:
        if str(schema["format"]) not in FORMATS:
            r.add("format_unknown", f"Format {schema['format']} is not enforced.", label, path)
        return
    free = PATTERN in schema or "enum" in schema or ("type" in schema and schema["type"] != "string")
    want = None if free else _format_for(path.split(".")[-1])
    if want:
        r.add("format_missing", f'Add "format": "{want}" so the value arrives in one form.', label, path)


def _check_required(schema: dict, label: str, r: _Report, path: str | None = None) -> None:
    if not isinstance(schema.get("required"), list):
        return
    props = schema[PROPERTIES] if isinstance(schema.get(PROPERTIES), dict) else {}
    for name in schema["required"]:
        if str(name) not in props:
            r.add("required_unknown", f"required lists {name}, which is not defined.", label, path)


def _check_parameters(t: dict, label: str, r: _Report) -> int:
    if "parameters" not in t:
        return 0
    params = t["parameters"]
    if (
        not isinstance(params, dict)
        or ("type" in params and params["type"] != "object")
        or (PROPERTIES in params and not isinstance(params[PROPERTIES], dict))
    ):
        r.add("parameters_invalid", 'parameters must be a JSON Schema object with type "object".', label)
        return 0
    problem, is_pattern, patterns = _walk(params)
    if problem:
        r.add("pattern_invalid" if is_pattern else "schema_too_large", f"parameters: {problem}.", label)
        return patterns
    if patterns > SCHEMA["maxPatternsPerTool"]:
        r.add("patterns_too_many", f"More than {SCHEMA['maxPatternsPerTool']} patterns in one tool.", label)
    _check_required(params, label, r)
    for path, field in _fields(params):
        _check_field(path, field, label, r)
        _check_required(field, label, r, path)
    return patterns


def _check_one(t: Any, i: int, seen: set[str], r: _Report) -> tuple[str | None, str | None, int] | None:
    if not isinstance(t, dict) or t.get("type") != "function":
        r.add("tool_invalid", 'Each tool must be an object with type "function".', f"tools[{i}]")
        return None
    named = t["name"] if isinstance(t.get("name"), str) and t["name"] else None
    label = named or f"tools[{i}]"
    if not named or not NAME_RE.fullmatch(named):
        r.add("name_invalid", f"Use a name matching {NAME_RE.pattern}.", label)
    elif named.lower().startswith(RESERVED):
        r.add(
            "name_reserved",
            f"Names starting with {RESERVED}, in any case, are reserved for Tavia's built-in tools; rename it.",
            label,
        )
    elif named in seen:
        r.add("name_duplicate", "Another tool already has this name.", label)
    if named:
        seen.add(named)
    _check_effect(t, label, r)
    _check_action(t, label, r)
    description = _check_description(t, label, r)
    return named, description, _check_parameters(t, label, r)


def _check_pairs(tools: list[tuple[str | None, str | None, int]], r: _Report) -> None:
    for i, (a_name, a_desc, _) in enumerate(tools):
        for b_name, b_desc, _ in tools[i + 1 :]:
            if not a_name or not b_name or a_name == b_name:
                continue
            names = name_similarity(a_name, b_name) >= SIMILAR["name"]
            texts = bool(a_desc and b_desc) and text_similarity(a_desc, b_desc) >= SIMILAR["description"]
            if names or texts:
                r.add(
                    "near_duplicate",
                    f"{a_name} and {b_name} look alike; the agent may pick the wrong one.",
                    f"{a_name}, {b_name}",
                )


def check_tools(tools: list, *, max_tools: int | None = None) -> ToolReport:
    """Checks a session's tools before you send them: {"errors": [...], "warnings": [...]}.

    Errors are what the server refuses at session.update; warnings cost accuracy or safety. max_tools defaults to
    the session cap. Raises TypeError when tools is not a list.

    Example:
        report = check_tools([find_order, book_slot])
        for issue in report["errors"] + report["warnings"]:
            log.warning("%s: %s", issue.get("tool"), issue["message"])
    """
    if not isinstance(tools, (list, tuple)):
        raise TypeError("tools must be a list")
    cap = MAX_TOOLS if max_tools is None else max_tools
    r = _Report()
    n = len(tools)
    if n > cap:
        r.add("tools_too_many", f"{n} tools; a session takes at most {cap}.")
    elif n > TOOL_CHECKER["accuracyTools"]:
        r.add("tools_many", f"{n} tools; above {TOOL_CHECKER['accuracyTools']} the agent picks less reliably.")
    seen: set[str] = set()
    checked = [c for c in (_check_one(t, i, seen, r) for i, t in enumerate(tools)) if c is not None]
    if sum(c[2] for c in checked) > SCHEMA["maxPatterns"]:
        r.add("patterns_too_many", f"More than {SCHEMA['maxPatterns']} patterns across the session's tools.")
    _check_pairs(checked, r)
    return r.out
