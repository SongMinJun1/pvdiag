<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_228_GENERATED_HANDOFF_REPRO_LITERAL_AUDIT_V1

## Summary
- This patch re-audits the `50` generated handoff/repro literals found by BR-227.
- It separates current handoff refresh candidates from supporting evidence-manifest literals, one generated note repro literal, and one validation output literal.
- It does not rewrite the literals, move artifacts, change runtime semantics, or touch `pv_ae/panel_day_engine.py`.

## Why
- BR-227 correctly blocked blanket historical path rewrite.
- The next risk is treating every generated `/private/tmp` repro literal as the same kind of debt.
- They are not the same:
  - latest handoff repro literals should be regenerated as one manifest-aware handoff,
  - evidence manifest repro literals should refresh only when promoted into current handoff,
  - episode note repro should refresh only when touching that note,
  - validation output temp paths are output destinations, not handoff inputs.

## Observed Result
- `path_portability_total_matches`: `1935`
- `generated_handoff_repro_literal_rows`: `50`
- `latest_handoff_manifest_repro_rows`: `41`
- `evidence_manifest_repro_rows`: `7`
- `episode_note_repro_rows`: `1`
- `validation_output_literal_rows`: `1`
- `manifestized_rebuild_candidate_rows`: `48`
- `stable_artifact_materialization_required_rows`: `0`
- `manual_literal_edit_allowed_rows`: `0`
- `runtime_semantic_change_allowed_rows`: `0`
- `operator_facing_change_allowed_rows`: `0`
- `audit_complete`: `1`

## Boundary
- Do not edit individual generated temp literals by hand.
- Refresh the latest handoff manifest as one generated, manifest-aware unit.
- Preserve validation output temp paths as explicit output destinations.
- Keep evidence-manifest literals until that manifest is promoted into the current handoff.

## Files
- `research/prognostics/build_generated_handoff_repro_literal_audit_v1.py`
- `research/prognostics/smoke_test_generated_handoff_repro_literal_audit_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_228_GENERATED_HANDOFF_REPRO_LITERAL_AUDIT_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_generated_handoff_repro_literal_audit_v1.py \
  research/prognostics/smoke_test_generated_handoff_repro_literal_audit_v1.py
python3 research/prognostics/smoke_test_generated_handoff_repro_literal_audit_v1.py
python3 research/prognostics/build_generated_handoff_repro_literal_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/generated_handoff_repro_literal_audit_br228_check"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Expected Result
- The audit should report `generated_handoff_repro_literal_rows=50`.
- The audit should report `latest_handoff_manifest_repro_rows=41`.
- The audit should report `manifestized_rebuild_candidate_rows=48`.
- The audit should report `manual_literal_edit_allowed_rows=0`.
- The audit should report `runtime_semantic_change_allowed_rows=0`.

## Next Decision
- Build the next branch as a latest-handoff manifest-aware repro refresh plan.
- Do not edit the 41 latest-handoff literals one by one.
- Do not treat the validation output literal as a handoff input gap.
