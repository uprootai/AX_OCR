"""
Ensemble Logic
Weighted voting and result merging for multi-engine OCR
"""
import re
from typing import List, Dict
from collections import defaultdict

from schemas import OCRResult, EnsembleResult


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    # Lowercase, normalize spaces, keep special chars (important for dimensions)
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity"""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)

    if t1 == t2:
        return 1.0

    # Jaccard similarity (character level)
    set1 = set(t1)
    set2 = set(t2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def merge_results(
    engine_results: Dict[str, List[OCRResult]],
    weights: Dict[str, float],
    similarity_threshold: float = 0.7
) -> List[EnsembleResult]:
    """
    Merge results using weighted voting

    1. Collect all results
    2. Group similar texts together
    3. Select final text based on weighted votes
    4. Calculate combined confidence
    """
    # Collect all results
    all_results = []
    for engine, results in engine_results.items():
        for r in results:
            all_results.append({
                "text": r.text,
                "confidence": r.confidence,
                "bbox": r.bbox,
                "source": engine,
                "weight": weights.get(engine, 0.1)
            })

    if not all_results:
        return []

    # Group similar texts
    groups = []
    used = set()

    for i, result in enumerate(all_results):
        if i in used:
            continue

        group = [result]
        used.add(i)

        for j, other in enumerate(all_results):
            if j in used:
                continue

            similarity = calculate_text_similarity(result["text"], other["text"])
            if similarity >= similarity_threshold:
                group.append(other)
                used.add(j)

        groups.append(group)

    # Select final result from each group
    ensemble_results = []

    for group in groups:
        # Weighted voting
        text_votes = defaultdict(float)
        text_sources = defaultdict(list)

        for item in group:
            normalized = normalize_text(item["text"])
            vote = item["weight"] * item["confidence"]
            text_votes[normalized] += vote
            text_sources[normalized].append(item["source"])

        # Select text with highest votes
        if not text_votes:
            continue

        best_text = max(text_votes.keys(), key=lambda t: text_votes[t])

        # Find original text (preserve case)
        original_text = best_text
        for item in group:
            if normalize_text(item["text"]) == best_text:
                original_text = item["text"]
                break

        # Calculate confidence (weighted average)
        total_weight = sum(item["weight"] for item in group)
        if total_weight > 0:
            weighted_confidence = sum(
                item["confidence"] * item["weight"]
                for item in group
            ) / total_weight
        else:
            weighted_confidence = 0.5

        # Agreement bonus (more engines agree = higher confidence)
        unique_sources = set(text_sources[best_text])
        agreement_bonus = min(len(unique_sources) * 0.05, 0.2)  # Max 0.2 bonus

        final_confidence = min(weighted_confidence + agreement_bonus, 1.0)

        # Select bbox (from highest confidence result)
        best_bbox = None
        for item in group:
            if item["bbox"] and normalize_text(item["text"]) == best_text:
                best_bbox = item["bbox"]
                break

        # Vote information
        votes = {}
        for item in group:
            engine = item["source"]
            votes[engine] = votes.get(engine, 0) + item["weight"] * item["confidence"]

        ensemble_results.append(EnsembleResult(
            text=original_text,
            confidence=final_confidence,
            bbox=best_bbox,
            votes=votes,
            sources=list(unique_sources)
        ))

    # Sort by confidence
    ensemble_results.sort(key=lambda x: x.confidence, reverse=True)

    return ensemble_results
