# OPS_ANOMALY_REGISTRY_SCHEMA_FREEZE_V1

## Purpose

This patch freezes the proposed anomaly-registry design into machine-readable schema artifacts before any implementation starts.

It does not change:

- official prediction output,
- official scoring logic,
- or canonical truth.

It only turns the design into reviewable tables, enums, reason codes, and config keys.

## Why Strict Rows Are Not Human-Facing Units

Strict rows are useful anchors, but they are not the main human-facing unit.

They are too fine-grained for most review workflows because:

- multiple strict rows can belong to one local episode,
- one common-cause incident can overlap many strict rows,
- and mixed local plus overlap evidence can coexist around the same strict trigger.

That is why the schema keeps a `strict_case_ledger_v1`, but does not treat it as the primary review object.

## Why Schema And Thresholds/Config Are Separated

The schema freeze is meant to survive later tuning.

Threshold defaults will almost certainly move during implementation or review.

If thresholds were baked into table structure, every tuning pass would look like a schema change.

So this design separates:

- stable entity and field structure,
- from adjustable config keys such as gap tolerance, incident thresholds, and precursor lead windows.

The freeze remains valid even if those default values later change.

## Why Panel-Local Episode And Common-Cause Incident Are Different Entities

They answer different questions.

`panel_local_episode_registry_v1` tracks what happened to one panel over a local time window.

`common_cause_incident_registry_v1` tracks a multi-panel or multi-group pattern that may span many local episodes.

That separation is intentional because:

- common-cause overlap must not by itself create a panel-local episode,
- overlap evidence may coexist with local evidence,
- and mixed cases need to stay representable without collapsing everything into one table.

## Why Relations Are Typed Edges, Not Automatic Merges

`episode_incident_relation_v1` stores typed edges between nodes.

That means a relation can say:

- the day windows overlap,
- one pattern leads another,
- or the signatures look similar.

It does not mean the two nodes are automatically the same cause.

Relation edges are evidence-bearing links, not forced merges.

## Why `membership_role` Is Necessary

One strict case can sit in awkward territory:

- clearly inside a local episode,
- clearly inside a common-cause incident,
- inside both,
- or inside neither.

The schema needs an explicit `membership_role` so those cases do not get flattened into an ambiguous yes/no mapping.

That is especially important for mixed local plus overlap situations.

## Why `panel_history_view_v1` Is A Logical View

`panel_history_view_v1` is for reading and summarizing, not for primary storage.

The canonical stores are the ledger, evidence, episode, incident, mapping, and relation entities.

The history view exists so downstream review can quickly answer:

- what episodes this panel has had,
- what incidents it was part of,
- and what the current summary status looks like.

Because it is a logical view, it can evolve in wording without redefining the canonical anomaly registry.

## What Remains Intentionally Unresolved Until Implementation

This freeze does not settle every implementation detail.

Still intentionally unresolved:

- exact threshold defaults beyond the provisional config keys,
- whether some optional evidence signals will be filled from existing raw feeds or future enrichments,
- exact node-type enum handling for typed relation endpoints,
- and how some review notes will be populated in partially manual workflows.

Those open items do not block the schema freeze because they live in config, notes, or future-optional columns rather than in the primary entity identities.

## Important Design Constraints Captured Here

- common-cause overlap must not by itself create a panel-local episode
- overlap evidence and local evidence may coexist
- relation edges do not imply same cause
- prior event/episode layers are context sources, not primary incident generators
- schema freeze stays valid even if default thresholds later change

## Outputs

- `_share/anomaly_registry_schema_tables_v1.csv`
- `_share/anomaly_registry_enum_catalog_v1.csv`
- `_share/anomaly_registry_reason_codes_v1.csv`
- `_share/anomaly_registry_config_keys_v1.csv`
