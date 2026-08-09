"""Impact Slide Renderer v3 — schema-v1 canonical rendering kernel.

Public surface for this delivery is validation into a typed deck model.
Painting lands in later tickets; this package stays isolated from the legacy renderer.
"""
from __future__ import annotations

from .diagnostics import DiagnosticEvent, RendererValidationError
from .validate import ValidationResult, validate_handoff

__version__ = "3.0.0"

__all__ = [
    "DiagnosticEvent",
    "RendererValidationError",
    "ValidationResult",
    "validate_handoff",
    "__version__",
]
