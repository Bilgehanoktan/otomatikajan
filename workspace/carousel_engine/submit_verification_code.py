"""Deprecated compatibility entrypoint for verification-code submission."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def submit_verification_code(code_str: str) -> None:
    """Block browser/session verification and discard the supplied code."""

    del code_str
    block_legacy_browser_mutation("Instagram verification-code submission")
