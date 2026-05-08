#!/usr/bin/env python3
"""Public controller for the empirical-autoresearch example."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
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
EDITABLE_DRIVER = Path("code/empirical_autoresearch/analyze.do")
LIVE_PREFIXES = ("results.tsv", "logs/", "output/", "state/")


def project_path(value: str) -> Path:
    return Path(value).resolve()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(
    command: list[str],
    project: Path,
    *,
    timeout_seconds: int | None = None,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    stdout_handle = stdout_path.open("w", encoding="utf-8") if stdout_path else subprocess.PIPE
    stderr_handle = stderr_path.open("w", encoding="utf-8") if stderr_path else subprocess.PIPE
    try:
        return subprocess.run(
            command,
            cwd=project,
            text=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
            timeout=timeout_seconds,
            check=False,
        )
    finally:
        if stdout_path:
            stdout_handle.close()
        if stderr_path:
            stderr_handle.close()


def git(project: Path, args: list[str], *, check: bool = True) -> str:
    proc = run_command(["git", *args], project)
    if check and proc.returncode != 0:
        stderr = proc.stderr.strip() if proc.stderr else ""
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return (proc.stdout or "").strip()


def has_git(project: Path) -> bool:
    proc = run_command(["git", "rev-parse", "--is-inside-work-tree"], project)
    return proc.returncode == 0 and (proc.stdout or "").strip() == "true"


def has_head(project: Path) -> bool:
    proc = run_command(["git", "rev-parse", "--verify", "HEAD"], project)
    return proc.returncode == 0


def short_ref(project: Path) -> str:
    if has_git(project) and has_head(project):
        return git(project, ["rev-parse", "--short", "HEAD"])
    return "no_git_ref"


def full_ref(project: Path) -> str:
    if has_git(project) and has_head(project):
        return git(project, ["rev-parse", "HEAD"])
    return "no_git_ref"


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


def write_note_files(project: Path, run_id: str, idea: str, decision: str, note: str) -> None:
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


def stata_executable() -> str:
    candidates = [
        os.environ.get("STATA_CLI"),
        shutil.which("stata-mp"),
        shutil.which("stata"),
        shutil.which("StataMP-64.exe"),
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    raise RuntimeError("Set STATA_CLI to a local Stata executable before running Stata phases.")


def command_for(path: Path) -> list[str]:
    if path.suffix == ".py":
        return ["python", str(path)]
    if path.suffix == ".do":
        exe = stata_executable()
        if os.name == "nt":
            return [exe, "/e", "do", str(path)]
        return [exe, "-b", "do", str(path)]
    raise RuntimeError(f"unsupported phase file: {path}")


def run_phase(project: Path, run_dir: Path, name: str, path: Path) -> tuple[bool, float, str]:
    stdout_path = run_dir / f"{name}.stdout.log"
    stderr_path = run_dir / f"{name}.stderr.log"
    start = datetime.now(timezone.utc)
    try:
        command = command_for(path)
        proc = run_command(
            command,
            project,
            timeout_seconds=int(BUDGET_MINUTES * 60),
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
    except subprocess.TimeoutExpired:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() / 60
        return False, elapsed, f"{name} timed out"
    except Exception as exc:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() / 60
        stderr_path.write_text(str(exc), encoding="utf-8")
        return False, elapsed, f"{name} failed: {exc}"
    elapsed = (datetime.now(timezone.utc) - start).total_seconds() / 60
    if proc.returncode != 0:
        return False, elapsed, f"{name} returned exit code {proc.returncode}"
    return True, elapsed, "none"


def run_pipeline(project: Path, run_id: str) -> tuple[bool, float, str]:
    run_dir = project / "logs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    phases = [
        ("prepare", Path("code/empirical_autoresearch/prepare.do")),
        ("analyze", EDITABLE_DRIVER),
        ("evaluate", Path("code/empirical_autoresearch/evaluate.py")),
    ]
    total = 0.0
    for name, rel_path in phases:
        ok, runtime, failure = run_phase(project, run_dir, name, rel_path)
        total += runtime
        if not ok:
            return False, total, failure
    return True, total, "none"


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
    parent_ref: str | None = None,
    candidate_ref: str | None = None,
) -> dict[str, str]:
    parent = best_kept(read_results(project))
    return {
        "run_id": run_id,
        "timestamp": now_iso(),
        "parent_ref": parent_ref or (parent["candidate_ref"] if parent else full_ref(project)),
        "candidate_ref": candidate_ref or full_ref(project),
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


def changed_paths(project: Path) -> list[str]:
    output = git(project, ["status", "--porcelain"], check=True)
    paths: list[str] = []
    for line in output.splitlines():
        if len(line) > 3:
            paths.append(line[3:].replace("\\", "/"))
    return paths


def is_live_path(path: str) -> bool:
    return path in LIVE_PREFIXES or any(path.startswith(prefix) for prefix in LIVE_PREFIXES if prefix.endswith("/"))


def enforce_edit_boundary(project: Path) -> None:
    allowed = EDITABLE_DRIVER.as_posix()
    relevant = [path for path in changed_paths(project) if not is_live_path(path)]
    if not relevant:
        raise RuntimeError("no candidate driver-file change found")
    offenders = [path for path in relevant if path != allowed]
    if offenders:
        raise RuntimeError("only the editable driver may change before iterate: " + ", ".join(offenders))


def commit_candidate(project: Path, idea: str) -> tuple[str, str]:
    parent = full_ref(project)
    git(project, ["add", EDITABLE_DRIVER.as_posix()])
    git(project, ["commit", "-m", f"Candidate: {idea[:72]}"])
    return parent, full_ref(project)


def driver_diff(project: Path, parent: str, candidate: str) -> str:
    return git(project, ["diff", f"{parent}..{candidate}", "--", EDITABLE_DRIVER.as_posix()])


def complexity_delta(project: Path, parent: str, candidate: str) -> int:
    try:
        before = git(project, ["show", f"{parent}:{EDITABLE_DRIVER.as_posix()}"])
        after = git(project, ["show", f"{candidate}:{EDITABLE_DRIVER.as_posix()}"])
        return len([line for line in after.splitlines() if line.strip()]) - len(
            [line for line in before.splitlines() if line.strip()]
        )
    except Exception:
        return 0


def decide(rows: list[dict[str, str]], metric_value: str, gate_status: str, complexity: int) -> tuple[str, str]:
    if gate_status != "pass":
        return "discard", "hard gate failed"
    incumbent = best_kept(rows)
    if incumbent is None:
        return "keep", "first gate-passing state"
    delta = float(metric_value) - float(incumbent["metric_value"])
    if delta >= EPSILON_KEEP:
        return "keep", "metric improved by at least epsilon_keep"
    if abs(delta) < EPSILON_KEEP and complexity < 0:
        return "keep", "metric tied and code became simpler"
    return "discard", "candidate did not clear epsilon_keep or simplicity rule"


def append_feedback(project: Path, run_id: str, idea: str, decision: str, note: str) -> None:
    state_dir = project / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "idea_bank.tsv"
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        if not exists:
            writer.writerow(["run_id", "idea", "decision", "note"])
        writer.writerow([run_id, idea, decision, note])


def execute_candidate(
    project: Path,
    run_id: str,
    phase: str,
    idea: str,
    parent_ref: str,
    candidate_ref: str,
    complexity: int,
) -> int:
    run_dir = project / "logs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    if parent_ref != candidate_ref:
        (run_dir / "driver.diff").write_text(driver_diff(project, parent_ref, candidate_ref), encoding="utf-8")
    ok, runtime, failure = run_pipeline(project, run_id)
    if not ok:
        row = make_result_row(
            project,
            run_id,
            phase,
            "NaN",
            "fail",
            "crash",
            runtime,
            idea,
            failure,
            failure,
            str(complexity),
            parent_ref,
            candidate_ref,
        )
        append_result(project, row)
        write_note_files(project, run_id, idea, "crash", failure)
        append_feedback(project, run_id, idea, "crash", failure)
        if has_git(project) and parent_ref != candidate_ref:
            git(project, ["reset", "--hard", parent_ref])
        print(f"[CRASH] {run_id} {failure}")
        return 1

    _, metric_value, gate_status = parse_outputs(project)
    clean_ok, _, clean_failure = run_pipeline(project, f"{run_id}_clean_rerun")
    if not clean_ok:
        gate_status = "fail"
        failure = clean_failure

    decision, note = decide(read_results(project), metric_value, gate_status, complexity)
    if failure != "none":
        note = failure
    row = make_result_row(
        project,
        run_id,
        phase,
        metric_value,
        gate_status,
        decision,
        runtime,
        idea,
        note,
        failure,
        str(complexity),
        parent_ref,
        candidate_ref,
    )
    append_result(project, row)
    write_note_files(project, run_id, idea, decision, note)
    append_feedback(project, run_id, idea, decision, note)
    if decision != "keep" and has_git(project) and parent_ref != candidate_ref:
        git(project, ["reset", "--hard", parent_ref])
    print(f"[{decision.upper()}] {run_id} metric={metric_value} gates={gate_status}")
    return 0 if decision in {"keep", "discard"} else 1


def doctor(project: Path) -> int:
    required = [
        "README.md",
        "program.md",
        "research_brief.md",
        "results.tsv",
        "data/manifest.md",
        "data/synthetic_threshold_response.csv",
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
        exists = (project / rel).exists()
        ok = ok and exists
        print(f"[{'OK' if exists else 'FAIL'}] {rel}")
    try:
        read_results(project)
        print("[OK] results.tsv schema")
    except Exception as exc:
        ok = False
        print(f"[FAIL] results.tsv schema: {exc}")
    if has_git(project):
        print(f"[OK] git repo {short_ref(project)}")
    else:
        print("[WARN] git repo missing, iterate cannot commit or reset candidates")
    try:
        stata_executable()
        print("[OK] Stata executable discovered")
    except Exception as exc:
        print(f"[WARN] {exc}")
    return 0 if ok else 1


def setup(project: Path) -> int:
    status = doctor(project)
    if status:
        return status
    state_dir = project / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    rows = read_results(project)
    best = best_kept(rows)
    state = {
        "current_best_ref": best["candidate_ref"] if best else full_ref(project),
        "best_metric": best["metric_value"] if best else None,
        "run_counter": len(rows),
        "branch_name": short_ref(project),
        "active_brief": "research_brief.md",
        "editable_driver_path": EDITABLE_DRIVER.as_posix(),
    }
    (state_dir / "autoresearch_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    append_feedback(project, "setup", "initialize public controller state", "keep", "state initialized")
    print("[OK] state/autoresearch_state.json")
    return 0


def baseline(project: Path) -> int:
    rows = read_results(project)
    existing = [row for row in rows if row["phase"] == "baseline"]
    if existing:
        print(f"[OK] baseline already recorded as {existing[0]['run_id']}")
        return 0
    return run_once(project, "baseline", "baseline channel-separation evaluation", "baseline_001")


def run_once(project: Path, phase: str, idea: str, run_id: str | None = None) -> int:
    rows = read_results(project)
    run_id = run_id or next_run_id(rows, phase)
    parent = full_ref(project)
    return execute_candidate(project, run_id, phase, idea, parent, parent, 0)


def iterate(project: Path, idea: str) -> int:
    if not has_git(project):
        raise RuntimeError("iterate requires a Git repository")
    enforce_edit_boundary(project)
    rows = read_results(project)
    run_id = next_run_id(rows, "iterate")
    parent, candidate = commit_candidate(project, idea)
    complexity = complexity_delta(project, parent, candidate)
    return execute_candidate(project, run_id, "iterate", idea, parent, candidate, complexity)


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
