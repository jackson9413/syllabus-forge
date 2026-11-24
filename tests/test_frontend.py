"""Frontend contract tests.

The browser cannot be screenshotted in this environment, so the UI is verified
by contract instead: every DOM id the JavaScript touches must exist in the
HTML, and every field the JavaScript reads must exist in the API response.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(ROOT, "static", "index.html")
JS_PATH = os.path.join(ROOT, "static", "app.js")

with open(HTML_PATH, encoding="utf-8") as handle:
    HTML = handle.read()
with open(JS_PATH, encoding="utf-8") as handle:
    JS = handle.read()


class TestFrontendContract(unittest.TestCase):
    def test_every_js_selector_exists_in_html(self):
        ids_in_html = set(re.findall(r'id="([^"]+)"', HTML))
        referenced = set(re.findall(r'\$\("#([^"]+)"\)', JS))
        self.assertTrue(referenced, "no selectors found - the regex is probably wrong")
        missing = referenced - ids_in_html
        self.assertEqual(missing, set(), msg=f"JS references missing DOM ids: {missing}")

    def test_static_assets_referenced_exist(self):
        for asset in re.findall(r'(?:href|src)="(/static/[^"]+)"', HTML):
            self.assertTrue(os.path.exists(os.path.join(ROOT, asset.lstrip("/"))),
                            msg=f"missing asset {asset}")

    def test_js_reads_fields_the_api_actually_returns(self):
        import engine
        import samples
        result = engine.analyse_text(samples.SAMPLES["clean_course"]["brief"])
        for path in ("score.overall", "score.verdict", "score.axes", "meta.course",
                     "meta.code", "meta.term", "meta.level", "meta.credits",
                     "meta.weeks", "meta.meetings_per_week", "meta.minutes_per_meeting",
                     "meta.students", "totals.critical", "totals.high",
                     "totals.medium", "totals.low", "findings", "fix_plan",
                     "coverage", "course_map", "syllabus", "caps"):
            node = result
            for part in path.split("."):
                self.assertIn(part, node, msg=f"API is missing {path}")
                node = node[part]

    def test_finding_shape_matches_what_js_renders(self):
        import engine
        import samples
        result = engine.analyse_text(samples.SAMPLES["cram_term"]["brief"])
        for finding in result["findings"]:
            for field in ("severity", "title", "evidence", "why", "fix", "axis"):
                self.assertIn(field, finding)
            self.assertIn(finding["severity"], ("critical", "high", "medium", "low"))

    def test_course_map_shape_matches_what_js_renders(self):
        import engine
        import samples
        result = engine.analyse_text(samples.SAMPLES["cram_term"]["brief"])
        for row in result["course_map"]:
            for field in ("week", "topics", "assessments", "flags"):
                self.assertIn(field, row)
            for assessment in row["assessments"]:
                self.assertIn("name", assessment)
                self.assertIn("weight", assessment)

    def test_coverage_shape_matches_what_js_renders(self):
        import engine
        import samples
        result = engine.analyse_text(samples.SAMPLES["clean_course"]["brief"])
        for row in result["coverage"]:
            for field in ("id", "text", "taught_weeks", "assessed_by", "inferred"):
                self.assertIn(field, row)

    def test_api_endpoints_the_js_calls_exist(self):
        from app import app
        routes = {rule.rule for rule in app.url_map.iter_rules()}
        for endpoint in ("/api/analyze", "/api/export", "/api/runs", "/api/samples",
                         "/api/health"):
            self.assertIn(endpoint, routes)

    def test_html_is_well_formed_enough_to_parse(self):
        self.assertTrue(HTML.strip().startswith("<!DOCTYPE html>"))
        self.assertIn("</html>", HTML)
        self.assertEqual(HTML.count("<script"), HTML.count("</script>"))
        self.assertEqual(HTML.count("<textarea"), 1)
        self.assertEqual(HTML.count("<select"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
