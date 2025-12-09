"""
Feature Extraction module
Extracts 19-dimensional feature vectors from Bezier curves

Feature breakdown (n=4 sampling points):
- Shape: 2n = 8 (XY coordinates of n sample points)
- Length: n-1 + 2 = 5 (segment lengths + total + ratio)
- Angle: n-2 = 2 (cosine angles between consecutive segments)
- Curvature: n = 4 (curvature at each sample point)
Total: 19 dimensions
"""

import numpy as np


def extract_features(bezier, n_samples=4, normalize=True, image_size=(1000, 1000)):
    """
    Extract 19-dimensional feature vector from a Bezier curve

    Args:
        bezier: CubicBezier object
        n_samples: Number of sampling points (default: 4)
        normalize: Whether to normalize coordinates to unit square
        image_size: Original image size for normalization (width, height)

    Returns:
        Feature vector as numpy array (19,)
    """
    # Sample points along the curve
    t_vals = np.linspace(0, 1, n_samples)
    sample_points = bezier.evaluate(t_vals)  # (n_samples, 2)

    # Normalize to unit square if requested
    if normalize:
        sample_points = sample_points / np.array([image_size[0], image_size[1]])

    # 1. Shape features (2n = 8)
    shape_features = sample_points.flatten()  # (8,)

    # 2. Length features (n-1 + 2 = 5)
    # Segment lengths
    segment_lengths = []
    for i in range(n_samples - 1):
        p1 = sample_points[i]
        p2 = sample_points[i + 1]
        length = np.linalg.norm(p2 - p1)
        segment_lengths.append(length)

    # Total length
    total_length = bezier.length(num_samples=100)
    if normalize:
        total_length = total_length / np.sqrt(image_size[0]**2 + image_size[1]**2)

    # First-to-last distance / total length ratio
    first_to_last = np.linalg.norm(sample_points[-1] - sample_points[0])
    length_ratio = first_to_last / (total_length + 1e-8)

    length_features = np.array(segment_lengths + [total_length, length_ratio])  # (5,)

    # 3. Angle features (n-2 = 2)
    # Cosine angles between consecutive segments
    angles = []
    for i in range(1, n_samples - 1):
        v1 = sample_points[i] - sample_points[i - 1]
        v2 = sample_points[i + 1] - sample_points[i]

        # Cosine angle
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 < 1e-8 or norm2 < 1e-8:
            cos_angle = 1.0  # Straight line
        else:
            cos_angle = np.dot(v1, v2) / (norm1 * norm2)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)

        angles.append(cos_angle)

    angle_features = np.array(angles)  # (2,)

    # 4. Curvature features (n = 4)
    # Curvature at each sample point
    curvatures = []
    for t in t_vals:
        curvature = bezier.curvature(t)
        if normalize:
            # Normalize curvature by image diagonal
            curvature = curvature * np.sqrt(image_size[0]**2 + image_size[1]**2)
        curvatures.append(curvature)

    curvature_features = np.array(curvatures)  # (4,)

    # Concatenate all features
    features = np.concatenate([
        shape_features,      # 8
        length_features,     # 5
        angle_features,      # 2
        curvature_features   # 4
    ])  # Total: 19

    return features


def extract_batch_features(bezier_curves, n_samples=4, normalize=True, image_size=(1000, 1000)):
    """
    Extract features from multiple Bezier curves

    Args:
        bezier_curves: List of CubicBezier objects
        n_samples: Number of sampling points
        normalize: Whether to normalize
        image_size: Image size for normalization

    Returns:
        Feature matrix as numpy array (num_curves, 19)
    """
    features_list = []

    for bezier in bezier_curves:
        features = extract_features(bezier, n_samples, normalize, image_size)
        features_list.append(features)

    return np.array(features_list)


def feature_names(n_samples=4):
    """
    Get feature names for interpretation

    Args:
        n_samples: Number of sampling points

    Returns:
        List of feature names
    """
    names = []

    # Shape features
    for i in range(n_samples):
        names.append(f'x_{i}')
        names.append(f'y_{i}')

    # Length features
    for i in range(n_samples - 1):
        names.append(f'seg_len_{i}')
    names.append('total_length')
    names.append('length_ratio')

    # Angle features
    for i in range(n_samples - 2):
        names.append(f'cos_angle_{i}')

    # Curvature features
    for i in range(n_samples):
        names.append(f'curvature_{i}')

    return names


if __name__ == '__main__':
    # Test feature extraction
    from vectorization.bezier import CubicBezier
    import matplotlib.pyplot as plt

    # Create test Bezier curves
    # Straight line
    straight = CubicBezier(np.array([[0, 0], [100, 0], [200, 0], [300, 0]]))

    # Circular arc
    arc = CubicBezier(np.array([[0, 0], [100, 100], [200, 100], [300, 0]]))

    # Extract features
    features_straight = extract_features(straight, normalize=False, image_size=(1000, 1000))
    features_arc = extract_features(arc, normalize=False, image_size=(1000, 1000))

    # Print features
    names = feature_names()
    print("Feature extraction test:")
    print("\nStraight line:")
    for name, val in zip(names, features_straight):
        print(f"  {name:15s}: {val:8.4f}")

    print("\nCircular arc:")
    for name, val in zip(names, features_arc):
        print(f"  {name:15s}: {val:8.4f}")

    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Plot curves
    t_vals = np.linspace(0, 1, 100)
    straight_points = straight.evaluate(t_vals)
    arc_points = arc.evaluate(t_vals)

    axes[0].plot(straight_points[:, 0], straight_points[:, 1], 'b-', linewidth=2, label='Straight')
    axes[0].plot(arc_points[:, 0], arc_points[:, 1], 'r-', linewidth=2, label='Arc')
    axes[0].axis('equal')
    axes[0].legend()
    axes[0].set_title('Curves')
    axes[0].grid(True)

    # Plot features
    axes[1].bar(range(len(features_straight)), features_straight, alpha=0.7, label='Straight')
    axes[1].bar(range(len(features_arc)), features_arc, alpha=0.7, label='Arc')
    axes[1].set_xlabel('Feature Index')
    axes[1].set_ylabel('Feature Value')
    axes[1].set_title('Feature Comparison')
    axes[1].legend()
    axes[1].grid(True, axis='y')

    plt.tight_layout()
    plt.savefig('/home/uproot/ax/dev/edgnet/tests/features_test.png', dpi=150)
    print("\nTest visualization saved to tests/features_test.png")
