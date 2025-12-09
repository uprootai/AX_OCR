"""
EDGNet Main Pipeline
End-to-end processing: Image → Vectorization → Graph → Classification
"""

import numpy as np
import cv2
import argparse
import json
import pickle
from pathlib import Path

from vectorization import thin_image, trace_trajectories, fit_bezier_curves
from vectorization.tracing import clean_trajectories
from graph import extract_batch_features, build_graph
from graph.builder import graph_to_pytorch_geometric, visualize_graph
from models import GraphSAGEModel, load_model


class EDGNetPipeline:
    """Complete EDGNet pipeline"""

    def __init__(self, model_path=None, device='cpu'):
        """
        Args:
            model_path: Path to trained GraphSAGE model
            device: 'cpu' or 'cuda'
        """
        self.model = None
        self.device = device

        if model_path and Path(model_path).exists():
            self.model = load_model(model_path, device=device)
            print(f"Loaded model from {model_path}")

    def process_drawing(self, image_path, output_dir=None, visualize=False):
        """
        Process a single engineering drawing

        Args:
            image_path: Path to input image
            output_dir: Output directory for results
            visualize: Whether to save visualizations

        Returns:
            Dictionary with results
        """
        print(f"\n{'='*60}")
        print(f"Processing: {image_path}")
        print(f"{'='*60}\n")

        # Read image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")

        image_size = (image.shape[1], image.shape[0])  # (width, height)
        print(f"Image size: {image_size}")

        # Step 1: Vectorization
        print("\n[1/4] Vectorization...")
        skeleton = thin_image(image, method='skeletonize', smooth=True)
        print("  ✓ Thinning complete")

        trajectories = trace_trajectories(skeleton)
        print(f"  ✓ Tracing complete: {len(trajectories)} trajectories")

        trajectories = clean_trajectories(trajectories, min_length=4)
        print(f"  ✓ Cleaning complete: {len(trajectories)} trajectories")

        bezier_curves = fit_bezier_curves(trajectories, method='least_squares')
        print(f"  ✓ Bezier fitting complete: {len(bezier_curves)} curves")

        # Step 2: Feature Extraction
        print("\n[2/4] Feature extraction...")
        features = extract_batch_features(bezier_curves, n_samples=4,
                                          normalize=True, image_size=image_size)
        print(f"  ✓ Extracted {features.shape[0]} feature vectors (dim={features.shape[1]})")

        # Step 3: Graph Construction
        print("\n[3/4] Graph construction...")
        G = build_graph(bezier_curves, features, connection_threshold=10.0,
                       image_size=image_size)
        print(f"  ✓ Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Step 4: Classification (if model is loaded)
        predictions = None
        if self.model is not None:
            print("\n[4/4] Classification...")
            pyg_data = graph_to_pytorch_geometric(G)
            predictions = self.model.predict(pyg_data['x'].to(self.device),
                                            pyg_data['edge_index'].to(self.device))
            predictions = predictions.cpu().numpy()
            print(f"  ✓ Classification complete")

            # Count classes
            unique, counts = np.unique(predictions, return_counts=True)
            for cls, cnt in zip(unique, counts):
                class_names = {0: 'Contour', 1: 'Text', 2: 'Dimension'}
                name = class_names.get(cls, f'Class {cls}')
                print(f"    {name}: {cnt} components")
        else:
            print("\n[4/4] Classification skipped (no model loaded)")

        # Save results
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save skeleton
            cv2.imwrite(str(output_dir / 'skeleton.png'), skeleton)

            # Save graph
            with open(output_dir / 'graph.pkl', 'wb') as f:
                pickle.dump(G, f)

            # Save features
            np.save(output_dir / 'features.npy', features)

            # Save predictions
            if predictions is not None:
                np.save(output_dir / 'predictions.npy', predictions)

                # Save results as JSON
                results = {
                    'image_path': str(image_path),
                    'image_size': image_size,
                    'num_components': len(bezier_curves),
                    'num_edges': G.number_of_edges(),
                    'predictions': predictions.tolist()
                }
                with open(output_dir / 'results.json', 'w') as f:
                    json.dump(results, f, indent=2)

            # Visualize
            if visualize:
                print("\n[5/5] Visualization...")
                visualize_graph(G, bezier_curves, image_size,
                              output_path=str(output_dir / 'graph_viz.png'))

                # Visualize with predictions
                if predictions is not None:
                    self._visualize_predictions(image, bezier_curves, predictions,
                                               output_path=str(output_dir / 'predictions.png'))

            print(f"\n✓ Results saved to: {output_dir}")

        return {
            'skeleton': skeleton,
            'bezier_curves': bezier_curves,
            'features': features,
            'graph': G,
            'predictions': predictions
        }

    def _visualize_predictions(self, image, bezier_curves, predictions, output_path):
        """Visualize classification results"""
        import matplotlib.pyplot as plt

        # Color map for classes
        colors = {
            0: (0, 0, 255),      # Contour: Blue
            1: (0, 255, 0),      # Text: Green
            2: (255, 0, 0)       # Dimension: Red
        }

        # Create colored output
        output = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        for i, (bezier, pred) in enumerate(zip(bezier_curves, predictions)):
            color = colors.get(pred, (128, 128, 128))
            t_vals = np.linspace(0, 1, 50)
            points = bezier.evaluate(t_vals)
            points = points.astype(np.int32)

            for j in range(len(points) - 1):
                cv2.line(output, tuple(points[j]), tuple(points[j+1]), color, 2)

        cv2.imwrite(output_path, output)
        print(f"  ✓ Predictions visualized: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='EDGNet Pipeline')
    parser.add_argument('--input', type=str, required=True,
                       help='Input image path')
    parser.add_argument('--output', type=str, default='./output',
                       help='Output directory')
    parser.add_argument('--model', type=str, default=None,
                       help='Path to trained model')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate visualizations')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='Device to run on')

    args = parser.parse_args()

    # Create pipeline
    pipeline = EDGNetPipeline(model_path=args.model, device=args.device)

    # Process drawing
    results = pipeline.process_drawing(
        image_path=args.input,
        output_dir=args.output,
        visualize=args.visualize
    )

    print("\n" + "="*60)
    print("Processing complete!")
    print("="*60)


if __name__ == '__main__':
    main()
