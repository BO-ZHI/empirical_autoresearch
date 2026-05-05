version 18
clear all
set more off

capture mkdir "output"
capture mkdir "logs"

display "autoresearch_driver=sanitized threshold-response workflow"
display "editable_file=analyze.do"
display "metric_name=channel_separation_score"

tempname manifest
file open `manifest' using "output/run_manifest.tsv", write replace text
file write `manifest' "item" _tab "status" _tab "note" _n
file write `manifest' "analysis_driver" _tab "present" _tab "single editable file" _n
file write `manifest' "metric_contract" _tab "present" _tab "channel_separation_score is fixed" _n
file write `manifest' "data_manifest" _tab "present" _tab "public sanitized manifest only" _n
file write `manifest' "mechanism_outputs" _tab "present" _tab "evaluator writes channel artifacts" _n
file close `manifest'

display "analyze_status=complete"
