#!/usr/bin/env python3
"""Syllabus Forge - Flask application and REST API."""

from __future__ import annotations

import io
import os
import sys

from flask import Flask, jsonify, request, send_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine          # noqa: E402
import exporters      # noqa: E402
import storage        # noqa: E402
from samples import list_samples  # noqa: E402

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["JSON_SORT_KEYS"] = False


@app.after_request
def _no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/")
def index():
    return send_file(os.path.join(app.static_folder, "index.html"))


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "service": "syllabus-forge",
                    "profiles": sorted(engine.PROFILES.keys())})


@app.route("/api/samples")
def samples():
    return jsonify({"samples": list_samples()})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    brief = payload.get("brief", "")
    profile = payload.get("profile", "general")
    if profile not in engine.PROFILES:
        return jsonify({"error": f"Unknown profile '{profile}'"}), 400
    if not brief.strip():
        return jsonify({"error": "A course brief is required."}), 400
    result = engine.analyse_text(brief, profile=profile)
    return jsonify(result)


@app.route("/api/export", methods=["POST"])
def export():
    payload = request.get_json(silent=True) or {}
    brief = payload.get("brief", "")
    fmt = payload.get("format", "md")
    profile = payload.get("profile", "general")
    if not brief.strip():
        return jsonify({"error": "A course brief is required."}), 400
    if fmt not in ("md", "json", "csv"):
        return jsonify({"error": "format must be md, json or csv"}), 400
    result = engine.analyse_text(brief, profile=profile)
    if fmt == "json":
        body, mimetype, name = exporters.to_json(result), "application/json", "syllabus-review.json"
    elif fmt == "csv":
        body, mimetype, name = exporters.to_csv(result), "text/csv", "syllabus-review.csv"
    else:
        body, mimetype, name = exporters.to_markdown(result), "text/markdown", "syllabus-review.md"
    return send_file(io.BytesIO(body.encode("utf-8")), mimetype=mimetype,
                     as_attachment=True, download_name=name)


@app.route("/api/runs", methods=["GET"])
def runs_list():
    return jsonify({"runs": storage.list_runs()})


@app.route("/api/runs", methods=["POST"])
def runs_create():
    payload = request.get_json(silent=True) or {}
    brief = payload.get("brief", "")
    profile = payload.get("profile", "general")
    if not brief.strip():
        return jsonify({"error": "A course brief is required."}), 400
    result = engine.analyse_text(brief, profile=profile)
    title = payload.get("title") or result["meta"]["course"]
    run_id = storage.save_run(title, profile, brief, result,
                              rating=payload.get("rating"), notes=payload.get("notes", ""))
    return jsonify({"id": run_id, "run": storage.get_run(run_id)}), 201


@app.route("/api/runs/<int:run_id>", methods=["GET"])
def runs_get(run_id):
    run = storage.get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(run)


@app.route("/api/runs/<int:run_id>", methods=["PATCH"])
def runs_update(run_id):
    payload = request.get_json(silent=True) or {}
    rating = payload.get("rating")
    if rating is not None:
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return jsonify({"error": "rating must be an integer 1-5"}), 400
        if rating < 1 or rating > 5:
            return jsonify({"error": "rating must be between 1 and 5"}), 400
    run = storage.update_run(run_id, rating=rating, notes=payload.get("notes"))
    if not run:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(run)


@app.route("/api/runs/<int:run_id>", methods=["DELETE"])
def runs_delete(run_id):
    if storage.delete_run(run_id):
        return jsonify({"deleted": run_id})
    return jsonify({"error": "Run not found"}), 404


if __name__ == "__main__":
    storage.init_db()
    port = int(os.environ.get("PORT", "5055"))
    app.run(host="127.0.0.1", port=port, debug=False)
