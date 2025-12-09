"""
Cubic Bezier Curve Fitting module
Fits traced trajectories with cubic Bezier curves
"""

import numpy as np
from scipy.optimize import least_squares


class CubicBezier:
    """Cubic Bezier curve representation"""

    def __init__(self, control_points):
        """
        Args:
            control_points: 4 control points as (4, 2) array [P0, P1, P2, P3]
        """
        assert control_points.shape == (4, 2), "Need exactly 4 control points"
        self.control_points = control_points

    def evaluate(self, t):
        """
        Evaluate Bezier curve at parameter t

        Args:
            t: Parameter in [0, 1] or array of parameters

        Returns:
            Point(s) on curve as (2,) or (N, 2) array
        """
        t = np.asarray(t)
        t = np.clip(t, 0, 1)

        # Bernstein basis functions for cubic Bezier
        b0 = (1 - t) ** 3
        b1 = 3 * t * (1 - t) ** 2
        b2 = 3 * t ** 2 * (1 - t)
        b3 = t ** 3

        # If t is a scalar
        if t.ndim == 0:
            return (b0 * self.control_points[0] +
                    b1 * self.control_points[1] +
                    b2 * self.control_points[2] +
                    b3 * self.control_points[3])

        # If t is an array
        basis = np.stack([b0, b1, b2, b3], axis=1)  # (N, 4)
        return basis @ self.control_points  # (N, 2)

    def derivative(self, t):
        """
        Compute first derivative (tangent) at parameter t

        Args:
            t: Parameter in [0, 1]

        Returns:
            Tangent vector as (2,) array
        """
        t = np.clip(t, 0, 1)

        # Derivative of Bernstein basis
        db0 = -3 * (1 - t) ** 2
        db1 = 3 * (1 - t) ** 2 - 6 * t * (1 - t)
        db2 = 6 * t * (1 - t) - 3 * t ** 2
        db3 = 3 * t ** 2

        return (db0 * self.control_points[0] +
                db1 * self.control_points[1] +
                db2 * self.control_points[2] +
                db3 * self.control_points[3])

    def curvature(self, t):
        """
        Compute curvature at parameter t

        Args:
            t: Parameter in [0, 1]

        Returns:
            Curvature value (scalar)
        """
        # First derivative
        dp = self.derivative(t)

        # Second derivative
        t = np.clip(t, 0, 1)
        d2b0 = 6 * (1 - t)
        d2b1 = -12 * (1 - t) + 6 * t
        d2b2 = 6 * (1 - t) - 12 * t
        d2b3 = 6 * t

        d2p = (d2b0 * self.control_points[0] +
               d2b1 * self.control_points[1] +
               d2b2 * self.control_points[2] +
               d2b3 * self.control_points[3])

        # Curvature formula: |dp x d2p| / |dp|^3
        cross = np.abs(dp[0] * d2p[1] - dp[1] * d2p[0])
        norm_dp = np.linalg.norm(dp)

        if norm_dp < 1e-8:
            return 0.0

        return cross / (norm_dp ** 3)

    def length(self, num_samples=100):
        """
        Estimate curve length using numerical integration

        Args:
            num_samples: Number of samples for integration

        Returns:
            Approximate curve length
        """
        t_vals = np.linspace(0, 1, num_samples)
        points = self.evaluate(t_vals)
        diffs = np.diff(points, axis=0)
        lengths = np.linalg.norm(diffs, axis=1)
        return np.sum(lengths)


def fit_bezier_curves(trajectories, method='least_squares'):
    """
    Fit cubic Bezier curves to trajectories

    Args:
        trajectories: List of trajectories (list of (x, y) points)
        method: Fitting method ('least_squares' or 'simple')

    Returns:
        List of CubicBezier objects
    """
    bezier_curves = []

    for traj in trajectories:
        if len(traj) < 4:
            # Too few points, skip or handle specially
            continue

        if method == 'simple':
            bezier = fit_bezier_simple(traj)
        else:
            bezier = fit_bezier_least_squares(traj)

        bezier_curves.append(bezier)

    return bezier_curves


def fit_bezier_simple(trajectory):
    """
    Simple Bezier fitting: endpoints + 1/3 and 2/3 points

    Args:
        trajectory: List of (x, y) points

    Returns:
        CubicBezier object
    """
    traj_array = np.array(trajectory)

    # P0 and P3 are endpoints
    P0 = traj_array[0]
    P3 = traj_array[-1]

    # P1 and P2 are approximated as 1/3 and 2/3 along the trajectory
    n = len(traj_array)
    idx1 = max(1, n // 3)
    idx2 = max(2, 2 * n // 3)

    P1 = traj_array[idx1]
    P2 = traj_array[idx2]

    control_points = np.array([P0, P1, P2, P3])
    return CubicBezier(control_points)


def fit_bezier_least_squares(trajectory):
    """
    Fit Bezier curve using least squares optimization

    Args:
        trajectory: List of (x, y) points

    Returns:
        CubicBezier object
    """
    traj_array = np.array(trajectory)

    # Endpoints are fixed
    P0 = traj_array[0]
    P3 = traj_array[-1]

    # Parameterize points along trajectory
    n = len(traj_array)
    t_params = np.linspace(0, 1, n)

    # Initial guess for P1 and P2 (middle control points)
    P1_init = traj_array[n // 3]
    P2_init = traj_array[2 * n // 3]
    x0 = np.concatenate([P1_init, P2_init])

    # Objective function: minimize distance to trajectory points
    def residual(x):
        P1 = x[:2]
        P2 = x[2:]
        control_points = np.array([P0, P1, P2, P3])
        bezier = CubicBezier(control_points)
        fitted_points = bezier.evaluate(t_params)
        return (fitted_points - traj_array).flatten()

    # Optimize
    result = least_squares(residual, x0, method='lm')

    # Create final Bezier curve
    P1 = result.x[:2]
    P2 = result.x[2:]
    control_points = np.array([P0, P1, P2, P3])

    return CubicBezier(control_points)


if __name__ == '__main__':
    # Test the Bezier fitting module
    import matplotlib.pyplot as plt

    # Create a test trajectory (circular arc)
    theta = np.linspace(0, np.pi / 2, 20)
    trajectory = np.column_stack([100 * np.cos(theta), 100 * np.sin(theta)])

    # Fit Bezier curve
    bezier = fit_bezier_least_squares(trajectory.tolist())

    # Evaluate fitted curve
    t_vals = np.linspace(0, 1, 100)
    fitted_points = bezier.evaluate(t_vals)

    # Visualize
    plt.figure(figsize=(8, 8))
    plt.plot(trajectory[:, 0], trajectory[:, 1], 'o-', label='Original Trajectory', markersize=8)
    plt.plot(fitted_points[:, 0], fitted_points[:, 1], 'r-', label='Fitted Bezier', linewidth=2)
    plt.plot(bezier.control_points[:, 0], bezier.control_points[:, 1],
             'gs--', label='Control Points', markersize=10, linewidth=1)
    plt.axis('equal')
    plt.legend()
    plt.title('Cubic Bezier Curve Fitting')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('/home/uproot/ax/dev/edgnet/tests/bezier_test.png')
    print("Test image saved to tests/bezier_test.png")
    print(f"Curve length: {bezier.length():.2f}")
    print(f"Curvature at t=0.5: {bezier.curvature(0.5):.4f}")
