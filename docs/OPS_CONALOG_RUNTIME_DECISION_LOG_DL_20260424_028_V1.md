<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_028_V1

## Decision
- cleanup priority의 의미를 `branch 정리`가 아니라 `confusion reduction`으로 재정의한다.
- immediate emphasis remains cleanup-first, but the intended outcome is clearer role separation, not cosmetic git hygiene.

## Why
- user clarified that the real pain is "여러개가 서로 얽히고 설켜서 헷갈리는 상태".
- repo-wide inventory also supports that reading:
  - mixed dirty scopes
  - mirror surface skew
  - builder entrypoint sprawl
  - archive/current overlap

## Lock
- next order becomes:
  1. `mixed_scope_disentangle`
  2. `source_vs_packaged_mirror_boundary`
  3. `active_builder_entrypoint_registry`
- runtime evidence order stays intact behind this prelude.
