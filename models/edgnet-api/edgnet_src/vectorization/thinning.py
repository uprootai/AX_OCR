"""
Thinning/Skeletonization module
Implements Datta & Parui algorithm and alternatives
"""

import numpy as np
import cv2
from skimage.morphology import skeletonize, thin
from scipy import ndimage


def _safe_to_gray(img):
    """이미 그레이스케일인 경우에도 안전하게 변환"""
    if img is None or img.size == 0:
        return img
    if len(img.shape) == 2:
        return img
    if img.shape[2] == 1:
        return img[:, :, 0]
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def thin_image(image, method='datta_parui', smooth=True):
    """
    Apply thinning/skeletonization to binary image

    Args:
        image: Binary image (numpy array)
        method: Thinning algorithm ('datta_parui', 'zhang_suen', 'medial_axis')
        smooth: Apply smoothing before thinning

    Returns:
        Thinned binary image
    """
    # Ensure binary image
    if len(image.shape) == 3:
        image = _safe_to_gray(image)

    _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)

    # Apply smoothing to reduce noise
    if smooth:
        binary = cv2.GaussianBlur(binary, (3, 3), 0)
        _, binary = cv2.threshold(binary, 127, 255, cv2.THRESH_BINARY)

    # Convert to boolean for scikit-image
    binary_bool = binary > 0

    # Apply thinning algorithm
    if method == 'datta_parui' or method == 'skeletonize':
        # Using scikit-image skeletonize (similar to Datta & Parui)
        skeleton = skeletonize(binary_bool)
    elif method == 'zhang_suen':
        # Zhang-Suen thinning
        skeleton = thin(binary_bool, max_num_iter=None)
    elif method == 'medial_axis':
        # Medial axis transform
        from skimage.morphology import medial_axis
        skeleton = medial_axis(binary_bool)
    elif method == 'opencv':
        # OpenCV thinning
        skeleton = cv2.ximgproc.thinning(binary)
        skeleton = skeleton > 0
    else:
        raise ValueError(f"Unknown thinning method: {method}")

    return skeleton.astype(np.uint8) * 255


def smooth_skeleton(skeleton, kernel_size=3):
    """
    Smooth skeleton to remove pixel noise

    Args:
        skeleton: Binary skeleton image
        kernel_size: Size of smoothing kernel

    Returns:
        Smoothed skeleton
    """
    kernel = np.ones((kernel_size, kernel_size), np.uint8)

    # Morphological operations to clean skeleton
    skeleton = cv2.morphologyEx(skeleton, cv2.MORPH_CLOSE, kernel)
    skeleton = cv2.morphologyEx(skeleton, cv2.MORPH_OPEN, kernel)

    return skeleton


def identify_points(skeleton):
    """
    Identify junction points, endpoints, and passing points

    Args:
        skeleton: Binary skeleton image

    Returns:
        Dictionary with 'junctions', 'endpoints', 'passing' point coordinates
    """
    # Create kernel to count neighbors
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]], dtype=np.uint8)

    # Count neighbors for each skeleton pixel
    neighbor_count = cv2.filter2D(skeleton // 255, -1, kernel)

    # Mask of skeleton pixels
    skeleton_mask = skeleton > 0

    # Junction points: 3 or more neighbors
    junctions = np.where((skeleton_mask) & (neighbor_count >= 3))

    # Endpoints: exactly 1 neighbor
    endpoints = np.where((skeleton_mask) & (neighbor_count == 1))

    # Passing points: exactly 2 neighbors
    passing = np.where((skeleton_mask) & (neighbor_count == 2))

    return {
        'junctions': np.column_stack((junctions[1], junctions[0])),  # (x, y) format
        'endpoints': np.column_stack((endpoints[1], endpoints[0])),
        'passing': np.column_stack((passing[1], passing[0]))
    }


if __name__ == '__main__':
    # Test the thinning module
    import matplotlib.pyplot as plt

    # Create a simple test image
    test_img = np.zeros((200, 200), dtype=np.uint8)
    cv2.line(test_img, (50, 50), (150, 150), 255, 3)
    cv2.circle(test_img, (100, 100), 30, 255, 2)

    # Apply thinning
    skeleton = thin_image(test_img, method='skeletonize')

    # Identify points
    points = identify_points(skeleton)

    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(test_img, cmap='gray')
    axes[0].set_title('Original')
    axes[1].imshow(skeleton, cmap='gray')
    axes[1].plot(points['junctions'][:, 0], points['junctions'][:, 1], 'ro', label='Junctions')
    axes[1].plot(points['endpoints'][:, 0], points['endpoints'][:, 1], 'go', label='Endpoints')
    axes[1].set_title('Skeleton with Points')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig('/home/uproot/ax/dev/edgnet/tests/thinning_test.png')
    print("Test image saved to tests/thinning_test.png")
