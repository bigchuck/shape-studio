"""
spatial.py - Pure geometry for Shape Studio composition system.

No Shape Studio dependencies except PCA imported from deform.py.
All functions operate on plain lists of (x, y) tuples.
Fully testable in isolation.

Primary geometric primitive: convex hull (ordered point list).

Function inventory:
  Hull:
    convex_hull(points)              -> hull_points
    hull_area(hull_points)           -> float
    hull_centroid(hull_points)       -> (cx, cy)
    combined_hull(list_of_points)    -> hull_points

  Axes:
    principal_axes(points)           -> (major_vec, minor_vec, centroid)
    axis_line(points, axis)          -> (point, direction_vec)

  Separation:
    hull_separation(hull_a, hull_b)  -> (distance, pt_a, pt_b)
    point_to_hull_distance(pt, hull) -> (distance, nearest_pt)

  Axis relationships:
    axis_angle_between(pts_a, pts_b, axis)     -> degrees
    axis_to_axis_distance(pts_a, pts_b, axis)  -> float (px)

  Contact detection:
    hull_contact_points(hull_a, hull_b, tol)   -> list of (pt_a, pt_b) pairs

  Compositional grid:
    grid_points(w, h, division)                -> list of (x, y)
    named_grid_point(w, h, division, position) -> (x, y)
    nearest_grid_point(centroid, w, h, division) -> (x, y)
"""

import math


# ---------------------------------------------------------------------------
# Convex hull — Graham scan (no external dependencies)
# ---------------------------------------------------------------------------

def convex_hull(points):
    """Compute the convex hull of a point set using Graham scan.

    Args:
        points: List of (x, y) tuples (at least 3)

    Returns:
        Ordered list of (x, y) tuples forming the convex hull,
        counter-clockwise. Returns input points if fewer than 3.
    """
    pts = [tuple(p) for p in points]
    pts = list(set(pts))  # deduplicate

    if len(pts) < 3:
        return pts

    # Find bottom-most (then left-most) point as pivot
    pivot = min(pts, key=lambda p: (p[1], p[0]))

    def _polar_angle(p):
        dx = p[0] - pivot[0]
        dy = p[1] - pivot[1]
        return math.atan2(dy, dx)

    def _dist_sq(p):
        dx = p[0] - pivot[0]
        dy = p[1] - pivot[1]
        return dx * dx + dy * dy

    # Sort by polar angle, break ties by distance
    rest = [p for p in pts if p != pivot]
    rest.sort(key=lambda p: (_polar_angle(p), _dist_sq(p)))

    # Graham scan
    hull = [pivot, rest[0]]
    for p in rest[1:]:
        while len(hull) >= 2 and _cross(hull[-2], hull[-1], p) <= 0:
            hull.pop()
        hull.append(p)

    return hull


def _cross(o, a, b):
    """Cross product of vectors OA and OB. Positive = counter-clockwise."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def hull_area(hull_points):
    """Compute area of a convex hull polygon using the shoelace formula.

    Args:
        hull_points: Ordered list of (x, y) tuples

    Returns:
        Area in square pixels (float)
    """
    n = len(hull_points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += hull_points[i][0] * hull_points[j][1]
        area -= hull_points[j][0] * hull_points[i][1]
    return abs(area) / 2.0


def hull_centroid(hull_points):
    """Compute the centroid of a convex hull polygon.

    Args:
        hull_points: Ordered list of (x, y) tuples

    Returns:
        (cx, cy) float tuple
    """
    n = len(hull_points)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return (float(hull_points[0][0]), float(hull_points[0][1]))
    if n == 2:
        return (
            (hull_points[0][0] + hull_points[1][0]) / 2.0,
            (hull_points[0][1] + hull_points[1][1]) / 2.0,
        )

    # Polygon centroid formula
    cx = cy = 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        cross = hull_points[i][0] * hull_points[j][1] - hull_points[j][0] * hull_points[i][1]
        cx += (hull_points[i][0] + hull_points[j][0]) * cross
        cy += (hull_points[i][1] + hull_points[j][1]) * cross
        area += cross

    area /= 2.0
    if abs(area) < 1e-10:
        # Degenerate — fall back to mean
        cx = sum(p[0] for p in hull_points) / n
        cy = sum(p[1] for p in hull_points) / n
        return (cx, cy)

    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return (cx, cy)


def combined_hull(list_of_point_lists):
    """Compute the convex hull of multiple point sets combined.

    Args:
        list_of_point_lists: List of point lists, one per shape

    Returns:
        Convex hull of all combined points
    """
    all_points = []
    for pts in list_of_point_lists:
        all_points.extend(pts)
    return convex_hull(all_points)


# ---------------------------------------------------------------------------
# Principal axes — wraps deform.py PCA, does not duplicate it
# ---------------------------------------------------------------------------

def principal_axes(points):
    """Compute the principal axes of a point cloud via PCA.

    Delegates to deform.py's _compute_centroid and _compute_principal_axis
    so PCA logic lives in exactly one place.

    Args:
        points: List of (x, y) tuples

    Returns:
        (major_vec, minor_vec, centroid)
        where each vec is a (ux, uy) unit vector and centroid is (cx, cy)

    Raises:
        ValueError: if points is empty
    """
    if not points:
        raise ValueError("principal_axes: points list is empty")

    from src.composition.deform import _compute_centroid, _compute_principal_axis

    centroid = _compute_centroid(points)
    major_vec, minor_vec = _compute_principal_axis(points, centroid)
    return major_vec, minor_vec, centroid


def axis_line(points, axis='major'):
    """Represent the named principal axis as an infinite line.

    Args:
        points: List of (x, y) tuples
        axis:   'major' or 'minor'

    Returns:
        (point, direction) where:
          point:     (cx, cy) centroid — a point on the line
          direction: (ux, uy) unit vector along the axis
    """
    major_vec, minor_vec, centroid = principal_axes(points)
    direction = major_vec if axis == 'major' else minor_vec
    return centroid, direction


# ---------------------------------------------------------------------------
# Separation
# ---------------------------------------------------------------------------

def _segment_to_segment_distance(p1, p2, p3, p4):
    """Minimum distance between segment p1-p2 and segment p3-p4.
    Returns (distance, point_on_seg1, point_on_seg2).
    """
    def _point_to_segment(p, a, b):
        """Closest point on segment a-b to point p, and distance."""
        ax, ay = a
        bx, by = b
        px, py = p
        dx, dy = bx - ax, by - ay
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-10:
            return a, math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
        nx, ny = ax + t * dx, ay + t * dy
        return (nx, ny), math.hypot(px - nx, py - ny)

    # Check all four endpoint-to-segment combinations
    candidates = []
    np1, d1 = _point_to_segment(p1, p3, p4)
    candidates.append((d1, p1, np1))
    np2, d2 = _point_to_segment(p2, p3, p4)
    candidates.append((d2, p2, np2))
    np3, d3 = _point_to_segment(p3, p1, p2)
    candidates.append((d3, np3, p3))
    np4, d4 = _point_to_segment(p4, p1, p2)
    candidates.append((d4, np4, p4))

    return min(candidates, key=lambda c: c[0])


def hull_separation(hull_a, hull_b):
    """Minimum distance between two convex hull boundaries.

    Args:
        hull_a, hull_b: Ordered lists of (x, y) hull points

    Returns:
        (distance, pt_on_a, pt_on_b) — closest approach pair
        distance is 0.0 if hulls overlap or touch
    """
    if len(hull_a) < 2 or len(hull_b) < 2:
        # Degenerate — distance between centroids
        ca = hull_centroid(hull_a)
        cb = hull_centroid(hull_b)
        d = math.hypot(ca[0] - cb[0], ca[1] - cb[1])
        return d, ca, cb

    best_dist = float('inf')
    best_pa = hull_a[0]
    best_pb = hull_b[0]

    n_a = len(hull_a)
    n_b = len(hull_b)

    for i in range(n_a):
        a1 = hull_a[i]
        a2 = hull_a[(i + 1) % n_a]
        for j in range(n_b):
            b1 = hull_b[j]
            b2 = hull_b[(j + 1) % n_b]
            d, pa, pb = _segment_to_segment_distance(a1, a2, b1, b2)
            if d < best_dist:
                best_dist = d
                best_pa = pa
                best_pb = pb

    return best_dist, best_pa, best_pb


def point_to_hull_distance(point, hull):
    """Minimum distance from a point to a hull boundary.

    Args:
        point: (x, y) tuple
        hull:  Ordered list of (x, y) hull points

    Returns:
        (distance, nearest_point_on_hull)
    """
    if not hull:
        return float('inf'), point

    n = len(hull)
    best_dist = float('inf')
    best_pt = hull[0]

    for i in range(n):
        a = hull[i]
        b = hull[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-10:
            d = math.hypot(point[0] - a[0], point[1] - a[1])
            np_ = a
        else:
            t = max(0.0, min(1.0,
                ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / len_sq
            ))
            nx, ny = a[0] + t * dx, a[1] + t * dy
            np_ = (nx, ny)
            d = math.hypot(point[0] - nx, point[1] - ny)
        if d < best_dist:
            best_dist = d
            best_pt = np_

    return best_dist, best_pt


# ---------------------------------------------------------------------------
# Axis relationships
# ---------------------------------------------------------------------------

def axis_angle_between(points_a, points_b, axis='major'):
    """Angle in degrees between the named axis of two shapes.

    Returns a value in [0, 90] — the acute angle between the axes.
    0 = perfectly aligned, 90 = perpendicular.

    Args:
        points_a, points_b: Point lists for the two shapes
        axis: 'major' or 'minor'

    Returns:
        Angle in degrees (float, 0-90)
    """
    major_a, minor_a, _ = principal_axes(points_a)
    major_b, minor_b, _ = principal_axes(points_b)

    vec_a = major_a if axis == 'major' else minor_a
    vec_b = major_b if axis == 'major' else minor_b

    # Dot product of unit vectors gives cos(angle)
    dot = vec_a[0] * vec_b[0] + vec_a[1] * vec_b[1]
    # Clamp for numerical safety
    dot = max(-1.0, min(1.0, abs(dot)))  # abs: axes have no direction, take acute angle
    angle_rad = math.acos(dot)
    return math.degrees(angle_rad)


def axis_to_axis_distance(points_a, points_b, axis='major'):
    """Perpendicular distance between the named axes of two shapes.

    Measures how far apart the two parallel (or near-parallel) axis lines
    are in the direction perpendicular to the axis.

    Args:
        points_a, points_b: Point lists for the two shapes
        axis: 'major' or 'minor'

    Returns:
        Distance in pixels (float). 0.0 = collinear axes.
    """
    major_a, minor_a, centroid_a = principal_axes(points_a)
    _, _, centroid_b = principal_axes(points_b)

    # Use shape A's axis direction as the reference line direction
    direction = major_a if axis == 'major' else minor_a

    # Vector from centroid_a to centroid_b
    dx = centroid_b[0] - centroid_a[0]
    dy = centroid_b[1] - centroid_a[1]

    # Project onto perpendicular of axis direction
    # Perpendicular to (ux, uy) is (-uy, ux)
    perp_x = -direction[1]
    perp_y =  direction[0]

    distance = abs(dx * perp_x + dy * perp_y)
    return distance


# ---------------------------------------------------------------------------
# Contact detection
# ---------------------------------------------------------------------------

def hull_contact_points(hull_a, hull_b, tolerance_px=2.0):
    """Find pairs of points where two hulls are within tolerance of touching.

    Args:
        hull_a, hull_b:  Ordered lists of (x, y) hull points
        tolerance_px:    Distance threshold in pixels for contact detection

    Returns:
        List of (pt_on_a, pt_on_b) tuples where distance <= tolerance_px.
        Empty list if no contact within tolerance.
    """
    contacts = []
    n_a = len(hull_a)
    n_b = len(hull_b)

    for i in range(n_a):
        a1 = hull_a[i]
        a2 = hull_a[(i + 1) % n_a]
        for j in range(n_b):
            b1 = hull_b[j]
            b2 = hull_b[(j + 1) % n_b]
            d, pa, pb = _segment_to_segment_distance(a1, a2, b1, b2)
            if d <= tolerance_px:
                contacts.append((pa, pb))

    return contacts


# ---------------------------------------------------------------------------
# Compositional grid
# ---------------------------------------------------------------------------

def grid_points(canvas_w, canvas_h, division=3):
    """Compute all intersection points of an N-division compositional grid.

    Args:
        canvas_w, canvas_h: Canvas dimensions in pixels
        division:           Number of divisions (3=thirds, 5=fifths, etc.)

    Returns:
        List of (x, y) tuples for all interior grid intersections,
        ordered left-to-right, top-to-bottom.
    """
    if division < 2:
        raise ValueError(f"grid_points: division must be >= 2, got {division}")

    pts = []
    for row in range(1, division):
        for col in range(1, division):
            x = canvas_w * col / division
            y = canvas_h * row / division
            pts.append((x, y))
    return pts


# Named position aliases for common grid placements
_NAMED_POSITIONS = {
    # Thirds (division=3) names
    'top_left':      (1, 1),
    'top_center':    (1, 2),  # only meaningful if division allows it
    'top_right':     (1, 3),
    'center_left':   (2, 1),
    'center':        None,    # special case — canvas center, any division
    'center_right':  (2, 3),
    'bottom_left':   (3, 1),
    'bottom_center': (3, 2),
    'bottom_right':  (3, 3),
    # Directional aliases
    'upper_left':    (1, 1),
    'upper_right':   (1, 3),
    'lower_left':    (3, 1),
    'lower_right':   (3, 3),
    # Portrait
    'portrait_top':  (1, 2),   # 1/3 down, horizontally centered
}


def named_grid_point(canvas_w, canvas_h, division=3, position='center'):
    """Return a named compositional grid point.

    Args:
        canvas_w, canvas_h: Canvas dimensions
        division:           Grid division (3, 5, 7, ...)
        position:           Named position string (see _NAMED_POSITIONS)
                            or 'nearest' to find closest to current centroid

    Returns:
        (x, y) float tuple

    Raises:
        ValueError: if position name is not recognised
    """
    pos = position.lower().replace(' ', '_')

    # Dead center is always canvas_w/2, canvas_h/2
    if pos == 'center':
        return (canvas_w / 2.0, canvas_h / 2.0)

    if pos not in _NAMED_POSITIONS:
        raise ValueError(
            f"named_grid_point: unknown position '{position}'. "
            f"Known: {', '.join(sorted(_NAMED_POSITIONS.keys()))}"
        )

    row, col = _NAMED_POSITIONS[pos]
    # row/col are 1-indexed grid line numbers (out of division lines)
    # For division=3: lines at 1/3 and 2/3
    # Position (1,1) = first row line x first col line
    x = canvas_w * col / (division + 1)  # +1 so col=1 gives 1/(d+1) for portrait
    y = canvas_h * row / (division + 1)

    # Clamp to canvas
    x = max(0.0, min(float(canvas_w), x))
    y = max(0.0, min(float(canvas_h), y))
    return (x, y)


def nearest_grid_point(centroid, canvas_w, canvas_h, division=3):
    """Find the nearest grid intersection to a given centroid.

    Args:
        centroid:           (cx, cy) current shape centroid
        canvas_w, canvas_h: Canvas dimensions
        division:           Grid division

    Returns:
        (x, y) of the nearest grid intersection
    """
    pts = grid_points(canvas_w, canvas_h, division)
    if not pts:
        return (canvas_w / 2.0, canvas_h / 2.0)

    cx, cy = centroid
    return min(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)