"""D115 authored semantic ID format."""
from __future__ import annotations

import re

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def is_semantic_id(value: object) -> bool:
    return isinstance(value, str) and ID_PATTERN.fullmatch(value) is not None
