# Data Manifest

This public repository uses a sanitized data manifest and a small synthetic fixture. Confidential source data are excluded.

## Public Fields

The empirical workflow assumes a panel with:

- unit identifier.
- fiscal or calendar period.
- pre-policy exposure measure.
- post-policy indicator.
- threshold forcing variable.
- reported-count outcomes.
- real-adjustment proxy families.
- category and timing proxy families.

## Synthetic Fixture

The file `data/synthetic_threshold_response.csv` is a toy firm-year panel created only for public reproduction. It contains treated and control firms before and after a policy event. The synthetic values are designed to show a stronger change in reported-count outcomes than in real-activity proxies, which lets the public evaluator exercise the channel-separation logic without exposing confidential data.

## Data Policy

- Raw source data are read-only.
- Confidential data are never committed to this public repository.
- Public artifacts demonstrate the autoresearch workflow, controller, gates, and logging contract.
- Public fixture results should be treated as software validation evidence, not as empirical evidence about any real setting.
- Claim-ready empirical work requires running the same fixed harness on the authorized private data.
