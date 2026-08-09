"""Impact Slide Renderer v3 — schema-v1 canonical rendering kernel.

Public surface: validate_handoff + render_deck (+ CLI module entry).
"""
from __future__ import annotations

from .diagnostics import (
    DiagnosticEvent,
    RendererConfigurationError,
    RendererPublicationError,
    RendererValidationError,
)
from .render import SELF_CONTAINED, render_deck
from .validate import ValidationResult, validate_handoff

from ._version import __version__

__all__ = [
    "DiagnosticEvent",
    "RendererConfigurationError",
    "RendererPublicationError",
    "RendererValidationError",
    "SELF_CONTAINED",
    "ValidationResult",
    "render_deck",
    "validate_handoff",
    "__version__",
]
