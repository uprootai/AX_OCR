"""
Test script for EDGNet pipeline
Creates synthetic test image and runs full pipeline
"""

import numpy as np
import cv2
from pathlib import Path

from vectorization import thin_image, trace_trajectories, fit_bezier_curves
from vectorization.tracing import clean_trajectories
from graph import extract_batch_features, build_graph
from graph.builder import visualize_graph


def create_test_drawing(output_path, size=(1000, 800)):
    """
    Create synthetic engineering drawing for testing

    Args:
        output_path: Path to save test image
        size: Image size (width, height)
    """
    img = np.ones((size[1], size[0]), dtype=np.uint8) * 255

    # Draw contours (rectangles)
    cv2.rectangle(img, (100, 100), (400, 300), 0, 3)
    cv2.rectangle(img, (500, 100), (800, 300), 0, 3)

    # Draw dimensions (lines with arrows)
    cv2.line(img, (100, 350), (400, 350), 0, 2)
    cv2.arrowedLine(img, (100, 350), (110, 350), 0, 2)
    cv2.arrowedLine(img, (400, 350), (390, 350), 0, 2)

    # Draw text regions (simulate text with small rectangles)
    for i in range(5):
        x = 150 + i * 20
        cv2.rectangle(img, (x, 400), (x + 15, 420), 0, -1)

    # Draw circles
    cv2.circle(img, (250, 200), 50, 0, 3)
    cv2.circle(img, (650, 200), 50, 0, 3)

    # Draw angled lines
    cv2.line(img, (100, 500), (300, 600), 0, 2)
    cv2.line(img, (500, 500), (700, 600), 0, 2)

    cv2.imwrite(str(output_path), img)
    print(f"Created test image: {output_path}")

    return img


def test_vectorization():
    """Test vectorization module"""
    print("\n" + "="*60)
    print("TEST 1: Vectorization")
    print("="*60)

    # Create output directory
    output_dir = Path('tests')
    output_dir.mkdir(exist_ok=True)

    # Create test image
    test_img_path = output_dir / 'test_drawing.png'
    img = create_test_drawing(test_img_path)

    # Step 1: Thinning
    print("\n[1/3] Thinning...")
    skeleton = thin_image(img, method='skeletonize', smooth=True)
    cv2.imwrite(str(output_dir / 'test_skeleton.png'), skeleton)
    print(f"  ✓ Skeleton saved")

    # Step 2: Tracing
    print("\n[2/3] Tracing...")
    trajectories = trace_trajectories(skeleton)
    print(f"  ✓ Found {len(trajectories)} trajectories")

    trajectories = clean_trajectories(trajectories, min_length=4)
    print(f"  ✓ After cleaning: {len(trajectories)} trajectories")

    # Step 3: Bezier fitting
    print("\n[3/3] Bezier fitting...")
    bezier_curves = fit_bezier_curves(trajectories, method='least_squares')
    print(f"  ✓ Fitted {len(bezier_curves)} curves")

    # Visualize trajectories
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(img, cmap='gray')
    axes[0].set_title('Original')
    axes[0].axis('off')

    axes[1].imshow(skeleton, cmap='gray')
    axes[1].set_title('Skeleton')
    axes[1].axis('off')

    axes[2].imshow(img, cmap='gray', alpha=0.3)
    for bezier in bezier_curves:
        t_vals = np.linspace(0, 1, 50)
        points = bezier.evaluate(t_vals)
        axes[2].plot(points[:, 0], points[:, 1], 'r-', linewidth=1)
    axes[2].set_title(f'Bezier Curves ({len(bezier_curves)})')
    axes[2].axis('off')

    plt.tight_layout()
    plt.savefig(output_dir / 'test_vectorization.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ Visualization saved to {output_dir / 'test_vectorization.png'}")

    return bezier_curves, img.shape


def test_graph_construction(bezier_curves, image_shape):
    """Test graph construction"""
    print("\n" + "="*60)
    print("TEST 2: Graph Construction")
    print("="*60)

    output_dir = Path('tests')
    image_size = (image_shape[1], image_shape[0])

    # Extract features
    print("\n[1/2] Feature extraction...")
    features = extract_batch_features(bezier_curves, n_samples=4,
                                      normalize=True, image_size=image_size)
    print(f"  ✓ Extracted features: shape={features.shape}")

    # Build graph
    print("\n[2/2] Building graph...")
    G = build_graph(bezier_curves, features, connection_threshold=15.0,
                   image_size=image_size)
    print(f"  ✓ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Visualize
    visualize_graph(G, bezier_curves, image_size,
                   output_path=str(output_dir / 'test_graph.png'))

    return G, features


def test_model():
    """Test GraphSAGE model with synthetic data"""
    print("\n" + "="*60)
    print("TEST 3: GraphSAGE Model")
    print("="*60)

    import torch
    from models import GraphSAGEModel, train_model, evaluate_model, create_data_object

    # Create synthetic data
    print("\nCreating synthetic training data...")
    num_nodes = 100
    num_features = 19
    num_classes = 3

    x = torch.randn(num_nodes, num_features)
    edge_index = torch.randint(0, num_nodes, (2, 200))
    y = torch.randint(0, num_classes, (num_nodes,))

    # Masks
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    train_mask[:60] = True
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask[60:80] = True
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask[80:] = True

    data = create_data_object(x.numpy(), edge_index.numpy(), y.numpy(),
                             train_mask.numpy(), val_mask.numpy(), test_mask.numpy())

    # Create model
    print("\nCreating model...")
    model = GraphSAGEModel(in_channels=num_features, hidden_channels=32,
                           out_channels=num_classes, dropout=0.3)
    print(f"  ✓ Model created: {sum(p.numel() for p in model.parameters())} parameters")

    # Train
    print("\nTraining model (20 epochs)...")
    history = train_model(model, data, num_epochs=20, learning_rate=0.01)

    # Evaluate
    print("\nEvaluating model...")
    metrics = evaluate_model(model, data)

    # Save model
    output_dir = Path('models')
    output_dir.mkdir(exist_ok=True)
    from models.graphsage import save_model
    save_model(model, str(output_dir / 'test_model.pth'))

    return model, history, metrics


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# EDGNet Pipeline Tests")
    print("#"*60)

    try:
        # Test 1: Vectorization
        bezier_curves, image_shape = test_vectorization()

        # Test 2: Graph Construction
        G, features = test_graph_construction(bezier_curves, image_shape)

        # Test 3: Model
        model, history, metrics = test_model()

        print("\n" + "#"*60)
        print("# ALL TESTS PASSED ✓")
        print("#"*60)
        print("\nTest outputs saved to:")
        print("  - tests/test_*.png (visualizations)")
        print("  - models/test_model.pth (trained model)")

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
