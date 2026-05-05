# Empirical Autoresearch Program

## Setup

Research question: do regulated firms respond to a disclosure threshold through real changes in underlying activity or through reported-number management?

Estimand: pre-policy near-threshold exposure effect on post-policy threshold behavior, separated into real-adjustment and reporting-management channels.

Empirical design: regulatory-notch density design plus firm-year difference-in-differences and event-study checks.

Primary language: Stata for the empirical driver, Python for the fixed evaluator.

Metric:
- Name: `channel_separation_score`.
- Direction: `max`.
- Extractor: `output/metric.tsv::metric_value`.
- Minimum improvement to keep added complexity: `0.05`.
- Fixed wall-clock budget: `45` minutes per run.

The scalar metric is fixed for the full autonomous run. Hard gates are pass or fail and are evaluated separately from the metric.

## File Boundaries

Editable file:
- `code/empirical_autoresearch/analyze.do`.

Read-only files during the loop:
- `code/empirical_autoresearch/prepare.do`.
- `code/empirical_autoresearch/evaluate.py`.
- `program.md`.
- `research_brief.md`.
- `results.tsv` schema.
- `data/manifest.md`.

Forbidden changes:
- Do not modify raw or confidential source data.
- Do not change the metric during an iteration.
- Do not redefine treatment status using post-treatment outcomes.
- Do not edit the evaluation harness during the autonomous loop.
- Do not optimize p-values, stars, or the count of significant coefficients.
- Do not add new dependencies during the loop.

## Output Format

Every run must produce:
- `output/metric.tsv`.
- `output/gates.tsv`.
- `output/evaluation_summary.json`.
- `output/mechanism_split.tsv`.
- `output/count_management.tsv`.
- `output/real_adjustment.tsv`.
- `output/gate_report.tsv`.
- `output/review_feedback.md`.
- run notes under `logs/<run_id>/`.

`results.tsv` schema:

```tsv
run_id	timestamp	parent_ref	candidate_ref	language	design	phase	metric_name	metric_value	metric_direction	gate_status	complexity_delta	decision	runtime_minutes	idea	review_note	failure_cause
```

Valid decisions:
- `keep`.
- `discard`.
- `crash`.

## Hard Gates

The required gates are:
- `reproducibility`: the fixed pipeline completes and produces a readable run log.
- `data_audit`: sample construction and data lineage remain fixed and documented.
- `design_validity`: treatment, timing, threshold, and placebo checks match the research brief.
- `inference`: clustering, fixed effects, and standard-error choices match the design.
- `outputs_present`: expected tables, figures, metric files, gates, logs, and review notes exist.

No candidate can advance when a hard gate fails.

## Experiment Loop

The loop follows six phases.

1. Think: inspect the current kept state and write one bounded empirical idea to `logs/<run_id>/idea.md`.
2. Construct: edit only `analyze.do`, commit the candidate, and save a driver diff.
3. Analyze: run `prepare.do`, `analyze.do`, and `evaluate.py` within the fixed wall-clock budget.
4. Test: parse `output/metric.tsv`, `output/gates.tsv`, and `output/evaluation_summary.json`.
5. Review: compare candidate versus incumbent using metric direction, `epsilon_keep`, hard gates, and complexity delta.
6. Feedback: write `logs/<run_id>/feedback.md` and update the idea bank.

Keep the candidate only when every hard gate passes and the metric improves by at least `0.05`. If the metric is effectively tied, keep only when the candidate is simpler or cleaner. Discard and reset candidates that fail gates, worsen the metric, improve too little with added complexity, or drift from the estimand. Record `crash` after timeout or repeated repair failure.

## Mechanism Agenda

The first idea family tests reported-number management:
- below-threshold mass.
- record counts.
- average amount per record.
- subtype or counterparty counts.
- reporting category movement.

The second idea family tests real underlying adjustment:
- predeclared economic-outcome proxies.
- balance-sheet proxy families.
- cash-flow proxy families.
- aggregate-offset tests.

The third idea family tests timing and substitution:
- adjacent-period movement.
- alternative reporting categories.
- aggregate-offset tests.
- category-share shifts.

## Human Checkpoints

`data_lock_review`: review sample construction, merge logic, treatment coding, data lineage, and the manifest.

`claim_ready_result_review`: review main tables, figures, inference, and mechanism classification before making a publication-facing claim.

`estimand_or_design_shift_review`: review any proposal to change the estimand, design, metric, treatment definition, or fixed evaluator.

## Autonomy Policy

Continuous autonomy is appropriate after the data, metric, and evaluator are locked. Human oversight is required when data definitions, empirical claims, estimands, or gate definitions change.
