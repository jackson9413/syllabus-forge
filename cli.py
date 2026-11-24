#!/usr/bin/env python3
"""Command-line interface for Syllabus Forge.

Usage:
    python3 cli.py --brief course.txt
    python3 cli.py --sample clean_course --format md
    python3 cli.py --brief course.txt --profile pacing_audit --save
"""

from __future__ import annotations

import argparse
import sys

import engine
import exporters
import samples as sample_module


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Review a course brief for syllabus readiness.")
    parser.add_argument("--brief", help="path to a text file containing the course brief")
    parser.add_argument("--sample", help="id of a built-in sample brief")
    parser.add_argument("--profile", default="general", choices=sorted(engine.PROFILES.keys()))
    parser.add_argument("--format", default="md", choices=["md", "json", "csv"])
    parser.add_argument("--save", action="store_true", help="save the run to the local SQLite log")
    args = parser.parse_args(argv)

    if args.sample:
        if args.sample not in sample_module.SAMPLES:
            print(f"Unknown sample '{args.sample}'. Available: "
                  f"{', '.join(sample_module.SAMPLES.keys())}", file=sys.stderr)
            return 2
        brief = sample_module.SAMPLES[args.sample]["brief"]
    elif args.brief:
        try:
            with open(args.brief, "r", encoding="utf-8") as handle:
                brief = handle.read()
        except OSError as exc:
            print(f"Could not read {args.brief}: {exc}", file=sys.stderr)
            return 2
    else:
        print("Provide --brief <file> or --sample <id>", file=sys.stderr)
        return 2

    result = engine.analyse_text(brief, profile=args.profile)

    if args.save:
        import storage
        run_id = storage.save_run(result["meta"]["course"], args.profile, brief, result)
        print(f"Saved run #{run_id} to the local log.", file=sys.stderr)

    if args.format == "json":
        print(exporters.to_json(result))
    elif args.format == "csv":
        print(exporters.to_csv(result))
    else:
        print(exporters.to_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
