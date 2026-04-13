# OPS_PANEL_DAY_EVIDENCE_MATRIX_V1

## Purpose

This patch materializes `panel_day_evidence_matrix_v1` from `panel_day_core.csv` as the first executable layer of the anomaly-registry design.

It does not change:

- official prediction output,
- official scoring logic,
- or canonical truth.

It only preserves one row per `site + panel_id + date` from `panel_day_core` and derives stable evidence fields that later episode and incident layers can consume.

## Why This Is The First Executable Anomaly-Registry Layer

The schema freeze defined the target table, but nothing executable yet produced it.

`panel_day_evidence_matrix_v1` is the safest first implementation step because it stays close to existing `panel_day_core` inputs:

- it preserves the same panel-day grain,
- it derives evidence flags from already available algorithm-side fields,
- and it avoids premature grouping decisions.

That makes it a good foundation layer for later panel-local episode and common-cause incident work.

## Why Row Preservation Is Critical

This layer is meant to be a faithful evidence matrix, not a filtered candidate set.

If rows were silently dropped or duplicated here, every later layer would inherit that distortion:

- panel episode construction would see the wrong day windows,
- incident aggregation would see the wrong site-wide footprint,
- and auditability back to `panel_day_core` would be weakened.

For that reason, the builder keeps one output row per `site + panel_id + date` and fails loudly if duplicate raw keys appear.

## Why `local_signal_signature` Includes Negative Evidence

Later grouping logic needs more than positive tags like "electrical" or "open-device."

It also needs to know when a dimension is notably *not* low or *not* collapsed.

That is why `local_signal_signature` includes token families for:

- output,
- voltage,
- and current,

with both positive and negative-style states such as:

- `output_zero_like`,
- `voltage_drop`,
- `current_preserved`.

Those negative-evidence tokens help downstream logic distinguish patterns that look superficially similar but have different preserved-vs-collapsed structure.

## Why Missing Shape/Instability Evidence Must Stay Null

Shape and instability evidence are optional in the current raw inputs.

When those source columns are absent, that means the evidence is unavailable, not that the signal was observed and judged negative.

So this layer keeps:

- `shape_flag`,
- `shape_score`,
- `instability_flag`,
- `instability_score`

as null when the raw source columns are unavailable.

That avoids collapsing:

- unavailable evidence,
- observed false,
- and observed zero strength

into the same meaning.

## Why Group Proxy Derivation Is Included Here

Episode and incident work will need a stable grouping anchor, even before full topology implementation exists.

This layer therefore emits:

- `group_proxy_value`,
- `group_proxy_source`,
- `topology_confidence`

using a simple, explicit rule:

- prefer nonblank `group_key_base`,
- else fall back to `panel_id` token0.token1.

That keeps the provenance of the grouping hint visible rather than hiding it inside later layers.

## Why This Layer Does Not Yet Perform Episode/Incident Grouping

`panel_day_evidence_matrix_v1` is intentionally limited to evidence materialization.

It does not:

- open or close panel-local episodes,
- merge panels into common-cause incidents,
- or assert causal structure.

Those are later layers in the anomaly-registry design.

Keeping this first executable layer narrow is important because it lets us validate:

- row preservation,
- evidence derivation,
- and null semantics

before introducing more complex grouping behavior.

## Outputs

- `_share/panel_day_evidence_matrix_v1.csv`
- `_share/panel_day_evidence_matrix_summary_v1.csv`
