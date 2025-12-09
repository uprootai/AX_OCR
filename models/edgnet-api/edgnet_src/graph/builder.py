"""
Graph Builder module
Constructs graph G(N, E) from vectorized components
"""

import numpy as np
import networkx as nx
from scipy.spatial import cKDTree


def build_graph(bezier_curves, features, connection_threshold=10.0, image_size=(1000, 1000)):
    """
    Build graph from Bezier curves and their features

    Args:
        bezier_curves: List of CubicBezier objects
        features: Feature matrix (num_curves, feature_dim)
        connection_threshold: Maximum distance for edge connection (pixels)
        image_size: Image size for distance calculation

    Returns:
        NetworkX graph with node features and edge connections
    """
    num_nodes = len(bezier_curves)

    # Create graph
    G = nx.Graph()

    # Add nodes with features
    for i in range(num_nodes):
        G.add_node(i, features=features[i])

    # Extract endpoints of all curves
    endpoints = []
    for bezier in bezier_curves:
        p0 = bezier.control_points[0]  # Start point
        p3 = bezier.control_points[3]  # End point
        endpoints.append([p0, p3])

    endpoints = np.array(endpoints)  # (num_nodes, 2, 2)

    # Build spatial index for efficient nearest neighbor search
    all_points = endpoints.reshape(-1, 2)  # (num_nodes * 2, 2)
    tree = cKDTree(all_points)

    # Find connections between curves
    edges = set()

    for i in range(num_nodes):
        # Query both endpoints of curve i
        for ep_idx in range(2):
            point = endpoints[i, ep_idx]

            # Find nearby points
            indices = tree.query_ball_point(point, connection_threshold)

            for idx in indices:
                # Convert flat index to (curve_id, endpoint_id)
                j = idx // 2
                ep_j = idx % 2

                # Skip self-connections
                if i == j:
                    continue

                # Add edge (avoid duplicates)
                edge = tuple(sorted([i, j]))
                edges.add(edge)

    # Add edges to graph
    G.add_edges_from(edges)

    return G


def build_graph_from_skeleton(skeleton, bezier_curves, features):
    """
    Build graph using skeleton connectivity (alternative method)

    Args:
        skeleton: Binary skeleton image
        bezier_curves: List of CubicBezier objects
        features: Feature matrix

    Returns:
        NetworkX graph
    """
    # This is a more accurate method that uses the original skeleton
    # to determine connectivity, but requires keeping track of which
    # Bezier curve came from which skeleton trajectory

    # For now, we use the simpler endpoint-based method above
    # This can be enhanced later

    pass


def graph_to_pytorch_geometric(G):
    """
    Convert NetworkX graph to PyTorch Geometric format

    Args:
        G: NetworkX graph

    Returns:
        Dictionary with 'x' (node features) and 'edge_index' (edges)
    """
    import torch

    num_nodes = G.number_of_nodes()

    # Extract node features
    features_list = []
    for i in range(num_nodes):
        features_list.append(G.nodes[i]['features'])
    x = torch.tensor(np.array(features_list), dtype=torch.float)

    # Extract edges
    edges = list(G.edges())
    if len(edges) == 0:
        # No edges - create empty edge index
        edge_index = torch.zeros((2, 0), dtype=torch.long)
    else:
        # PyG expects edges in COO format: (2, num_edges)
        # Each edge should appear twice (bidirectional)
        edge_list = []
        for i, j in edges:
            edge_list.append([i, j])
            edge_list.append([j, i])
        edge_index = torch.tensor(edge_list, dtype=torch.long).t()

    return {'x': x, 'edge_index': edge_index}


def graph_to_dgl(G):
    """
    Convert NetworkX graph to DGL format

    Args:
        G: NetworkX graph

    Returns:
        DGL graph
    """
    import dgl
    import torch

    num_nodes = G.number_of_nodes()

    # Extract node features
    features_list = []
    for i in range(num_nodes):
        features_list.append(G.nodes[i]['features'])
    x = torch.tensor(np.array(features_list), dtype=torch.float)

    # Convert to DGL graph
    dgl_graph = dgl.from_networkx(G)
    dgl_graph.ndata['features'] = x

    return dgl_graph


def visualize_graph(G, bezier_curves, image_size=(1000, 1000), output_path=None):
    """
    Visualize graph structure on top of Bezier curves

    Args:
        G: NetworkX graph
        bezier_curves: List of CubicBezier objects
        image_size: Image size
        output_path: Path to save visualization
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 12))

    # Draw Bezier curves
    for i, bezier in enumerate(bezier_curves):
        t_vals = np.linspace(0, 1, 50)
        points = bezier.evaluate(t_vals)
        ax.plot(points[:, 0], points[:, 1], 'b-', linewidth=1, alpha=0.5)

        # Draw control points
        cp = bezier.control_points
        ax.plot([cp[0, 0]], [cp[0, 1]], 'go', markersize=4)  # Start
        ax.plot([cp[3, 0]], [cp[3, 1]], 'ro', markersize=4)  # End

    # Draw graph edges
    for i, j in G.edges():
        # Connect midpoints of curves
        mid_i = bezier_curves[i].evaluate(0.5)
        mid_j = bezier_curves[j].evaluate(0.5)
        ax.plot([mid_i[0], mid_j[0]], [mid_i[1], mid_j[1]],
                'r--', linewidth=0.5, alpha=0.3)

    # Draw node labels
    for i in range(len(bezier_curves)):
        mid = bezier_curves[i].evaluate(0.5)
        ax.text(mid[0], mid[1], str(i), fontsize=8,
                ha='center', va='center',
                bbox=dict(boxstyle='circle', facecolor='yellow', alpha=0.5))

    ax.set_xlim(0, image_size[0])
    ax.set_ylim(0, image_size[1])
    ax.set_aspect('equal')
    ax.invert_yaxis()  # Image coordinates
    ax.set_title(f'Graph Structure: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
    ax.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Graph visualization saved to {output_path}")
    else:
        plt.show()

    plt.close()


if __name__ == '__main__':
    # Test graph building
    from vectorization.bezier import CubicBezier
    from .features import extract_batch_features

    # Create test Bezier curves (connected lines)
    curves = [
        CubicBezier(np.array([[0, 0], [50, 0], [50, 0], [100, 0]])),      # Horizontal
        CubicBezier(np.array([[100, 0], [100, 50], [100, 50], [100, 100]])),  # Vertical down
        CubicBezier(np.array([[100, 100], [150, 100], [150, 100], [200, 100]])),  # Horizontal
    ]

    # Extract features
    features = extract_batch_features(curves, normalize=False, image_size=(1000, 1000))

    # Build graph
    G = build_graph(curves, features, connection_threshold=15.0)

    print(f"Graph created:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Edge list: {list(G.edges())}")

    # Visualize
    visualize_graph(G, curves, image_size=(250, 150),
                    output_path='/home/uproot/ax/dev/edgnet/tests/graph_test.png')
