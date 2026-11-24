# Syllabus Forge

A local-first **course design and syllabus readiness workbench** for instructors.

Paste a course brief - metadata, learning objectives, a week-by-week topic list, the
assessment breakdown and the policy set - and get back a **0-100 readiness score**
across five axes, every finding with the evidence that triggered it, a prioritised fix
plan, an objective-to-assessment alignment matrix, a week-by-week course map, and a
**generated syllabus document** with explicit `TODO` markers where you still need to
supply something.

No API keys. No network calls. No LLM. Everything runs on your machine.

---

## Why

Every other syllabus tool in this family is aimed at the *student*: study planners,
flashcard generators, note takers. Almost nothing is aimed at the person who has to
*write* the syllabus - the instructor, the teaching assistant who is covering a
course, the department chair reviewing a proposal, the coordinator who has to check
that a new course satisfies a credit-hour rule.

And the instructor's job has a specific, unglamorous shape:

- the outcomes have to be **aligned** to what is actually taught and actually assessed
- the **weights have to add to 100** or the grade is undefined
- the **schedule has to fit** - no week with five new topics, no exam crammed against
  another exam, no new content in the final week
- the **policy set has to be complete** - integrity, AI use, accommodations, late work,
  drop deadline, make-up work
- the **contact hours have to match the credit value**, and the meeting pattern has to
  be publishable

Each of those is a discrete, checkable failure, and each one has a specific fix. That
is what this tool does.

---

## Quick start

```bash
git clone https://github.com/jackson9413/syllabus-forge.git
cd syllabus-forge
python3 -m pip install -r requirements.txt
python3 app.py
```

Open <http://127.0.0.1:5055>. Click a sample in the **Sample** dropdown to see the tool
work immediately, then paste your own brief.

### Command line

```bash
# review a brief and print a markdown report
python3 cli.py --brief course.txt

# use a built-in sample
python3 cli.py --sample cram_term --format md

# machine-readable output
python3 cli.py --brief course.txt --format json
python3 cli.py --brief course.txt --format csv

# audit one axis only (re-weights the five axes)
python3 cli.py --brief course.txt --profile pacing_audit

# also save the run to the local SQLite log
python3 cli.py --brief course.txt --save
```

---

## The brief format

Sections are marked with square brackets. Everything before the first header is treated
as course metadata.

```
[Course]
Course: Introduction to Data Science
Code: DS 110
Term: Fall 2026
Level: sophomore
Credits: 4
Weeks: 15
Meetings per week: 4
Minutes per meeting: 50
Students: 80
Start: 2026-08-24
Final exam: 2026-12-11
Meeting days: Mon/Wed/Fri and Thu
Times: 9:00-9:50
Description: One or two sentences about the course.
Textbook: Python for Data Analysis, 3rd edition

[Objectives]
- Implement and evaluate core supervised learning algorithms | topics: 3-9 | assessed: Lab project
- Analyze datasets for bias and missingness | topics: 2,4,10 | assessed: Lab project

[Topics]
Week 1 | Course orientation, data ethics | obj 2
Week 2 | Data collection and sampling | obj 2

[Assessments]
Homework | 14 | 30% | weeks 1-14
Lab project | 1 | 20% | week 13 | obj 1,2
Midterm | 1 | 15% | week 8
Final exam | 1 | 20% | week 15

[Policies]
Grading scale: A 93-100, B 90-92, C 87-89, D 84-86, F below 84
Academic integrity: Work must be your own.
AI use: Generative AI is permitted for exploration but not for submitted work.
Accommodations: Contact Disability Services; documentation is kept confidential.
Late work: 10% per calendar day, up to 3 days, with documentation.
Attendance: Attendance is expected; absences are excused with documentation.
Participation: Lab attendance and discussion contribution, 5% of the grade.
Drop deadline: The drop deadline is the end of week 9.
Makeup work: Missed labs may be completed within one week of returning.
Final exam: Week 15, 50 minutes, covering all course material, 20% of the grade.
Textbook: Required text is Python for Data Analysis, 3rd edition.
Office hours: Tuesdays 2-4pm in Engineering 402; email answered within one business day.
```

Field notes:

- **Weeks** accepts ranges: `weeks: 1-14`, `weeks: 2,4,6,8`, `weeks 1-14`.
- **Topics** need a leading week number: `Week 1 | Title | obj 2` or `1 | Title`.
- **Assessments** are pipe-delimited: name, count, weight, weeks, objective refs. Only
  the weight needs a `%` sign.
- **Objective refs** on a topic are objective numbers (`obj 1`); on an assessment they
  are objective numbers or the assessment name (`assessed: Lab project`).
- **Alignment is inferred** when you do not tag it: an assessment whose words overlap an
  objective is linked and marked `inferred` in the coverage table, so you can see what
  the engine guessed.

---

## What you get back

### 1. A five-axis readiness score

| Axis | Weight | What it measures |
| --- | --- | --- |
| Alignment | 25% | Objectives that are taught, assessed, or neither |
| Assessment design | 20% | Weight arithmetic, exam balance, feedback cadence |
| Pacing | 20% | Topic density, exam placement, collisions, back-loading |
| Policy completeness | 20% | The twelve policies every course needs |
| Logistics | 15% | Contact hours vs credit value, dates, enrolment scale |

Verdict bands: `ready_to_publish` (90+), `minor_edits` (75+), `needs_work` (60+),
`not_ready` (below 60).

**Structural caps** stop a course from scoring well by skipping the hard part. No
learning objectives caps alignment at 25 and the overall at 40. Weights that do not
sum to 100 cap assessment design at 35 and the overall at 50. No policy section caps
policy at 35 and the overall at 45. Missing integrity, AI, accommodations or grading
scale policies cap the overall at 70. Contact hours under 70% of the credit-hour
requirement cap logistics at 35 and the overall at 48.

### 2. Findings that show their work

Every finding carries the evidence that triggered it, why it matters in teaching terms,
and a concrete fix - around 60 rules across the five axes, for example:

- an objective that is taught but never assessed
- an assessment that serves no objective
- weights that total 85%
- a single assessment worth 45% of the grade
- exams worth 80% of the grade
- an exam in week 2 of 14, or two exams three weeks apart
- new content in the final week
- a term where 100% of the topics land in the last quarter
- four assessments stacked in one week
- a late-work policy with no penalty attached
- a 3-credit course scheduled for 100 minutes a week
- a 260-student course with no scalable assessment
- dates that span a different number of weeks than the syllabus claims

### 3. A prioritised fix plan

Findings ordered by severity then by the weight of the axis they damage, each with an
estimated score gain.

### 4. An objective coverage matrix

Which weeks teach each objective, which assessments measure it, and the `inferred`
flag where the engine linked them by keyword.

### 5. A week-by-week course map

Every week with its topics, the assessments due that week, and flags for gaps, heavy
weeks, stacked assessments and the final week.

### 6. A generated syllabus draft

A complete Markdown syllabus - description, meeting pattern, learning outcomes with
their assessments, materials, the weekly schedule table, the grading table, the policy
set, and a **"Still missing before you publish"** checklist. Anything you did not
supply comes back as an explicit `TODO` rather than a blank.

---

## Built-in samples

| id | what it exercises |
| --- | --- |
| `clean_course` | A healthy 4-credit course. The control case: 100/100, zero findings. |
| `cram_term` | All content in the last four weeks, exam-heavy grading, no policies. |
| `weight_mess` | Everything sound except weights that total 85%. |
| `unaligned` | Six outcomes taught, assessments that measure one of them. |
| `logistics_crunch` | 3 credits in 100 minutes a week, 260 students, no dates. |
| `policy_gap` | Excellent course design, almost no policies. |

---

## REST API

```
GET    /api/health                  service info and the list of review profiles
GET    /api/samples                 built-in sample briefs
POST   /api/analyze                 {brief, profile} -> full analysis JSON
POST   /api/export                  {brief, profile, format} -> md | json | csv download
GET    /api/runs                    list saved runs
POST   /api/runs                    {brief, profile, title, rating, notes} -> save
GET    /api/runs/<id>               one run with its full result
PATCH  /api/runs/<id>               {rating: 1-5, notes}
DELETE /api/runs/<id>               delete a run
```

Review profiles re-weight the five axes: `general`, `alignment_audit`,
`assessment_audit`, `pacing_audit`, `policy_audit`, `logistics_audit`.

---

## Stack

- **Backend:** Python 3 / Flask. The analysis engine is pure standard library - no
  third-party analysis dependencies, no model calls.
- **Frontend:** vanilla HTML/CSS/JS, dark theme, no build step, no CDN.
- **Storage:** SQLite for the saved-run log (and a 1-5 star self-rating with notes).
- **Tests:** `pytest` / `unittest`, 37 tests covering the parser, the scoring rules,
  the structural caps, the exports and the API.

```bash
python3 -m pytest tests/ -q
```

---

## Design notes and honest limitations

- **The contact-hour rule** used here is one 50-minute period per credit hour per week.
  Some institutions use the 2.5-hour rule for one-credit courses and other
  conventions. The engine flags a ratio below 70% or above 160% of that baseline so you
  can see the arithmetic, and the evidence line shows the numbers it used.
- **Alignment inference is heuristic.** Keyword overlap links an assessment to an
  objective when you have not tagged it. It is marked `inferred` so you never mistake a
  guess for a fact. Tagging is always better.
- **The AI-policy check is a presence check.** It confirms that a policy exists, not
  that the policy is any good.
- **There is no accreditation model.** The axes are teaching-practice heuristics
  derived from what makes a syllabus defensible in a course review, not a compliance
  framework.
- **No shared database, no sync, no accounts.** One local SQLite file.

---

## License

MIT.
