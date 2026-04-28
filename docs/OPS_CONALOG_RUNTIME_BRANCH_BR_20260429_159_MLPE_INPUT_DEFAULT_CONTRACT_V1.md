<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_159_MLPE_INPUT_DEFAULT_CONTRACT_V1

## Purpose
- Refine BR-158's `mlpe_field_trial` input/default rows by dependency contract before changing any path default.
- Keep this branch audit/reporting only: no panel-engine runtime semantic change, no default rewrite, and no large data committed.
- Separate "safe to replace with package-relative defaults" from "must be supplied by operator or upstream pipeline output".

## Change
- The path portability detail output now includes `dependency_contract`.
- Summary, note, and JSON outputs now report non-empty dependency contract counts.
- The smoke test verifies that an MLPE field-trial capture-input default is classified as `mlpe_template_or_schema_input`.

## Contract Definitions
| dependency_contract | meaning | default handling implication |
|---|---|---|
| `mlpe_chain_directory_bundle_input` | a directory bundle consumed by the MLPE field-trial chain | should resolve from an explicit package/manifest root, not a volatile temp root |
| `mlpe_user_filled_input` | an operator/reviewer/labeler-filled artifact | should not be auto-created as a silent default; require explicit input or fixture mode |
| `mlpe_template_or_schema_input` | template/schema/allowed-values inputs | can be package-relative if shipped as contract material |
| `mlpe_upstream_generated_artifact_input` | artifact expected from an earlier builder stage | should resolve through upstream output manifest or fail closed when missing |

## Observed Effect
- Current audit total matches: `1937`.
- `private_tmp`: `1335`.
- `repo_absolute`: `602`.
- MLPE field-trial input/directory dependency split:
  - `mlpe_upstream_generated_artifact_input`: `27`
  - `mlpe_template_or_schema_input`: `10`
  - `mlpe_user_filled_input`: `7`
  - `mlpe_chain_directory_bundle_input`: `4`

## Interpretation
- The next cleanup should not rewrite all MLPE defaults the same way.
- `mlpe_user_filled_input` is the highest safety-sensitive bucket because a silent default could hide missing real labels, returned capture packets, or reviewer decisions.
- `mlpe_upstream_generated_artifact_input` is the largest bucket, but it should be solved by manifest chaining rather than by embedding a new static default.
- `mlpe_template_or_schema_input` is the safest package-relative candidate because templates and schemas are intended to be bundled contract material.
- `mlpe_chain_directory_bundle_input` needs an explicit root contract so a whole bundle moves together.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir "${TMPDIR:-/tmp}/pvdiag_mlpe_input_default_contract_check_v2"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- Next patch candidate: add a guard/report lane for `mlpe_user_filled_input` defaults so missing real field-trial inputs fail closed unless fixture mode is explicit.
- Do not change panel-engine evidence defaults in the same patch.
- Do not claim performance, truth, threshold, or engine improvement from this audit-only branch.
