"""Markdown, JSON and CSV exports for a syllabus review."""

from __future__ import annotations

import csv
import io
import json

SEVERITY_MARK = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}


def to_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def to_csv(result: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["section", "key", "value"])
    meta = result.get("meta", {})
    for key in ("course", "code", "term", "level", "credits", "weeks",
                "meetings_per_week", "minutes_per_meeting", "students",
                "start_date", "final_date"):
        if meta.get(key) not in (None, ""):
            writer.writerow(["course", key, meta[key]])
    writer.writerow(["score", "overall", result.get("score", {}).get("overall", 0)])
    writer.writerow(["score", "verdict", result.get("score", {}).get("verdict", "")])
    for axis, data in result.get("score", {}).get("axes", {}).items():
        writer.writerow(["axis", axis, f"{data['score']} (weight {data['weight']}%)"])
    for row in result.get("course_map", []):
        writer.writerow([
            "week", row["week"],
            "; ".join(row["topics"]) or "(no topic)",
            "; ".join(f"{a['name']} {a['weight']}%" for a in row["assessments"]) or "",
            ",".join(row["flags"]),
        ])
    for c in result.get("coverage", []):
        writer.writerow([
            "objective", c["id"], c["text"],
            ",".join(str(w) for w in c["taught_weeks"]),
            ",".join(c["assessed_by"]) or "NONE",
        ])
    for a in result.get("assessments", []):
        writer.writerow(["assessment", a["name"],
                         f"{a['weight']}%",
                         ",".join(str(w) for w in a["weeks"]) or "unscheduled",
                         ",".join(str(o) for o in a["objective_refs"])])
    for f in result.get("findings", []):
        writer.writerow(["finding", f["id"],
                         f"[{SEVERITY_MARK.get(f['severity'], f['severity'])}] {f['title']}",
                         f["axis"], f["evidence"], f["fix"]])
    for step in result.get("fix_plan", []):
        writer.writerow(["fix", step["id"], step["title"], step["severity"],
                         step["fix"], step["estimated_score_gain"]])
    return buf.getvalue()


def to_markdown(result: dict) -> str:
    meta = result.get("meta", {})
    score = result.get("score", {})
    lines = []
    lines.append(f"# Syllabus review: {meta.get('course', 'Untitled course')}")
    parts = [p for p in (meta.get("code"), meta.get("term"), meta.get("level")) if p]
    if parts:
        lines.append("")
        lines.append("*" + " | ".join(parts) + "*")
    lines.append("")
    lines.append(f"**Readiness: {score.get('overall', 0)}/100 - "
                 f"{score.get('verdict', '').replace('_', ' ')}**")
    lines.append("")
    lines.append("| Axis | Score | Weight |")
    lines.append("| --- | --- | --- |")
    for axis, data in score.get("axes", {}).items():
        lines.append(f"| {data['label']} | {data['score']} | {data['weight']}% |")
    lines.append("")

    caps = result.get("caps", [])
    if caps:
        lines.append("## Structural caps applied")
        lines.append("")
        for cap in caps:
            lines.append(f"- **{cap['axis']}** capped at {cap['cap']}: {cap['reason']}")
        lines.append("")

    findings = result.get("findings", [])
    lines.append(f"## Findings ({len(findings)})")
    lines.append("")
    if not findings:
        lines.append("No findings. The brief is clean on every axis checked.")
        lines.append("")
    for f in findings:
        lines.append(f"### [{SEVERITY_MARK.get(f['severity'], f['severity'])}] {f['title']}")
        lines.append("")
        lines.append(f"- **Axis:** {f['axis']}")
        lines.append(f"- **Evidence:** {f['evidence']}")
        lines.append(f"- **Why it matters:** {f['why']}")
        lines.append(f"- **Fix:** {f['fix']}")
        lines.append("")

    plan = result.get("fix_plan", [])
    lines.append("## Prioritised fix plan")
    lines.append("")
    if not plan:
        lines.append("Nothing to fix. The brief passes on every axis checked.")
        lines.append("")
    else:
        lines.append("| # | Finding | Severity | Est. score gain | Fix |")
        lines.append("| --- | --- | --- | --- | --- |")
        for i, step in enumerate(plan, 1):
            lines.append(f"| {i} | {step['title']} | {step['severity']} | "
                         f"+{step['estimated_score_gain']} | {step['fix']} |")
        lines.append("")

    coverage = result.get("coverage", [])
    if coverage:
        lines.append("## Objective coverage")
        lines.append("")
        lines.append("| # | Objective | Taught in weeks | Assessed by |")
        lines.append("| --- | --- | --- | --- |")
        for c in coverage:
            taught = ", ".join(str(w) for w in c["taught_weeks"]) or "**never**"
            assessed = ", ".join(c["assessed_by"]) or "**never**"
            lines.append(f"| {c['id']} | {c['text']} | {taught} | {assessed} |")
        lines.append("")

    course_map = result.get("course_map", [])
    if course_map:
        lines.append("## Course map")
        lines.append("")
        lines.append("| Week | Topics | Assessments due | Flags |")
        lines.append("| --- | --- | --- | --- |")
        for row in course_map:
            topics = "; ".join(row["topics"]) or ("_no topic_" if "no_topic" in row["flags"] else "-")
            due = "; ".join(f"{a['name']} ({a['weight']}%)" for a in row["assessments"]) or "-"
            lines.append(f"| {row['week']} | {topics} | {due} | {', '.join(row['flags'])} |")
        lines.append("")

    syllabus = result.get("syllabus", "")
    if syllabus:
        lines.append("---")
        lines.append("")
        lines.append("## Generated syllabus draft")
        lines.append("")
        lines.append(syllabus)
    return "\n".join(lines)
