"""Science Card Improvement Toolkit.

A comprehensive toolkit for discovering, assessing, and improving dataset
and model cards on Hugging Face, with a focus on scientific datasets and models.
"""

__version__ = "1.0.0"
__author__ = "Science Card Improvement Team"

from src.core.discovery import RepositoryDiscovery
from src.core.assessment import CardAssessment
from src.core.generator import CardGenerator
from src.core.submitter import PRSubmitter

__all__ = [
    "RepositoryDiscovery",
    "CardAssessment",
    "CardGenerator",
    "PRSubmitter",
]