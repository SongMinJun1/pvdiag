# MLPE Field-Trial Contract Artifacts V1

This directory contains small, repo-tracked contract artifacts used by MLPE field-trial support builders.

These files are templates, schemas, and allowed-value tables only. They are not field-trial observations, truth labels, raw data, or adjudicated evidence.

## Contract Files
- `capture_schema/mlpe_field_trial_capture_template_v1.csv`
- `capture_schema/mlpe_field_trial_capture_schema_v1.csv`
- `capture_schema/mlpe_field_trial_capture_allowed_values_v1.csv`
- `final_label_intake_schema/mlpe_field_trial_final_label_intake_schema_v1.csv`
- `final_label_intake_schema/mlpe_field_trial_final_label_allowed_values_v1.csv`
- `truth_seed_reviewer_decision_schema/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv`
- `truth_seed_reviewer_decision_schema/mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv`

## Boundary
- User-filled captures, labels, reviewed checklists, and reviewer decisions must still be supplied explicitly.
- These contract files do not authorize truth intake, threshold changes, or engine patches.
