"""Science Card Improvement Toolkit.

A comprehensive toolkit for discovering, assessing, and improving dataset
and model cards on Hugging Face, with a focus on scientific datasets and models.
"""

from __future__ import annotations

import asyncio
import types

__version__ = "1.0.0"
__author__ = "Science Card Improvement Team"

if not hasattr(asyncio, "coroutine"):
    asyncio.coroutine = types.coroutine  # type: ignore[attr-defined]

from src.core.discovery import RepositoryDiscovery

__all__ = [
    "RepositoryDiscovery",
]
