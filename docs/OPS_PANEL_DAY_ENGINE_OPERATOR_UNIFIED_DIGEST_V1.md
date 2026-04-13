# OPS PANEL DAY ENGINE OPERATOR UNIFIED DIGEST V1

## Why The Current Preview And Delta Artifacts Were Still Split
- Operators could already read:
  - current baseline attention plus discovery cluster preview
  - attention delta
  - discovery cluster delta
- But those artifacts were still split across separate files.
- That meant the operator still had to mentally join:
  - what is currently visible
  - which current rows changed
  - whether that change came from baseline attention or from discovery cluster movement

## Why Policy Audit Had To Come First
- Packaging completion alone does not answer which operator view should become the default workflow.
- We first needed `operator_attention_policy_audit_v1` to compare:
  - baseline only
  - baseline plus discovery panel
  - baseline plus discovery narrow
  - baseline plus discovery cluster
- That audit chose `baseline_plus_discovery_cluster` as the best default because it preserved useful retrospective linked proxy gain while keeping operator load smaller than panel-level expansion.

## Why Unified Digest Is The Right Source Artifact
- The next operator-facing step is not another detector or scorer change.
- It is a current-state digest layer that already keeps only what the operator can act on now:
  - `queue_run`
  - `watch_now_panel`
  - `secondary_value_cluster`
- And for each current row it adds the latest change context from the relevant delta feed.
- Because the chosen default policy is `baseline_plus_discovery_cluster`, the unified digest is already the correct source artifact for the official default workflow output.

## Why Unified Digest Is The Next Operator-Facing Step
- The next operator-facing step is still not another detector or scorer change.
- It is to declare one official default workflow file that operators can read without separately choosing among multiple preview variants.
- The builder now keeps the existing unified digest outputs unchanged and adds:
  - `panel_day_engine_operator_workflow_default_v1.csv`
  - `panel_day_engine_operator_workflow_default_summary_v1.csv`
- This default workflow is emitted only when the policy recommendation confirms `baseline_plus_discovery_cluster`.

## How Attention Delta And Cluster Delta Are Merged
- Base current rows come only from:
  - `panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv`
- Queue/watch rows are matched to:
  - `panel_day_engine_operator_attention_delta_v1.csv`
  - by `site + panel_id`
  - where `panel_id == display_entity_id`
- Cluster rows are matched to:
  - `panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv`
  - by `site + current_cluster_id`
  - where `current_cluster_id == display_entity_id`
- If a current row does not appear in its relevant delta feed:
  - `changed_since_previous_flag = 0`
  - `latest_delta_source = none`
  - `latest_delta_class` stays blank

## Why Only Current Rows Are Shown
- This digest is deliberately current-state only.
- It does not emit dropped historical rows from either delta feed.
- The reason is operational:
  - the operator digest should answer “what should I look at now?”
  - not “what existed only in the previous snapshot?”
- Historical removals still remain available in the source delta feeds when needed.

## Operational Reading Guide
- `queue_run`
  - current baseline queue item
- `watch_now_panel`
  - current baseline watch-now item
- `secondary_value_cluster`
  - current supplemental discovery cluster item
- `latest_delta_source`
  - `attention_delta` if the current baseline attention item changed
  - `cluster_delta` if the current discovery cluster changed
  - `none` if the current row is unchanged versus the previous snapshot

## Workflow Default Interpretation
- `workflow_policy_name`
  - always `baseline_plus_discovery_cluster`
- `workflow_role`
  - `primary_attention` for `queue_run` and `watch_now_panel`
  - `supplemental_discovery` for `secondary_value_cluster`
- `workflow_priority_class`
  - `queue_priority` for `queue_run`
  - `watch_priority` for `watch_now_panel`
  - `discovery_priority` for `secondary_value_cluster`

Operationally:
- `primary_attention` rows are the core queue/watch workflow.
- `supplemental_discovery` rows are explicitly included because the policy audit judged cluster preview useful enough to sit beside the baseline by default.
- The priority class does not change detector/scorer logic; it only makes the chosen default workflow easier to scan consistently.

## Scope Notes
- This is a non-core operator-facing packaging patch.
- Detector logic and scorer logic are unchanged.
- Existing preview/delta/policy-audit builders are unchanged.
- Canonical truth template contract is unchanged.
