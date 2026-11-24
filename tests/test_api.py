"""API tests for Syllabus Forge."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP_DB = tempfile.mkdtemp(prefix="syllabus-forge-test-")
os.environ["SYLLABUS_FORGE_DB"] = os.path.join(_TMP_DB, "test.db")

import app as application   # noqa: E402
import samples              # noqa: E402

application.app.config["TESTING"] = True
client = application.app.test_client()


class TestApi(unittest.TestCase):
    def test_health(self):
        resp = client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("general", data["profiles"])

    def test_samples_listing(self):
        resp = client.get("/api/samples")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertGreaterEqual(len(payload["samples"]), 6)
        ids = {s["id"] for s in payload["samples"]}
        self.assertIn("clean_course", ids)

    def test_analyze(self):
        resp = client.post("/api/analyze", json={
            "brief": samples.SAMPLES["clean_course"]["brief"], "profile": "general"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("score", data)
        self.assertIn("findings", data)
        self.assertIn("course_map", data)
        self.assertIn("syllabus", data)

    def test_analyze_rejects_empty_brief(self):
        resp = client.post("/api/analyze", json={"brief": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_analyze_rejects_unknown_profile(self):
        resp = client.post("/api/analyze", json={
            "brief": "Course: X", "profile": "nope"})
        self.assertEqual(resp.status_code, 400)

    def test_export_formats(self):
        for fmt in ("md", "json", "csv"):
            resp = client.post("/api/export", json={
                "brief": samples.SAMPLES["clean_course"]["brief"], "format": fmt})
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.data)

    def test_export_rejects_bad_format(self):
        resp = client.post("/api/export", json={
            "brief": "Course: X", "format": "pdf"})
        self.assertEqual(resp.status_code, 400)

    def test_run_lifecycle(self):
        resp = client.post("/api/runs", json={
            "brief": samples.SAMPLES["clean_course"]["brief"],
            "profile": "general", "title": "Test course"})
        self.assertEqual(resp.status_code, 201)
        run_id = resp.get_json()["id"]

        resp = client.get("/api/runs/%d" % run_id)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("result", resp.get_json())

        resp = client.patch("/api/runs/%d" % run_id, json={"rating": 4, "notes": "good"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["rating"], 4)

        resp = client.patch("/api/runs/%d" % run_id, json={"rating": 9})
        self.assertEqual(resp.status_code, 400)

        resp = client.get("/api/runs")
        self.assertTrue(any(r["id"] == run_id for r in resp.get_json()["runs"]))

        resp = client.delete("/api/runs/%d" % run_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(client.get("/api/runs/%d" % run_id).status_code, 404)

    def test_missing_run_is_404(self):
        self.assertEqual(client.get("/api/runs/999999").status_code, 404)

    def test_index_page_served(self):
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Syllabus Forge", resp.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
