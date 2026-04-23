<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_BLOCKER_DETAIL_REVIEW_PACKET_V1

## Purpose
- BR-022 split the broad common-cause blocker into detail buckets.
- BR-023 creates a review packet for the two detail buckets that need the next human/evidence pass before any subtype promotion discussion:
  - `group_off`
  - `strict_trigger_proximal`
- This branch is packet-only. It does not change runtime code, final verdicts, heuristics, or audit-builder logic.

## Source
- source audit: `/private/tmp/br022_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- tracked packet outputs are generated under `docs/`.

## Reproduction Command
```bash
python - <<'PY'
# read BR-022 runtime audit, filter blocker detail in
# {'group_off', 'strict_trigger_proximal'}, derive packet/review columns,
# and write BR-023 docs CSV/JSON artifacts
PY
```

## Outputs
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_BLOCKER_DETAIL_REVIEW_PACKET_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_GROUP_OFF_REVIEW_PACKET_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_STRICT_TRIGGER_PROXIMAL_REVIEW_PACKET_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_BLOCKER_DETAIL_REVIEW_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_VALIDATION_V1.json`

## Packet Counts
| bucket | count |
|---|---:|
| all packet rows | 77 |
| `group_off` | 28 |
| `strict_trigger_proximal` | 49 |
| `group_off | gangui` | 28 |
| `strict_trigger_proximal | conalog` | 38 |
| `strict_trigger_proximal | gangui` | 11 |
| `subtype_production_write_allowed_sum` | 0 |

## Review Priorities
| priority | count | meaning |
|---|---:|---|
| `P1_cluster_false_positive_check` | 26 | group-off rows already in blocked cluster-risk path |
| `P1_strict_proximal_vs_secondary_window_check` | 43 | strict-proximal rows with secondary-window candidate evidence |
| `P2_group_episode_boundary_check` | 2 | group-off rows not in cluster-risk bucket |
| `P2_strict_proximal_anchor_check` | 6 | strict-proximal rows without secondary-window candidate |

## Initial Reading
- `group_off=28` is entirely `gangui`, concentrated in a small number of root/branch groups.
- `group_off` rows are mostly `blocked_cluster_risk`, so the next question is not "can this be promoted?" but "is this a group episode false-positive boundary?"
- `strict_trigger_proximal=49` is split across `conalog=38` and `gangui=11`.
- The `conalog` strict-proximal rows mostly look like repeated `간헐 접촉저항형` hypotheses with strict-trigger anchors on 2024-12-05 or 2024-12-06.
- The `gangui` strict-proximal rows mix diode/subsubstring, degradation, and open-connection hypotheses around the November 2025 event cluster.

## Decision
- BR-023 is safe to merge as a review-packet-only branch.
- No production subtype promotion is allowed from this packet.
- Next safe step is a row/cluster adjudication note for:
  - `group_off` cluster false-positive boundary
  - `strict_trigger_proximal` vs secondary-window evidence
