"""Focused tests for detection_service regressions."""

from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.detection_service import merge_collinear_lines


def test_merge_collinear_lines_does_not_merge_wrapped_right_angle() -> None:
    """Regression for wrapped angle diffs like -90.3 vs 180.0."""
    lines = [
        {
            "id": 0,
            "start_point": (0.0, 0.0),
            "end_point": (0.0, 10.0),
            "length": 10.0,
            "angle": -90.3,
        },
        {
            "id": 1,
            "start_point": (0.0, 10.0),
            "end_point": (-10.0, 10.0),
            "length": 10.0,
            "angle": 180.0,
        },
    ]

    merged = merge_collinear_lines(lines, angle_threshold=5.0, distance_threshold=20.0)

    assert len(merged) == 2
