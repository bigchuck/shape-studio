"""
constraints.py - Constraint definitions for Shape Studio composition system.

Each constraint is a plain function that takes shape point data and returns
a ConstraintResult describing whether the constraint is satisfied and
what corrective action (if any) is needed.

Constraints are pure geometry — no executor, no canvas access.
The solver.py module applies corrections using the executor.

Supported constraint types (used in placement_block specs):
  size_ratio          shape area <= ratio * reference area
  grid_placement      centroid near a compositional grid point
  canvas_size_limit   hull fits within N% of canvas in each direction
  axis_align          major/minor axes aligned within tolerance
  axis_misalign       axes differ by at least min_deg (guaranteed non-alignment)
  axis_collinear      axes are parallel AND on the same line (distance ~ 0)
  axis_not_collinear  axes are parallel but offset by at least min_offset_px
  axis_near_parallel  aligned within tolerance THEN offset by misalign_deg
  tangent             hulls are within tolerance_px of touching (near-tangency)
  separation_from_group  target hull is further from a group hull than ref shape
  separation_from_shape  target hull is a controlled distance from a named shape
"""

import math
from src.composition import spatial as sp


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

class ConstraintResult:
    """Outcome of evaluating a single constraint.

    Attributes:
        satisfied:    True if constraint is already met
        constraint:   The constraint type string
        message:      Human-readable description of outcome
        correction:   Dict describing what corrective transform to apply,
                      or None if satisfied or no correction computable.
                      Keys depend on correction type:
                        {'type': 'rotate', 'angle_deg': float}
                        {'type': 'scale',  'factor': float}
                        {'type': 'move',   'dx': float, 'dy': float}
    """
    def __init__(self, satisfied, constraint, message, correction=None):
        self.satisfied  = satisfied
        self.constraint = constraint
        self.message    = message
        self.correction = correction

    def __repr__(self):
        status = 'OK' if self.satisfied else 'FAIL'
        return f"ConstraintResult({status} {self.constraint}: {self.message})"


# ---------------------------------------------------------------------------
# size_ratio
# ---------------------------------------------------------------------------

def check_size_ratio(target_points, reference_points, max_ratio=0.8):
    """Target convex hull area must be <= max_ratio * reference hull area.

    Correction: uniform scale factor to bring target into compliance.

    Args:
        target_points:    Point list for shape being constrained
        reference_points: Point list for reference shape
        max_ratio:        Maximum allowed area ratio (0.0-1.0)

    Returns:
        ConstraintResult
    """
    target_hull = sp.convex_hull(target_points)
    ref_hull    = sp.convex_hull(reference_points)

    target_area = sp.hull_area(target_hull)
    ref_area    = sp.hull_area(ref_hull)

    if ref_area < 1e-6:
        return ConstraintResult(
            True, 'size_ratio',
            f"Reference area near zero — constraint skipped"
        )

    ratio = target_area / ref_area

    if ratio <= max_ratio:
        return ConstraintResult(
            True, 'size_ratio',
            f"Area ratio {ratio:.3f} <= {max_ratio} (OK)"
        )

    # Scale factor needed: sqrt because area scales as factor^2
    needed_factor = math.sqrt(max_ratio / ratio)
    return ConstraintResult(
        False, 'size_ratio',
        f"Area ratio {ratio:.3f} exceeds {max_ratio} — scale by {needed_factor:.4f}",
        correction={'type': 'scale', 'factor': needed_factor}
    )


# ---------------------------------------------------------------------------
# canvas_size_limit
# ---------------------------------------------------------------------------

def check_canvas_size_limit(target_points, canvas_w, canvas_h, max_fraction=0.25):
    """Target hull must not exceed max_fraction of canvas in either dimension.

    Checks bounding rectangle of hull (width and height separately).
    Correction: scale to fit within limit.

    Args:
        target_points:  Point list for shape being constrained
        canvas_w/h:     Canvas dimensions in pixels
        max_fraction:   Maximum fraction of canvas dimension (0.0-1.0)

    Returns:
        ConstraintResult
    """
    hull = sp.convex_hull(target_points)
    if not hull:
        return ConstraintResult(True, 'canvas_size_limit', "Empty hull — skipped")

    xs = [p[0] for p in hull]
    ys = [p[1] for p in hull]
    w  = max(xs) - min(xs)
    h  = max(ys) - min(ys)

    max_w = canvas_w * max_fraction
    max_h = canvas_h * max_fraction

    w_ratio = w / max_w if max_w > 0 else 0.0
    h_ratio = h / max_h if max_h > 0 else 0.0

    worst = max(w_ratio, h_ratio)

    if worst <= 1.0:
        return ConstraintResult(
            True, 'canvas_size_limit',
            f"Size within {max_fraction*100:.0f}% limit (w={w:.0f}px h={h:.0f}px OK)"
        )

    factor = 1.0 / worst
    return ConstraintResult(
        False, 'canvas_size_limit',
        f"Shape exceeds {max_fraction*100:.0f}% canvas limit "
        f"(w={w:.0f} h={h:.0f}) — scale by {factor:.4f}",
        correction={'type': 'scale', 'factor': factor}
    )


# ---------------------------------------------------------------------------
# canvas_bounds
# ---------------------------------------------------------------------------

def check_canvas_bounds(target_points, canvas_w, canvas_h, margin_px=0.0):
    """All hull points must lie within canvas bounds (with optional margin).

    When points exceed the canvas, the shape is scaled down around its
    centroid until it fits — preserving contact relationships rather than
    moving the shape.

    Correction type: 'scale_to_fit' — includes centroid so solver can
    apply the scale correctly without breaking contact points.

    Args:
        target_points:  Point list for shape being constrained
        canvas_w/h:     Canvas dimensions in pixels
        margin_px:      Additional inset margin from canvas edge. Default 0.

    Returns:
        ConstraintResult
    """
    hull = sp.convex_hull(target_points)
    if not hull:
        return ConstraintResult(True, 'canvas_bounds', "Empty hull — skipped")

    x_min_allowed = margin_px
    y_min_allowed = margin_px
    x_max_allowed = canvas_w - margin_px
    y_max_allowed = canvas_h - margin_px

    xs = [p[0] for p in hull]
    ys = [p[1] for p in hull]

    x_lo = min(xs)
    x_hi = max(xs)
    y_lo = min(ys)
    y_hi = max(ys)

    if (x_lo >= x_min_allowed and x_hi <= x_max_allowed and
            y_lo >= y_min_allowed and y_hi <= y_max_allowed):
        return ConstraintResult(
            True, 'canvas_bounds',
            f"Hull within canvas bounds (OK)"
        )

    # Compute centroid for scale_to_fit correction
    centroid = sp.hull_centroid(hull)
    cx, cy = centroid

    # How much do we need to shrink so all points fit?
    # For each point, the max scale factor that keeps it inside:
    # new_x = cx + factor * (px - cx) must be in [x_min, x_max]
    # => factor <= (x_max - cx) / (px - cx)  when px > cx
    # => factor <= (cx - x_min) / (cx - px)  when px < cx
    min_factor = 1.0
    for px, py in hull:
        if px > cx and (px - cx) > 1e-6:
            min_factor = min(min_factor, (x_max_allowed - cx) / (px - cx))
        elif px < cx and (cx - px) > 1e-6:
            min_factor = min(min_factor, (cx - x_min_allowed) / (cx - px))
        if py > cy and (py - cy) > 1e-6:
            min_factor = min(min_factor, (y_max_allowed - cy) / (py - cy))
        elif py < cy and (cy - py) > 1e-6:
            min_factor = min(min_factor, (cy - y_min_allowed) / (cy - py))

    # Apply a small additional shrink to land cleanly inside
    factor = max(0.01, min_factor * 0.98)

    violations = []
    if x_lo < x_min_allowed: violations.append(f"left={x_lo:.0f}")
    if x_hi > x_max_allowed: violations.append(f"right={x_hi:.0f}")
    if y_lo < y_min_allowed: violations.append(f"top={y_lo:.0f}")
    if y_hi > y_max_allowed: violations.append(f"bottom={y_hi:.0f}")

    return ConstraintResult(
        False, 'canvas_bounds',
        f"Hull exceeds canvas ({', '.join(violations)}) — scale_to_fit by {factor:.4f}",
        correction={
            'type':    'scale_to_fit',
            'factor':  factor,
            'cx':      cx,
            'cy':      cy,
        }
    )


# ---------------------------------------------------------------------------
# grid_placement
# ---------------------------------------------------------------------------

def check_grid_placement(target_points, canvas_w, canvas_h,
                          division=3, position='nearest', tolerance_px=20.0,
                          resolved_pt=None):
    """Target centroid must be within tolerance of a grid point.

    Correction: move centroid to the target grid point.

    Args:
        target_points:  Point list for shape being constrained
        canvas_w/h:     Canvas dimensions
        division:       Grid division (3=thirds, 5=fifths, ...)
        position:       Named position, 'nearest', or 'random'
                        'random' picks one intersection at random each evaluation.
        tolerance_px:   Acceptable distance from grid point
        resolved_pt:    Pre-resolved (x,y) for 'random' — locks the target across
                        solver iterations so it doesn't change each pass.

    Returns:
        ConstraintResult
    """
    import random as _random

    hull     = sp.convex_hull(target_points)
    centroid = sp.hull_centroid(hull)

    if resolved_pt is not None:
        target_pt = resolved_pt
    elif position == 'nearest':
        target_pt = sp.nearest_grid_point(centroid, canvas_w, canvas_h, division)
    elif position == 'random':
        pts = sp.grid_points(canvas_w, canvas_h, division)
        target_pt = _random.choice(pts) if pts else (canvas_w / 2, canvas_h / 2)
    else:
        target_pt = sp.named_grid_point(canvas_w, canvas_h, division, position)

    dx = target_pt[0] - centroid[0]
    dy = target_pt[1] - centroid[1]
    dist = math.hypot(dx, dy)

    if dist <= tolerance_px:
        return ConstraintResult(
            True, 'grid_placement',
            f"Centroid within {tolerance_px}px of grid point {position} (dist={dist:.1f}px OK)"
        )

    return ConstraintResult(
        False, 'grid_placement',
        f"Centroid {dist:.1f}px from grid point {position} — move by ({dx:.1f},{dy:.1f})",
        correction={'type': 'move', 'dx': dx, 'dy': dy}
    )


# ---------------------------------------------------------------------------
# axis_align
# ---------------------------------------------------------------------------

def check_axis_align(target_points, reference_points, axis='major', tolerance_deg=10.0):
    """Target axis must be aligned with reference axis within tolerance.

    Correction: rotate target by the measured angle between axes.

    Args:
        target_points:    Point list for shape being constrained
        reference_points: Point list for reference shape
        axis:             'major' or 'minor'
        tolerance_deg:    Acceptable angular deviation in degrees

    Returns:
        ConstraintResult
    """
    angle = sp.axis_angle_between(target_points, reference_points, axis)

    if angle <= tolerance_deg:
        return ConstraintResult(
            True, 'axis_align',
            f"{axis} axis angle {angle:.1f}deg within tolerance {tolerance_deg}deg (OK)"
        )

    # Rotation needed: angle itself (axis_angle_between returns acute angle)
    # Direction: try both +angle and -angle; caller (solver) will verify
    return ConstraintResult(
        False, 'axis_align',
        f"{axis} axis misaligned by {angle:.1f}deg — rotate by {angle:.1f}deg",
        correction={'type': 'rotate', 'angle_deg': angle}
    )


# ---------------------------------------------------------------------------
# axis_misalign
# ---------------------------------------------------------------------------

def check_axis_misalign(target_points, reference_points, axis='minor', min_deg=15.0):
    """Target axis must differ from reference axis by at least min_deg.

    Correction: rotate target by (min_deg - current_angle) to push it
    past the minimum misalignment threshold.

    Args:
        target_points:    Point list for shape being constrained
        reference_points: Point list for reference shape
        axis:             'major' or 'minor'
        min_deg:          Minimum required angular difference

    Returns:
        ConstraintResult
    """
    angle = sp.axis_angle_between(target_points, reference_points, axis)

    if angle >= min_deg:
        return ConstraintResult(
            True, 'axis_misalign',
            f"{axis} axis angle {angle:.1f}deg >= {min_deg}deg minimum (OK)"
        )

    needed = min_deg - angle
    return ConstraintResult(
        False, 'axis_misalign',
        f"{axis} axes too close ({angle:.1f}deg) — rotate by {needed:.1f}deg to separate",
        correction={'type': 'rotate', 'angle_deg': needed}
    )


# ---------------------------------------------------------------------------
# axis_collinear
# ---------------------------------------------------------------------------

def check_axis_collinear(target_points, reference_points, axis='minor',
                          align_tolerance_deg=5.0, collinear_tolerance_px=10.0):
    """Target axis must be collinear with reference axis.

    Two-stage check:
      1. Axes must be parallel (angle < align_tolerance_deg)
      2. Perpendicular distance between axis lines must be < collinear_tolerance_px

    Correction:
      Stage 1 fail -> rotate
      Stage 2 fail -> move perpendicular to axis

    Args:
        target_points:          Point list for shape being constrained
        reference_points:       Point list for reference shape
        axis:                   'major' or 'minor'
        align_tolerance_deg:    Max angle for parallel check
        collinear_tolerance_px: Max perpendicular distance for collinear check

    Returns:
        ConstraintResult
    """
    # Stage 1: parallel check
    angle = sp.axis_angle_between(target_points, reference_points, axis)
    if angle > align_tolerance_deg:
        return ConstraintResult(
            False, 'axis_collinear',
            f"{axis} axes not parallel ({angle:.1f}deg) — rotate first",
            correction={'type': 'rotate', 'angle_deg': angle}
        )

    # Stage 2: collinear check
    dist = sp.axis_to_axis_distance(target_points, reference_points, axis)
    if dist <= collinear_tolerance_px:
        return ConstraintResult(
            True, 'axis_collinear',
            f"{axis} axes collinear (dist={dist:.1f}px <= {collinear_tolerance_px}px OK)"
        )

    # Move target perpendicular to axis direction by dist
    _, _, centroid_ref = sp.principal_axes(reference_points)
    _, _, centroid_tgt = sp.principal_axes(target_points)

    major_ref, minor_ref, _ = sp.principal_axes(reference_points)
    axis_dir = major_ref if axis == 'major' else minor_ref

    # Perpendicular direction
    perp = (-axis_dir[1], axis_dir[0])

    # Sign: move target toward reference axis line
    v = (centroid_ref[0] - centroid_tgt[0], centroid_ref[1] - centroid_tgt[1])
    sign = 1.0 if (v[0] * perp[0] + v[1] * perp[1]) >= 0 else -1.0

    dx = sign * dist * perp[0]
    dy = sign * dist * perp[1]

    return ConstraintResult(
        False, 'axis_collinear',
        f"{axis} axes parallel but offset {dist:.1f}px — move by ({dx:.1f},{dy:.1f})",
        correction={'type': 'move', 'dx': dx, 'dy': dy}
    )


# ---------------------------------------------------------------------------
# axis_not_collinear
# ---------------------------------------------------------------------------

def check_axis_not_collinear(target_points, reference_points, axis='minor',
                              min_offset_px=20.0):
    """Target axis must be parallel but NOT collinear — offset by min_offset_px.

    Correction: move target perpendicular to axis by needed amount.

    Args:
        target_points:    Point list for shape being constrained
        reference_points: Point list for reference shape
        axis:             'major' or 'minor'
        min_offset_px:    Minimum required perpendicular separation

    Returns:
        ConstraintResult
    """
    dist = sp.axis_to_axis_distance(target_points, reference_points, axis)

    if dist >= min_offset_px:
        return ConstraintResult(
            True, 'axis_not_collinear',
            f"{axis} axis offset {dist:.1f}px >= {min_offset_px}px minimum (OK)"
        )

    needed = min_offset_px - dist
    major_ref, minor_ref, _ = sp.principal_axes(reference_points)
    axis_dir = major_ref if axis == 'major' else minor_ref
    perp = (-axis_dir[1], axis_dir[0])

    # Push target away from reference axis line
    _, _, centroid_ref = sp.principal_axes(reference_points)
    _, _, centroid_tgt = sp.principal_axes(target_points)
    v = (centroid_tgt[0] - centroid_ref[0], centroid_tgt[1] - centroid_ref[1])
    sign = 1.0 if (v[0] * perp[0] + v[1] * perp[1]) >= 0 else -1.0

    dx = sign * needed * perp[0]
    dy = sign * needed * perp[1]

    return ConstraintResult(
        False, 'axis_not_collinear',
        f"{axis} axes too close ({dist:.1f}px < {min_offset_px}px) — move by ({dx:.1f},{dy:.1f})",
        correction={'type': 'move', 'dx': dx, 'dy': dy}
    )


# ---------------------------------------------------------------------------
# tangent
# ---------------------------------------------------------------------------

def check_tangent(target_points, reference_points,
                  tolerance_px=3.0, max_contact_points=1):
    """Target hull should touch reference hull at approximately one point.

    reference_points may be a single point list OR a list of point lists
    (for reference_group support). When multiple point lists are provided,
    the combined convex hull is used as the reference.

    Near-tangency: hulls are within tolerance_px of touching.
    Correction: move toward reference along closest-approach vector.

    Args:
        target_points:      Point list for shape being constrained
        reference_points:   Point list OR list of point lists (group)
        tolerance_px:       Distance threshold for contact
        max_contact_points: Maximum allowed contact segments

    Returns:
        ConstraintResult with correction = move toward reference
    """
    target_hull = sp.convex_hull(target_points)

    # Support both single reference and group reference
    if reference_points and isinstance(reference_points[0], (list, tuple)) and \
            isinstance(reference_points[0][0], (list, tuple)):
        ref_hull = sp.combined_hull(reference_points)
    else:
        ref_hull = sp.convex_hull(reference_points)

    # Check for overlap first — hull_separation returns 0 for both
    # touching and overlapping, so we must distinguish them explicitly
    if sp.hull_overlaps(target_hull, ref_hull):
        push_dx, push_dy = sp.hull_push_apart(target_hull, ref_hull)
        # Push apart plus an extra tolerance_px gap so tangency can re-establish
        total_dx = push_dx + (push_dx / max(abs(push_dx), 1e-6)) * tolerance_px
        total_dy = push_dy + (push_dy / max(abs(push_dy), 1e-6)) * tolerance_px
        return ConstraintResult(
            False, 'tangent',
            f"Hulls overlap — push apart ({push_dx:.1f},{push_dy:.1f})",
            correction={'type': 'move', 'dx': push_dx, 'dy': push_dy}
        )

    dist, pt_target, pt_ref = sp.hull_separation(target_hull, ref_hull)

    if dist <= tolerance_px:
        contacts = sp.hull_contact_points(target_hull, ref_hull, tolerance_px)
        if len(contacts) <= max_contact_points:
            return ConstraintResult(
                True, 'tangent',
                f"Near-tangent: separation={dist:.1f}px, contacts={len(contacts)} (OK)"
            )
        else:
            return ConstraintResult(
                True, 'tangent',
                f"Touching with {len(contacts)} contact segments (exceeds {max_contact_points} "
                f"— acceptable for now)"
            )

    # Move target toward reference along the closest-approach vector
    dx = pt_ref[0] - pt_target[0]
    dy = pt_ref[1] - pt_target[1]
    length = math.hypot(dx, dy)
    if length > 1e-6:
        move_dist = dist - tolerance_px
        dx = dx / length * move_dist
        dy = dy / length * move_dist
    else:
        dx, dy = 0.0, 0.0

    return ConstraintResult(
        False, 'tangent',
        f"Separation {dist:.1f}px — move by ({dx:.1f},{dy:.1f}) to reach tangency",
        correction={'type': 'move', 'dx': dx, 'dy': dy}
    )


# ---------------------------------------------------------------------------
# separation_from_group
# ---------------------------------------------------------------------------

def check_separation_from_group(target_points, group_point_lists,
                                 min_separation_px=0.0,
                                 greater_than_points=None):
    """Target hull must be separated from a group's combined hull.

    Optionally: target must be further than a reference shape from the group.

    Args:
        target_points:       Point list for shape being constrained
        group_point_lists:   List of point lists (one per shape in group)
        min_separation_px:   Minimum required separation from group hull
        greater_than_points: If given, target separation must exceed this
                             shape's separation from the group hull

    Returns:
        ConstraintResult
    """
    target_hull = sp.convex_hull(target_points)
    group_hull  = sp.combined_hull(group_point_lists)

    target_dist, pt_t, pt_g = sp.hull_separation(target_hull, group_hull)

    # Check greater_than constraint
    if greater_than_points is not None:
        ref_hull = sp.convex_hull(greater_than_points)
        ref_dist, _, _ = sp.hull_separation(ref_hull, group_hull)
        if target_dist <= ref_dist:
            # Move target further away from group
            dx = pt_t[0] - pt_g[0]
            dy = pt_t[1] - pt_g[1]
            length = math.hypot(dx, dy)
            if length > 1e-6:
                needed = ref_dist - target_dist + 10.0  # 10px buffer
                dx = dx / length * needed
                dy = dy / length * needed
            return ConstraintResult(
                False, 'separation_from_group',
                f"Target separation {target_dist:.1f}px not greater than "
                f"reference {ref_dist:.1f}px — move by ({dx:.1f},{dy:.1f})",
                correction={'type': 'move', 'dx': dx, 'dy': dy}
            )

    if target_dist >= min_separation_px:
        return ConstraintResult(
            True, 'separation_from_group',
            f"Group separation {target_dist:.1f}px >= {min_separation_px}px (OK)"
        )

    needed = min_separation_px - target_dist
    dx = pt_t[0] - pt_g[0]
    dy = pt_t[1] - pt_g[1]
    length = math.hypot(dx, dy)
    if length > 1e-6:
        dx = dx / length * needed
        dy = dy / length * needed

    return ConstraintResult(
        False, 'separation_from_group',
        f"Group separation {target_dist:.1f}px < {min_separation_px}px "
        f"— move by ({dx:.1f},{dy:.1f})",
        correction={'type': 'move', 'dx': dx, 'dy': dy}
    )


# ---------------------------------------------------------------------------
# Dispatcher — evaluate a constraint spec dict
# ---------------------------------------------------------------------------

def evaluate(constraint_spec, target_points, shape_registry):
    """Evaluate a single constraint spec against a target shape.

    Args:
        constraint_spec:  Dict with 'type' key and constraint-specific params
        target_points:    Current point list for the target shape
        shape_registry:   Dict mapping working_name -> point list,
                          used to resolve reference shapes by name

    Returns:
        ConstraintResult

    Raises:
        ValueError: if constraint type is unknown or required keys missing
    """
    ctype = constraint_spec.get('type', '')

    def _pts(name):
        if name not in shape_registry:
            raise ValueError(f"Constraint reference shape '{name}' not found")
        return shape_registry[name]

    if ctype == 'size_ratio':
        return check_size_ratio(
            target_points,
            _pts(constraint_spec['reference']),
            max_ratio=float(constraint_spec.get('max', 0.8))
        )

    elif ctype == 'canvas_size_limit':
        return check_canvas_size_limit(
            target_points,
            canvas_w=float(constraint_spec.get('canvas_w', 768)),
            canvas_h=float(constraint_spec.get('canvas_h', 768)),
            max_fraction=float(constraint_spec.get('max_fraction', 0.25))
        )

    elif ctype == 'canvas_bounds':
        return check_canvas_bounds(
            target_points,
            canvas_w=float(constraint_spec.get('canvas_w', 768)),
            canvas_h=float(constraint_spec.get('canvas_h', 768)),
            margin_px=float(constraint_spec.get('margin_px', 0.0))
        )

    elif ctype == 'grid_placement':
        return check_grid_placement(
            target_points,
            canvas_w=float(constraint_spec.get('canvas_w', 768)),
            canvas_h=float(constraint_spec.get('canvas_h', 768)),
            division=int(constraint_spec.get('division', 3)),
            position=constraint_spec.get('position', 'nearest'),
            tolerance_px=float(constraint_spec.get('tolerance_px', 20.0)),
            resolved_pt=constraint_spec.get('_resolved_random_pt')
        )

    elif ctype == 'axis_align':
        return check_axis_align(
            target_points,
            _pts(constraint_spec['reference']),
            axis=constraint_spec.get('axis', 'major'),
            tolerance_deg=float(constraint_spec.get('tolerance_deg', 10.0))
        )

    elif ctype == 'axis_misalign':
        return check_axis_misalign(
            target_points,
            _pts(constraint_spec['reference']),
            axis=constraint_spec.get('axis', 'minor'),
            min_deg=float(constraint_spec.get('min_deg', 15.0))
        )

    elif ctype == 'axis_collinear':
        return check_axis_collinear(
            target_points,
            _pts(constraint_spec['reference']),
            axis=constraint_spec.get('axis', 'minor'),
            align_tolerance_deg=float(constraint_spec.get('align_tolerance_deg', 5.0)),
            collinear_tolerance_px=float(constraint_spec.get('collinear_tolerance_px', 10.0))
        )

    elif ctype == 'axis_not_collinear':
        return check_axis_not_collinear(
            target_points,
            _pts(constraint_spec['reference']),
            axis=constraint_spec.get('axis', 'minor'),
            min_offset_px=float(constraint_spec.get('min_offset_px', 20.0))
        )

    elif ctype == 'tangent':
        # Support single reference or reference_group (list of names)
        ref_group = constraint_spec.get('reference_group')
        if ref_group:
            ref_pts = [_pts(n) for n in ref_group]
        else:
            ref_pts = _pts(constraint_spec['reference'])
        return check_tangent(
            target_points,
            ref_pts,
            tolerance_px=float(constraint_spec.get('tolerance_px', 3.0)),
            max_contact_points=int(constraint_spec.get('max_contact_points', 1))
        )

    elif ctype == 'separation_from_group':
        group_names = constraint_spec.get('reference_group', [])
        group_pts   = [_pts(n) for n in group_names]
        gt_name     = constraint_spec.get('greater_than')
        gt_pts      = _pts(gt_name) if gt_name else None
        return check_separation_from_group(
            target_points,
            group_pts,
            min_separation_px=float(constraint_spec.get('min_separation_px', 0.0)),
            greater_than_points=gt_pts
        )

    else:
        raise ValueError(
            f"Unknown constraint type '{ctype}'. "
            f"Supported: size_ratio, canvas_size_limit, canvas_bounds, "
            f"grid_placement, axis_align, axis_misalign, axis_collinear, "
            f"axis_not_collinear, tangent, separation_from_group"
        )