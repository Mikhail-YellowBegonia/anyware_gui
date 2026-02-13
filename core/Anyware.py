"""
Compatibility entrypoint for Anyware.

Preferred import:
    from core.anyware import AnywareApp, Page, Component
Legacy-compatible import:
    from core import Anyware
"""

from core.anyware import *  # noqa: F401,F403
