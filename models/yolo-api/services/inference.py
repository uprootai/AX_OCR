"""
YOLO Inference Service
"""
from typing import List, Optional
from pathlib import Path
import torch
from ultralytics import YOLO

from models.schemas import Detection
from utils.helpers import CLASS_NAMES


class YOLOInferenceService:
    """YOLO model inference service"""

    def __init__(self, model_path: str):
        """
        Initialize YOLO inference service

        Args:
            model_path: Path to YOLO model file
        """
        self.model_path = model_path
        self.model: Optional[YOLO] = None
        self.device: str = "cpu"

    def load_model(self):
        """Load YOLO model and detect device"""
        # Check GPU availability
        if torch.cuda.is_available():
            self.device = "0"
            print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
            print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            self.device = "cpu"
            print("⚠️  GPU not available, using CPU")

        # Check model file
        if not Path(self.model_path).exists():
            print(f"⚠️  Model not found at {self.model_path}")
            print(f"   Using default YOLOv11n pretrained model for prototype")
            self.model = YOLO('yolo11n.pt')
        else:
            print(f"📥 Loading model from {self.model_path}")
            self.model = YOLO(self.model_path)

        print(f"✅ Model loaded successfully on {self.device}")

    def predict(
        self,
        image_path: str,
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        imgsz: int = 1280,
        task: str = "detect"
    ) -> List[Detection]:
        """
        Run YOLO inference on image

        Args:
            image_path: Path to image file
            conf_threshold: Confidence threshold (0-1)
            iou_threshold: NMS IoU threshold (0-1)
            imgsz: Input image size
            task: Task type (detect or segment)

        Returns:
            List of Detection objects
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        # Validate task
        if task not in ["detect", "segment"]:
            print(f"⚠️  Invalid task '{task}', using 'detect'")
            task = "detect"

        # Run inference
        # Note: Task is determined by model file type:
        # - Detection models: yolo11n.pt, best.pt
        # - Segmentation models: yolo11n-seg.pt, best-seg.pt
        # The task parameter is accepted but currently ignored until -seg models are available
        results = self.model.predict(
            source=image_path,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=imgsz,
            device=self.device,
            verbose=False
        )

        # Convert to Detection format
        detections = self._yolo_to_detection_format(results[0])
        return detections

    def _yolo_to_detection_format(self, result) -> List[Detection]:
        """
        Convert YOLO result to Detection format

        Args:
            result: YOLO detection result

        Returns:
            List of Detection objects
        """
        detections = []
        boxes = result.boxes

        for box in boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = CLASS_NAMES.get(cls_id, 'unknown')

            # Bounding box (xyxy format)
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # Convert to pixel coordinates
            bbox = {
                'x': int(x1),
                'y': int(y1),
                'width': int(x2 - x1),
                'height': int(y2 - y1)
            }

            detection = Detection(
                class_id=cls_id,
                class_name=class_name,
                confidence=confidence,
                bbox=bbox,
                value=None  # OCR refinement needed
            )

            detections.append(detection)

        return detections

    def filter_text_blocks(self, detections: List[Detection], min_confidence: float = 0.65) -> List[Detection]:
        """
        Filter text blocks to remove noise

        Strategy:
        1. Keep all priority classes (dimensions, GD&T)
        2. Keep only high-confidence text_blocks (>0.65)
        3. Keep reference_dim

        Args:
            detections: List of Detection objects
            min_confidence: Minimum confidence for text_blocks

        Returns:
            Filtered detections
        """
        priority_classes = [
            'diameter_dim', 'linear_dim', 'radius_dim', 'angular_dim', 'chamfer_dim',
            'tolerance_dim', 'reference_dim',
            'flatness', 'cylindricity', 'position', 'perpendicularity', 'parallelism',
            'surface_roughness'
        ]

        filtered = []
        for det in detections:
            # Keep all priority classes
            if det.class_name in priority_classes:
                filtered.append(det)
            # Keep high-confidence text_blocks only
            elif det.class_name == 'text_block' and det.confidence >= min_confidence:
                filtered.append(det)

        return filtered

    def remove_duplicate_detections(
        self,
        detections: List[Detection],
        iou_threshold: float = 0.3
    ) -> List[Detection]:
        """
        Remove duplicate detections

        Remove lower-confidence boxes that overlap with higher-confidence ones
        within the same class.

        Args:
            detections: List of Detection objects
            iou_threshold: IoU threshold for duplicates

        Returns:
            Filtered detections
        """
        from utils.helpers import calculate_iou

        if not detections:
            return []

        # Group by class
        class_groups = {}
        for det in detections:
            if det.class_name not in class_groups:
                class_groups[det.class_name] = []
            class_groups[det.class_name].append(det)

        result = []

        for cls, dets in class_groups.items():
            # Sort by confidence descending
            sorted_dets = sorted(dets, key=lambda x: x.confidence, reverse=True)

            keep = []
            for det in sorted_dets:
                should_keep = True
                for kept_det in keep:
                    if calculate_iou(det, kept_det) > iou_threshold:
                        should_keep = False
                        break

                if should_keep:
                    keep.append(det)

            result.extend(keep)

        return result
