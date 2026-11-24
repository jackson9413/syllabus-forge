"""Built-in sample course briefs.

Each sample exercises a different failure mode so the engine can be calibrated
and so a new user can see the tool do something useful in one click.
"""

SAMPLES = {
    "clean_course": {
        "title": "Healthy course (control case)",
        "blurb": "A well-built 4-credit course: everything aligns, weights sum to 100, "
                 "policies are complete.",
        "brief": """[Course]
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
Description: An introduction to data science covering data wrangling, statistical
inference, and machine learning, with a term-long laboratory project.
Textbook: Python for Data Analysis, 3rd edition

[Objectives]
- Implement and evaluate core supervised learning algorithms | topics: 3-9 | assessed: Lab project
- Analyze datasets for bias, missingness and sampling problems | topics: 2,4,10 | assessed: Lab project
- Communicate statistical findings with appropriate uncertainty | topics: 11-13 | assessed: Quizzes
- Compare model performance using appropriate validation strategies | topics: 6,7,12 | assessed: Midterm
- Design an end-to-end reproducible data pipeline | topics: 8,14 | assessed: Final exam

[Topics]
Week 1 | Course orientation, data ethics and the data lifecycle | obj 2
Week 2 | Data collection, sampling and survey design | obj 2
Week 3 | Data cleaning and missing data | obj 2
Week 4 | Exploratory analysis and data visualisation | obj 1
Week 5 | Linear regression and interpretation | obj 1
Week 6 | Model validation and cross-validation | obj 4
Week 7 | Classification and decision boundaries | obj 4
Week 8 | Midterm review and applied modelling workshop | obj 4
Week 9 | Regularisation and feature selection | obj 1
Week 10 | Fairness, bias and dataset shift | obj 2
Week 11 | Statistical communication and uncertainty | obj 3
Week 12 | Evaluation metrics beyond accuracy | obj 3
Week 13 | Laboratory project clinic and peer review | obj 3
Week 14 | Pipelines, reproducibility and deployment | obj 5
Week 15 | Cumulative review and integration | obj 5

[Assessments]
Homework | 14 | 30% | weeks 1-14
Quizzes | 6 | 10% | weeks 2,4,6,8,10,12
Lab project | 1 | 20% | week 13 | obj 1,2
Midterm | 1 | 15% | week 8 | obj 4
Final exam | 1 | 20% | week 15 | obj 5
Participation | 1 | 5% | weeks 1-15

[Policies]
Grading scale: A 93-100, B 90-92, C 87-89, D 84-86, F below 84
Academic integrity: Work must be your own. Violations are reported under the university honour code.
AI use: Generative AI is permitted for exploration but not for submitted code or analysis; disclose any use.
Accommodations: Contact Disability Services to arrange accommodations; documentation is kept confidential.
Late work: 10% per calendar day, up to 3 days, with documentation for illness or emergency.
Attendance: Attendance is expected. Absences are excused with documentation and do not affect your grade directly.
Participation: Participation covers lab attendance and discussion contribution, assessed 5% of the grade.
Drop deadline: The drop deadline is the end of week 9; after that a W is recorded.
Makeup work: Missed labs and quizzes may be completed within one week of returning.
Final exam: Final exam is week 15, covering all course material, 50 minutes, worth 20% of the grade.
Textbook: Required text is Python for Data Analysis, 3rd edition.
Office hours: Office hours Tuesdays 2-4pm in Engineering 402; email is answered within one business day.
""",
    },

    "cram_term": {
        "title": "Everything crammed into the last month",
        "blurb": "All content scheduled in the final four weeks, exam-heavy grading, no policies.",
        "brief": """[Course]
Course: Introduction to Sociology
Code: SOC 101
Term: Fall 2026
Level: freshman
Credits: 3
Weeks: 14
Meetings per week: 3
Minutes per meeting: 50
Students: 220
Start: 2026-08-24
Final exam: 2026-12-11

[Objectives]
- Explain core sociological perspectives and apply them to a case study | topics: 11
- Evaluate a research design using ethical research standards | topics: 12
- Analyse census and survey data to support a written argument | topics: 13,14

[Topics]
Week 11 | Socialisation, culture and identity | obj 1
Week 12 | Research methods and ethics | obj 2
Week 13 | Quantitative data analysis and the census | obj 3
Week 14 | Writing the sociology essay | obj 3

[Assessments]
Midterm | 1 | 35% | week 13
Final exam | 1 | 45% | week 14
Reflection paper | 1 | 10% | week 12
Participation | 1 | 10% | weeks 1-14
""",
    },

    "weight_mess": {
        "title": "Grade weights that do not add up",
        "blurb": "Everything else is sound but the weights total 85%, so the grade is undefined.",
        "brief": """[Course]
Course: Introduction to Environmental Science
Code: ENV 120
Term: Spring 2027
Level: freshman
Credits: 3
Weeks: 15
Meetings per week: 3
Minutes per meeting: 50
Students: 140
Start: 2027-01-19
Final exam: 2027-05-07
Meeting days: Mon/Wed/Fri
Times: 11:00-11:50

[Objectives]
- Explain the major physical and biological processes in ecosystems | topics: 1-6 | assessed: Midterm
- Apply the scientific method to environmental questions | topics: 2,7 | assessed: Field report
- Interpret environmental data and communicate findings | topics: 8-13 | assessed: Final exam
- Evaluate the policy implications of environmental science | topics: 14 | assessed: Policy brief

[Topics]
Week 1 | Energy flow and ecosystem structure | obj 1
Week 2 | The scientific method in environmental context | obj 2
Week 3 | Biogeochemical cycles | obj 1
Week 4 | Population dynamics and community ecology | obj 1
Week 5 | Ecosystem resilience and disturbance | obj 1
Week 6 | Field methods and sampling design | obj 2
Week 7 | Field study and data collection | obj 2
Week 8 | Statistical analysis of environmental data | obj 3
Week 9 | Water resources and watershed analysis | obj 3
Week 10 | Air quality and atmospheric chemistry | obj 3
Week 11 | Climate systems and modelling | obj 3
Week 12 | Soil systems and land use | obj 3
Week 13 | Biodiversity assessment methods | obj 3
Week 14 | Environmental policy case studies | obj 4
Week 15 | Synthesis review and course integration | obj 4

[Assessments]
Quizzes | 8 | 15% | weeks 2,4,6,8,10,12,14,15
Lab reports | 4 | 15% | weeks 3,7,9,11
Field report | 1 | 15% | week 7 | obj 2
Midterm | 1 | 15% | week 8 | obj 1
Policy brief | 1 | 10% | week 14 | obj 4
Final exam | 1 | 15% | week 15 | obj 3

[Policies]
Grading scale: A 90-100, B 80-89, C 70-79, D 60-69, F below 60
Academic integrity: All work must be your own; violations follow the university honour code.
AI use: Generative AI is not permitted for lab reports or the final; disclose any use for review questions.
Accommodations: Disability Services handles accommodations confidentially.
Late work: 5% per day for up to 5 days with documentation.
Attendance: Attendance is expected and unexcused absences are reported.
Participation: Laboratory participation and field safety count toward participation.
Drop deadline: Drop without penalty through the end of week 8.
Makeup work: Missed labs may be completed with an approved alternative.
Final exam: Final exam is in week 15 and covers all course material.
Textbook: Required text is Essential Environment, 6th edition.
Office hours: Office hours Mondays 3-5pm, and email is answered within one business day.
""",
    },

    "unaligned": {
        "title": "Outcomes nobody checks",
        "blurb": "Six learning objectives are taught, but the assessments only measure one of them.",
        "brief": """[Course]
Course: Modern World History since 1900
Code: HIS 240
Term: Fall 2026
Level: sophomore
Credits: 3
Weeks: 15
Meetings per week: 3
Minutes per meeting: 75
Students: 95
Start: 2026-08-24
Final exam: 2026-12-11

[Objectives]
- Explain the causes and consequences of the world wars | topics: 3,4,5
- Evaluate competing interpretations of the interwar period | topics: 4,6
- Analyse primary sources for historical argument | topics: 7,8,9
- Compare decolonisation across three regions | topics: 10,11,12
- Construct a research-based essay with citations | topics: 13,14
- Assess the limits of using history to explain the present | topics: 15

[Topics]
Week 1 | Course introduction and periodisation debates | obj 1
Week 2 | Imperialism before 1914 | obj 1
Week 3 | The First World War: causes | obj 1
Week 4 | The First World War: consequences | obj 1
Week 5 | Interwar politics and competing interpretations | obj 2
Week 6 | The rise of fascism | obj 2
Week 7 | Source analysis workshop | obj 3
Week 8 | The Second World War | obj 3
Week 9 | Aftermath, Nuremberg and the Cold War | obj 3
Week 10 | Decolonisation in South Asia | obj 4
Week 11 | Decolonisation in Africa | obj 4
Week 12 | Decolonisation and the Caribbean | obj 4
Week 13 | Writing the research essay | obj 5
Week 14 | Essay workshop and peer review | obj 5
Week 15 | History and the present: synthesis review | obj 6

[Assessments]
Reading responses | 12 | 25% | weeks 1-12
Source analysis | 1 | 20% | week 9
Midterm | 1 | 20% | week 8
Research essay | 1 | 25% | week 14
Participation | 1 | 10% | weeks 1-15
""",
    },

    "logistics_crunch": {
        "title": "A course squeezed into too few hours",
        "blurb": "3 credits scheduled in 100 minutes a week, 260 students, a 3-hour lab, no dates.",
        "brief": """[Course]
Course: Introduction to Public Health
Code: PBH 105
Term: Spring 2027
Level: freshman
Credits: 3
Weeks: 15
Meetings per week: 2
Minutes per meeting: 50
Students: 260

[Objectives]
- Describe the organisation and financing of health systems | topics: 1-4 | assessed: Midterm
- Apply epidemiological methods to a population dataset | topics: 5-9 | assessed: Data lab
- Design a health communication campaign for a defined audience | topics: 10-13 | assessed: Campaign plan
- Evaluate policy interventions using cost-effectiveness reasoning | topics: 14,15 | assessed: Final exam

[Topics]
Week 1 | Health as a system: scope and history | obj 1
Week 2 | Health systems and financing | obj 1
Week 3 | Health workforce and infrastructure | obj 1
Week 4 | Health equity and the social determinants | obj 1
Week 5 | Measures of health and disease | obj 2
Week 6 | Study design and confounding | obj 2
Week 7 | Screening and diagnostic testing | obj 2
Week 8 | Outbreak investigation | obj 2
Week 9 | Regression and risk estimation | obj 2
Week 10 | Behaviour change theory | obj 3
Week 11 | Audience research and segmentation | obj 3
Week 12 | Message design and testing | obj 3
Week 13 | Campaign delivery and evaluation | obj 3
Week 14 | Cost-effectiveness analysis | obj 4
Week 15 | Synthesis review and policy exercise | obj 4

[Assessments]
Weekly readings | 15 | 20% | weeks 1-15
Data lab | 1 | 25% | week 9 | obj 2
Campaign plan | 1 | 20% | week 13 | obj 3
Midterm | 1 | 15% | week 7 | obj 1
Final exam | 1 | 20% | week 15 | obj 4
""",
    },

    "policy_gap": {
        "title": "Good course, empty policy section",
        "blurb": "Strong alignment and pacing, but nearly every required policy is missing.",
        "brief": """[Course]
Course: Technical Writing and Communication
Code: EN 275
Term: Spring 2027
Level: sophomore
Credits: 3
Weeks: 15
Meetings per week: 3
Minutes per meeting: 50
Students: 30
Start: 2027-01-19
Final exam: 2027-05-07
Meeting days: Tue/Thu
Times: 14:00-14:50

[Objectives]
- Write clear, audience-appropriate technical documents | topics: 1-6 | assessed: Portfolio
- Analyse the rhetorical situation of a communication task | topics: 3,4 | assessed: Analysis memo
- Design documentation for a real product | topics: 7-13 | assessed: Final project
- Evaluate drafts using structured feedback | topics: 9,10 | assessed: Peer review

[Topics]
Week 1 | Writing as a professional practice | obj 1
Week 2 | Audience analysis | obj 1
Week 3 | Situation analysis and purpose | obj 2
Week 4 | Rhetorical situations and genre | obj 2
Week 5 | Sentence-level clarity and style | obj 1
Week 6 | Information architecture and navigation | obj 1
Week 7 | Documentation types and templates | obj 3
Week 8 | Tooling: markup, versioning and review | obj 3
Week 9 | Structured feedback and rubric design | obj 4
Week 10 | Review workshops | obj 4
Week 11 | Accessibility and inclusive documentation | obj 3
Week 12 | API and reference documentation | obj 3
Week 13 | Final project clinic | obj 3
Week 14 | Final project presentations | obj 3
Week 15 | Cumulative review and integration | obj 4

[Assessments]
Portfolio | 1 | 25% | week 13 | obj 1
Analysis memo | 1 | 15% | week 6 | obj 2
Peer review | 1 | 10% | week 10 | obj 4
Final project | 1 | 30% | week 14 | obj 3
Group presentation | 1 | 15% | week 12 | obj 3
Participation | 1 | 5% | weeks 1-15

[Policies]
Grading scale: A 93-100, B 90-92, C 87-89, D 84-86, F below 84
Late work: Drafts are due as checkpoints; later drafts lose the workshop slot.
""",
    },
}


def list_samples():
    return [
        {
            "id": key,
            "title": value["title"],
            "blurb": value["blurb"],
            "brief": value["brief"],
        }
        for key, value in SAMPLES.items()
    ]
