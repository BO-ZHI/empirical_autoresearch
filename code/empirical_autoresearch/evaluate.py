#!/usr/bin/env python3
"""Fixed evaluator for the public empirical-autoresearch fixture."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic_threshold_response.csv"
OUTPUT = ROOT / "output"
METRIC_NAME = "channel_separation_score"
METRIC_DIRECTION = "max"
REQUIRED_DATA_COLUMNS = {
    "firm_id",
    "year",
    "treat",
    "post",
    "near_threshold",
    "reported_count",
    "below_threshold_mass",
    "avg_amount_per_record",
    "real_activity_proxy",
    "category_shift",
}
REQUIRED_OUTPUTS = [
    "prepare_status.tsv",
    "run_manifest.tsv",
    "channel_stats.tsv",
    "regression_summary.tsv",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def coefficient(rows: list[dict[str, str]], dependent_variable: str) -> float | None:
    for row in rows:
        if row.get("dependent_variable") == dependent_variable:
            return float(row["coefficient"])
    return None


def gate_row(gate: str, status: bool, evidence_path: str, note: str) -> dict[str, str]:
    return {
        "gate": gate,
        "status": "pass" if status else "fail",
        "severity": "hard",
        "evidence_path": evidence_path,
        "note": note,
    }


def validate_data(rows: list[dict[str, str]]) -> tuple[bool, str]:
    if not rows:
        return False, "synthetic fixture has no rows"
    missing = REQUIRED_DATA_COLUMNS.difference(rows[0].keys())
    if missing:
        return False, "missing columns: " + ", ".join(sorted(missing))
    cells = {(row["treat"], row["post"]) for row in rows}
    if cells != {("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")}:
        return False, "fixture lacks all treatment-by-period cells"
    return True, "synthetic fixture has required fields and all design cells"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    data_rows = read_csv(DATA) if DATA.exists() else []
    data_ok, data_note = validate_data(data_rows)

    output_status = {name: (OUTPUT / name).exists() for name in REQUIRED_OUTPUTS}
    regression_rows = read_tsv(OUTPUT / "regression_summary.tsv") if output_status["regression_summary.tsv"] else []
    stats_rows = read_tsv(OUTPUT / "channel_stats.tsv") if output_status["channel_stats.tsv"] else []

    count_coef = coefficient(regression_rows, "reported_count")
    mass_coef = coefficient(regression_rows, "below_threshold_mass")
    real_coef = coefficient(regression_rows, "real_activity_proxy")
    category_coef = coefficient(regression_rows, "category_shift")

    inference_ok = all(value is not None for value in [count_coef, mass_coef, real_coef, category_coef])
    design_ok = data_ok and len(stats_rows) == 4
    reproducibility_ok = output_status["prepare_status.tsv"] and output_status["run_manifest.tsv"]
    outputs_ok = all(output_status.values())

    gates = [
        gate_row(
            "reproducibility",
            reproducibility_ok,
            "output/prepare_status.tsv; output/run_manifest.tsv",
            "prep and driver manifests exist" if reproducibility_ok else "prep or driver manifest missing",
        ),
        gate_row("data_audit", data_ok, "data/synthetic_threshold_response.csv", data_note),
        gate_row(
            "design_validity",
            design_ok,
            "output/channel_stats.tsv",
            "all treatment-period cells are present" if design_ok else "missing design cell summary",
        ),
        gate_row(
            "inference",
            inference_ok,
            "output/regression_summary.tsv",
            "driver exported coefficient, standard-error, and sample-size rows"
            if inference_ok
            else "regression summary lacks required rows",
        ),
        gate_row(
            "outputs_present",
            outputs_ok,
            "output/",
            "required public fixture artifacts are present" if outputs_ok else "one or more required artifacts are missing",
        ),
    ]
    gate_status = "pass" if all(row["status"] == "pass" for row in gates) else "fail"

    reporting_score = 0.0
    reporting_score += 0.25 if count_coef is not None and count_coef < -2 else 0.0
    reporting_score += 0.20 if mass_coef is not None and mass_coef > 0.1 else 0.0
    reporting_score += 0.15 if category_coef is not None and category_coef > 0.1 else 0.0
    reporting_score += 0.15 if real_coef is not None and abs(real_coef) < 2 else 0.0
    reporting_score += 0.15 if gate_status == "pass" else 0.0
    metric_value = round(reporting_score, 2)
    classification = "reporting_management" if metric_value >= 0.75 else "inconclusive"

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
                "description": "fixture-based channel-separation score with hard gates applied",
            }
        ],
    )
    write_tsv(
        OUTPUT / "mechanism_split.tsv",
        ["channel", "proxy_family", "support", "interpretation"],
        [
            {
                "channel": classification,
                "proxy_family": "count_bunching_category_shift",
                "support": "current_classification",
                "interpretation": "synthetic fixture shows stronger reporting-channel movement than real-activity movement",
            },
            {
                "channel": "real_adjustment",
                "proxy_family": "real_activity_proxy",
                "support": "weak",
                "interpretation": "real-activity interaction is small relative to reporting-channel interactions",
            },
        ],
    )
    write_tsv(
        OUTPUT / "count_management.tsv",
        ["channel", "proxy", "coefficient", "support", "interpretation"],
        [
            {
                "channel": "reported_number_management",
                "proxy": "reported_count",
                "coefficient": count_coef,
                "support": "strong" if count_coef is not None and count_coef < -2 else "weak",
                "interpretation": "treated post-period units report fewer records in the synthetic fixture",
            },
            {
                "channel": "reported_number_management",
                "proxy": "below_threshold_mass",
                "coefficient": mass_coef,
                "support": "strong" if mass_coef is not None and mass_coef > 0.1 else "weak",
                "interpretation": "treated post-period units show higher below-threshold mass in the synthetic fixture",
            },
        ],
    )
    write_tsv(
        OUTPUT / "real_adjustment.tsv",
        ["channel", "proxy_family", "coefficient", "support", "interpretation"],
        [
            {
                "channel": "real_adjustment",
                "proxy_family": "real_activity_proxy",
                "coefficient": real_coef,
                "support": "weak" if real_coef is not None and abs(real_coef) < 2 else "mixed",
                "interpretation": "real-activity proxy moves less than reporting-channel proxies",
            }
        ],
    )

    feedback = "\n".join(
        [
            "# Review Feedback",
            "",
            f"- Classification: {classification}.",
            f"- Metric: {metric_value:.2f}.",
            f"- Gate status: {gate_status}.",
            "- Next idea 1: replace the fixture with authorized project data after data-lock review.",
            "- Next idea 2: expand the coefficient parser to direct count, timing, and category-substitution tables.",
            "- Next idea 3: require a clean Stata rerun before any claim-ready empirical statement.",
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
        "coefficients": {
            "reported_count": count_coef,
            "below_threshold_mass": mass_coef,
            "real_activity_proxy": real_coef,
            "category_shift": category_coef,
        },
        "gates": gates,
        "recommended_next_iterations": [
            "Run the same harness on authorized project data.",
            "Add structured coefficient parsing for timing and category-offset tests.",
            "Use clean Stata reruns before claim-ready review.",
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
