version 18
clear all
set more off

capture mkdir "output"
capture mkdir "logs"

display "autoresearch_driver=sanitized threshold-response workflow"
display "editable_file=analyze.do"
display "metric_name=channel_separation_score"

import delimited using "data/synthetic_threshold_response.csv", clear varnames(1)
xtset firm_id year

preserve
collapse (mean) reported_count below_threshold_mass avg_amount_per_record real_activity_proxy category_shift, by(treat post)
export delimited using "output/channel_stats.tsv", delimiter(tab) replace
restore

tempname regs
file open `regs' using "output/regression_summary.tsv", write replace text
file write `regs' "channel" _tab "dependent_variable" _tab "coefficient" _tab "standard_error" _tab "n" _tab "interpretation" _n

reg reported_count i.treat##i.post, vce(cluster firm_id)
local b_count = _b[1.treat#1.post]
local se_count = _se[1.treat#1.post]
local n_count = e(N)
file write `regs' "reported_number_management" _tab "reported_count" _tab %9.4f (`b_count') _tab %9.4f (`se_count') _tab "`n_count'" _tab "negative interaction supports fewer reported records" _n

reg below_threshold_mass i.treat##i.post, vce(cluster firm_id)
local b_mass = _b[1.treat#1.post]
local se_mass = _se[1.treat#1.post]
local n_mass = e(N)
file write `regs' "reported_number_management" _tab "below_threshold_mass" _tab %9.4f (`b_mass') _tab %9.4f (`se_mass') _tab "`n_mass'" _tab "positive interaction supports threshold bunching" _n

reg real_activity_proxy i.treat##i.post, vce(cluster firm_id)
local b_real = _b[1.treat#1.post]
local se_real = _se[1.treat#1.post]
local n_real = e(N)
file write `regs' "real_adjustment" _tab "real_activity_proxy" _tab %9.4f (`b_real') _tab %9.4f (`se_real') _tab "`n_real'" _tab "small interaction weakens real-adjustment interpretation" _n

reg category_shift i.treat##i.post, vce(cluster firm_id)
local b_cat = _b[1.treat#1.post]
local se_cat = _se[1.treat#1.post]
local n_cat = e(N)
file write `regs' "category_substitution" _tab "category_shift" _tab %9.4f (`b_cat') _tab %9.4f (`se_cat') _tab "`n_cat'" _tab "positive interaction supports category movement" _n
file close `regs'

tempname manifest
file open `manifest' using "output/run_manifest.tsv", write replace text
file write `manifest' "item" _tab "status" _tab "note" _n
file write `manifest' "analysis_driver" _tab "present" _tab "single editable file" _n
file write `manifest' "metric_contract" _tab "present" _tab "channel_separation_score is fixed" _n
file write `manifest' "data_manifest" _tab "present" _tab "public sanitized manifest plus synthetic fixture" _n
file write `manifest' "mechanism_outputs" _tab "present" _tab "channel_stats.tsv and regression_summary.tsv created" _n
file close `manifest'

display "analyze_status=complete"
