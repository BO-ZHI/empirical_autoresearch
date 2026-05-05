#!/usr/bin/env python3
"""Public controller for the empirical-autoresearch example."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
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

GATE_COLUMNS = ["gate", "status", "severity", "evidence_path", "note"]
METRIC_COLUMNS = ["metric_name", "metric_value", "metric_direction", "description"]
LANGUAGE = "stata"
DESIGN = "regulatory-notch density design plus firm-year DiD and event study"
METRIC_NAME = "channel_separation_score"
METRIC_DIRECTION = "max"
EPSILON_KEEP = 0.05
BUDGET_MINUTES = 45.0


def project_path(value: str) -> Path:
    return Path(value).resolve()


def read_results(project: Path) -> list[dict[str, str]]:
    path = project / "results.tsv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != RESULT_COLUMNS:
            raise ValueError("results.tsv schema does not match the public controller contract")
        return list(reader)


def write_results(project: Path, rows: list[dict[str, str]]) -> None:
    path = project / "results.tsv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def append_result(project: Path, row: dict[str, str]) -> None:
    rows = read_results(project)
    rows.append(row)
    write_results(project, rows)


def read_tsv(path: Path, expected: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != expected:
            raise ValueError(f"{path} schema mismatch")
        return list(reader)


def git_ref(project: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "no_git_ref"


def best_kept(rows: list[dict[str, str]]) -> dict[str, str] | None:
    kept = []
    for row in rows:
        if row["decision"] == "keep" and row["gate_status"] == "pass":
            try:
                kept.append((float(row["metric_value"]), row))
            except ValueError:
                continue
    return max(kept, key=lambda item: item[0])[1] if kept else None


def next_run_id(rows: list[dict[str, str]], prefix: str) -> str:
    return f"{prefix}_{len(rows) + 1:03d}"


def ensure_log_files(project: Path, run_id: str, idea: str, decision: str, note: str) -> None:
    log_dir = project / "logs" / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "idea.md").write_text(f"# Idea\n\n{idea}\n", encoding="utf-8")
    (log_dir / "review.md").write_text(
        f"# Review\n\nDecision: {decision}.\n\nReview note: {note}\n",
        encoding="utf-8",
    )
    (log_dir / "feedback.md").write_text(
        "# Feedback\n\nUse the next iteration to add one bounded channel test while keeping the metric and gates fixed.\n",
        encoding="utf-8",
    )


def run_evaluator(project: Path, run_id: str) -> tuple[int, float]:
    log_dir = project / "logs" / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    command = ["python", "code/empirical_autoresearch/evaluate.py"]
    start = datetime.now(timezone.utc)
    result = subprocess.run(command, cwd=project, text=True, capture_output=True, timeout=int(BUDGET_MINUTES * 60))
    elapsed = (datetime.now(timezone.utc) - start).total_seconds() / 60
    (log_dir / "evaluate.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (log_dir / "evaluate.stderr.txt").write_text(result.stderr, encoding="utf-8")
    return result.returncode, elapsed


def parse_outputs(project: Path) -> tuple[str, str, str]:
    metric_rows = read_tsv(project / "output" / "metric.tsv", METRIC_COLUMNS)
    gate_rows = read_tsv(project / "output" / "gates.tsv", GATE_COLUMNS)
    if not metric_rows:
        raise ValueError("output/metric.tsv has no metric row")
    metric = metric_rows[0]
    if metric["metric_name"] != METRIC_NAME or metric["metric_direction"] != METRIC_DIRECTION:
        raise ValueError("metric output does not match the fixed contract")
    float(metric["metric_value"])
    gate_status = "pass" if all(row["status"] == "pass" for row in gate_rows) else "fail"
    return metric["metric_name"], metric["metric_value"], gate_status


def make_result_row(
    project: Path,
    run_id: str,
    phase: str,
    metric_value: str,
    gate_status: str,
    decision: str,
    runtime_minutes: float,
    idea: str,
    review_note: str,
    failure_cause: str = "none",
    complexity_delta: str = "0",
) -> dict[str, str]:
    parent = best_kept(read_results(project))
    parent_ref = parent["candidate_ref"] if parent else git_ref(project)
    candidate_ref = run_id if decision != "crash" else f"{run_id}_failed"
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "parent_ref": parent_ref,
        "candidate_ref": candidate_ref,
        "language": LANGUAGE,
        "design": DESIGN,
        "phase": phase,
        "metric_name": METRIC_NAME,
        "metric_value": metric_value,
        "metric_direction": METRIC_DIRECTION,
        "gate_status": gate_status,
        "complexity_delta": complexity_delta,
        "decision": decision,
        "runtime_minutes": f"{runtime_minutes:.2f}",
        "idea": idea,
        "review_note": review_note,
        "failure_cause": failure_cause,
    }


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


def setup(project: Path) -> int:
    status = doctor(project)
    if status:
        return status
    rows = read_results(project)
    best = best_kept(rows)
    state_dir = project / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "current_best_ref": best["candidate_ref"] if best else git_ref(project),
        "best_metric": best["metric_value"] if best else None,
        "run_counter": len(rows),
        "branch_name": git_ref(project),
        "active_brief": "research_brief.md",
        "editable_driver_path": "code/empirical_autoresearch/analyze.do",
    }
    (state_dir / "autoresearch_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    idea_bank = state_dir / "idea_bank.tsv"
    if not idea_bank.exists():
        idea_bank.write_text("run_id\tidea\tstatus\tnote\n", encoding="utf-8")
    print("[OK] state/autoresearch_state.json")
    print("[OK] state/idea_bank.tsv")
    return 0


def baseline(project: Path) -> int:
    rows = read_results(project)
    existing = [row for row in rows if row["phase"] == "baseline"]
    if existing:
        print(f"[OK] baseline already recorded as {existing[0]['run_id']}")
        return 0
    return run_once(project, "baseline", "baseline channel-separation evaluation", "baseline_001")


def decide(rows: list[dict[str, str]], metric_value: str, gate_status: str, complexity_delta: int) -> tuple[str, str]:
    if gate_status != "pass":
        return "discard", "hard gate failed"
    incumbent = best_kept(rows)
    if incumbent is None:
        return "keep", "first gate-passing state"
    delta = float(metric_value) - float(incumbent["metric_value"])
    if delta >= EPSILON_KEEP:
        return "keep", "metric improved by at least epsilon_keep"
    if abs(delta) < EPSILON_KEEP and complexity_delta < 0:
        return "keep", "metric tied and code became simpler"
    return "discard", "candidate did not clear epsilon_keep or simplicity rule"


def run_once(project: Path, phase: str, idea: str, run_id: str | None = None) -> int:
    rows = read_results(project)
    run_id = run_id or next_run_id(rows, phase)
    try:
        return_code, runtime = run_evaluator(project, run_id)
    except subprocess.TimeoutExpired:
        row = make_result_row(project, run_id, phase, "NaN", "fail", "crash", BUDGET_MINUTES, idea, "timeout exceeded budget", "timeout")
        append_result(project, row)
        ensure_log_files(project, run_id, idea, "crash", row["review_note"])
        print(f"[CRASH] {run_id} timeout")
        return 1
    if return_code:
        row = make_result_row(project, run_id, phase, "NaN", "fail", "crash", runtime, idea, "evaluator returned a nonzero exit status", "evaluator_failure")
        append_result(project, row)
        ensure_log_files(project, run_id, idea, "crash", row["review_note"])
        print(f"[CRASH] {run_id} evaluator_failure")
        return return_code
    _, metric_value, gate_status = parse_outputs(project)
    if phase == "baseline":
        decision, note = ("keep", "baseline state recorded") if gate_status == "pass" else ("discard", "baseline gate failed")
    else:
        decision, note = decide(rows, metric_value, gate_status, complexity_delta=0)
    row = make_result_row(project, run_id, phase, metric_value, gate_status, decision, runtime, idea, note)
    append_result(project, row)
    ensure_log_files(project, run_id, idea, decision, note)
    print(f"[{decision.upper()}] {run_id} metric={metric_value} gates={gate_status}")
    return 0


def iterate(project: Path, idea: str) -> int:
    rows = read_results(project)
    run_id = next_run_id(rows, "iterate")
    return run_once(project, "iterate", idea, run_id)


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
    for command in ["setup", "baseline", "doctor", "summarize"]:
        sub = subparsers.add_parser(command)
        sub.add_argument("--project", default=".", type=project_path)
    run_parser = subparsers.add_parser("run-once")
    run_parser.add_argument("--project", default=".", type=project_path)
    run_parser.add_argument("--phase", default="iterate", choices=["baseline", "iterate"])
    run_parser.add_argument("--idea", default="manual bounded empirical change")
    run_parser.add_argument("--run-id", default=None)
    iterate_parser = subparsers.add_parser("iterate")
    iterate_parser.add_argument("--project", default=".", type=project_path)
    iterate_parser.add_argument("--idea", required=True)
    args = parser.parse_args()
    if args.command == "setup":
        return setup(args.project)
    if args.command == "baseline":
        return baseline(args.project)
    if args.command == "doctor":
        return doctor(args.project)
    if args.command == "run-once":
        return run_once(args.project, args.phase, args.idea, args.run_id)
    if args.command == "iterate":
        return iterate(args.project, args.idea)
    if args.command == "summarize":
        return summarize(args.project)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
