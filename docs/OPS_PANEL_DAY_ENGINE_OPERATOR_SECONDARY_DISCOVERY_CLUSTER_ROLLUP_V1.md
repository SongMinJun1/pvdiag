# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY CLUSTER ROLLUP V1

## Why Narrow Preview Thresholding Was Not Enough
- The secondary discovery value lane became narrower after score-threshold filtering, but operator load could still stay high when many neighboring panels from the same site appeared as separate rows.
- That meant the lane was still vulnerable to site skew:
  - one active site could occupy many rows
  - even when the operational question was closer to "is this one site entering a local burst?" than "which exact panel row is first?"

## Why Site-Time Clustering Is The Next Logical Compression Step
- The next compression step is therefore not another scorer change.
- It is a site-time rollup:
  - keep the same secondary value panels
  - collapse nearby representative intervals within the same site
  - expose one cluster row instead of many adjacent panel rows
- This reduces operator burden while preserving whether a site is showing concentrated hidden-value activity.

## Why Clustering Uses Current-State Dates Only
- Clustering uses only:
  - `site`
  - `representative_run_start_date`
  - `representative_run_end_date`
- Panels are chained into one cluster when the next representative run starts within 3 days of the current cluster end.
- That means clustering stays current-state and online-safe:
  - no future fault flags
  - no future truth flags
  - no retrospective recurrence fields
  are used to decide the clusters.
- Retrospective future flags remain summary/reference context only.

## How To Interpret A Discovery Cluster Operationally
- A discovery cluster means:
  - one site
  - one bounded time window
  - one or more secondary value panels appearing close enough in time to be reviewed together
- The representative panel is chosen by:
  - highest `representative_electrical_core_minus_broadshape_050`
  - then highest `representative_logistic_v3_discovery_score`
  - then latest `representative_run_end_date`
  - then larger `representative_run_day_count`
- Operationally, the cluster should be read as:
  - a compressed site-level discovery burst
  - where the representative panel is the strongest current panel to inspect first
  - while `panel_ids_csv` preserves which additional hidden panels were folded underneath the same burst

## Scope Notes
- This is a non-core operator-facing audit patch.
- Detector logic is unchanged.
- Current operator baseline attention files remain unchanged.
- Canonical truth template contract is unchanged.
