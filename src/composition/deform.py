"""
Deform - Principal axis deformation for Shape Studio
Stretches/compresses a polygon along its computed major or minor axis.

Usage:
    from src.composition.deform import deform_points

    new_points = deform_points(
        points,
        axis='major',   # 'major' or 'minor'
        along=1.25,     # scale factor along the named axis
        across=0.85,    # scale factor perpendicular to named axis
    )
"""
import math


def _compute_centroid(points):
    """Return (cx, cy) centroid of point list."""
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return cx, cy


def _compute_principal_axis(points, centroid):
    """
    Compute the major principal axis direction via 2D PCA on the point cloud.

    Returns:
        (major_ux, major_uy): unit vector along the major axis
        (minor_ux, minor_uy): unit vector along the minor axis (perpendicular)
    """
    cx, cy = centroid
    # Covariance matrix entries
    sxx = sum((p[0] - cx) ** 2 for p in points)
    syy = sum((p[1] - cy) ** 2 for p in points)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in points)

    n = len(points)
    sxx /= n
    syy /= n
    sxy /= n

    # Eigenvalues of 2x2 symmetric matrix [[sxx, sxy], [sxy, syy]]
    trace = sxx + syy
    det = sxx * syy - sxy * sxy
    discriminant = max(0.0, (trace / 2) ** 2 - det)
    sqrt_disc = math.sqrt(discriminant)

    lambda1 = trace / 2 + sqrt_disc  # larger eigenvalue -> major axis
    lambda2 = trace / 2 - sqrt_disc  # smaller eigenvalue -> minor axis

    # Eigenvector for lambda1 (major axis)
    if abs(sxy) > 1e-10:
        vx = lambda1 - syy
        vy = sxy
    elif abs(sxx - lambda1) < abs(syy - lambda1):
        # Axis aligned: major is x
        vx, vy = 1.0, 0.0
    else:
        vx, vy = 0.0, 1.0

    length = math.sqrt(vx * vx + vy * vy)
    if length < 1e-10:
        vx, vy = 1.0, 0.0
    else:
        vx /= length
        vy /= length

    # Minor axis is perpendicular
    minor_ux = -vy
    minor_uy = vx

    return (vx, vy), (minor_ux, minor_uy)


def deform_points(points, axis='major', along=1.0, across=1.0):
    """
    Deform a polygon by scaling along its principal axes.

    Args:
        points: List of (x, y) tuples
        axis:   'major' — along/across refer to major/minor axes respectively
                'minor' — along/across refer to minor/major axes respectively
        along:  Scale factor along the named axis  (1.0 = no change)
        across: Scale factor perpendicular to named axis (1.0 = no change)

    Returns:
        List of transformed (x, y) tuples (integers, matching Shape Studio convention)

    Raises:
        ValueError: if points is empty, axis is invalid, or factors are non-positive
    """
    if not points:
        raise ValueError("deform_points: points list is empty")
    if axis not in ('major', 'minor'):
        raise ValueError(f"deform_points: axis must be 'major' or 'minor', got '{axis}'")
    if along <= 0 or across <= 0:
        raise ValueError(
            f"deform_points: along and across must be positive (got along={along}, across={across})"
        )

    centroid = _compute_centroid(points)
    major_u, minor_u = _compute_principal_axis(points, centroid)

    # Assign scale factors to axes based on 'axis' parameter
    if axis == 'major':
        scale_major = along
        scale_minor = across
    else:  # 'minor'
        scale_major = across
        scale_minor = along

    cx, cy = centroid
    result = []
    for px, py in points:
        # Translate to centroid-relative
        rx = px - cx
        ry = py - cy

        # Project onto major and minor axes
        proj_major = rx * major_u[0] + ry * major_u[1]
        proj_minor = rx * minor_u[0] + ry * minor_u[1]

        # Scale each component
        proj_major *= scale_major
        proj_minor *= scale_minor

        # Reconstruct in canvas space
        nx = cx + proj_major * major_u[0] + proj_minor * minor_u[0]
        ny = cy + proj_major * major_u[1] + proj_minor * minor_u[1]

        result.append((int(round(nx)), int(round(ny))))

    return result