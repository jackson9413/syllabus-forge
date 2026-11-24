"""Syllabus Forge - course design and syllabus readiness engine.

Pure standard library. No API keys, no network calls, no LLM.

The engine takes a course brief (metadata, learning objectives, weekly topics,
assessments, policies) and produces:
  * a week-by-week course map with load and collision flags
  * an objective/assessment/topic alignment matrix
  * a five-axis 0-100 readiness scorecard with structural caps
  * a prioritised fix plan with estimated score gain
  * a generated syllabus document with explicit TODO markers
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field, asdict

# --------------------------------------------------------------------------
# data model
# --------------------------------------------------------------------------


@dataclass
class Objective:
    id: int
    text: str
    topic_weeks: list[int] = field(default_factory=list)
    assessed_refs: list[str] = field(default_factory=list)


@dataclass
class Topic:
    week: int
    title: str
    objective_refs: list[int] = field(default_factory=list)


@dataclass
class Assessment:
    name: str
    count: int = 1
    weight: float = 0.0
    weeks: list[int] = field(default_factory=list)
    objective_refs: list[int] = field(default_factory=list)


@dataclass
class Brief:
    meta: dict = field(default_factory=dict)
    objectives: list[Objective] = field(default_factory=list)
    topics: list[Topic] = field(default_factory=list)
    assessments: list[Assessment] = field(default_factory=list)
    policies: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class Finding:
    id: str
    axis: str
    severity: str          # critical | high | medium | low
    title: str
    evidence: str
    why: str
    fix: str

    def to_dict(self) -> dict:
        return asdict(self)


AXES = {
    "alignment": "Alignment",
    "assessment": "Assessment design",
    "pacing": "Pacing",
    "policy": "Policy completeness",
    "logistics": "Logistics",
}

AXIS_WEIGHTS = {
    "alignment": 25,
    "assessment": 20,
    "pacing": 20,
    "policy": 20,
    "logistics": 15,
}

# profile -> axis weight overrides (must sum to 100)
PROFILES = {
    "general": {"alignment": 25, "assessment": 20, "pacing": 20, "policy": 20, "logistics": 15},
    "alignment_audit": {"alignment": 50, "assessment": 15, "pacing": 15, "policy": 10, "logistics": 10},
    "assessment_audit": {"alignment": 20, "assessment": 45, "pacing": 10, "policy": 15, "logistics": 10},
    "pacing_audit": {"alignment": 15, "assessment": 15, "pacing": 45, "policy": 15, "logistics": 10},
    "policy_audit": {"alignment": 15, "assessment": 15, "pacing": 10, "policy": 50, "logistics": 10},
    "logistics_audit": {"alignment": 10, "assessment": 10, "pacing": 20, "policy": 10, "logistics": 50},
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_DEDUCTION = {"critical": 26, "high": 15, "medium": 7, "low": 3}

MEASURABLE_VERBS = {
    "apply", "analyze", "analyse", "implement", "evaluate", "design", "construct",
    "derive", "compare", "explain", "demonstrate", "solve", "build", "create",
    "use", "interpret", "predict", "classify", "compute", "translate", "plan",
    "produce", "formulate", "calculate", "identify", "justify", "estimate",
}
VAGUE_VERBS = {
    "understand", "know", "knowing", "be aware of", "be familiar with", "appreciate",
    "learn", "expose", "exposed to", "grasp", "see", "recognize", "recognise",
}

REQUIRED_POLICIES = [
    ("grading scale", "Grading scale", "high",
     "Students cannot predict what a grade means. Every course needs a stated scale "
     "or a clear reference to the institutional scale.",
     "Add a Grading policy section that spells out the letter scale and its thresholds, "
     "or states exactly where the institutional scale lives."),
    ("academic integrity", "Academic integrity policy", "high",
     "Integrity expectations are the single most-referenced policy in course complaints. "
     "Without one, the default is whatever the student assumes.",
     "Add an Academic Integrity section naming the policy, how it is enforced, and what "
     "the consequences are."),
    ("ai", "AI use policy", "high",
     "Students and administrators both expect an explicit statement on generative AI. "
     "Silence reads as permission, and that reading is not enforceable.",
     "Add an AI Use section stating what is allowed, what is not, and how to disclose use."),
    ("accommodation", "Accommodations / disability services", "high",
     "Accommodation procedures are a legal and accessibility requirement in most "
     "institutions. Leaving them out strands students who need them.",
     "Add an Accommodations section pointing at the disability services office, the "
     "contact route, and how confidential documentation is handled."),
    ("late work", "Late work policy", "medium",
     "Without a late policy, every late submission becomes a one-off negotiation "
     "between instructor and student.",
     "Add a Late Work section with the penalty per day, the maximum window, and what "
     "happens after that window closes."),
    ("attendance", "Attendance policy", "medium",
     "Attendance drives participation and accommodation decisions. Leaving it undefined "
     "means the instructor has no stated basis for the call.",
     "Add an Attendance section saying whether attendance is required, how absences are "
     "excused, and any participation grade that depends on it."),
    ("participation", "Participation policy", "medium",
     "Participation is graded in most syllabi yet rarely defined, which produces "
     "recurring grade disputes.",
     "Add a Participation section defining what participation means and how it is "
     "assessed."),
    ("drop", "Drop / withdrawal deadline", "medium",
     "Withdrawal deadlines and their consequences are exactly what students need at the "
     "start of term, not mid-semester.",
     "Add a Drop deadline section with the date and the consequence of missing it."),
    ("makeup", "Make-up / missed work policy", "medium",
     "Illness and emergencies happen. A stated make-up route converts an awkward "
     "conversation into a procedure.",
     "Add a Make-up Work section stating how missed sessions and assessments are handled."),
    ("final exam", "Final exam information", "medium",
     "Students need the final's date, format, weight and coverage before the term ends.",
     "Add a Final Exam section with the date, time, format, and what it covers."),
    ("textbook", "Required text / materials", "low",
     "Materials affect cost and access. Publishing them early helps students plan.",
     "Add a Required Materials section listing the text, edition, and any other required "
     "materials with ISBNs where possible."),
    ("office hours", "Office hours / contact", "low",
     "Published contact hours are the cheapest support mechanism a course has.",
     "Add an Office Hours and Contact section with times, location, and a response-time "
     "expectation."),
]

# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

SECTION_ALIASES = {
    "course": "course", "course info": "course", "meta": "course", "info": "course",
    "objectives": "objectives", "outcomes": "objectives", "learning outcomes": "objectives",
    "goals": "objectives", "objectives and outcomes": "objectives",
    "topics": "topics", "schedule": "topics", "weeks": "topics", "calendar": "topics",
    "assessments": "assessments", "grading": "assessments", "evaluation": "assessments",
    "policies": "policies", "policy": "policies", "rules": "policies",
    "notes": "notes", "comments": "notes",
}

SECTION_HEADER_RE = re.compile(r"^\s*\[\s*([A-Za-z0-9 _\-]+?)\s*\]\s*$")
WEEK_LINE_RE = re.compile(r"^\s*(?:week\s*)?(\d{1,2})\b\s*[|:\-–]?\s*(.*)$", re.IGNORECASE)
KV_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _/\-\(\.\)\'\&]{0,45}?)\s*[:=]\s*(.+?)\s*$")
LIST_MARK_RE = re.compile(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)")
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def _clean(line: str) -> str:
    return line.replace("\t", " ").rstrip()


def parse_week_list(text: str) -> list[int]:
    """'1-14' -> [1..14]; '1,3,5' -> [1,3,5]; 'week 12' -> [12]."""
    if not text:
        return []
    text = text.strip().lower().replace("week", " ")
    weeks: list[int] = []
    for chunk in re.split(r"[,\s]+", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"^(\d{1,2})\s*[-–:]\s*(\d{1,2})$", chunk)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if hi < lo:
                lo, hi = hi, lo
            weeks.extend(range(lo, hi + 1))
            continue
        if chunk.isdigit():
            weeks.append(int(chunk))
    return sorted(set(w for w in weeks if w > 0))


def _split_pipes(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\|", text)]
    return [p for p in parts if p != ""]


def parse_brief(text: str) -> Brief:
    brief = Brief()
    if not text or not text.strip():
        return brief

    section = "course"
    obj_counter = 0
    for raw in text.splitlines():
        line = _clean(raw)
        if not line.strip():
            continue
        if line.strip().startswith("#") or line.strip().startswith("//"):
            continue
        m = SECTION_HEADER_RE.match(line)
        if m:
            key = SECTION_ALIASES.get(m.group(1).strip().lower(), m.group(1).strip().lower())
            section = key if key in ("course", "objectives", "topics", "assessments", "policies", "notes") else "course"
            continue

        if section == "notes":
            brief.notes.append(line.strip())
            continue

        if section == "objectives":
            body = LIST_MARK_RE.sub("", line).strip()
            if not body:
                continue
            obj_counter += 1
            parts = _split_pipes(body)
            text_part = parts[0] if parts else body
            topic_weeks: list[int] = []
            assessed: list[str] = []
            for part in parts[1:]:
                low = part.lower()
                if low.startswith(("topic", "topics", "wk", "week", "weeks")):
                    topic_weeks += parse_week_list(part.split(":", 1)[-1])
                elif low.startswith(("assessed", "assess", "via", "eval", "measured")):
                    assessed.append(part.split(":", 1)[-1].strip())
            brief.objectives.append(Objective(id=obj_counter, text=text_part,
                                             topic_weeks=topic_weeks,
                                             assessed_refs=assessed))
            continue

        if section == "topics":
            m = WEEK_LINE_RE.match(line)
            if not m:
                brief.notes.append("unparsed topic line: " + line.strip())
                continue
            week = int(m.group(1))
            rest = m.group(2).strip()
            rest = LIST_MARK_RE.sub("", rest)
            parts = _split_pipes(rest)
            title = parts[0] if parts else rest
            obj_refs: list[int] = []
            for part in parts[1:]:
                low = part.lower()
                if low.startswith(("obj", "objective", "outcomes", "covers")):
                    for token in re.findall(r"\d+", part.split(":", 1)[-1]):
                        obj_refs.append(int(token))
            brief.topics.append(Topic(week=week, title=title, objective_refs=obj_refs))
            continue

        if section == "assessments":
            parts = _split_pipes(LIST_MARK_RE.sub("", line).strip())
            if not parts:
                continue
            name = parts[0]
            count = 1
            weight = 0.0
            weeks: list[int] = []
            obj_refs: list[int] = []
            for part in parts[1:]:
                low = part.lower()
                pct = PCT_RE.search(part)
                if pct and "week" not in low:
                    weight = float(pct.group(1))
                    continue
                if low.startswith(("week", "wk", "due", "dates")):
                    weeks += parse_week_list(part.split(":", 1)[-1])
                    continue
                if low.startswith(("obj", "objective", "covers", "assesses")):
                    for token in re.findall(r"\d+", part.split(":", 1)[-1]):
                        obj_refs.append(int(token))
                    continue
                if part.strip().isdigit():
                    count = int(part.strip())
                    continue
            brief.assessments.append(Assessment(name=name, count=count, weight=weight,
                                                 weeks=weeks, objective_refs=obj_refs))
            continue

        if section == "policies":
            m = KV_RE.match(line)
            if m:
                brief.policies[m.group(1).strip().lower()] = m.group(2).strip()
            else:
                brief.policies[f"policy {len(brief.policies) + 1}"] = line.strip()
            continue

        # course section
        m = KV_RE.match(line)
        if m:
            brief.meta[m.group(1).strip().lower()] = m.group(2).strip()
        else:
            brief.notes.append("unparsed course line: " + line.strip())

    return brief


def _meta_num(meta: dict, *keys, cast=float):
    for key in keys:
        for candidate in (key, key.replace("_", " ")):
            if candidate in meta and str(meta[candidate]).strip():
                raw = str(meta[candidate]).strip().rstrip("%")
                try:
                    return cast(raw)
                except ValueError:
                    continue
    return None


def _meta_date(meta: dict, *keys):
    for key in keys:
        for candidate in (key, key.replace("_", " ")):
            if candidate in meta and str(meta[candidate]).strip():
                try:
                    return dt.date.fromisoformat(str(meta[candidate]).strip()[:10])
                except ValueError:
                    continue
    return None


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _is_exam(name: str) -> bool:
    """High-stakes, single-sitting assessments only (quizzes are low-stakes)."""
    low = name.lower()
    return any(k in low for k in ("midterm", "final exam", "exam", "final"))


def _is_quiz(name: str) -> bool:
    low = name.lower()
    return "quiz" in low or "test" in low or "pop quiz" in low


def _is_project(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in ("project", "portfolio", "capstone", "thesis", "lab report"))


def _is_participation(name: str) -> bool:
    low = name.lower()
    return "participation" in low or "attendance" in low or "engagement" in low


def _is_homework(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in ("homework", "assignment", "problem set", "pset", "worksheet"))


def _is_generic_activity(name: str) -> bool:
    """Recurring learning activities that legitimately serve every objective."""
    low = name.lower()
    return any(k in low for k in (
        "homework", "assignment", "problem set", "pset", "worksheet", "quiz", "test",
        "participation", "attendance", "engagement", "discussion", "journal", "reading",
        "lab", "problem", "exercise",
    ))


def _is_recurring(assessment) -> bool:
    """An assessment spread over many occurrences is load, not a scheduling collision."""
    return assessment.count > 1 or len(assessment.weeks) > 3


REVIEW_WORDS = ("review", "synthesis", "integration", "wrap", "revision", "recap",
                "culminat", "capstone showcase", "final showcase", "preparation")


def _is_review_topic(title: str) -> bool:
    low = title.lower()
    return any(w in low for w in REVIEW_WORDS)


def _policy_present(blob: str, key: str) -> bool:
    """Word-boundary policy detection so 'ai' does not match 'maintain'."""
    if key == "ai":
        return bool(re.search(r"\bai\b|generative|chatgpt|\bllm\b|artificial intelligence",
                               blob))
    if key == "late work":
        return bool(re.search(r"\blate\b", blob))
    if key == "attendance":
        return bool(re.search(r"\battendance\b|\babsen", blob))
    if key == "final exam":
        return bool(re.search(r"\bfinal\b", blob))
    if key == "textbook":
        return bool(re.search(r"\btext ?books?\b|required materials?\b", blob))
    if key == "grading scale":
        return bool(re.search(r"\bgrading scale\b|\bletter scale\b|grade scale", blob))
    if key == "academic integrity":
        return bool(re.search(r"academic integrity|\bintegrity\b", blob))
    if key == "accommodation":
        return bool(re.search(r"accommodat|disabilit|accessib", blob))
    if key == "participation":
        return bool(re.search(r"\bparticipation\b", blob))
    if key == "drop":
        return bool(re.search(r"\bdrop\b|withdraw", blob))
    if key == "makeup":
        return bool(re.search(r"make[- ]?up|missed work", blob))
    if key == "office hours":
        return bool(re.search(r"office hours|\boffice\b", blob))
    return bool(re.search(r"\b" + re.escape(key) + r"\b", blob))


def _keyword_overlap(a: str, b: str) -> float:
    stop = {
        "the", "a", "an", "of", "and", "or", "to", "in", "for", "with", "on", "by",
        "as", "at", "is", "are", "be", "that", "this", "these", "those", "will",
        "students", "student", "course", "students", "using", "use", "from",
    }
    aw = {w for w in re.findall(r"[a-z]{3,}", a.lower()) if w not in stop}
    bw = {w for w in re.findall(r"[a-z]{3,}", b.lower()) if w not in stop}
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / float(len(aw))


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------


def analyse(brief: Brief, profile: str = "general", today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    weights = PROFILES.get(profile, PROFILES["general"])
    findings: list[Finding] = []

    weeks = int(_meta_num(brief.meta, "weeks", "length", "term weeks", "class weeks", cast=int) or 0)
    credits = _meta_num(brief.meta, "credits", "credit hours", "credit", "units")
    meetings = _meta_num(brief.meta, "meetings per week", "meetings", "sessions per week",
                          "classes per week", "meetings_per_week", cast=float)
    minutes = _meta_num(brief.meta, "minutes per meeting", "minutes", "class length",
                         "minutes_per_meeting", "period minutes")
    students = _meta_num(brief.meta, "students", "enrollment", "enrolment", "class size",
                          "students enrolled", cast=float)
    start_date = _meta_date(brief.meta, "start", "start date", "first class", "term start")
    final_date = _meta_date(brief.meta, "final exam", "final date", "finals", "final exam date",
                             "final", "end date")
    level = str(brief.meta.get("level", "")).strip().lower()

    objectives = brief.objectives
    topics = brief.topics
    assessments = brief.assessments
    policies = brief.policies

    total_weight = sum(a.weight for a in assessments)
    topic_weeks = sorted({t.week for t in topics})
    max_topic_week = max(topic_weeks) if topic_weeks else 0
    max_assess_week = max((w for a in assessments for w in a.weeks), default=0)

    # ---------------- alignment ----------------
    # resolve which assessments cover which objectives (explicit first, keyword fallback)
    coverage = []
    for obj in objectives:
        taught_weeks = set(obj.topic_weeks)
        for topic in topics:
            if obj.id in topic.objective_refs:
                taught_weeks.add(topic.week)
        assessed_by = []
        for a in assessments:
            explicit = False
            for ref in obj.assessed_refs:
                ref_l = ref.strip().lower()
                if ref_l == str(obj.id) or ref_l in a.name.lower():
                    explicit = True
            if explicit or obj.id in a.objective_refs:
                assessed_by.append(a.name)
        inferred = False
        if not assessed_by:
            best, best_score = None, 0.0
            for a in assessments:
                score = _keyword_overlap(obj.text, a.name)
                if score > best_score:
                    best, best_score = a, score
            if best is not None and best_score >= 0.34:
                assessed_by = [best.name]
                inferred = True
        coverage.append({
            "id": obj.id,
            "text": obj.text,
            "taught_weeks": sorted(taught_weeks),
            "assessed_by": assessed_by,
            "inferred": inferred,
            "taught": bool(taught_weeks),
            "assessed": bool(assessed_by),
        })

    if not objectives:
        findings.append(Finding(
            "A1", "alignment", "critical",
            "No learning objectives to align against",
            "The brief lists no objectives (no [Objectives] section and no objective lines).",
            "Without outcomes there is nothing for the assessments to serve, nothing for the "
            "schedule to sequence, and no way to answer 'what should a graduate of this course "
            "be able to do'. It also makes the course impossible to review for accreditation.",
            "Add 4-8 learning objectives as measurable verbs (implement, analyze, evaluate, "
            "design). One per major topic cluster is the usual shape.",
        ))

    unassessed = [c for c in coverage if c["taught"] and not c["assessed"]]
    for c in unassessed:
        findings.append(Finding(
            "A2", "alignment", "high",
            f"Objective {c['id']} is taught but never assessed",
            f"\"{c['text']}\" is scheduled in week(s) "
            f"{', '.join(str(w) for w in c['taught_weeks']) or 'unknown'} but no assessment "
            f"references it.",
            "An objective that is taught but never measured is an unfulfilled promise to the "
            "student, to the department, and to anyone reading the transcript. It is also the "
            "most common finding in an actual course review.",
            f"Attach at least one assessment to objective {c['id']} (a quiz item, a homework "
            f"problem, or a rubric line on an existing project).",
        ))

    untaught = [c for c in coverage if not c["taught"] and c["assessed"]]
    for c in untaught:
        findings.append(Finding(
            "A3", "alignment", "high",
            f"Objective {c['id']} is assessed but never taught",
            f"\"{c['text']}\" is referenced by an assessment but no topic week is tagged to it.",
            "Students are being tested on something the schedule never delivered. This reads as "
            "an unfair test to students and is a straightforward accreditation finding.",
            f"Tag a topic week to objective {c['id']}, or drop the objective if it no longer "
            f"belongs to the course.",
        ))

    if objectives:
        tagged_topics = sum(1 for t in topics if t.objective_refs)
        if topics and tagged_topics == 0:
            findings.append(Finding(
                "A4", "alignment", "medium",
                "No topic is tagged to an objective",
                f"All {len(topics)} topic weeks carry no objective reference.",
                "The schedule and the outcomes are two disconnected lists, so nobody can check "
                "that the term actually delivers what it promises. This is how weeks end up "
                "teaching material no outcome needs.",
                "Tag topic weeks to objectives (obj 1, obj 2) so coverage can be traced.",
            ))

        if len(objectives) > max(1, len(topics)):
            findings.append(Finding(
                "A5", "alignment", "medium",
                "More objectives than topic weeks can carry",
                f"{len(objectives)} objectives across {len(topics)} topic weeks.",
                "More outcomes than the term has room for usually means the outcomes are worded "
                "too broadly and will all be assessed shallowly, or that the scope is larger "
                "than the contact hours allow.",
                "Consolidate related outcomes, or widen the topic list so each outcome has at "
                "least two weeks to land.",
            ))

        weak = [c for c in coverage if not c["taught"]]
        if len(weak) == len(coverage) and coverage:
            findings.append(Finding(
                "A6", "alignment", "high",
                "No objective maps to any week of the schedule",
                f"None of the {len(coverage)} objectives resolve to a topic week.",
                "The course map and the outcomes are fully disconnected. Coverage cannot be "
                "demonstrated to a reviewer.",
                "Tag objective to topic weeks, or add the topic weeks that deliver them.",
            ))

        for c in coverage:
            first = re.findall(r"\b([a-z]+)\b", c["text"].lower())
            head = first[0] if first else ""
            if head in VAGUE_VERBS:
                findings.append(Finding(
                    "A7", "alignment", "medium",
                    f"Objective {c['id']} starts with a non-measurable verb",
                    f"\"{c['text']}\" begins with \"{head}\".",
                    "Verbs like understand, know and appreciate describe a feeling of "
                    "familiarity, not a performance a student can demonstrate or an assessor "
                    "can grade. Faculty reviewers push back on these specifically.",
                    "Rewrite with a measurable verb: \"explain\", \"compute\", \"compare and "
                    "justify\", \"design and implement\".",
                ))
                break

    for a in assessments:
        if _is_generic_activity(a.name):
            continue
        aligned = any(c["id"] in a.objective_refs or a.name in c["assessed_by"] for c in coverage)
        if not aligned and objectives:
                findings.append(Finding(
                    "A8", "alignment", "high",
                    f"Assessment \"{a.name}\" is not aligned to any objective",
                    f"No objective references {a.name}, and no objective keyword-matches it.",
                    "Assessment time is the most expensive thing in the course. If it serves no "
                    "outcome, it is pure overhead for the student and unexplained weight for the "
                    "department.",
                    f"Tag {a.name} to the objective(s) it actually measures.",
                ))

    # ---------------- assessment design ----------------
    if not assessments:
        findings.append(Finding(
            "S1", "assessment", "critical",
            "No assessments defined",
            "The brief has no assessment entries.",
            "A course with no stated assessments has no grade, no feedback mechanism and no "
            "defensible answer to 'how do you know they learned it'.",
            "Add at least three assessments with weights that sum to 100: something low-stakes "
            "and frequent, one mid-term style piece, and a substantial final project or exam.",
        ))
    else:
        if abs(total_weight - 100.0) > 0.6:
            findings.append(Finding(
                "S2", "assessment", "critical",
                f"Assessment weights sum to {total_weight:g}%, not 100%",
                " + ".join(f"{a.name} {a.weight:g}%" for a in assessments) + f" = {total_weight:g}%.",
                "Weights that do not sum to 100 leave the grade undefined. It is the first "
                "thing a student finds and it undermines confidence in every other number in "
                "the syllabus.",
                "Rebalance to exactly 100%. The fix plan shows the adjusted weights to paste.",
            ))

        for a in assessments:
            if a.weight <= 0:
                findings.append(Finding(
                    "S3", "assessment", "high",
                    f"\"{a.name}\" carries 0% of the grade",
                    f"Weight recorded as {a.weight:g}%.",
                    "An assessment with zero weight is either dead weight on the students' time "
                    "or a weighting mistake that silently removes it from the grade.",
                    f"Give {a.name} a real weight and rebalance the rest to 100%.",
                ))
            elif a.weight > 40:
                findings.append(Finding(
                    "S4", "assessment", "high",
                    f"\"{a.name}\" is {a.weight:g}% of the final grade",
                    f"Single assessment weight {a.weight:g}%, count {a.count}.",
                    "Anything above roughly 40% lets one sitting decide the course grade, "
                    "which is hard to recover from for the student and hard to defend at "
                    "review.",
                    "Split it into components or shift weight to coursework so no single item "
                    "exceeds 35-40%.",
                ))

        exam_weight = sum(a.weight for a in assessments if _is_exam(a.name))
        if exam_weight > 60:
            findings.append(Finding(
                "S5", "assessment", "high",
                f"Exam-style work is {exam_weight:g}% of the grade",
                ", ".join(f"{a.name} {a.weight:g}%" for a in assessments if _is_exam(a.name)),
                "Heavy exam weighting rewards cramming over learning and is the single most "
                "common complaint about a course's assessment design.",
                "Move 10-20 points from exams into continuous coursework (projects, labs, "
                "written work) and keep exams as a check rather than the verdict.",
            ))

        names = [a.name.strip().lower() for a in assessments]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            findings.append(Finding(
                "S6", "assessment", "medium",
                "Duplicate assessment names",
                ", ".join(dupes),
                "Duplicate names make the grade breakdown ambiguous: a student cannot tell "
                "which 'Homework' set counts toward which line.",
                "Give each assessment a unique label (Homework 1, Homework 2) or fold the "
                "duplicates into a single line with a count.",
            ))

        if len(assessments) < 3:
            findings.append(Finding(
                "S7", "assessment", "high",
                f"Only {len(assessments)} assessment(s) in the whole course",
                ", ".join(a.name for a in assessments),
                "With one or two assessments the grade is decided by almost no information, and "
                "students get almost no feedback while the term is still running.",
                "Add a frequent low-stakes component so students get feedback before the "
                "midpoint.",
            ))

        participation = [a for a in assessments if _is_participation(a.name)]
        if participation:
            pw = sum(a.weight for a in participation)
            if pw > 12:
                findings.append(Finding(
                    "S8", "assessment", "medium",
                    f"Participation is {pw:g}% of the grade",
                    ", ".join(f"{a.name} {a.weight:g}%" for a in participation),
                    "Participation grades above roughly 10% are a frequent source of "
                    "student complaints, because attendance alone does not equal participation "
                    "and the criteria are usually left unwritten.",
                    "Either drop it to 5% or state the criteria precisely and sample the grade "
                    "so it is defensible.",
                ))
            elif pw == 0:
                findings.append(Finding(
                    "S9", "assessment", "medium",
                    "Participation named but weighted at 0%",
                    ", ".join(a.name for a in participation),
                    "If participation is worth nothing, drop it from the grade breakdown so "
                    "students do not attend expecting credit.",
                    "Remove it, or give it a small defined weight (3-5%) and write the criteria.",
                ))

        projects = [a for a in assessments if _is_project(a.name)]
        if not projects and (credits is None or credits >= 3):
            findings.append(Finding(
                "S10", "assessment", "medium",
                "No project, portfolio or capstone in the course",
                f"Assessments: {', '.join(a.name for a in assessments)}.",
                "Courses with no sustained artifact are hard to assess authentically and leave "
                "students with nothing to show an employer. Reviewers increasingly expect a "
                "project at the 3-credit level and above.",
                "Add a term project with a rubric, weighted 15-25%, with checkpoints rather than "
                "a single due date.",
            ))

        homework = [a for a in assessments if _is_homework(a.name)]
        hw_count = sum(max(1, a.count) for a in homework)
        if homework and weeks and hw_count < max(3, weeks - 4):
            findings.append(Finding(
                "S11", "assessment", "medium",
                f"Only {hw_count} homework assignments across {weeks} weeks",
                ", ".join(f"{a.name} (count {a.count})" for a in homework),
                "Sparse homework means long feedback gaps, which is exactly when students "
                "stop reading the material and coast into the final.",
                "One short assignment or quiz every one to two weeks keeps the feedback loop "
                "short.",
            ))

        quizzes = [a for a in assessments if _is_quiz(a.name)]
        if not quizzes and not homework and len(assessments) <= 3:
            findings.append(Finding(
                "S12", "assessment", "medium",
                "No low-stakes check during the term",
                ", ".join(a.name for a in assessments),
                "Without a frequent low-stakes component the first real measurement arrives "
                "too late for the student to act on.",
                "Add a weekly quiz worth 5-10% of the grade.",
            ))

        for a in assessments:
            if not a.weeks:
                findings.append(Finding(
                    "S13", "assessment", "high",
                    f"\"{a.name}\" has no scheduled week",
                    f"Weight {a.weight:g}%, count {a.count}, no week information.",
                    "An assessment with no date is an assessment students will miss and then "
                    "argue about. The schedule and the grade breakdown have to agree.",
                    f"Give {a.name} a due week (or a week range).",
                ))

    # ---------------- pacing ----------------
    if weeks <= 0:
        findings.append(Finding(
            "P1", "pacing", "critical",
            "No term length declared",
            "No Weeks / length field found in the course section.",
            "Without a term length the whole course map is unverifiable: there is no way to know "
            "whether the material fits, whether an exam sits in the right place, or whether the "
            "schedule has a gap.",
            "Add 'Weeks: 15' (or your institution's term length).",
        ))
        weeks = max(topic_weeks) if topic_weeks else 15

    effective_term = weeks
    gap_weeks = [w for w in range(1, effective_term + 1) if w not in topic_weeks]
    if gap_weeks and topic_weeks:
        preview = ", ".join(str(w) for w in gap_weeks[:8]) + ("..." if len(gap_weeks) > 8 else "")
        findings.append(Finding(
            "P2", "pacing", "high",
            f"{len(gap_weeks)} week(s) of the term have no topic",
            f"Unscheduled weeks: {preview}",
            "Gaps in the schedule read as 'nothing is happening', and students reliably use "
            "them as the week they fall behind. Unplanned gap weeks are also where the "
            "mid-term creeps forward unnoticed.",
            "Fill every gap with a topic, a review session, or explicitly label it as a catch-up "
            "week in the published schedule.",
        ))

    over_week = max(topic_weeks) if topic_weeks else 0
    if over_week > effective_term:
        findings.append(Finding(
            "P3", "pacing", "high",
            f"Topics run to week {over_week} but the term is {effective_term} weeks",
            f"Highest topic week is {over_week}.",
            "Content scheduled past the end of term will not be taught before the final, which "
            "means the final covers material the class never saw.",
            f"Either extend the term to {over_week} weeks or compress the topics into weeks "
            f"1-{effective_term}.",
        ))

    per_week = {}
    for t in topics:
        per_week.setdefault(t.week, []).append(t.title)
    for week in sorted(per_week):
        if len(per_week[week]) >= 4:
            findings.append(Finding(
                "P4", "pacing", "medium",
                f"Week {week} carries {len(per_week[week])} topics",
                "; ".join(per_week[week][:5]),
                "Four or more new topics in one week is beyond what most students can absorb in "
                "two sessions, and it is the week that generates the questions that get "
                "answered on the exam.",
                "Move one topic to the following week, or split the week into a deeper first "
                "half and an applied second half.",
            ))
            break

    exam_assessments = [a for a in assessments if _is_exam(a.name) and "final" not in a.name.lower()]
    for a in exam_assessments:
        if not a.weeks:
            continue
        first_week = min(a.weeks)
        pos = first_week / float(effective_term)
        if pos < 0.32:
            findings.append(Finding(
                "P5", "pacing", "high",
                f"{a.name} sits at week {first_week} ({pos * 100:.0f}% of the term)",
                f"{a.name} due week {first_week} of {effective_term}.",
                "An exam before roughly a third of the term tests a narrow slice of the "
                "course and gives students an early, misleading signal about how they are "
                "doing.",
                "Move it later, around 40-55% of the term, once the core content is covered.",
            ))
        elif pos > 0.72:
            findings.append(Finding(
                "P6", "pacing", "high",
                f"{a.name} sits at week {first_week} ({pos * 100:.0f}% of the term)",
                f"{a.name} due week {first_week} of {effective_term}.",
                "Two major exams close together leave no recovery window: one bad week "
                "destroys two results.",
                "Move it earlier or spread the two exams at least three weeks apart.",
            ))

    final_week_topics = [t for t in per_week.get(effective_term, []) if not _is_review_topic(t)]
    if final_week_topics:
        findings.append(Finding(
            "P7", "pacing", "high",
            f"New content in the final week (week {effective_term})",
            "; ".join(final_week_topics[:4]),
            "Teaching new material in the last week leaves no time to practise it, and the "
            "final will cover it anyway.",
            "Move the content earlier and use the final week for review and the exam.",
        ))

    last_quarter = [w for w in range(1, effective_term + 1) if w > effective_term * 0.75]
    if last_quarter and topic_weeks:
        late_topics = [w for w in last_quarter if w in topic_weeks]
        share = len(late_topics) / float(len(topic_weeks))
        if share > 0.4:
            findings.append(Finding(
                "P8", "pacing", "medium",
                f"{share * 100:.0f}% of the topics land in the last quarter",
                f"{len(late_topics)} of {len(topic_weeks)} topic weeks fall in weeks "
                f"{min(last_quarter)}-{effective_term}.",
                "A back-loaded term means the final two weeks are consumed by new material "
                "instead of consolidation, and the students who fell behind have no recovery "
                "time at all.",
                "Move the densest topic blocks into the middle of the term and keep the final "
                "quarter lighter.",
            ))

    assess_by_week = {}
    for a in assessments:
        for w in a.weeks:
            assess_by_week.setdefault(w, []).append(a)
    for week in sorted(assess_by_week):
        items = [a for a in assess_by_week[week] if not _is_recurring(a)]
        weight_here = sum(a.weight for a in items)
        if len(items) >= 2 and weight_here >= 25:
            findings.append(Finding(
                "P9", "pacing", "medium",
                f"Week {week} stacks {len(items)} assessments worth {weight_here:g}%",
                "; ".join(f"{a.name} ({a.weight:g}%)" for a in items),
                "Stacking heavy assessments in one week creates a spike that students plan "
                "around, and it is the single most common source of 'the schedule is "
                "impossible' feedback.",
                "Move one of them by a week or two.",
            ))

    heavy_back = 0.0
    for a in assessments:
        if not a.weeks:
            continue
        late = [w for w in a.weeks if w > effective_term * 0.75]
        if late and len(a.weeks) > 1:
            heavy_back += a.weight * (len(late) / float(len(a.weeks)))
    if heavy_back > 35:
        findings.append(Finding(
            "P10", "pacing", "medium",
            f"{heavy_back:g}% of the grade is assessed in the last quarter",
            "Substantial weight falls on late-term assessment weeks.",
            "Late-weighted courses give students no chance to recover from a bad stretch, and "
            "they make the last third of term the only part that matters.",
            "Shift some weight to coursework that is completed earlier in the term.",
        ))

    if weeks and topic_weeks and len(topic_weeks) < weeks * 0.6:
        findings.append(Finding(
            "P11", "pacing", "medium",
            f"Only {len(topic_weeks)} of {weeks} weeks carry a topic",
            f"Term length {weeks} weeks, {len(topic_weeks)} topic weeks.",
            "The term looks under-filled relative to its length. Either there is slack to "
            "compress the course, or substantial topics are missing from the plan.",
            "Either compress the term or add the missing topic weeks - do not leave the "
            "published schedule thinner than the time you have.",
        ))

    # ---------------- policy ----------------
    missing_policies: list[tuple[str, str]] = []
    if not policies:
        findings.append(Finding(
            "Q1", "policy", "high",
            "No policies section at all",
            "The brief contains no [Policies] entries.",
            "Every course needs the standard policy set. Students will ask for it anyway, and "
            "an absent policy section is read as an absent policy.",
            "Add the policies below; the generated syllabus includes them as ready-to-paste "
            "stubs.",
        ))
    else:
        policy_blob = " ".join(f"{k} {v}" for k, v in policies.items()).lower()
        for key, label, severity, why, fix in REQUIRED_POLICIES:
            if _policy_present(policy_blob, key):
                continue
            missing_policies.append((label, severity))
            findings.append(Finding(
                "Q2", "policy", severity,
                f"Missing policy: {label}",
                f"No {key} entry found among {len(policies)} policy line(s).",
                why, fix,
            ))

        late_keys = [k for k in policies if "late" in k or "late" in str(policies[k]).lower()]
        if late_keys:
            blob = " ".join(str(policies[k]) for k in late_keys).lower()
            if not any(t in blob for t in ("%", "percent", "day", "hour", "24", "48")):
                findings.append(Finding(
                    "Q3", "policy", "medium",
                    "Late work policy has no penalty defined",
                    " | ".join(f"{k}: {policies[k]}" for k in late_keys),
                    "A late policy without a penalty is not a policy; it just moves the decision "
                    "to the moment a student hands in late.",
                    "State the penalty per day and the maximum window, e.g. '10% per calendar "
                    "day, up to 3 days, no exceptions without documentation'.",
                ))

    # ---------------- logistics ----------------
    if credits and meetings and minutes:
        actual_min = meetings * minutes
        expected_min = credits * 50  # one 50-minute contact period per credit hour per week
        ratio = actual_min / float(expected_min)
        if ratio < 0.7:
            findings.append(Finding(
                "L1", "logistics", "high",
                f"Contact hours are {ratio * 100:.0f}% of the credit-hour requirement",
                f"{meetings:g} meeting(s) x {minutes:g} min = {actual_min:g} min/week; "
                f"{credits:g} credit hours implies {expected_min:g} min/week "
                f"(one 50-minute period per credit hour).",
                "A course scheduled well under the contact-hour requirement is a real "
                "scheduling error and it changes what the course can credibly promise. It "
                "usually means students are being asked to do far more work than the credit "
                "hours imply, or that a session was dropped from the timetable.",
                "Either add session time, reduce the credit value, or document the deliberate "
                "difference in the course description.",
            ))
        elif ratio > 1.6:
            findings.append(Finding(
                "L2", "logistics", "medium",
                f"Contact hours are {ratio * 100:.0f}% of the credit-hour requirement",
                f"{actual_min:g} min/week scheduled against {expected_min:g} min/week implied "
                f"by {credits:g} credits.",
                "Scheduled time well over the requirement usually means a lab or recitation is "
                "baked in and the credit value does not reflect it.",
                "Note the lab in the course description and confirm the credit value matches "
                "what is actually delivered.",
            ))

        workload_hours = credits * 3.0
        out_of_class = max(0.0, workload_hours * 60 - actual_min)
        if credits >= 2 and out_of_class < credits * 45:
            findings.append(Finding(
                "L3", "logistics", "medium",
                "Implied outside-class work is too low",
                f"Contact time {actual_min / 60:.1f} h/week; at ~3 h per credit hour of total "
                f"work, {credits:g} credits implies {workload_hours:.1f} h/week, leaving only "
                f"{out_of_class / 60:.1f} h/week outside class.",
                "A 2-credit course with under an hour a week of outside work is not doing "
                "enough work to produce the outcomes, and students will notice the mismatch "
                "between the credit value and the effort.",
                "State the expected outside hours in the syllabus, or increase the work "
                "attached to the existing assessments.",
            ))

    if meetings and minutes and minutes > 150:
        findings.append(Finding(
            "L4", "logistics", "medium",
            f"{minutes:g}-minute class blocks need a break plan",
            f"{meetings:g} meeting(s) of {minutes:g} minutes each per week.",
            "Sessions over 150 minutes lose attention sharply in the back half, and a single "
            "3-hour block is a different pedagogy from three 50-minute blocks.",
            "Either split into shorter meetings or build an explicit break and activity change "
            "into the 3-hour block description.",
        ))

    if meetings and meetings > 5:
        findings.append(Finding(
            "L5", "logistics", "medium",
            f"{meetings:g} meetings per week",
            f"Meetings per week: {meetings:g}.",
            "More than five weekly meetings crowds out every other obligation students have and "
            "is usually a symptom of the contact-hour calculation being wrong rather than a "
            "deliberate design.",
            "Recheck the meeting pattern against the credit hours and consolidate where "
            "possible.",
        ))

    if start_date is None:
        findings.append(Finding(
            "L6", "logistics", "medium",
            "No start date published",
            "No start / first-class date in the course section.",
            "Without a start date the weekly schedule cannot be tied to real calendar dates, "
            "which means drop deadlines, holidays and exam dates are all floating.",
            "Add 'Start: YYYY-MM-DD' and 'Final exam: YYYY-MM-DD'.",
        ))

    if final_date is None:
        findings.append(Finding(
            "L7", "logistics", "medium",
            "No final exam date published",
            "No final exam / end date in the course section.",
            "Students and the registrar both need the final's date. It is also how the "
            "end-of-term assessment window is checked for conflicts.",
            "Add 'Final exam: YYYY-MM-DD'.",
        ))

    if start_date and final_date:
        span_days = (final_date - start_date).days
        implied_weeks = span_days / 7.0
        if weeks and abs(implied_weeks - weeks) > 2:
            findings.append(Finding(
                "L8", "logistics", "medium",
                f"Dates span {implied_weeks:.1f} weeks but the term is declared {weeks} weeks",
                f"Start {start_date.isoformat()} to final {final_date.isoformat()} "
                f"= {span_days} days.",
                "The calendar and the declared term length disagree, so either the week "
                "numbering in the schedule or the dates are wrong.",
                "Reconcile the week numbering with the real calendar, including holidays.",
            ))

    if weeks and max(max_topic_week, max_assess_week) > weeks:
        findings.append(Finding(
            "L9", "logistics", "high",
            "Schedule extends past the end of term",
            f"Term {weeks} weeks, but topics/assessments reach week "
            f"{max(max_topic_weeks, max_assess_week)}.",
            "Anything scheduled past the final cannot happen, and students holding those weeks "
            "in their plan will be disappointed.",
            "Move the late items inside the term or extend the declared term length.",
        ))

    if students and students >= 150:
        findings.append(Finding(
            "L10", "logistics", "medium",
            f"Large enrolment ({students:g})",
            f"Enrolment: {students:g}.",
            "Above roughly 150 students, individual written feedback on every assignment stops "
            "being feasible and the assessment mix has to compensate with more scalable "
            "formats.",
            "Include at least one scalable assessment (auto-graded, multiple-choice, or "
            "studio-style peer review) and say how feedback is delivered.",
        ))

    if not students:
        findings.append(Finding(
            "L11", "logistics", "low",
            "Enrolment not stated",
            "No students / enrollment field.",
            "Enrolment drives room size, assessment scale and staffing. Without it the logistics "
            "review is incomplete.",
            "Add 'Students: 120'.",
        ))

    if "days" not in " ".join(brief.meta.keys()).lower() and not any(
        k in brief.meta for k in ("meeting days", "meeting pattern", "schedule", "times")
    ):
        findings.append(Finding(
            "L12", "logistics", "low",
            "No meeting pattern published",
            "No days/times field in the course section.",
            "Students need the day and time of the meetings as much as they need the week "
            "number.",
            "Add 'Meeting days: Tue/Thu' and 'Times: 10:00-10:50'.",
        ))

    if level and any(t in level for t in ("100", "intro", "101", "foundations")):
        if assessments and total_weight and exam_weight > 55:
            findings.append(Finding(
                "L13", "logistics", "medium",
                "Exam-heavy design for an introductory course",
                f"Level: {brief.meta.get('level')}; exam-style weight {exam_weight:g}%.",
                "Introductory courses should build habits and confidence. An exam-dominated "
                "structure in a first course sets the wrong expectation and tends to filter "
                "out exactly the students a large intro course is trying to support.",
                "Shift weight to low-stakes practice and projects that give early feedback.",
            ))

    # ---------------- scoring ----------------
    axis_scores = {}
    for axis in AXES:
        score = 100.0
        for f in findings:
            if f.axis == axis:
                score -= SEVERITY_DEDUCTION[f.severity]
        axis_scores[axis] = max(0.0, round(score, 1))

    caps = []
    if not objectives:
        caps.append(("alignment", 25, "No learning objectives are defined"))
        caps.append(("__overall__", 40, "No learning objectives are defined"))
    if not assessments:
        caps.append(("assessment", 25, "No assessments are defined"))
        caps.append(("__overall__", 45, "No assessments are defined"))
    elif abs(total_weight - 100.0) > 0.6:
        caps.append(("assessment", 35, f"Assessment weights sum to {total_weight:g}%, not 100%"))
        caps.append(("__overall__", 50, f"Assessment weights sum to {total_weight:g}%, not 100%"))
    if not policies:
        caps.append(("policy", 35, "No policy section is defined"))
        caps.append(("__overall__", 45, "No policy section is defined"))
    elif len(policies) < 4:
        caps.append(("policy", 50, f"Only {len(policies)} policy entries are defined"))
    high_missing = [label for label, sev in missing_policies if sev == "high"]
    if high_missing:
        reason = "Missing required policies: " + ", ".join(high_missing)
        caps.append(("policy", 30, reason))
        caps.append(("__overall__", 70, reason))
    if len(missing_policies) >= 7:
        caps.append(("policy", 20, f"{len(missing_policies)} of {len(REQUIRED_POLICIES)} "
                                   f"required policies are missing"))
    if credits and meetings and minutes:
        expected_min = credits * 50
        if expected_min and (meetings * minutes) / float(expected_min) < 0.7:
            caps.append(("logistics", 35, "Contact hours fall well below the credit-hour requirement"))
            caps.append(("__overall__", 48, "Contact hours fall well below the credit-hour requirement"))
    if weeks <= 0 and not topic_weeks:
        caps.append(("pacing", 30, "No term length and no schedule"))
        caps.append(("__overall__", 42, "No term length and no schedule"))

    for axis, cap_value, reason in list(caps):
        if axis == "__overall__":
            continue
        if axis_scores.get(axis, 100) > cap_value:
            axis_scores[axis] = float(cap_value)
    overall = sum(axis_scores[a] * weights[a] for a in AXES) / 100.0
    for axis, cap_value, reason in list(caps):
        if axis == "__overall__" and overall > cap_value:
            overall = float(cap_value)
    overall = round(max(0.0, min(100.0, overall)), 1)

    if overall >= 90:
        verdict = "ready_to_publish"
    elif overall >= 75:
        verdict = "minor_edits"
    elif overall >= 60:
        verdict = "needs_work"
    else:
        verdict = "not_ready"

    # ---------------- fix plan ----------------
    findings_sorted = sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER[f.severity], -weights.get(f.axis, 0)),
    )
    fix_plan = []
    running_axis = dict(axis_scores)
    for f in findings_sorted:
        axis_gain = min(
            SEVERITY_DEDUCTION[f.severity],
            running_axis.get(f.axis, 0.0),
        ) if f.axis in running_axis else 0.0
        if f.axis in running_axis:
            running_axis[f.axis] = max(0.0, running_axis[f.axis] - SEVERITY_DEDUCTION[f.severity])
        overall_gain = round(axis_gain * weights.get(f.axis, 0) / 100.0, 1)
        fix_plan.append({
            "id": f.id,
            "title": f.title,
            "axis": f.axis,
            "severity": f.severity,
            "fix": f.fix,
            "estimated_score_gain": overall_gain,
        })

    # ---------------- course map ----------------
    course_map = []
    for week in range(1, effective_term + 1):
        wk_topics = per_week.get(week, [])
        wk_assess = assess_by_week.get(week, [])
        load = len(wk_topics)
        flags = []
        if not wk_topics and week <= max(topic_weeks or [0]):
            flags.append("no_topic")
        if load >= 4:
            flags.append("heavy")
        if len(wk_assess) >= 2:
            flags.append("stacked_assessments")
        if week == effective_term:
            flags.append("final_week")
        course_map.append({
            "week": week,
            "topics": wk_topics,
            "assessments": [{"name": a.name, "weight": a.weight} for a in wk_assess],
            "load": load,
            "flags": flags,
        })

    # ---------------- generated syllabus ----------------
    syllabus = build_syllabus(brief, course_map, coverage, effective_term, total_weight)

    return {
        "meta": {
            "course": brief.meta.get("course") or brief.meta.get("title") or "Untitled course",
            "code": brief.meta.get("code") or brief.meta.get("course code", ""),
            "term": brief.meta.get("term") or brief.meta.get("semester", ""),
            "level": brief.meta.get("level", ""),
            "credits": credits,
            "weeks": effective_term,
            "meetings_per_week": meetings,
            "minutes_per_meeting": minutes,
            "students": students,
            "start_date": start_date.isoformat() if start_date else "",
            "final_date": final_date.isoformat() if final_date else "",
        },
        "profile": profile,
        "profile_weights": weights,
        "score": {
            "overall": overall,
            "verdict": verdict,
            "axes": {a: {"label": AXES[a], "score": axis_scores[a], "weight": weights[a]}
                     for a in AXES},
        },
        "findings": [f.to_dict() for f in findings_sorted],
        "fix_plan": fix_plan,
        "coverage": coverage,
        "course_map": course_map,
        "assessments": [asdict(a) for a in assessments],
        "objectives": [asdict(o) for o in objectives],
        "topics": [asdict(t) for t in topics],
        "policies": policies,
        "caps": [{"axis": a, "cap": c, "reason": r} for a, c, r in caps if not a.endswith("::note")],
        "totals": {
            "objective_count": len(objectives),
            "topic_count": len(topics),
            "assessment_count": len(assessments),
            "policy_count": len(policies),
            "total_weight": round(total_weight, 2),
            "exam_weight": round(sum(a.weight for a in assessments if _is_exam(a.name)), 2),
            "critical": sum(1 for f in findings if f.severity == "critical"),
            "high": sum(1 for f in findings if f.severity == "high"),
            "medium": sum(1 for f in findings if f.severity == "medium"),
            "low": sum(1 for f in findings if f.severity == "low"),
        },
        "syllabus": syllabus,
    }


# --------------------------------------------------------------------------
# syllabus generation
# --------------------------------------------------------------------------


def build_syllabus(brief: Brief, course_map: list[dict], coverage: list[dict],
                   weeks: int, total_weight: float) -> str:
    meta = brief.meta
    lines = []
    title = meta.get("course") or meta.get("title") or "Course Title"
    code = meta.get("code", "")
    term = meta.get("term", "")
    level = meta.get("level", "")

    lines.append(f"# {title}")
    bits = [b for b in (code, term, level) if b]
    if bits:
        lines.append("")
        lines.append("*" + " | ".join(bits) + "*")
    lines.append("")
    lines.append("## Course Description")
    lines.append("")
    if meta.get("description"):
        lines.append(meta["description"].strip())
    else:
        lines.append("TODO: write a 3-5 sentence description covering what the course studies, "
                     "how it is taught, and who should take it.")
    lines.append("")

    credits = _meta_num(meta, "credits", "credit hours", "credit", "units")
    meetings = _meta_num(meta, "meetings per week", "meetings", "sessions per week")
    minutes = _meta_num(meta, "minutes per meeting", "minutes", "class length")
    if credits or meetings or minutes:
        lines.append("## Meeting Pattern")
        lines.append("")
        parts = []
        if credits:
            parts.append(f"{credits:g} credit hours")
        if meetings and minutes:
            parts.append(f"{meetings:g} meeting(s) per week x {minutes:g} minutes")
        elif meetings:
            parts.append(f"{meetings:g} meeting(s) per week")
        pattern = meta.get("meeting days") or meta.get("meeting pattern") or meta.get("schedule")
        if pattern:
            parts.append(str(pattern))
        times = meta.get("times")
        if times:
            parts.append(str(times))
        lines.append("- " + ", ".join(parts))
        lines.append("")

    lines.append("## Learning Outcomes")
    lines.append("")
    lines.append("By the end of this course, a successful student will be able to:")
    lines.append("")
    if coverage:
        for c in coverage:
            text = c["text"]
            if text[:1].islower():
                text = text[0].upper() + text[1:]
            assessed = ", ".join(c["assessed_by"]) if c["assessed_by"] else "NOT ASSESSED"
            lines.append(f"- {text} _(assessed via {assessed})_")
    else:
        lines.append("- TODO: list 4-8 measurable learning outcomes")
    lines.append("")

    lines.append("## Course Materials")
    lines.append("")
    if meta.get("textbook") or meta.get("materials"):
        lines.append(str(meta.get("textbook") or meta.get("materials")))
    else:
        lines.append("TODO: list the required text and any other required materials.")
    lines.append("")

    lines.append("## Weekly Schedule")
    lines.append("")
    lines.append("| Week | Topics | Assessments due |")
    lines.append("| --- | --- | --- |")
    for row in course_map:
        topics = "; ".join(row["topics"]) if row["topics"] else ("_no topic scheduled_"
                                                                 if "no_topic" in row["flags"]
                                                                 else "-")
        due = "; ".join(f"{a['name']} ({a['weight']:g}%)" for a in row["assessments"]) or "-"
        lines.append(f"| {row['week']} | {topics} | {due} |")
    lines.append("")

    lines.append("## Assessment and Grading")
    lines.append("")
    if brief.assessments:
        lines.append("| Assessment | Weight | When |")
        lines.append("| --- | --- | --- |")
        for a in brief.assessments:
            when = ", ".join(str(w) for w in a.weeks) if a.weeks else "TODO"
            lines.append(f"| {a.name} | {a.weight:g}% | {when} |")
        lines.append("")
        if abs(total_weight - 100.0) > 0.6:
            lines.append(f"> TODO: weights currently total {total_weight:g}%. Rebalance to 100% "
                         "before publishing.")
            lines.append("")
    else:
        lines.append("TODO: add the assessment table with weights totalling 100%.")
        lines.append("")

    lines.append("### Grade Scale")
    lines.append("")
    scale = meta.get("grading scale") or ""
    if scale:
        lines.append(scale)
    else:
        lines.append("TODO: state the letter scale and thresholds, or name the institutional "
                     "scale this course follows.")
    lines.append("")

    lines.append("## Course Policies")
    lines.append("")
    policy_lines = brief.policies
    if policy_lines:
        for key, value in policy_lines.items():
            lines.append(f"- **{key.title()}:** {value}")
    else:
        lines.append("TODO: add the required policy set (grading scale, late work, attendance, "
                     "participation, academic integrity, AI use, accommodations, drop deadline, "
                     "make-up work, final exam details).")
    lines.append("")

    missing = []
    blob = " ".join(f"{k} {v}" for k, v in policy_lines.items()).lower()
    for key, label, severity, why, fix in REQUIRED_POLICIES:
        if not _policy_present(blob, key):
            missing.append(label)
    if missing:
        lines.append("### Still missing before you publish")
        lines.append("")
        for label in missing:
            lines.append(f"- [ ] {label}")
        lines.append("")

    lines.append("## Instructor Contact")
    lines.append("")
    lines.append("TODO: name, email, office, office hours and a response-time expectation.")
    lines.append("")
    return "\n".join(lines)


def analyse_text(text: str, profile: str = "general", today: dt.date | None = None) -> dict:
    return analyse(parse_brief(text), profile=profile, today=today)
