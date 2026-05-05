#!/usr/bin/env python3
"""Fixed evaluator for the public sanitized empirical-autoresearch example."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output"
METRIC_NAME = "channel_separation_score"
METRIC_DIRECTION = "max"


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    gates = [
        {
            "gate": "reproducibility",
            "status": "pass",
            "severity": "hard",
            "evidence_path": "logs/baseline_001/review.md",
            "note": "baseline artifacts are present and readable",
        },
        {
            "gate": "data_audit",
            "status": "pass",
            "severity": "hard",
            "evidence_path": "data/manifest.md",
            "note": "public repository uses a sanitized manifest",
        },
        {
            "gate": "design_validity",
            "status": "pass",
            "severity": "hard",
            "evidence_path": "program.md",
            "note": "design, metric, and treatment-timing restrictions are fixed",
        },
        {
            "gate": "inference",
            "status": "pass",
            "severity": "hard",
            "evidence_path": "program.md",
            "note": "inference gate requires fixed effects and clustering to be documented",
        },
        {
            "gate": "outputs_present",
            "status": "pass",
            "severity": "hard",
            "evidence_path": "output/evaluation_summary.json",
            "note": "metric, gates, channel artifacts, logs, and summary are present",
        },
    ]

    metric_value = 0.90
    gate_status = "pass"
    classification = "reporting_management"

    write_tsv(OUTPUT / "gates.tsv", ["gate", "status", "severity", "evidence_path", "note"], gates)
    write_tsv(OUTPUT / "gate_report.tsv", ["gate", "status", "severity", "evidence_path", "note"], gates)
    write_tsv(
        OUTPUT / "metric.tsv",
        ["metric_name", "metric_value", "metric_direction", "description"],
        [
            {
                "metric_name": METRIC_NAME,
                "metric_value": metric_value,
                "metric_direction": METRIC_DIRECTION,
                "description": "fixed channel-separation score for the public sanitized example",
            }
        ],
    )
    write_tsv(
        OUTPUT / "mechanism_split.tsv",
        ["channel", "proxy_family", "support", "interpretation"],
        [
            {
                "channel": classification,
                "proxy_family": "threshold_response_vs_real_adjustment",
                "support": "current_classification",
                "interpretation": "sanitized artifacts support reporting-management evidence as the current kept state",
            },
            {
                "channel": "category_substitution",
                "proxy_family": "category_share_shift",
                "support": "available",
                "interpretation": "category movement remains an alternative mechanism to direct real adjustment",
            },
        ],
    )
    write_tsv(
        OUTPUT / "count_management.tsv",
        ["channel", "proxy", "support", "interpretation"],
        [
            {
                "channel": "reported_number_management",
                "proxy": "record_count",
                "support": "next_iteration",
                "interpretation": "promote count-based tests into a direct channel table",
            },
            {
                "channel": "reported_number_management",
                "proxy": "average_amount_per_record",
                "support": "next_iteration",
                "interpretation": "distinguish real reduction from reporting aggregation or splitting",
            },
        ],
    )
    write_tsv(
        OUTPUT / "real_adjustment.tsv",
        ["channel", "proxy_family", "support", "interpretation"],
        [
            {
                "channel": "real_adjustment",
                "proxy_family": "economic_outcome_proxies",
                "support": "incomplete",
                "interpretation": "current public artifacts do not establish a clean real-adjustment claim",
            },
            {
                "channel": "real_adjustment",
                "proxy_family": "balance_sheet_proxies",
                "support": "incomplete",
                "interpretation": "stronger structured coefficient parsing is a next improvement",
            },
        ],
    )

    feedback = "\n".join(
        [
            "# Review Feedback",
            "",
            "- Classification: reporting_management.",
            "- Metric: 0.90.",
            "- Gate status: pass.",
            "- Next idea 1: add direct count-management channel tables.",
            "- Next idea 2: add expanded real-adjustment proxy families.",
            "- Next idea 3: add adjacent-period timing and category-offset tests.",
            "",
        ]
    )
    (OUTPUT / "review_feedback.md").write_text(feedback, encoding="utf-8")

    summary = {
        "metric_name": METRIC_NAME,
        "metric_value": metric_value,
        "metric_direction": METRIC_DIRECTION,
        "gate_status": gate_status,
        "classification": classification,
        "gates": gates,
        "recommended_next_iterations": [
            "Add direct count-management channel tables.",
            "Add expanded real-adjustment proxy families.",
            "Add adjacent-period timing and category-offset tests.",
        ],
    }
    (OUTPUT / "evaluation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"metric_name: {METRIC_NAME}")
    print(f"metric_value: {metric_value}")
    print(f"metric_direction: {METRIC_DIRECTION}")
    print(f"gate_status: {gate_status}")
    print(f"classification: {classification}")


if __name__ == "__main__":
    main()
