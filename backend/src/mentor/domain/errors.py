"""Domain-level exceptions.

The API layer translates these into HTTP responses; the domain itself never
imports anything HTTP-aware.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain-level failures."""


class ValidationError(DomainError):
    """A caller-supplied value violated a business rule."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class GuardrailBreach(DomainError):
    """A trade or aggregate state violates a configured risk guardrail."""
