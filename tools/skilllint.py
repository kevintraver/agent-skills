#!/usr/bin/env python3
"""skilllint: machine-checkable rules from Anthropic's "Complete Guide to Building
Skills for Claude" (PDF, Jan 2026) and the Agent Skills spec (agentskills.io/specification).

Usage: skilllint.py [--json] [SKILL_DIR...]
With no SKILL_DIR, lints every folder next to tools/ that contains a SKILL.md.

Each finding: (severity, rule_id, message, source). ERROR = must fix to pass, WARN = advisory.
Also re-implements skills-ref validate (agentskills/agentskills@f130f34 validator.py) as SR* rules,
including strictyaml's rejection of flow-style collections.
"""
import json, os, re, sys, unicodedata
from pathlib import Path

import yaml

ALLOWED_FIELDS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WHEN_RE = re.compile(
    r"(\buse (this|it)?\s*(skill\s*)?(when|whenever|for|if|to|before|on)\b|\bused when\b|\btrigger(s|ed)? (on|when|if|this)\b"
    r"|\bwhen (the )?(user|asked|you|someone|a |an |given|working|building|writing)|\bwhenever\b|\buse when\b|\bUSE WHEN\b|\bread first\b)",
    re.I,
)
FILE_EXT = r"(?:md|py|sh|js|mjs|cjs|ts|json|yaml|yml|txt|toml|html|css|swift|rb|go|lua|csv|png|jpg|svg)"


def find(sev, rid, msg, src):
    return {"severity": sev, "rule": rid, "message": msg, "source": src}


def split_frontmatter(text):
    if not text.startswith("---"):
        return None, None, "no leading --- delimiter"
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(\n|$)", text, re.S)
    if not m:
        return None, None, "frontmatter not closed with ---"
    return m.group(1), text[m.end():], None


def flow_style_lines(fm):
    """strictyaml (used by skills-ref) rejects flow mappings/sequences like [a, b] or {a: b}."""
    bad = []
    for i, line in enumerate(fm.splitlines(), 1):
        s = line.split(" #")[0].rstrip()
        m = re.match(r"^\s*(?:- )?[A-Za-z0-9_-]+:\s*([\[{].*)$", s)
        if m and not re.match(r"^[\[{].*[\]}]\s*\S", m.group(1)):
            bad.append(i)
        elif re.match(r"^\s*-\s*[\[{]", s):
            bad.append(i)
    return bad


def referenced_paths(body, skill_dir):
    """Yield (path, how) for things that look like references to files bundled in the skill."""
    out = set()
    # markdown links
    for m in re.finditer(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", body):
        t = m.group(1)
        if re.match(r"^[a-z]+:", t) or t.startswith("/") or t.startswith("~") or not re.search(r"[./]", t):
            continue  # URL, absolute path, or a bare-word placeholder like (permalink)
        out.add((t, "link"))
    # ${CLAUDE_SKILL_DIR}/x, {baseDir}/x, <skill>/x, <this-skill-dir>/x, ~/.claude/skills/<name>/x
    for m in re.finditer(r"(?:\$\{?CLAUDE_SKILL_DIR\}?|\{baseDir\}|<[a-z _-]*skill[a-z _-]*>|SKILL_DIR)/([A-Za-z0-9_./-]+)", body):
        out.add((m.group(1).rstrip(".,;:"), "skill-dir var"))
    name = skill_dir.name
    for m in re.finditer(r"~/\.(?:claude|agents|codex)/skills/" + re.escape(name) + r"/([A-Za-z0-9_./-]+)", body):
        out.add((m.group(1).rstrip(".,;:"), "home path"))
    # backticked or bare relative paths rooted at a bundled dir
    top = {p.name for p in skill_dir.iterdir()} | {"scripts", "references", "assets"}
    for m in re.finditer(r"(?<![\w./$~{-])((?:\./)?([A-Za-z0-9_-]+)/[A-Za-z0-9_./-]*[A-Za-z0-9_-](?:\." + FILE_EXT + r")?)", body):
        p = m.group(1)[2:] if m.group(1).startswith("./") else m.group(1)
        first = p.split("/")[0]
        if first in top and first not in {".git", "node_modules"}:
            # skip globs and placeholders
            if any(c in p for c in "*<>{}"):
                continue
            out.add((p.rstrip(".,;:"), "path"))
    return sorted(out)


def lint(skill_dir, folder_name=None):
    skill_dir = Path(skill_dir)
    folder_name = folder_name or skill_dir.name
    real = skill_dir.resolve()
    F = []
    entries = os.listdir(real)
    # --- SKILL.md exact spelling (case-sensitive even on APFS)
    if "SKILL.md" not in entries:
        variants = [e for e in entries if e.lower() == "skill.md"]
        F.append(find("ERROR", "E01-skill-md-name", f"no file named exactly SKILL.md (found {variants or 'none'})", "PDF p10 'Critical rules', p25; spec 'SKILL.md format'"))
        return F
    # --- folder naming
    if not KEBAB.match(folder_name):
        F.append(find("ERROR", "E05-folder-kebab", f"folder '{folder_name}' is not kebab-case", "PDF p10 'Skill folder naming', p30 Ref A"))
    if real.name != folder_name and not KEBAB.match(real.name):
        F.append(find("ERROR", "E05-folder-kebab", f"source folder '{real.name}' is not kebab-case", "PDF p10"))
    # --- README.md
    if "README.md" in entries:
        F.append(find("ERROR", "E11-no-readme", "README.md inside the skill folder", "PDF p10 'No README.md'"))
    for root, dirs, files in os.walk(real):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".git"}]
        if Path(root) != real and "README.md" in files:
            F.append(find("WARN", "W05-nested-readme", f"README.md at {Path(root).relative_to(real)}/ (PDF says docs belong in SKILL.md or references/)", "PDF p10"))
    text = (real / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    fm_text, body, err = split_frontmatter(text)
    if err:
        F.append(find("ERROR", "E02-frontmatter", err, "PDF p25, p30 Ref A; spec 'Frontmatter'"))
        return F
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        F.append(find("ERROR", "E02-frontmatter", f"invalid YAML: {str(e).splitlines()[0]}", "PDF p25; spec 'Frontmatter'"))
        return F
    if not isinstance(fm, dict):
        F.append(find("ERROR", "E02-frontmatter", "frontmatter is not a mapping", "spec 'Frontmatter'"))
        return F
    flow = flow_style_lines(fm_text)
    if flow:
        F.append(find("ERROR", "SR-strictyaml", f"flow-style YAML on frontmatter line(s) {flow}; skills-ref's strictyaml parser rejects it", "skills-ref parser.py (spec 'Validation')"))
    extra = set(fm) - ALLOWED_FIELDS
    if extra:
        F.append(find("ERROR", "SR-unexpected-fields", f"non-spec top-level fields: {', '.join(sorted(extra))}", "spec 'Frontmatter' table; skills-ref validator.py ALLOWED_FIELDS"))
    # --- name
    name = fm.get("name")
    if not isinstance(name, str) or not name.strip():
        F.append(find("ERROR", "E03-name", "missing/empty name", "spec 'name field'; PDF p10, p31"))
    else:
        n = unicodedata.normalize("NFKC", name.strip())
        if len(n) > 64:
            F.append(find("ERROR", "E03-name", f"name is {len(n)} chars (max 64)", "spec 'name field'"))
        if not KEBAB.match(n):
            F.append(find("ERROR", "E03-name", f"name '{n}' is not kebab-case (a-z, 0-9, single hyphens, no leading/trailing hyphen)", "spec 'name field'; PDF p10"))
        if n != folder_name:
            F.append(find("ERROR", "E04-name-matches-folder", f"name '{n}' != folder '{folder_name}'", "spec 'name field' (must); PDF p10 (should)"))
        if re.search(r"claude|anthropic", n, re.I):
            F.append(find("ERROR", "E06-reserved-word", f"name '{n}' contains a reserved word", "PDF p11 'Security restrictions' (contains), p31 (prefix)"))
    # --- every frontmatter value: no angle brackets
    def walk(v, path):
        if isinstance(v, dict):
            for k, x in v.items():
                yield from walk(x, f"{path}.{k}" if path else str(k))
        elif isinstance(v, list):
            for i, x in enumerate(v):
                yield from walk(x, f"{path}[{i}]")
        else:
            yield path, v
    for path, v in walk(fm, ""):
        if isinstance(v, str) and re.search(r"[<>]", v):
            F.append(find("ERROR", "E08-angle-brackets", f"'{path}' contains < or >", "PDF p10 (description), p11 + p31 (all frontmatter)"))
    # --- description
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        F.append(find("ERROR", "E07-description", "missing/empty description", "spec 'description field'; PDF p10"))
    else:
        d = desc.strip()
        if len(d) > 1024:
            F.append(find("ERROR", "E07-description", f"description is {len(d)} chars (max 1024)", "spec 'description field'; PDF p10, p31"))
        when = WHEN_RE.search(d)
        if not when:
            F.append(find("ERROR", "E09-what-and-when", "description has no 'when to use' clause", "PDF p10 (MUST include both), p30 Ref A; spec 'description field' (should)"))
        else:
            what = d[: when.start()].strip(" .,-—:;\"'")
            rest = d[when.end():]
            if len(what.split()) < 2 and not re.search(r"\.\s+\S", rest):
                F.append(find("ERROR", "E09-what-and-when", "description says when to use it but not what it does", "PDF p10 (MUST include both); spec 'description field'"))
    # --- compatibility
    if "compatibility" in fm:
        c = fm["compatibility"]
        if not isinstance(c, str) or not (1 <= len(c) <= 500):
            F.append(find("ERROR", "E10-compatibility", f"compatibility must be a 1-500 char string (got {type(c).__name__} len {len(c) if isinstance(c, str) else '-'})", "spec 'compatibility field'; PDF p11"))
    # --- metadata: string -> string
    if "metadata" in fm:
        md = fm["metadata"]
        if not isinstance(md, dict):
            F.append(find("ERROR", "E15-metadata", "metadata must be a mapping", "spec 'metadata field'"))
        else:
            nonscalar = [k for k, v in md.items() if isinstance(v, (dict, list))]
            if nonscalar:
                F.append(find("ERROR", "E15-metadata", f"metadata values must be strings: {nonscalar}", "spec 'metadata field' (PDF p31 example shows a list: conflict, spec wins)"))
    if "allowed-tools" in fm and not isinstance(fm["allowed-tools"], str):
        F.append(find("WARN", "W06-allowed-tools", "allowed-tools should be a space-separated string", "spec 'allowed-tools field'; PDF p31"))
    # --- body size
    words = len(re.findall(r"\S+", body))
    lines = text.count("\n") + 1
    if words >= 5000:
        F.append(find("ERROR", "E12-body-words", f"body is {words} words (keep under 5,000)", "PDF p27 'Large context issues'"))
    if lines > 500:
        F.append(find("WARN", "W01-lines", f"SKILL.md is {lines} lines (spec recommends < 500)", "spec 'Progressive disclosure'"))
    est_tokens = len(body) // 4
    if est_tokens > 5000:
        F.append(find("WARN", "W02-tokens", f"body is ~{est_tokens} tokens (spec recommends < 5,000)", "spec 'Progressive disclosure'"))
    # --- referenced files exist
    missing = []
    siblings = Path(skill_dir).parent
    for p, how in referenced_paths(body, real):
        target = (real / p)
        if target.exists():
            continue
        # cross-skill reference like "`/hyperframes-core` `references/x.md`": resolve in the named sibling
        lines = [l for l in body.splitlines() if p in l]
        named = {n for l in lines for n in re.findall(r"/([a-z0-9-]+)`?", l)}
        if any((siblings / n / p).exists() for n in named):
            continue
        if all(re.search(r"[├└│]", l) for l in lines):
            continue  # illustrative directory tree
        missing.append(f"{p} ({how})")
    if missing:
        F.append(find("ERROR", "E13-missing-file", "referenced but missing: " + ", ".join(missing), "PDF p13 'Reference bundled resources clearly', p30 Ref A; spec 'File references'"))
    return F


def main(argv):
    as_json = "--json" in argv
    dirs = [a for a in argv if a != "--json"]
    if not dirs:
        root = Path(__file__).resolve().parent.parent
        dirs = sorted(str(d) for d in root.iterdir() if (d / "SKILL.md").exists())
    report = {}
    for d in dirs:
        p = Path(d)
        report[p.name] = lint(p, p.name)
    if as_json:
        print(json.dumps(report, indent=1))
    else:
        for k, fs in report.items():
            status = "ok" if not any(f["severity"] == "ERROR" for f in fs) else "FAIL"
            print(f"{k}: {status}")
            for f in fs:
                print(f"  {f['severity']:5} {f['rule']}: {f['message']}  [{f['source']}]")
    sys.exit(1 if any(f["severity"] == "ERROR" for fs in report.values() for f in fs) else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
