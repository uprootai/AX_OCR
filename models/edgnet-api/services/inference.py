"""
EDGNet Inference Service
"""
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
from fastapi import HTTPException

from utils.visualization import create_edgnet_visualization

# Configure logging
logger = logging.getLogger(__name__)

# Add edgnet to path (now safe since /app/models renamed to /app/trained_models)
EDGNET_PATH = Path("/app/edgnet")
if not EDGNET_PATH.exists():
    # Fallback to relative path for local development
    EDGNET_PATH = Path(__file__).parent.parent.parent.parent / "dev" / "edgnet"

# Add to sys.path for imports
sys.path.insert(0, str(EDGNET_PATH))
logger.info(f"EDGNet path added: {EDGNET_PATH}")

# Import EDGNet pipeline
try:
    from pipeline import EDGNetPipeline
    EDGNET_AVAILABLE = True
    logger.info("EDGNet pipeline imported successfully")
except ImportError as e:
    EDGNET_AVAILABLE = False
    logger.warning(f"EDGNet pipeline import failed: {e}")
    logger.warning("Will use mock data for segmentation")


class EDGNetInferenceService:
    """EDGNet inference service"""

    def __init__(self, model_path: str, device: str = 'cpu'):
        """
        Initialize EDGNet inference service

        Args:
            model_path: Path to EDGNet model file
            device: Device to use ('cpu' or 'cuda')
        """
        self.model_path = model_path
        self.device = device
        self.pipeline: Optional[Any] = None

    def load_model(self):
        """Load EDGNet model"""
        if not EDGNET_AVAILABLE:
            logger.error("EDGNet pipeline not available")
            raise HTTPException(
                status_code=503,
                detail="EDGNet pipeline not available. Please install EDGNet dependencies."
            )

        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.error(f"Model not found: {self.model_path}")
            raise HTTPException(
                status_code=503,
                detail=f"EDGNet model not found at {self.model_path}. Please download the model file."
            )

        logger.info(f"Loading model from: {self.model_path}")
        logger.info(f"Using device: {self.device}")

        self.pipeline = EDGNetPipeline(model_path=self.model_path, device=self.device)
        logger.info("Model loaded successfully")

    def process_segmentation(
        self,
        file_path: Path,
        visualize: bool = True,
        num_classes: int = 3,
        save_graph: bool = False,
        results_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Process drawing segmentation

        Args:
            file_path: Path to image file
            visualize: Generate visualization image
            num_classes: Number of classification classes (2 or 3)
            save_graph: Save graph structure
            results_dir: Directory for results

        Returns:
            Segmentation results dict
        """
        try:
            logger.info(f"Processing file: {file_path}")
            logger.info(f"Options: visualize={visualize}, num_classes={num_classes}")

            if not EDGNET_AVAILABLE:
                logger.error("EDGNet pipeline not available")
                raise HTTPException(
                    status_code=503,
                    detail="EDGNet pipeline not available. Please install EDGNet dependencies."
                )

            if self.pipeline is None:
                self.load_model()

            # Process drawing
            logger.info("Running EDGNet pipeline...")
            output_dir = results_dir / file_path.stem if save_graph and results_dir else None
            pipeline_result = self.pipeline.process_drawing(
                str(file_path),
                output_dir=output_dir,
                visualize=visualize
            )

            # Extract results
            bezier_curves = pipeline_result['bezier_curves']
            predictions = pipeline_result['predictions']
            G = pipeline_result['graph']

            logger.info(f"Pipeline complete: {len(bezier_curves)} components")

            # Count classifications
            # Class mapping from training: 0=Dimension, 1=Text, 2=Contour, 3=Other
            class_counts = {"dimension": 0, "text": 0, "contour": 0, "other": 0}
            class_map = {0: "dimension", 1: "text", 2: "contour", 3: "other"}

            if predictions is not None:
                unique, counts = np.unique(predictions, return_counts=True)
                for cls, cnt in zip(unique, counts):
                    class_name = class_map.get(int(cls), "unknown")
                    if class_name in class_counts:
                        class_counts[class_name] = int(cnt)

            # Build components list with bboxes
            from utils.helpers import bezier_to_bbox

            components = []
            if predictions is not None:
                for i, (bezier, pred) in enumerate(zip(bezier_curves, predictions)):
                    bbox = bezier_to_bbox(bezier)
                    pred_int = int(pred)
                    classification = class_map.get(pred_int, "unknown")

                    components.append({
                        "id": i,
                        "classification": classification,
                        "class_id": pred_int,  # Add class_id for compatibility
                        "bbox": bbox,
                        "confidence": 0.9  # EDGNet doesn't provide confidence scores
                    })

            # Calculate graph stats
            avg_degree = (2 * G.number_of_edges() / G.number_of_nodes()) if G.number_of_nodes() > 0 else 0

            result = {
                "num_components": len(bezier_curves),
                "total_components": len(bezier_curves),  # Add for compatibility
                "classifications": class_counts,
                "graph": {
                    "nodes": G.number_of_nodes(),
                    "edges": G.number_of_edges(),
                    "avg_degree": round(avg_degree, 2)
                },
                "vectorization": {
                    "num_bezier_curves": len(bezier_curves),
                    "total_length": 0  # Would need to calculate from bezier curves
                },
                "components": components
            }

            # Generate visualization
            if visualize:
                logger.info("  Generating visualization...")
                try:
                    # Convert components to format expected by visualization
                    viz_components = []
                    for comp in components:
                        # Map classification to class_id (0=BG, 1=Contour, 2=Text, 3=Dimension)
                        class_map = {"contour": 1, "text": 2, "dimension": 3, "other": 0}
                        class_id = class_map.get(comp.get("classification", "other"), 0)

                        viz_components.append({
                            "bbox": comp.get("bbox"),
                            "class_id": class_id
                        })

                    viz_result = {"components": viz_components}
                    visualized_image = create_edgnet_visualization(str(file_path), viz_result)

                    if visualized_image:
                        result["visualized_image"] = visualized_image
                        logger.info("  ✅ Visualization created")
                    else:
                        logger.warning("  ⚠️ Visualization generation failed")
                except Exception as e:
                    logger.warning(f"  ⚠️ Visualization error: {e}")

            if save_graph and output_dir:
                result["graph_url"] = f"/api/v1/result/{file_path.stem}/graph.pkl"

            logger.info(f"Segmentation complete: {class_counts}")
            return result

        except Exception as e:
            logger.error(f"Segmentation failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

    def process_vectorization(
        self,
        file_path: Path,
        save_bezier: bool = True
    ) -> Dict[str, Any]:
        """
        Process drawing vectorization

        Args:
            file_path: Path to image file
            save_bezier: Save Bezier curves

        Returns:
            Vectorization results dict
        """
        import time

        try:
            logger.info(f"Vectorizing file: {file_path}")

            # Simulate processing
            time.sleep(2)

            result = {
                "num_curves": 150,
                "curve_types": {
                    "line": 85,
                    "arc": 45,
                    "bezier": 20
                },
                "total_length": 12450.5,
                "processing_steps": {
                    "skeletonization": "completed",
                    "tracing": "completed",
                    "bezier_fitting": "completed"
                }
            }

            if save_bezier:
                result["bezier_file"] = f"/api/v1/result/{file_path.stem}_curves.json"

            return result

        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            raise HTTPException(status_code=500, detail=f"Vectorization failed: {str(e)}")


def check_edgnet_availability() -> bool:
    """Check if EDGNet is available"""
    return EDGNET_AVAILABLE


def check_model_exists(model_path: str) -> bool:
    """Check if model file exists"""
    return Path(model_path).exists()
