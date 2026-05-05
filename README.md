# Empirical Autoresearch Workflow

This repository contains a public, sanitized example of an autoresearch-style empirical workflow for PS9. It adapts the core design from Andrej Karpathy's `autoresearch` project to an empirical threshold-response setting.

## Project

The empirical question is whether regulated firms respond to a disclosure threshold through real changes in underlying activity or through management of reported counts, timing, and classifications.

The workflow uses one scalar metric, `channel_separation_score`, plus hard validity gates. The metric is maximized and is extracted from `output/metric.tsv`.

## Repository Structure

- `program.md`: complete human-authored research process contract.
- `research_brief.md`: fixed metric, design, budget, boundaries, and constraints.
- `code/empirical_autoresearch/analyze.do`: the only editable empirical driver.
- `code/empirical_autoresearch/prepare.do`: read-only setup harness.
- `code/empirical_autoresearch/evaluate.py`: read-only evaluation harness.
- `data/manifest.md`: public sanitized data manifest.
- `results.tsv`: experiment history.
- `logs/`: iteration idea, review, and feedback notes.
- `output/`: metric, gates, mechanism artifacts, and evaluation summary.
- `reports/execution_summary.md`: PS9-ready execution summary.
- `scripts/controller.py`: public controller with setup, baseline, iterate, run-once, summarize, and doctor commands.

## Run Order

```powershell
python scripts/controller.py doctor --project .
python scripts/controller.py setup --project .
python scripts/controller.py baseline --project .
python scripts/controller.py summarize --project .
python code/empirical_autoresearch/evaluate.py
```

To run one new bounded iteration in the public scaffold:

```powershell
python scripts/controller.py iterate --project . --idea "add one predeclared channel test"
```

The Stata files document the empirical workflow. A full Stata run requires a local Stata installation and a project-specific dataset. The public repository includes sanitized artifacts so the PS9 workflow is inspectable without confidential data.

## Autoresearch Rules

- Keep one editable experiment file: `code/empirical_autoresearch/analyze.do`.
- Keep `prepare.do`, `evaluate.py`, `program.md`, and `research_brief.md` fixed during autonomous search.
- Keep the wall-clock budget fixed at 45 minutes per run.
- Keep the metric fixed as `channel_separation_score`.
- Keep live loop state in `results.tsv`, `logs/`, `output/`, and `state/`.
- Keep a candidate only if all hard gates pass and the metric improves by at least `epsilon_keep`.
- Discard or crash candidates that fail gates, time out, worsen the metric, or add complexity without useful improvement.

## Current Result

The baseline channel-separation evaluator is the current kept state:

- Metric: `channel_separation_score = 0.90`.
- Gate status: `pass`.
- Decision: `keep`.
- Interpretation: current sanitized evidence supports a threshold-response pattern consistent with reporting management or category movement, while direct real-adjustment evidence remains incomplete.

## AI Use Disclosure

This repository was prepared with an OpenAI coding agent. The agent was prompted to design an empirical autoresearch workflow, implement a controller and evaluation harness, run a sanitized forward test, and prepare PS9 documentation.
