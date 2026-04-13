# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY CLUSTER DELTA V1

## Why The Cluster Preview Needs A Delta Layer
- The cluster preview already compresses many secondary value panels into a smaller site-time view.
- Even so, operators still should not need to reread the full cluster preview every refresh.
- The next operator-facing layer is therefore a delta feed:
  - what is newly appearing
  - what disappeared
  - what meaningfully changed inside an overlapping cluster

## Why Cluster Id Alone Is Not Reliable
- `cluster_id` is useful for presentation, but it is not reliable enough as the only cross-refresh key.
- Cluster numbering can shift when:
  - cluster sort order changes
  - nearby panels merge differently
  - one cluster splits or disappears
- So the delta feed matches clusters by site-time overlap first, not by `cluster_id` alone.

## How Overlap-Based Matching Works
- Matching is done within each site only.
- A current cluster and previous cluster are matchable when their date intervals overlap by at least 1 day.
- Matching is one-to-one and greedy:
  - compute all site-local overlap candidates
  - sort by largest `overlap_days` first
  - lock each current cluster and previous cluster after the first accepted match
- Any unmatched current cluster becomes `new_cluster`.
- Any unmatched previous cluster becomes `dropped_cluster`.

## What Each Delta Class Means
- `new_cluster`
  - a current discovery cluster with no 1-day-overlap match in the previous snapshot
- `dropped_cluster`
  - a previous discovery cluster with no 1-day-overlap match in the current snapshot
- `cluster_span_changed`
  - the matched cluster still exists, but its start/end window changed
- `panel_count_changed`
  - the matched cluster still exists, but the number of folded panels changed
- `representative_changed`
  - the cluster still exists, but the representative panel/run changed
- `linked_ref_changed`
  - retrospective fault/truth-linked reference flags changed for the matched cluster
- `unchanged`
  - no relevant fields changed
  - these rows are not emitted into the operator delta output

## Change Priority Inside Matched Clusters
- A matched cluster emits at most one delta class.
- Priority is:
  - `representative_changed`
  - `linked_ref_changed`
  - `panel_count_changed`
  - `cluster_span_changed`
- This keeps the operator feed short and focused on the most important visible change.

## Bootstrap Behavior
- On first run, if the previous snapshot is absent:
  - all current clusters are treated as `new_cluster`
  - the build still succeeds
  - the current rollup is copied into the previous snapshot path after comparison output is written

## Scope Notes
- This is an operator-facing delta layer only.
- Detector logic and scorer logic are unchanged.
- Current baseline and pipeline builders are unchanged.
- Canonical truth template contract is unchanged.
