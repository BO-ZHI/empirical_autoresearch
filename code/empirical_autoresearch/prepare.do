version 18
clear all
set more off

capture mkdir "output"
capture mkdir "logs"

local data_file "data/synthetic_threshold_response.csv"
confirm file "`data_file'"

import delimited using "`data_file'", clear varnames(1)
foreach required in firm_id year treat post near_threshold reported_count below_threshold_mass avg_amount_per_record real_activity_proxy category_shift {
    confirm variable `required'
}

count
local n_obs = r(N)
levelsof treat, local(treat_levels)
levelsof post, local(post_levels)

tempname prep
file open `prep' using "output/prepare_status.tsv", write replace text
file write `prep' "item" _tab "status" _tab "note" _n
file write `prep' "data_file" _tab "pass" _tab "`data_file'" _n
file write `prep' "row_count" _tab "pass" _tab "`n_obs'" _n
file write `prep' "treatment_cells" _tab "pass" _tab "treat=`treat_levels'; post=`post_levels'" _n
file close `prep'

display "project=sanitized empirical autoresearch workflow"
display "prepare_status=ready"
