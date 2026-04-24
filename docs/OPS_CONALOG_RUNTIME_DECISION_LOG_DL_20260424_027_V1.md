<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_027_V1

## Decision
- user request 기준으로, current emphasis는 `new evidence axis`보다 `repo cleanup before more expansion`으로 둔다.
- this does not cancel BR-043/BR-044.
- it temporarily changes the next practical step from `common_cause_synchrony_axis` to `main_dirty_disentangle` planning.

## Why
- inventory shows cleanup pressure is not limited to evidence files.
- the strongest current pressures are:
  - `main dirty disentangle`
  - `source/release/final_delivery mirror policy`
  - `audit builder registry`
- if these remain blurry, new work can still be technically correct but operationally messy.

## Lock
- next cleanup order:
  1. `main_dirty_disentangle`
  2. `source_release_finaldelivery_mirror_policy`
  3. `audit_builder_registry`
- `common_cause_synchrony_axis` stays next on the runtime-evidence lane, but not before the cleanup prelude is acknowledged.
