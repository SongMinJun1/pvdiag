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
) -> None:
    if allow_user_filled_default or not same_path_text(input_path, default_path):
        return
    raise ValueError(
        f"{input_name} is a user-filled MLPE field-trial input. "
        f"Provide an explicit real input path, or pass --allow-user-filled-default "
        f"only for fixture/regression runs. Refusing default: {default_path}"
    )
