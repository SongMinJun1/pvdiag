#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ONECLICK_ENTRYPOINT = REPO_ROOT / "app/run_oneclick.py"

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


def run_oneclick(
    *,
    input_root: str,
    output_root: str,
    config_path: str,
    include_experimental: bool,
    report: bool,
    dry_run: bool,
) -> tuple[int, str]:
    cmd = [
        sys.executable,
        str(ONECLICK_ENTRYPOINT),
        "--input-root",
        input_root,
        "--output-root",
        output_root,
        "--config",
        config_path,
        "--include-experimental",
        "on" if include_experimental else "off",
        "--report",
        "on" if report else "off",
    ]
    if dry_run:
        cmd.append("--dry-run")
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    output_text = (result.stdout or "").strip()
    error_text = (result.stderr or "").strip()
    return result.returncode, "\n".join(part for part in [output_text, error_text] if part)


def render_app() -> None:
    assert st is not None
    st.set_page_config(page_title="Conalog Delivery Pack", layout="wide")
    st.title("Conalog Delivery Pack GUI")
    st.caption("stable output 과 optional experimental/reference output 을 분리해서 보여주는 foundation UI")

    default_input_root = str(REPO_ROOT / "stable_handoff" / "examples")
    default_output_root = str(REPO_ROOT / "demo_output")
    default_config_path = str(REPO_ROOT / "config" / "runtime.yaml")

    input_root = st.text_input("입력 root 경로", value=default_input_root)
    output_root = st.text_input("출력 root 경로", value=default_output_root)
    config_path = st.text_input("config 경로", value=default_config_path)
    include_experimental = st.checkbox("optional experimental/reference output 포함", value=False)
    report = st.checkbox("daily report 생성", value=True)
    dry_run = st.checkbox("dry-run", value=True)

    if st.button("실행", type="primary"):
        code, text = run_oneclick(
            input_root=input_root,
            output_root=output_root,
            config_path=config_path,
            include_experimental=include_experimental,
            report=report,
            dry_run=dry_run,
        )
        if code == 0:
            st.success("실행 완료")
        else:
            st.error("실행 실패")
        st.text_area("결과 / 상태", value=text, height=260)


def main() -> None:
    if st is None:
        raise SystemExit("streamlit is not installed; UI execution requires streamlit.")
    render_app()


if __name__ == "__main__":
    main()
