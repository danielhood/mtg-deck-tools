"""Deck validation and dependency analysis (dogfood matrices, reports)."""

from mtg_deck_tools.analysis.runner import AnalysisSuiteResult, run_analysis_suite
from mtg_deck_tools.analysis.serialize import case_result_to_dict

__all__ = [
    "AnalysisSuiteResult",
    "case_result_to_dict",
    "run_analysis_suite",
]
