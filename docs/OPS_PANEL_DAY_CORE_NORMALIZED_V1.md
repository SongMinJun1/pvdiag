# OPS_PANEL_DAY_CORE_NORMALIZED_V1

## Purpose

This patch materializes safe normalized `panel_day_core` sidecars from the duplicate-resolution audit and lets `panel_day_evidence_matrix_v1` build from those sidecars.

It does not change:

- raw source files,
- official prediction output,
- official scoring logic,
- or canonical truth.

It only creates a sidecar layer for safe duplicate collapse and adds source-mode selection to the evidence-matrix builder.

## Why Raw Source Files Are Not Modified

The raw `panel_day_core.csv` files remain the canonical exported source.

Changing them in place would make it harder to:

- re-audit duplicate behavior,
- compare pre-normalized vs post-normalized behavior,
- and separate governance decisions from upstream data generation.

That is why normalization writes only to:

- `_share/panel_day_core_normalized_v1/<site>.csv`

and leaves `data/<site>/out/panel_day_core.csv` untouched.

## Why Only Safe Duplicate Classes Are Normalized

The v2 duplicate-resolution audit already separated duplicate groups into:

- `provenance_only_duplicate`
- `evidence_equivalent_duplicate`
- `numeric_jitter_duplicate`
- `material_conflict_duplicate`

This patch only collapses the first two classes because they do not change the evidence-critical frame used by `panel_day_evidence_matrix_v1`.

That means normalization is allowed only when duplicate groups are already audited as safe.

## Why `numeric_jitter_duplicate` And `material_conflict_duplicate` Still Block Normalization

`numeric_jitter_duplicate` still needs an explicit tolerance policy decision.

`material_conflict_duplicate` is even stronger evidence that the duplicate group should not be silently collapsed.

So the normalizer fails loudly by default if either unresolved class is present.

That keeps normalization narrow and reversible instead of turning an audit label into an unreviewed collapse rule.

## How Representative Rows Are Chosen Deterministically

For each safe duplicate group, the normalizer picks exactly one representative row using this fixed priority:

1. highest count of nonblank non-provenance columns
2. prefer nonblank `group_key_base`
3. lexicographically smallest `provenance_fingerprint`
4. stable original row order

`provenance_fingerprint` is built from provenance-like columns when available.
If those columns are absent or blank, the builder falls back to the source path plus original row-order info.

That makes the selection deterministic and auditable.

## How `panel_day_evidence_matrix_v1` Source Mode Works

`build_panel_day_evidence_matrix_v1.py` now supports:

- `--panel-day-source auto`
- `--panel-day-source raw`
- `--panel-day-source normalized`

Behavior:

- `auto`: use the normalized sidecar for a site when it exists, else use raw
- `raw`: force raw input and keep the existing duplicate-fail behavior
- `normalized`: require the normalized sidecar and fail if it is missing

This keeps the old raw safety behavior intact while unblocking real builds once safe normalized sidecars exist.

## Outputs

- `_share/panel_day_core_normalized_v1/conalog.csv`
- `_share/panel_day_core_normalized_v1/gangui.csv`
- `_share/panel_day_core_normalized_v1/ktc_ess.csv`
- `_share/panel_day_core_normalized_v1/sinhyo.csv`
- `_share/panel_day_core_normalized_summary_v1.csv`
- `_share/panel_day_core_normalized_drop_manifest_v1.csv`
