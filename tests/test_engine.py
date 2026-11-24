"""Engine tests for Syllabus Forge."""

from __future__ import annotations

import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine      # noqa: E402
import exporters   # noqa: E402
import samples     # noqa: E402


def analyse_sample(key, profile="general"):
    return engine.analyse_text(samples.SAMPLES[key]["brief"], profile=profile)


class TestParsing(unittest.TestCase):
    def test_week_list_ranges_and_lists(self):
        self.assertEqual(engine.parse_week_list("1-14"), list(range(1, 15)))
        self.assertEqual(engine.parse_week_list("2,4,6"), [2, 4, 6])
        self.assertEqual(engine.parse_week_list("week 12"), [12])
        self.assertEqual(engine.parse_week_list(""), [])
        self.assertEqual(engine.parse_week_list("weeks 3-5 and 9"), [3, 4, 5, 9])

    def test_sections_and_fields(self):
        brief = engine.parse_brief(samples.SAMPLES["clean_course"]["brief"])
        self.assertEqual(brief.meta["course"], "Introduction to Data Science")
        self.assertEqual(brief.meta["credits"], "4")
        self.assertEqual(len(brief.objectives), 5)
        self.assertEqual(len(brief.topics), 15)
        self.assertEqual(len(brief.assessments), 6)
        self.assertGreater(len(brief.policies), 10)

    def test_objective_topics_and_assessed_refs(self):
        brief = engine.parse_brief(samples.SAMPLES["clean_course"]["brief"])
        first = brief.objectives[0]
        self.assertEqual(first.topic_weeks, list(range(3, 10)))
        self.assertEqual(first.assessed_refs, ["Lab project"])

    def test_assessment_fields(self):
        brief = engine.parse_brief(samples.SAMPLES["clean_course"]["brief"])
        by_name = {a.name: a for a in brief.assessments}
        homework = by_name["Homework"]
        self.assertEqual(homework.count, 14)
        self.assertEqual(homework.weight, 30)
        self.assertEqual(homework.weeks, list(range(1, 15)))
        self.assertEqual(by_name["Lab project"].objective_refs, [1, 2])

    def test_topic_objective_tags(self):
        brief = engine.parse_brief(samples.SAMPLES["clean_course"]["brief"])
        week1 = [t for t in brief.topics if t.week == 1][0]
        self.assertEqual(week1.objective_refs, [2])
        self.assertIn("orientation", week1.title.lower())

    def test_empty_brief_parses_without_error(self):
        brief = engine.parse_brief("")
        self.assertEqual(brief.objectives, [])
        self.assertEqual(brief.topics, [])
        self.assertEqual(brief.assessments, [])

    def test_comments_ignored(self):
        brief = engine.parse_brief("# a comment\n// another\nCourse: X\n")
        self.assertEqual(brief.meta["course"], "X")


class TestScoring(unittest.TestCase):
    def test_score_is_in_range(self):
        for key in samples.SAMPLES:
            result = analyse_sample(key)
            self.assertGreaterEqual(result["score"]["overall"], 0)
            self.assertLessEqual(result["score"]["overall"], 100)

    def test_clean_course_scores_high(self):
        result = analyse_sample("clean_course")
        self.assertGreaterEqual(result["score"]["overall"], 90,
                                msg=result["findings"])
        self.assertEqual(result["score"]["verdict"], "ready_to_publish")
        self.assertEqual(result["totals"]["critical"], 0)

    def test_cram_term_is_not_ready(self):
        result = analyse_sample("cram_term")
        self.assertLess(result["score"]["overall"], 55)
        ids = {f["id"] for f in result["findings"]}
        self.assertIn("P2", ids)          # gap weeks
        self.assertIn("Q1", ids)          # no policy section
        self.assertIn("S5", ids)          # exam-heavy
        self.assertTrue(any(c["axis"] == "policy" for c in result["caps"]))

    def test_weight_mess_is_critical(self):
        result = analyse_sample("weight_mess")
        findings = {f["id"]: f for f in result["findings"]}
        self.assertIn("S2", findings)
        self.assertEqual(findings["S2"]["severity"], "critical")
        self.assertLessEqual(result["score"]["axes"]["assessment"]["score"], 35)
        self.assertLessEqual(result["score"]["overall"], 50)

    def test_unaligned_objectives_flagged(self):
        result = analyse_sample("unaligned")
        unassessed = [f for f in result["findings"] if f["id"] == "A2"]
        self.assertGreaterEqual(len(unassessed), 3)
        self.assertLess(result["score"]["axes"]["alignment"]["score"], 50)

    def test_policy_gap_scores_low_on_policy_axis(self):
        result = analyse_sample("policy_gap")
        self.assertLessEqual(result["score"]["axes"]["policy"]["score"], 30)
        missing = [f for f in result["findings"] if f["id"] == "Q2"]
        self.assertGreaterEqual(len(missing), 5)

    def test_logistics_contact_hours_flagged(self):
        result = analyse_sample("logistics_crunch")
        ids = {f["id"] for f in result["findings"]}
        self.assertIn("L1", ids)
        self.assertLessEqual(result["score"]["axes"]["logistics"]["score"], 35)
        self.assertIn("L10", ids)   # large enrolment

    def test_every_finding_is_fully_specified(self):
        for key in samples.SAMPLES:
            for f in analyse_sample(key)["findings"]:
                self.assertTrue(f["evidence"].strip(), msg=f)
                self.assertTrue(f["why"].strip(), msg=f)
                self.assertTrue(f["fix"].strip(), msg=f)
                self.assertIn(f["severity"], ("critical", "high", "medium", "low"))

    def test_fix_plan_is_ordered_and_sane(self):
        result = analyse_sample("cram_term")
        plan = result["fix_plan"]
        self.assertEqual(len(plan), len(result["findings"]))
        order = ["critical", "high", "medium", "low"]
        ranks = [order.index(step["severity"]) for step in plan]
        self.assertEqual(ranks, sorted(ranks))
        for step in plan:
            self.assertGreaterEqual(step["estimated_score_gain"], 0)

    def test_profiles_change_the_score(self):
        general = analyse_sample("policy_gap", "general")["score"]["overall"]
        policy = analyse_sample("policy_gap", "policy_audit")["score"]["overall"]
        self.assertNotEqual(general, policy)
        # policy_gap is broken on the policy axis, so a policy-weighted profile
        # must score it lower than the balanced profile.
        self.assertLess(policy, general)

    def test_axis_weights_sum_to_100(self):
        for name, weights in engine.PROFILES.items():
            self.assertEqual(sum(weights.values()), 100, msg=name)

    def test_empty_brief_produces_critical_findings(self):
        result = engine.analyse_text("")
        ids = {f["id"] for f in result["findings"]}
        self.assertIn("A1", ids)
        self.assertIn("S1", ids)
        self.assertLess(result["score"]["overall"], 50)


class TestCourseMapAndSyllabus(unittest.TestCase):
    def test_course_map_covers_every_week(self):
        result = analyse_sample("clean_course")
        weeks = result["meta"]["weeks"]
        self.assertEqual(len(result["course_map"]), weeks)
        self.assertEqual([row["week"] for row in result["course_map"]],
                         list(range(1, weeks + 1)))

    def test_course_map_flags_gaps_and_stacks(self):
        result = analyse_sample("cram_term")
        flagged = {row["week"]: row["flags"] for row in result["course_map"]}
        self.assertIn("no_topic", flagged[1])
        self.assertIn("final_week", flagged[result["meta"]["weeks"]])

    def test_generated_syllabus_has_sections(self):
        result = analyse_sample("clean_course")
        syllabus = result["syllabus"]
        for heading in ("# Introduction to Data Science", "## Learning Outcomes",
                        "## Weekly Schedule", "## Assessment and Grading",
                        "## Course Policies"):
            self.assertIn(heading, syllabus)

    def test_generated_syllabus_marks_missing_pieces(self):
        result = analyse_sample("policy_gap")
        self.assertIn("TODO", result["syllabus"])
        self.assertIn("Still missing before you publish", result["syllabus"])

    def test_coverage_rows_have_shape(self):
        result = analyse_sample("clean_course")
        for row in result["coverage"]:
            self.assertIn("id", row)
            self.assertIn("taught_weeks", row)
            self.assertIn("assessed_by", row)
            self.assertTrue(row["taught"])
            self.assertTrue(row["assessed"])


class TestExports(unittest.TestCase):
    def setUp(self):
        self.result = analyse_sample("clean_course")

    def test_markdown_export(self):
        md = exporters.to_markdown(self.result)
        self.assertIn("# Syllabus review:", md)
        self.assertIn("Prioritised fix plan", md)
        self.assertIn("Generated syllabus draft", md)

    def test_json_export_round_trips(self):
        import json
        payload = json.loads(exporters.to_json(self.result))
        self.assertEqual(payload["score"]["overall"], self.result["score"]["overall"])

    def test_csv_export_has_rows(self):
        csv_text = exporters.to_csv(self.result)
        lines = [ln for ln in csv_text.splitlines() if ln.strip()]
        self.assertGreater(len(lines), 20)
        self.assertTrue(lines[0].startswith("section,key,value"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
