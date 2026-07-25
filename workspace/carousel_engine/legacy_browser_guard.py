"""Central fail-closed guard for deprecated Instagram browser mutations."""

from __future__ import annotations


class LegacyBrowserMutationDisabledError(RuntimeError):
    """Raised when code attempts an unsupported Instagram UI mutation."""


def block_legacy_browser_mutation(action: str) -> None:
    """Reject password, cookie, session, or UI-driven Instagram mutations."""

    raise LegacyBrowserMutationDisabledError(
        f"{action} disabled; use the official services.social_growth Meta Graph workflow"
    )
