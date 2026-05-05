#!/usr/bin/env python3
"""Minimal public controller for the empirical-autoresearch example."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


RESULT_COLUMNS = [
    "run_id",
    "timestamp",
    "parent_ref",
    "candidate_ref",
    "language",
    "design",
    "phase",
    "metric_name",
    "metric_value",
    "metric_direction",
    "gate_status",
    "complexity_delta",
    "decision",
    "runtime_minutes",
    "idea",
    "review_note",
    "failure_cause",
]


def project_path(value: str) -> Path:
    return Path(value).resolve()


def read_results(project: Path) -> list[dict[str, str]]:
    path = project / "results.tsv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != RESULT_COLUMNS:
            raise ValueError("results.tsv schema does not match the public controller contract")
        return list(reader)


def doctor(project: Path) -> int:
    required = [
        "README.md",
        "program.md",
        "research_brief.md",
        "results.tsv",
        "data/manifest.md",
        "code/empirical_autoresearch/analyze.do",
        "code/empirical_autoresearch/prepare.do",
        "code/empirical_autoresearch/evaluate.py",
        "output/metric.tsv",
        "output/gates.tsv",
        "output/evaluation_summary.json",
        "reports/execution_summary.md",
    ]
    ok = True
    for rel in required:
        path = project / rel
        exists = path.exists()
        ok = ok and exists
        print(f"[{'OK' if exists else 'FAIL'}] {rel}")
    if ok:
        read_results(project)
        print("[OK] results.tsv schema")
    return 0 if ok else 1


def summarize(project: Path) -> int:
    rows = read_results(project)
    kept = [row for row in rows if row["decision"] == "keep" and row["gate_status"] == "pass"]
    best = max(kept, key=lambda row: float(row["metric_value"])) if kept else None
    summary = {
        "runs": len(rows),
        "keeps": sum(row["decision"] == "keep" for row in rows),
        "discards": sum(row["decision"] == "discard" for row in rows),
        "crashes": sum(row["decision"] == "crash" for row in rows),
        "best_run": best["run_id"] if best else None,
        "best_metric": best["metric_value"] if best else None,
    }
    print(json.dumps(summary, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ["doctor", "summarize"]:
        sub = subparsers.add_parser(command)
        sub.add_argument("--project", default=".", type=project_path)
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor(args.project)
    if args.command == "summarize":
        return summarize(args.project)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
