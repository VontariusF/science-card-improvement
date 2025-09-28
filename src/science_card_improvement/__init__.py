"""Science Card Improvement Toolkit."""

from __future__ import annotations

import asyncio
import types

__version__ = "1.0.0"
__author__ = "Science Card Improvement Team"

if not hasattr(asyncio, "coroutine"):
    asyncio.coroutine = types.coroutine  # type: ignore[attr-defined]

from .discovery.repository import RepositoryDiscovery

__all__ = [
    "RepositoryDiscovery",
]
