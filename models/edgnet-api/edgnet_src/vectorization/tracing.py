"""
Trajectory Tracing module
Traces connected pixel sequences from skeleton image
"""

import numpy as np
from collections import deque


def trace_trajectories(skeleton, points=None):
    """
    Trace connected pixel sequences (trajectories) in skeleton

    Args:
        skeleton: Binary skeleton image
        points: Optional dict with 'junctions', 'endpoints', 'passing' points
                If None, will compute automatically

    Returns:
        List of trajectories, each as list of (x, y) coordinates
    """
    if points is None:
        from .thinning import identify_points
        points = identify_points(skeleton)

    # Create a visited map
    visited = np.zeros_like(skeleton, dtype=bool)

    # Mark junction points
    for jx, jy in points['junctions']:
        visited[jy, jx] = True

    trajectories = []

    # Start tracing from endpoints
    for ex, ey in points['endpoints']:
        if visited[ey, ex]:
            continue

        trajectory = trace_from_point(skeleton, (ex, ey), visited, points['junctions'])
        if len(trajectory) > 1:  # Only keep non-trivial trajectories
            trajectories.append(trajectory)

    # Trace from junctions
    for jx, jy in points['junctions']:
        # Find all neighbors of junction
        neighbors = get_neighbors(skeleton, (jx, jy))
        for nx, ny in neighbors:
            if not visited[ny, nx]:
                trajectory = trace_from_point(skeleton, (nx, ny), visited, points['junctions'])
                if len(trajectory) > 1:
                    # Add junction point at the beginning
                    trajectory.insert(0, (jx, jy))
                    trajectories.append(trajectory)

    return trajectories


def trace_from_point(skeleton, start_point, visited, junctions):
    """
    Trace a single trajectory from a starting point

    Args:
        skeleton: Binary skeleton image
        start_point: (x, y) starting coordinate
        visited: Boolean array marking visited pixels
        junctions: Array of junction point coordinates

    Returns:
        List of (x, y) coordinates forming the trajectory
    """
    trajectory = [start_point]
    visited[start_point[1], start_point[0]] = True

    current = start_point

    while True:
        # Find unvisited neighbors
        neighbors = get_neighbors(skeleton, current)
        unvisited = [(x, y) for x, y in neighbors if not visited[y, x]]

        if len(unvisited) == 0:
            # No more unvisited neighbors - end of trajectory
            break
        elif len(unvisited) == 1:
            # Single neighbor - continue tracing
            next_point = unvisited[0]
            trajectory.append(next_point)
            visited[next_point[1], next_point[0]] = True
            current = next_point

            # Check if we reached a junction
            if any(np.array_equal([next_point[0], next_point[1]], j) for j in junctions):
                break
        else:
            # Multiple neighbors - reached a junction or bifurcation
            break

    return trajectory


def get_neighbors(skeleton, point, connectivity=8):
    """
    Get valid neighbors of a skeleton point

    Args:
        skeleton: Binary skeleton image
        point: (x, y) coordinate
        connectivity: 4 or 8 connectivity

    Returns:
        List of (x, y) neighbor coordinates
    """
    x, y = point
    h, w = skeleton.shape

    if connectivity == 8:
        offsets = [(-1, -1), (-1, 0), (-1, 1),
                   (0, -1),          (0, 1),
                   (1, -1),  (1, 0), (1, 1)]
    else:  # 4-connectivity
        offsets = [(0, -1), (-1, 0), (1, 0), (0, 1)]

    neighbors = []
    for dx, dy in offsets:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and skeleton[ny, nx] > 0:
            neighbors.append((nx, ny))

    return neighbors


def split_trajectory(trajectory, angle_threshold=20):
    """
    Split trajectory at sharp corners

    Args:
        trajectory: List of (x, y) coordinates
        angle_threshold: Angle threshold in degrees for corner detection

    Returns:
        List of sub-trajectories
    """
    if len(trajectory) < 3:
        return [trajectory]

    split_indices = [0]

    # Calculate angles at each point
    for i in range(1, len(trajectory) - 1):
        p0 = np.array(trajectory[i - 1])
        ps = np.array(trajectory[i])
        pe = np.array(trajectory[i + 1])

        # Calculate cosine angle
        v1 = ps - p0
        v2 = pe - ps

        # Avoid division by zero
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 < 1e-6 or norm2 < 1e-6:
            continue

        cos_angle = np.dot(v1, v2) / (norm1 * norm2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))

        # If angle is sharp, mark as split point
        if angle > angle_threshold:
            split_indices.append(i)

    split_indices.append(len(trajectory) - 1)

    # Create sub-trajectories
    sub_trajectories = []
    for i in range(len(split_indices) - 1):
        start = split_indices[i]
        end = split_indices[i + 1] + 1
        sub_traj = trajectory[start:end]
        if len(sub_traj) > 1:
            sub_trajectories.append(sub_traj)

    return sub_trajectories if sub_trajectories else [trajectory]


def clean_trajectories(trajectories, min_length=4):
    """
    Remove trajectories shorter than min_length pixels

    Args:
        trajectories: List of trajectories
        min_length: Minimum trajectory length in pixels

    Returns:
        Filtered list of trajectories
    """
    return [t for t in trajectories if len(t) >= min_length]


if __name__ == '__main__':
    # Test the tracing module
    import cv2
    import matplotlib.pyplot as plt
    from .thinning import thin_image, identify_points

    # Create a simple test image
    test_img = np.zeros((200, 200), dtype=np.uint8)
    cv2.line(test_img, (50, 50), (150, 150), 255, 3)
    cv2.line(test_img, (100, 50), (100, 150), 255, 3)
    cv2.circle(test_img, (150, 100), 30, 255, 2)

    # Apply thinning
    skeleton = thin_image(test_img, method='skeletonize')

    # Identify points
    points = identify_points(skeleton)

    # Trace trajectories
    trajectories = trace_trajectories(skeleton, points)

    print(f"Found {len(trajectories)} trajectories")

    # Visualize
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(test_img, cmap='gray')
    plt.title('Original')

    plt.subplot(1, 2, 2)
    plt.imshow(skeleton, cmap='gray')
    for i, traj in enumerate(trajectories):
        traj_array = np.array(traj)
        plt.plot(traj_array[:, 0], traj_array[:, 1], 'o-', label=f'Traj {i+1}')
    plt.title(f'Trajectories ({len(trajectories)})')
    plt.legend()
    plt.tight_layout()
    plt.savefig('/home/uproot/ax/dev/edgnet/tests/tracing_test.png')
    print("Test image saved to tests/tracing_test.png")
