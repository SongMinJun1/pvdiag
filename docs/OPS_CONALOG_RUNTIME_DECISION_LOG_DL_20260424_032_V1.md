<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_032_V1

## Decision
- Accept `panel_day_engine_common_cause_synchrony_axis_v1` as the evidence-only sidecar for common-cause synchrony.

## Reason
- Previous blocker work showed that common-cause evidence is not one thing.
- `site_event`, `group_off`, `subgroup_common_cause`, `prefault_B_common_cause_overlap`, and broad `co_drop_frac` need to be separated before any rule or projection discussion.
- A sidecar is safer than a runtime semantic patch because exact family closure is still not complete.

## Evidence
- Real tri-site output root:
  - `/private/tmp/common_cause_synchrony_axis_sidecar_check`
- Detail / summary rows:
  - `detail_rows = 206`
  - `summary_rows = 23`
- Site-level profile:
  - `conalog`: `82` panels, `111` common-cause rows, mostly `subgroup_synchrony_candidate`
  - `gangui`: `46` panels, `97` common-cause rows, including `20` group-off panels and `1` prefault-B overlap panel
  - `ktc_ess`: `78` panels, `188` common-cause rows, including `30` site-event panels and `51` co-drop hint panels

## Consequence
- Cross-axis review can now compare:
  - report entry friction
  - recovery/recurrence morphology
  - common-cause synchrony
- `co_drop_breadth_hint` remains a weak context marker, not a direct diagnosis.
- `group_off_group` placeholder values such as `False`, `none`, and `0` are not meaningful group keys.
- No runtime verdict, row universe, threshold, or operator-facing semantics changed.
