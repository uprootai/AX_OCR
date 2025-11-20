"""
Visualization utilities for EDGNet API
"""
import cv2
import base64
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_edgnet_visualization(
    image_path: str,
    edgnet_results: Dict[str, Any]
) -> Optional[str]:
    """
    Create visualization for EDGNet segmentation results

    Args:
        image_path: Path to the image file
        edgnet_results: EDGNet results with components

    Returns:
        Base64 encoded visualization image
    """
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Failed to read image: {image_path}")
            return None

        # Create overlay with alpha blending
        overlay = img.copy()

        # Vibrant color map for different classes (BGR format)
        class_colors = {
            0: (128, 128, 128),  # Background - gray (skip)
            1: (255, 100, 0),    # Contour - bright blue/cyan
            2: (50, 255, 50),    # Text - bright lime green
            3: (0, 100, 255),    # Dimension - bright orange/red
        }

        # Draw components with semi-transparent overlay
        components = edgnet_results.get('components', [])
        for comp in components:
            bbox = comp.get('bbox', {})
            class_id = comp.get('class_id', 0)

            if class_id == 0:  # Skip background
                continue

            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            width = bbox.get('width', 0)
            height = bbox.get('height', 0)

            color = class_colors.get(class_id, (255, 255, 255))

            # Draw thicker rectangle
            cv2.rectangle(overlay, (x, y), (x + width, y + height), color, 3)

            # Add semi-transparent fill
            temp_overlay = overlay.copy()
            cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), color, -1)
            cv2.addWeighted(temp_overlay, 0.1, overlay, 0.9, 0, overlay)

            # Draw class label with background
            class_names = {1: 'Contour', 2: 'Text', 3: 'Dim'}
            label = class_names.get(class_id, 'Unknown')

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1

            # Get text size
            (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, thickness)

            # Draw text background
            bg_y = max(y - text_height - 8, 0)
            cv2.rectangle(
                overlay,
                (x, bg_y),
                (x + text_width + 4, y - 2),
                color,
                -1
            )

            # Draw text with outline
            text_pos = (x + 2, y - 4)
            cv2.putText(overlay, label, text_pos, font, font_scale, (0, 0, 0), thickness + 1)
            cv2.putText(overlay, label, text_pos, font, font_scale, (255, 255, 255), thickness)

        # Add enhanced legend with better visibility
        legend_x = 10
        legend_y = 35
        legend_bg_height = 85

        # Draw legend background (semi-transparent black)
        cv2.rectangle(overlay, (legend_x - 5, legend_y - 30), (160, legend_y + legend_bg_height - 30), (0, 0, 0), -1)
        overlay_with_alpha = overlay.copy()
        cv2.rectangle(overlay_with_alpha, (legend_x - 5, legend_y - 30), (160, legend_y + legend_bg_height - 30), (0, 0, 0), -1)
        cv2.addWeighted(overlay_with_alpha, 0.6, overlay, 0.4, 0, overlay)

        for class_id, color in class_colors.items():
            if class_id == 0:
                continue  # Skip background
            class_names = {1: 'Contour', 2: 'Text', 3: 'Dimension'}
            label = class_names.get(class_id, 'Unknown')

            # Draw color box with border
            cv2.rectangle(overlay, (legend_x, legend_y - 15), (legend_x + 25, legend_y), color, -1)
            cv2.rectangle(overlay, (legend_x, legend_y - 15), (legend_x + 25, legend_y), (255, 255, 255), 2)

            # Draw label with outline
            text_pos = (legend_x + 30, legend_y - 3)
            cv2.putText(overlay, label, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(overlay, label, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            legend_y += 25

        # Encode to base64
        _, buffer = cv2.imencode('.jpg', overlay)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        logger.info(f"Created EDGNet visualization with {len(components)} components")
        return img_base64

    except Exception as e:
        logger.error(f"Failed to create EDGNet visualization: {e}")
        return None


def create_unet_visualization(
    image_path: str,
    segmentation_mask: np.ndarray
) -> Optional[str]:
    """
    UNet 세그멘테이션 결과 시각화 생성

    Args:
        image_path: 원본 이미지 경로
        segmentation_mask: 세그멘테이션 마스크 (0 또는 255)

    Returns:
        Base64로 인코딩된 시각화 이미지
    """
    try:
        # Load original image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Failed to read image: {image_path}")
            return None

        # Ensure mask has same size as image
        if segmentation_mask.shape[:2] != img.shape[:2]:
            logger.warning(
                f"Mask size {segmentation_mask.shape[:2]} != Image size {img.shape[:2]}"
            )
            segmentation_mask = cv2.resize(
                segmentation_mask,
                (img.shape[1], img.shape[0]),
                interpolation=cv2.INTER_NEAREST
            )

        # Create colored overlay (cyan for edges)
        overlay = img.copy()

        # Create mask for edges (where mask > 0)
        edge_mask = segmentation_mask > 0

        # Apply cyan color to edges
        overlay[edge_mask] = cv2.addWeighted(
            overlay[edge_mask],
            0.5,  # 50% original
            np.full_like(overlay[edge_mask], [255, 255, 0]),  # Cyan (BGR)
            0.5,  # 50% cyan
            0
        )

        # Draw edge contours for better visibility
        contours, _ = cv2.findContours(
            segmentation_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(overlay, contours, -1, (0, 255, 255), 2)  # Yellow outline

        # Add statistics box
        edge_pixels = np.sum(edge_mask)
        total_pixels = edge_mask.size
        edge_percentage = (edge_pixels / total_pixels) * 100

        # Draw info box background
        info_box_height = 80
        info_box_width = 280
        info_x, info_y = 10, 10

        # Semi-transparent background
        overlay_bg = overlay.copy()
        cv2.rectangle(
            overlay_bg,
            (info_x, info_y),
            (info_x + info_box_width, info_y + info_box_height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay_bg, 0.6, overlay, 0.4, 0, overlay)

        # Draw border
        cv2.rectangle(
            overlay,
            (info_x, info_y),
            (info_x + info_box_width, info_y + info_box_height),
            (255, 255, 255),
            2
        )

        # Add text information
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        line_height = 20

        texts = [
            f"UNet Segmentation",
            f"Edge Pixels: {edge_pixels:,}",
            f"Coverage: {edge_percentage:.2f}%",
        ]

        y_offset = info_y + 20
        for text in texts:
            # Black outline
            cv2.putText(
                overlay,
                text,
                (info_x + 10, y_offset),
                font,
                font_scale,
                (0, 0, 0),
                thickness + 1
            )
            # White text
            cv2.putText(
                overlay,
                text,
                (info_x + 10, y_offset),
                font,
                font_scale,
                (255, 255, 255),
                thickness
            )
            y_offset += line_height

        # Add color legend
        legend_y = info_y + info_box_height + 20
        legend_height = 40

        # Legend background
        overlay_bg = overlay.copy()
        cv2.rectangle(
            overlay_bg,
            (info_x, legend_y),
            (info_x + info_box_width, legend_y + legend_height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay_bg, 0.6, overlay, 0.4, 0, overlay)

        # Legend border
        cv2.rectangle(
            overlay,
            (info_x, legend_y),
            (info_x + info_box_width, legend_y + legend_height),
            (255, 255, 255),
            2
        )

        # Color box and label
        color_box_size = 20
        cv2.rectangle(
            overlay,
            (info_x + 10, legend_y + 10),
            (info_x + 10 + color_box_size, legend_y + 10 + color_box_size),
            (255, 255, 0),  # Cyan
            -1
        )
        cv2.rectangle(
            overlay,
            (info_x + 10, legend_y + 10),
            (info_x + 10 + color_box_size, legend_y + 10 + color_box_size),
            (255, 255, 255),
            1
        )

        # Legend text
        cv2.putText(
            overlay,
            "Detected Edges",
            (info_x + 40, legend_y + 25),
            font,
            font_scale,
            (0, 0, 0),
            thickness + 1
        )
        cv2.putText(
            overlay,
            "Detected Edges",
            (info_x + 40, legend_y + 25),
            font,
            font_scale,
            (255, 255, 255),
            thickness
        )

        # Encode to base64
        _, buffer = cv2.imencode('.jpg', overlay, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        logger.info(
            f"Created UNet visualization: {edge_pixels} edge pixels ({edge_percentage:.2f}%)"
        )
        return img_base64

    except Exception as e:
        logger.error(f"Failed to create UNet visualization: {e}", exc_info=True)
        return None
