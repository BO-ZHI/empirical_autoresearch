---
research_question: "Do regulated firms respond to a disclosure threshold through real activity changes or through reported-number management?"
estimand: "Pre-policy near-threshold exposure effect on post-policy threshold behavior, separated into real-adjustment and reporting-management channels"
empirical_design: "regulatory-notch density design plus firm-year difference-in-differences and event-study checks"
dataset_path_or_manifest: "data/manifest.md"
language: "stata"
metric_name: "channel_separation_score"
metric_direction: "max"
metric_extractor: "output/metric.tsv::metric_value"
epsilon_keep: 0.05
budget_minutes: 45
run_tag: "sanitized-threshold-response"
max_repair_attempts: 2
timeout_multiplier: 1.0
gate_mode: "hard"
review_mode: "continuous"
results_tracking: "live_untracked"
forbidden_edits:
  - "Do not modify raw or confidential source data."
  - "Do not change the metric definition during an iteration."
  - "Do not use post-treatment outcomes to redefine treatment status."
  - "Do not edit evaluate.py during the autonomous loop."
hard_constraints:
  - "Pass a reproducibility gate before any candidate can be kept."
  - "Pass a data-audit gate before any candidate can be kept."
  - "Pass a design-validity gate with pre-policy treatment definitions and placebo checks."
  - "Pass an inference gate documenting fixed effects and clustering choices."
  - "Pass an outputs-present gate for metric, gates, logs, and mechanism artifacts."
---

This brief defines a public, sanitized empirical-autoresearch workflow. The score rewards separation between reported-number management and real underlying adjustment while refusing raw statistical-significance optimization.
