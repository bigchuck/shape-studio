"""
solver.py - Constraint-based placement solver for Shape Studio composition.

Placement block JSON spec:

  {
    "target": "compose_shape_3",
    "max_iterations": 20,
    "pre_constraints": [
      {"type": "size_ratio",         "reference": "compose_shape_1", "max": 0.8},
      {"type": "axis_align",         "reference": "compose_shape_1", "axis": "major", "tolerance_deg": 10},
      {"type": "axis_not_collinear", "reference": "compose_shape_1", "axis": "minor", "min_offset_px": 20}
    ],
    "placement": {
      "type": "tangent",
      "reference_group": ["compose_shape_1", "compose_shape_2"],
      "approach": "random",
      "tolerance_px": 3,
      "canvas_bounds_margin_px": 5
    }
  }

Execution sequence:
  1. pre_constraints loop  — size, axis etc. while shape is in loaded position
  2. pre_size              — scale shape to fit within usable canvas area
  3. pre_position          — move to approach side of reference (clamped to canvas)
  4. tangent move          — close gap to reference hull in one direct move
  5. bounds fit            — if hull exceeds canvas: exact resize + re-tangent

Legacy format (constraints list without placement key) is still supported
for backward compatibility — shape_1 and shape_2 style placement blocks.
"""

import math
from src.composition import constraints as con


CANVAS_W = 768
CANVAS_H = 768


class PlacementSolver:
    """Applies constraints to place a shape on the canvas.

    Args:
        executor: CommandExecutor instance
        verbose:  If True, emit progress to the app UI log
    """

    def __init__(self, executor, verbose=True):
        self.executor = executor
        self.verbose  = verbose

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def solve(self, placement_block):
        """Execute a placement_block spec.

        Returns:
            (summary string, commands_applied list)
        """
        target_name      = placement_block['target']
        verbose          = bool(placement_block.get('verbose', self.verbose))
        commands_applied = []
        applied_count    = 0

        # Detect format: new (pre_constraints + placement) vs legacy (constraints)
        has_placement_key = 'placement' in placement_block

        if has_placement_key:
            # --- New format ---
            pre_constraints = placement_block.get('pre_constraints', [])
            placement_spec  = placement_block['placement']
            max_iters       = int(placement_block.get('max_iterations', 10))

            self._log(
                f"Solving '{target_name}': {len(pre_constraints)} pre_constraint(s) "
                f"+ tangent placement",
                verbose
            )

            # Step 1: pre_constraints — run on shape in its loaded position
            if pre_constraints:
                n = self._run_constraint_loop(
                    target_name, pre_constraints,
                    max_iters, int(placement_block.get('tolerance_iterations', 3)),
                    verbose, commands_applied
                )
                applied_count += n

            # Steps 2-5: tangent placement with bounds handling
            n = self._place_tangent(
                target_name, placement_spec, verbose, commands_applied
            )
            applied_count += n

            return (
                f"PlacementSolver: '{target_name}' placed, "
                f"{applied_count} correction(s) applied",
                commands_applied
            )

        else:
            # --- Legacy format: plain constraints list ---
            constraints = placement_block.get('constraints', [])
            max_iters   = int(placement_block.get('max_iterations', 20))
            tol_iters   = int(placement_block.get('tolerance_iterations', 3))

            if not constraints:
                return (
                    f"PlacementSolver: no constraints for '{target_name}' — nothing to do",
                    []
                )

            self._log(
                f"Solving '{target_name}': {len(constraints)} constraint(s), "
                f"max {max_iters} iterations",
                verbose
            )

            n = self._run_constraint_loop(
                target_name, constraints, max_iters, tol_iters,
                verbose, commands_applied
            )
            applied_count += n

            return (
                f"PlacementSolver: '{target_name}' done, "
                f"{applied_count} correction(s) applied",
                commands_applied
            )

    # -----------------------------------------------------------------------
    # Tangent placement — new direct algorithm
    # -----------------------------------------------------------------------

    def _place_tangent(self, target_name, placement_spec, verbose, commands_applied):
        """Execute the 4-step tangent placement algorithm.

        Steps:
          2. pre_size    — scale to fit canvas
          3. pre_position — move to approach side, clamped to canvas
          4. tangent move — close gap in one direct move
          5. bounds fit  — exact resize + re-tangent if needed

        Returns:
            Number of corrections applied
        """
        from src.composition import spatial as sp

        applied      = 0
        margin_px       = float(placement_spec.get('canvas_bounds_margin_px', 0.0))
        tolerance_px    = float(placement_spec.get('tolerance_px', 3.0))
        approach        = placement_spec.get('approach')
        overlap_allowed = bool(placement_spec.get('overlap_allowed', False))

        # Step 2: pre_size
        shape_registry = self._build_shape_registry()
        if target_name not in shape_registry:
            return applied

        if margin_px > 0:
            if self._pre_size_for_canvas(
                    target_name, margin_px, verbose, commands_applied):
                applied += 1
                shape_registry = self._build_shape_registry()

        # Resolve reference cluster hull
        ref_pts = self._resolve_reference_points(placement_spec, shape_registry)
        if not ref_pts:
            self._log(
                f"  [tangent] reference not found for '{target_name}' — skipping placement",
                verbose
            )
            return applied

        ref_hull = sp.convex_hull(ref_pts)

        # Step 3: pre_position (clamped to canvas)
        if approach and target_name in shape_registry:
            if self._pre_position_for_approach(
                    target_name, approach, ref_hull,
                    shape_registry[target_name],
                    margin_px, verbose, commands_applied):
                applied += 1
                shape_registry = self._build_shape_registry()

        # Step 4: tangent move — handle overlap or separation
        if target_name not in shape_registry:
            return applied

        target_hull = sp.convex_hull(shape_registry[target_name])

        if sp.hull_overlaps(target_hull, ref_hull):
            # Shapes overlap — push apart first, then re-approach to tangency
            push_dx, push_dy = sp.hull_push_apart(target_hull, ref_hull)
            if abs(push_dx) > 0.1 or abs(push_dy) > 0.1:
                cmd = f"MOVE {target_name} {push_dx:.4f},{push_dy:.4f}"
                self._log(
                    f"  [tangent] overlap detected — push apart "
                    f"({push_dx:.1f},{push_dy:.1f})",
                    verbose
                )
                self.executor.execute(cmd)
                commands_applied.append(cmd)
                applied += 1
                shape_registry = self._build_shape_registry()
                target_hull = sp.convex_hull(shape_registry[target_name])

            # Close back to tolerance_px
            dist, pt_target, pt_ref = sp.hull_separation(target_hull, ref_hull)
            if dist > tolerance_px:
                move_dist = dist - tolerance_px
                dx_vec = pt_ref[0] - pt_target[0]
                dy_vec = pt_ref[1] - pt_target[1]
                length = math.hypot(dx_vec, dy_vec)
                if length > 1e-6:
                    dx = dx_vec / length * move_dist
                    dy = dy_vec / length * move_dist
                    cmd = f"MOVE {target_name} {dx:.4f},{dy:.4f}"
                    self._log(
                        f"  [tangent] re-approach MOVE {target_name} "
                        f"({dx:.1f},{dy:.1f})",
                        verbose
                    )
                    self.executor.execute(cmd)
                    commands_applied.append(cmd)
                    applied += 1
                    shape_registry = self._build_shape_registry()

        else:
            dist, pt_target, pt_ref = sp.hull_separation(target_hull, ref_hull)
            if dist > tolerance_px:
                move_dist = dist - tolerance_px
                dx_vec = pt_ref[0] - pt_target[0]
                dy_vec = pt_ref[1] - pt_target[1]
                length = math.hypot(dx_vec, dy_vec)
                if length > 1e-6:
                    dx = dx_vec / length * move_dist
                    dy = dy_vec / length * move_dist
                    cmd = f"MOVE {target_name} {dx:.4f},{dy:.4f}"
                    self._log(
                        f"  [tangent] MOVE {target_name} ({dx:.1f},{dy:.1f}) "
                        f"dist={dist:.1f}px",
                        verbose
                    )
                    self.executor.execute(cmd)
                    commands_applied.append(cmd)
                    applied += 1
                    shape_registry = self._build_shape_registry()
            else:
                self._log(
                    f"  [tangent] already touching "
                    f"(dist={dist:.1f}px <= {tolerance_px}px)",
                    verbose
                )

        # Step 5: bounds fit — only if canvas_bounds_margin_px specified
        if margin_px > 0 and target_name in shape_registry:
            n = self._fit_and_retangent(
                target_name, ref_hull, margin_px, tolerance_px,
                overlap_allowed, verbose, commands_applied
            )
            applied += n

        # Final overlap cleanup — catch any residual overlaps
        if not overlap_allowed:
            applied += self._push_off_all(target_name, commands_applied, verbose)

        return applied

    def _fit_and_retangent(self, target_name, ref_hull, margin_px, tolerance_px,
                            overlap_allowed, verbose, commands_applied):
        """If shape exceeds canvas bounds after placement: exact resize + re-tangent.

        Direct calculation — no iteration:
          a. Compute exact scale factor to bring all points inside canvas
          b. Apply scale (centroid fixed — preserves contact direction)
          c. Re-establish tangency in one direct move
          d. If overlap_allowed is False, push off any overlapping shapes

        Returns:
            Number of corrections applied (0, 1, or 2)
        """
        from src.composition import spatial as sp

        applied = 0
        shape_registry = self._build_shape_registry()
        if target_name not in shape_registry:
            return applied

        hull = sp.convex_hull(shape_registry[target_name])
        xs   = [p[0] for p in hull]
        ys   = [p[1] for p in hull]

        x_min_ok = margin_px
        y_min_ok = margin_px
        x_max_ok = CANVAS_W - margin_px
        y_max_ok = CANVAS_H - margin_px

        if (min(xs) >= x_min_ok and max(xs) <= x_max_ok and
                min(ys) >= y_min_ok and max(ys) <= y_max_ok):
            self._log("  [bounds] Within canvas bounds (OK)", verbose)
            return applied

        # Check if a simple move would fix the violation without scaling.
        # Only scale when the shape is genuinely too large for the canvas.
        cx, cy   = sp.hull_centroid(hull)
        shape_w  = max(xs) - min(xs)
        shape_h  = max(ys) - min(ys)
        usable_w = x_max_ok - x_min_ok
        usable_h = y_max_ok - y_min_ok

        if shape_w <= usable_w and shape_h <= usable_h:
            # Shape fits within canvas — move centroid to bring it inside
            half_w  = shape_w / 2.0
            half_h  = shape_h / 2.0
            move_cx = max(x_min_ok + half_w, min(x_max_ok - half_w, cx))
            move_cy = max(y_min_ok + half_h, min(y_max_ok - half_h, cy))
            dx = move_cx - cx
            dy = move_cy - cy
            if abs(dx) > 0.5 or abs(dy) > 0.5:
                self._log(
                    f"  [bounds] Shape fits — move to clear edge "
                    f"({dx:.1f},{dy:.1f})",
                    verbose
                )
                cmd = f"MOVE {target_name} {dx:.4f},{dy:.4f}"
                self.executor.execute(cmd)
                commands_applied.append(cmd)
                applied += 1
                shape_registry = self._build_shape_registry()
                if target_name not in shape_registry:
                    return applied
                target_hull = sp.convex_hull(shape_registry[target_name])
                dist, pt_target, pt_ref = sp.hull_separation(target_hull, ref_hull)
                if dist > tolerance_px:
                    move_dist = dist - tolerance_px
                    dx_vec = pt_ref[0] - pt_target[0]
                    dy_vec = pt_ref[1] - pt_target[1]
                    length = math.hypot(dx_vec, dy_vec)
                    if length > 1e-6:
                        mv_dx = dx_vec / length * move_dist
                        mv_dy = dy_vec / length * move_dist
                        cmd = f"MOVE {target_name} {mv_dx:.4f},{mv_dy:.4f}"
                        self._log(
                            f"  [bounds] Re-tangent after move "
                            f"({mv_dx:.1f},{mv_dy:.1f})",
                            verbose
                        )
                        self.executor.execute(cmd)
                        commands_applied.append(cmd)
                        applied += 1
            if not overlap_allowed:
                applied += self._push_off_all(target_name, commands_applied, verbose)
            return applied

        # Shape is genuinely too large for canvas.
        # Find the contact direction — vector from target centroid toward
        # the nearest point on the reference hull.
        _, pt_contact_target, pt_contact_ref = sp.hull_separation(
            hull, ref_hull
        )
        contact_dx = pt_contact_ref[0] - cx
        contact_dy = pt_contact_ref[1] - cy
        contact_len = math.hypot(contact_dx, contact_dy)
        if contact_len > 1e-6:
            contact_ux = contact_dx / contact_len
            contact_uy = contact_dy / contact_len
        else:
            contact_ux, contact_uy = 0.0, -1.0  # default upward

        # Worst-violating point: the hull point that violates canvas bounds
        # AND is most opposite to the contact direction (dot product most negative).
        # This point is the controlling factor — scaling it inside the canvas
        # is the minimum scale needed without over-shrinking the contact side.
        worst_factor = 1.0
        worst_point  = None

        for px, py in hull:
            # Is this point violating canvas bounds?
            point_factor = 1.0
            if px < x_min_ok and (cx - px) > 1e-6:
                point_factor = min(point_factor, (cx - x_min_ok) / (cx - px))
            if px > x_max_ok and (px - cx) > 1e-6:
                point_factor = min(point_factor, (x_max_ok - cx) / (px - cx))
            if py < y_min_ok and (cy - py) > 1e-6:
                point_factor = min(point_factor, (cy - y_min_ok) / (cy - py))
            if py > y_max_ok and (py - cy) > 1e-6:
                point_factor = min(point_factor, (y_max_ok - cy) / (py - cy))

            if point_factor < 1.0:
                # This point violates — check if it's the worst opposing one
                # Dot product with contact direction: negative = opposing
                rel_x = px - cx
                rel_y = py - cy
                dot = rel_x * contact_ux + rel_y * contact_uy
                # Weight: combine factor (smaller = more violation) and
                # opposition (more negative dot = more opposing).
                # We want the most violating point on the opposing side.
                if worst_point is None or point_factor < worst_factor:
                    worst_factor = point_factor
                    worst_point  = (px, py)

        if worst_factor >= 1.0:
            # No single point drives scale — fall back to all-points approach
            for px, py in hull:
                if px > cx and (px - cx) > 1e-6:
                    worst_factor = min(worst_factor, (x_max_ok - cx) / (px - cx))
                elif px < cx and (cx - px) > 1e-6:
                    worst_factor = min(worst_factor, (cx - x_min_ok) / (cx - px))
                if py > cy and (py - cy) > 1e-6:
                    worst_factor = min(worst_factor, (y_max_ok - cy) / (py - cy))
                elif py < cy and (cy - py) > 1e-6:
                    worst_factor = min(worst_factor, (cy - y_min_ok) / (cy - py))

        factor = max(0.1, worst_factor * 0.98)  # 2% buffer

        violations = []
        if min(xs) < x_min_ok: violations.append(f"left={min(xs):.0f}")
        if max(xs) > x_max_ok: violations.append(f"right={max(xs):.0f}")
        if min(ys) < y_min_ok: violations.append(f"top={min(ys):.0f}")
        if max(ys) > y_max_ok: violations.append(f"bottom={max(ys):.0f}")

        self._log(
            f"  [bounds] Exceeds canvas ({', '.join(violations)}) — "
            f"resize by {factor:.4f}",
            verbose
        )

        cmd = f"SCALE {target_name} {factor:.6f}"
        self.executor.execute(cmd)
        commands_applied.append(cmd)
        applied += 1

        # Re-establish tangency after resize
        shape_registry = self._build_shape_registry()
        if target_name not in shape_registry:
            return applied

        target_hull = sp.convex_hull(shape_registry[target_name])
        dist, pt_target, pt_ref = sp.hull_separation(target_hull, ref_hull)

        if dist <= tolerance_px:
            self._log("  [bounds] Still touching after resize (OK)", verbose)
            return applied

        move_dist = dist - tolerance_px
        dx_vec = pt_ref[0] - pt_target[0]
        dy_vec = pt_ref[1] - pt_target[1]
        length = math.hypot(dx_vec, dy_vec)

        if length > 1e-6:
            dx = dx_vec / length * move_dist
            dy = dy_vec / length * move_dist
            cmd = f"MOVE {target_name} {dx:.4f},{dy:.4f}"
            self._log(
                f"  [bounds] Re-tangent MOVE {target_name} ({dx:.1f},{dy:.1f})",
                verbose
            )
            self.executor.execute(cmd)
            commands_applied.append(cmd)
            applied += 1

        if not overlap_allowed:
            applied += self._push_off_all(target_name, commands_applied, verbose)

        return applied

    # -----------------------------------------------------------------------
    # Legacy constraint loop
    # -----------------------------------------------------------------------

    def _run_constraint_loop(self, target_name, constraints, max_iters, tol_iters,
                              verbose, commands_applied):
        """Run the iterative constraint evaluation loop.

        Used for pre_constraints (new format) and all constraints (legacy format).

        Returns:
            Total corrections applied
        """
        applied_count = 0
        no_progress   = 0

        for iteration in range(max_iters):
            shape_registry = self._build_shape_registry()

            if target_name not in shape_registry:
                raise ValueError(
                    f"PlacementSolver: target '{target_name}' not found on canvas"
                )

            target_points = shape_registry[target_name]
            augmented     = self._augment_constraints(constraints)
            all_satisfied = True
            iter_applied  = 0

            for cidx, cspec in enumerate(augmented):
                result = con.evaluate(cspec, target_points, shape_registry)

                self._log(
                    f"  [{iteration+1}] c[{cidx}] {result.constraint}: {result.message}",
                    verbose
                )

                if result.satisfied:
                    continue

                all_satisfied = False
                if result.correction:
                    applied = self._apply_correction(
                        target_name, result.correction, verbose, commands_applied
                    )
                    if applied:
                        applied_count += 1
                        iter_applied  += 1
                        shape_registry = self._build_shape_registry()
                        if target_name in shape_registry:
                            target_points = shape_registry[target_name]

            if all_satisfied:
                self._log(
                    f"  Constraints satisfied after {iteration+1} iteration(s).",
                    verbose
                )
                return applied_count

            if iter_applied == 0:
                no_progress += 1
                if no_progress >= tol_iters:
                    self._log(
                        f"  No progress for {tol_iters} iterations — stopping",
                        verbose
                    )
                    break
            else:
                no_progress = 0

        return applied_count

    # -----------------------------------------------------------------------
    # Reference resolution
    # -----------------------------------------------------------------------

    def _resolve_reference_points(self, placement_spec, shape_registry):
        """Resolve reference or reference_group to a flat point list.

        Always returns a flat point list (hull of group if reference_group).
        """
        from src.composition import spatial as sp

        ref_group = placement_spec.get('reference_group')
        ref_name  = placement_spec.get('reference')

        if ref_group:
            group_pts = [shape_registry[n] for n in ref_group
                         if n in shape_registry]
            if group_pts:
                return list(sp.combined_hull(group_pts))
            return None
        elif ref_name and ref_name in shape_registry:
            return shape_registry[ref_name]
        return None

    # -----------------------------------------------------------------------
    # Shape registry
    # -----------------------------------------------------------------------

    def _build_shape_registry(self):
        """Read current geometry of all shapes on the active canvas."""
        registry = {}
        shapes = self.executor.get_active_shapes()
        for name, shape in shapes.items():
            geom = shape.attrs.get('geometry', {})
            pts  = geom.get('points')
            if pts:
                registry[name] = [tuple(p) for p in pts]
        return registry

    # -----------------------------------------------------------------------
    # Corrections
    # -----------------------------------------------------------------------

    def _apply_correction(self, target_name, correction, verbose, commands_applied):
        """Apply a corrective transform to the target shape."""
        ctype = correction.get('type')

        if ctype == 'move':
            dx = correction.get('dx', 0.0)
            dy = correction.get('dy', 0.0)
            if abs(dx) < 0.1 and abs(dy) < 0.1:
                return False
            cmd = f"MOVE {target_name} {dx:.4f},{dy:.4f}"
            self._log(f"    -> MOVE {target_name} {dx:.2f},{dy:.2f}", verbose)
            self.executor.execute(cmd)
            commands_applied.append(cmd)
            return True

        elif ctype == 'rotate':
            angle = correction.get('angle_deg', 0.0)
            if abs(angle) < 0.1:
                return False
            cmd = f"ROTATE {target_name} {angle:.4f}"
            self._log(f"    -> ROTATE {target_name} {angle:.2f}deg", verbose)
            self.executor.execute(cmd)
            commands_applied.append(cmd)
            return True

        elif ctype in ('scale', 'scale_to_fit'):
            factor = correction.get('factor', 1.0)
            if abs(factor - 1.0) < 0.001:
                return False
            cmd = f"SCALE {target_name} {factor:.6f}"
            self._log(f"    -> SCALE {target_name} {factor:.4f}", verbose)
            self.executor.execute(cmd)
            commands_applied.append(cmd)
            return True

        else:
            self._log(f"    -> Unknown correction type '{ctype}' — skipped", verbose)
            return False

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _augment_constraints(self, constraints):
        """Inject canvas dimensions into constraint specs that need them."""
        augmented = []
        for c in constraints:
            c = dict(c)
            if c.get('type') in ('canvas_size_limit', 'canvas_bounds', 'grid_placement'):
                c.setdefault('canvas_w', CANVAS_W)
                c.setdefault('canvas_h', CANVAS_H)
            augmented.append(c)
        return augmented

    def _pre_size_for_canvas(self, target_name, margin_px, verbose, commands_applied):
        """Scale shape so its hull fits within the usable canvas area.

        Conservative pre-sizing — ensures shape cannot exceed usable canvas
        regardless of where it lands.
        """
        from src.composition import spatial as sp

        shape_registry = self._build_shape_registry()
        if target_name not in shape_registry:
            return False

        hull = sp.convex_hull(shape_registry[target_name])
        xs   = [p[0] for p in hull]
        ys   = [p[1] for p in hull]
        w    = max(xs) - min(xs)
        h    = max(ys) - min(ys)

        usable_w = CANVAS_W - 2 * margin_px
        usable_h = CANVAS_H - 2 * margin_px

        if w <= usable_w and h <= usable_h:
            return False

        factor = min(usable_w / w, usable_h / h) * 0.95
        factor = max(0.1, factor)

        cmd = f"SCALE {target_name} {factor:.6f}"
        self._log(
            f"    -> pre-size SCALE {target_name} {factor:.4f} "
            f"(w={w:.0f} h={h:.0f} -> fits {usable_w:.0f}x{usable_h:.0f})",
            verbose
        )
        self.executor.execute(cmd)
        commands_applied.append(cmd)
        return True

    def _pre_position_for_approach(self, target_name, approach_spec,
                                    ref_hull, target_points,
                                    margin_px, verbose, commands_applied):
        """Pre-position target to approach from a specified direction.

        Destination = reference_centroid + approach_vector * safe_distance
        Destination is clamped to keep target hull within canvas bounds.

        approach_spec forms:
          Compass/degree/random — passed to CommandLoopRunner._resolve_direction
          {"axis": "major"|"minor", "reference": "<name>", "random_sign": true}
            — derive direction from named shape's principal axis
        """
        from src.composition import spatial as sp
        from src.composition.command_loop import CommandLoopRunner

        # Resolve approach direction to unit vector (ux, uy)
        if isinstance(approach_spec, dict) and 'axis' in approach_spec:
            ux, uy, dir_label = self._resolve_axis_approach(approach_spec)
        else:
            runner = CommandLoopRunner(self.executor)
            direction, dir_label = runner._resolve_direction(approach_spec)
            ux, uy = runner._direction_to_delta(direction, 1.0)

        ref_cx, ref_cy = sp.hull_centroid(ref_hull)

        def _hull_extent(pts):
            h = sp.convex_hull(pts)
            xs = [p[0] for p in h]
            ys = [p[1] for p in h]
            return math.hypot(max(xs) - min(xs), max(ys) - min(ys))

        # Safe distance: ref extent + target extent + buffer
        ref_extent    = _hull_extent(list(ref_hull))
        target_extent = _hull_extent(target_points)
        safe_dist     = ref_extent + target_extent + 20.0

        # Unclamped destination
        dest_x = ref_cx + ux * safe_dist
        dest_y = ref_cy + uy * safe_dist

        # Clamp destination to keep target centroid within canvas with margin
        t_hull = sp.convex_hull(target_points)
        t_xs   = [p[0] for p in t_hull]
        t_ys   = [p[1] for p in t_hull]
        t_cx, t_cy = sp.hull_centroid(t_hull)

        # Half-extents of target hull from centroid
        half_w = max(abs(max(t_xs) - t_cx), abs(t_cx - min(t_xs)))
        half_h = max(abs(max(t_ys) - t_cy), abs(t_cy - min(t_ys)))

        clamp_margin = margin_px + 5.0
        dest_x = max(half_w + clamp_margin,
                     min(CANVAS_W - half_w - clamp_margin, dest_x))
        dest_y = max(half_h + clamp_margin,
                     min(CANVAS_H - half_h - clamp_margin, dest_y))

        dx = dest_x - t_cx
        dy = dest_y - t_cy

        if math.hypot(dx, dy) < 1.0:
            return False

        cmd = f"MOVE {target_name} {dx:.4f},{dy:.4f}"
        self._log(
            f"    -> pre-position MOVE {target_name} approach={dir_label} "
            f"({dx:.1f},{dy:.1f}) -> dest=({dest_x:.0f},{dest_y:.0f})",
            verbose
        )
        self.executor.execute(cmd)
        commands_applied.append(cmd)
        return True

    def _resolve_axis_approach(self, approach_spec):
        """Resolve an axis-based approach spec to a unit vector.

        Args:
            approach_spec: Dict with keys:
              'axis':        'major' or 'minor'
              'reference':   working name of the shape providing the axis
              'random_sign': if True, randomly pick + or - direction along axis

        Returns:
            (ux, uy, label_string)
        """
        import random as _random
        from src.composition import spatial as sp

        axis       = approach_spec.get('axis', 'minor')
        ref_name   = approach_spec.get('reference')
        rand_sign  = bool(approach_spec.get('random_sign', True))

        shape_registry = self._build_shape_registry()
        if not ref_name or ref_name not in shape_registry:
            # Fallback: approach from north
            self._log(
                f"  [approach] axis reference '{ref_name}' not found — "
                f"defaulting to N",
                True
            )
            return 0.0, -1.0, 'N(fallback)'

        ref_points = shape_registry[ref_name]
        major_vec, minor_vec, _ = sp.principal_axes(ref_points)

        base_vec = major_vec if axis == 'major' else minor_vec
        ux, uy   = base_vec

        # Choose sign — random or always positive
        if rand_sign:
            sign = _random.choice([1.0, -1.0])
        else:
            sign = 1.0

        ux *= sign
        uy *= sign

        label = f"{axis}_axis({'+'if sign>0 else'-'})"
        return ux, uy, label

    def _push_off_all(self, target_name, commands_applied, verbose):
        """Push target shape off any shapes it overlaps on the canvas.

        Checks every other shape — not just the reference cluster.
        Iterates until no overlaps remain or max_attempts is reached.

        Args:
            target_name:      Working name of shape to deconflict
            commands_applied: Command log list
            verbose:          Log flag

        Returns:
            Number of corrections applied
        """
        from src.composition import spatial as sp

        applied      = 0
        max_attempts = 8

        for attempt in range(max_attempts):
            shape_registry = self._build_shape_registry()
            if target_name not in shape_registry:
                return applied

            target_hull  = sp.convex_hull(shape_registry[target_name])
            found_overlap = False

            for other_name, other_pts in shape_registry.items():
                if other_name == target_name:
                    continue
                other_hull = sp.convex_hull(other_pts)
                if sp.hull_overlaps(target_hull, other_hull):
                    push_dx, push_dy = sp.hull_push_apart(target_hull, other_hull)
                    if abs(push_dx) > 0.1 or abs(push_dy) > 0.1:
                        cmd = f"MOVE {target_name} {push_dx:.4f},{push_dy:.4f}"
                        self._log(
                            f"  [overlap] push off '{other_name}' "
                            f"({push_dx:.1f},{push_dy:.1f})",
                            verbose
                        )
                        self.executor.execute(cmd)
                        commands_applied.append(cmd)
                        applied += 1
                        found_overlap = True
                        break  # re-check all shapes after each push

            if not found_overlap:
                if attempt > 0:
                    self._log(
                        f"  [overlap] cleared after {attempt+1} push(es)",
                        verbose
                    )
                return applied

        self._log(
            f"  [overlap] max attempts reached — some overlap may remain",
            verbose
        )
        return applied

    def _log(self, msg, verbose=True):
        """Emit a message to the app UI log if verbose is enabled."""
        if not verbose:
            return
        if hasattr(self.executor, 'ui_instance') and self.executor.ui_instance:
            self.executor.ui_instance._log_output(f"    [solver] {msg}")
        else:
            print(f"[solver] {msg}")