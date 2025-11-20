"""
Visualization utilities for Skin Model API
"""
import cv2
import base64
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_tolerance_visualization(
    tolerance_results: Dict[str, Any],
    width: int = 800,
    height: int = 600
) -> Optional[str]:
    """
    Create visualization for tolerance prediction results

    Args:
        tolerance_results: Tolerance prediction results
        width: Image width
        height: Image height

    Returns:
        Base64 encoded visualization image
    """
    try:
        # Create blank canvas
        img = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Extract data
        data = tolerance_results.get('data', {})
        manufacturability = data.get('manufacturability', {})
        score = manufacturability.get('score', 0)
        difficulty = manufacturability.get('difficulty', 'Unknown')

        feasibility_score = data.get('feasibility_score', 0)
        recommended_tolerance = data.get('recommended_tolerance', {})
        material = data.get('material', 'Unknown')
        process = data.get('manufacturing_process', 'Unknown')

        # Title
        cv2.putText(
            img,
            "Tolerance Analysis Results",
            (width // 2 - 200, 50),
            cv2.FONT_HERSHEY_DUPLEX,
            1.2,
            (0, 0, 0),
            2
        )

        # Draw manufacturability score gauge
        center_x = width // 4
        center_y = height // 2 - 50
        radius = 100

        # Background circle
        cv2.circle(img, (center_x, center_y), radius, (200, 200, 200), 10)

        # Score arc (0-100%)
        angle = int(score * 3.6)  # Convert to degrees
        color = (0, 255, 0) if score > 70 else (0, 165, 255) if score > 40 else (0, 0, 255)

        cv2.ellipse(
            img,
            (center_x, center_y),
            (radius, radius),
            -90,
            0,
            angle,
            color,
            10
        )

        # Score text
        cv2.putText(
            img,
            f"{score:.1f}%",
            (center_x - 50, center_y + 10),
            cv2.FONT_HERSHEY_DUPLEX,
            1.5,
            (0, 0, 0),
            3
        )

        cv2.putText(
            img,
            "Manufacturability",
            (center_x - 80, center_y + 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            1
        )

        # Draw difficulty badge
        difficulty_y = center_y + 180
        difficulty_colors = {
            'Easy': (0, 255, 0),
            'Medium': (0, 165, 255),
            'Hard': (0, 0, 255),
            'Very Hard': (128, 0, 128)
        }
        diff_color = difficulty_colors.get(difficulty, (128, 128, 128))

        cv2.rectangle(
            img,
            (center_x - 60, difficulty_y - 25),
            (center_x + 60, difficulty_y + 10),
            diff_color,
            -1
        )

        cv2.putText(
            img,
            difficulty,
            (center_x - 50, difficulty_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # Information panel
        info_x = width // 2 + 50
        info_y = 150
        line_height = 40

        info_items = [
            ("Material:", material),
            ("Process:", process),
            ("Feasibility:", f"{feasibility_score:.2f}" if feasibility_score else "N/A"),
        ]

        if recommended_tolerance.get('value'):
            tol_val = recommended_tolerance.get('value', 0)
            tol_unit = recommended_tolerance.get('unit', 'mm')
            info_items.append(("Recommended Tol:", f"{tol_val} {tol_unit}"))

        for i, (label, value) in enumerate(info_items):
            y = info_y + i * line_height

            # Label
            cv2.putText(
                img,
                label,
                (info_x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (100, 100, 100),
                1
            )

            # Value
            cv2.putText(
                img,
                str(value),
                (info_x + 180, y),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (0, 0, 0),
                2
            )

        # Draw tolerance range bar (if available)
        if 'tolerance_range' in data:
            tol_range = data['tolerance_range']
            min_tol = tol_range.get('min', 0)
            max_tol = tol_range.get('max', 1)
            recommended = tol_range.get('recommended', 0.5)

            bar_x = info_x
            bar_y = info_y + len(info_items) * line_height + 50
            bar_width = 300
            bar_height = 30

            # Background
            cv2.rectangle(
                img,
                (bar_x, bar_y),
                (bar_x + bar_width, bar_y + bar_height),
                (200, 200, 200),
                -1
            )

            # Recommended position
            if max_tol > min_tol:
                rec_pos = int(bar_width * (recommended - min_tol) / (max_tol - min_tol))
                cv2.circle(img, (bar_x + rec_pos, bar_y + bar_height // 2), 8, (0, 255, 0), -1)

            # Labels
            cv2.putText(
                img,
                "Tolerance Range",
                (bar_x, bar_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                1
            )

            cv2.putText(
                img,
                f"{min_tol}",
                (bar_x, bar_y + bar_height + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (100, 100, 100),
                1
            )

            cv2.putText(
                img,
                f"{max_tol}",
                (bar_x + bar_width - 30, bar_y + bar_height + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (100, 100, 100),
                1
            )

        # Footer
        cv2.putText(
            img,
            "Generated by Skin Model Tolerance Predictor",
            (width // 2 - 220, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (150, 150, 150),
            1
        )

        # Encode to base64
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        logger.info(f"Created tolerance visualization (score: {score}%, difficulty: {difficulty})")
        return img_base64

    except Exception as e:
        logger.error(f"Failed to create tolerance visualization: {e}")
        import traceback
        traceback.print_exc()
        return None
