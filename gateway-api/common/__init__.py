"""
Common utilities for Gateway API
"""
from .weighted_voting import (
    VotingCandidate,
    VotingResult,
    WeightedVoter,
    create_iou_cluster_fn,
    create_text_similarity_cluster_fn,
    normalize_dimension_value,
    normalize_ocr_text,
)

__all__ = [
    "VotingCandidate",
    "VotingResult",
    "WeightedVoter",
    "create_iou_cluster_fn",
    "create_text_similarity_cluster_fn",
    "normalize_dimension_value",
    "normalize_ocr_text",
]
