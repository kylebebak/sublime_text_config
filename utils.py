from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def not_none(var: T | None) -> T:
    """
    This narrows type from `T | None` -> `T`.
    """
    assert var is not None
    return var


def maybe_none(var: T) -> T | None:
    return var
