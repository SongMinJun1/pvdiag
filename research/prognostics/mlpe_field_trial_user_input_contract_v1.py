#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def same_path_text(left: str | Path, right: str | Path) -> bool:
    return str(Path(left).expanduser()) == str(Path(right).expanduser())


def require_explicit_user_filled_input(
    *,
    input_name: str,
    input_path: str | Path,
    default_path: str | Path,
    allow_user_filled_default: bool,
    explicit_flag: str = "",
) -> None:
    if allow_user_filled_default or not same_path_text(input_path, default_path):
        return
    flag_hint = f" with {explicit_flag}" if explicit_flag else ""
    raise ValueError(
        "\n".join(
            [
                f"{input_name} is a user-filled MLPE field-trial input.",
                "Refusing to read the default template path as real evidence.",
                f"Provide an explicit real input path{flag_hint}.",
                "Use --allow-user-filled-default only for fixture/regression runs.",
                f"Refused default path: {default_path}",
            ]
        )
    )
