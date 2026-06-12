"""
solver.py - Constraint-based placement solver for Shape Studio composition.

Takes a placement_block spec, evaluates constraints against current shape
geometry, and applies corrective transforms via the executor until all
constraints are satisfied or max_iterations is reached.

Placement block JSON spec:
  {
    "target": "compose_shape_2",
    "reference": "compose_shape_1",      (optional — used by constraints)
    "max_iterations": 20,                (default 20)
    "tolerance_iterations": 3,           (stop early if no progress for N iters)
    "verbose": true,
    "constraints": [
      {"type": "size_ratio",     "reference": "compose_shape_1", "max": 0.8},
      {"type": "canvas_size_limit", "max_fraction": 0.25},
      {"type": "grid_placement", "division": 3, "position": "top_left"},
      {"type": "axis_align",     "reference": "compose_shape_1", "axis": "major"},
      {"type": "axis_not_collinear", "reference": "compose_shape_1", "axis": "minor"},
      {"type": "tangent",        "reference": "compose_shape_1"}
    ]
  }

Constraints are evaluated and applied in order. Each corrective transform
is applied immediately so subsequent constraints see the updated geometry.

The solver is self-contained — it reads shape geometry from the executor,
applies transforms via executor.execute(), and logs to the app UI log.
"""

import math
from src.composition import constraints as con


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

CANVAS_W = 768
CANVAS_H = 768


class PlacementSolver:
    """Applies a sequence of constraints to place a shape on the canvas.

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

        Args:
            placement_block: Dict from compose_parameters or command_loop

        Returns:
            Summary string

        Raises:
            ValueError: if target shape not found or constraint type unknown
        """
        target_name   = placement_block['target']
        constraints   = placement_block.get('constraints', [])
        max_iters     = int(placement_block.get('max_iterations', 20))
        tol_iters     = int(placement_block.get('tolerance_iterations', 3))
        verbose       = bool(placement_block.get('verbose', self.verbose))

        if not constraints:
            return f"PlacementSolver: no constraints for '{target_name}' — nothing to do"

        self._log(
            f"Solving '{target_name}': {len(constraints)} constraint(s), "
            f"max {max_iters} iterations",
            verbose
        )

        applied_count  = 0
        no_progress    = 0

        for iteration in range(max_iters):
            # Rebuild shape registry each iteration (geometry may have changed)
            shape_registry = self._build_shape_registry()

            if target_name not in shape_registry:
                raise ValueError(
                    f"PlacementSolver: target '{target_name}' not found on canvas"
                )

            target_points = shape_registry[target_name]

            # Inject canvas dimensions into each constraint spec
            augmented = self._augment_constraints(constraints)

            all_satisfied = True
            iter_applied  = 0

            for cidx, cspec in enumerate(augmented):
                result = con.evaluate(cspec, target_points, shape_registry)

                if result.satisfied:
                    self._log(
                        f"  [{iteration+1}] c[{cidx}] {result.constraint}: {result.message}",
                        verbose
                    )
                    continue

                all_satisfied = False
                self._log(
                    f"  [{iteration+1}] c[{cidx}] {result.constraint}: {result.message}",
                    verbose
                )

                if result.correction:
                    applied = self._apply_correction(target_name, result.correction, verbose)
                    if applied:
                        applied_count += 1
                        iter_applied  += 1
                        # Refresh target points after correction
                        shape_registry = self._build_shape_registry()
                        if target_name in shape_registry:
                            target_points = shape_registry[target_name]

            if all_satisfied:
                self._log(
                    f"All constraints satisfied after {iteration+1} iteration(s). "
                    f"Total corrections: {applied_count}",
                    verbose
                )
                return (
                    f"PlacementSolver: '{target_name}' placed in {iteration+1} "
                    f"iteration(s), {applied_count} correction(s) applied"
                )

            if iter_applied == 0:
                no_progress += 1
                if no_progress >= tol_iters:
                    self._log(
                        f"No progress for {tol_iters} iterations — stopping early",
                        verbose
                    )
                    break
            else:
                no_progress = 0

        self._log(
            f"Max iterations reached. Constraints may not be fully satisfied. "
            f"Total corrections: {applied_count}",
            verbose
        )
        return (
            f"PlacementSolver: '{target_name}' — max iterations reached, "
            f"{applied_count} correction(s) applied"
        )

    # -----------------------------------------------------------------------
    # Shape registry — maps working_name -> point list
    # -----------------------------------------------------------------------

    def _build_shape_registry(self):
        """Read current geometry of all shapes on the active canvas.

        Returns:
            Dict mapping shape name -> list of (x, y) tuples
        """
        registry = {}
        shapes = self.executor.get_active_shapes()
        for name, shape in shapes.items():
            geom = shape.attrs.get('geometry', {})
            pts  = geom.get('points')
            if pts:
                registry[name] = [tuple(p) for p in pts]
        return registry

    # -----------------------------------------------------------------------
    # Correction dispatch
    # -----------------------------------------------------------------------

    def _apply_correction(self, target_name, correction, verbose):
        """Apply a corrective transform to the target shape via the executor.

        Args:
            target_name: Working name of the shape to transform
            correction:  Dict with 'type' and correction-specific keys
            verbose:     Whether to log the correction

        Returns:
            True if a command was issued, False otherwise
        """
        ctype = correction.get('type')

        if ctype == 'move':
            dx = correction.get('dx', 0.0)
            dy = correction.get('dy', 0.0)
            if abs(dx) < 0.1 and abs(dy) < 0.1:
                return False
            self._log(f"    -> MOVE {target_name} {dx:.2f},{dy:.2f}", verbose)
            self.executor.execute(f"MOVE {target_name} {dx:.4f},{dy:.4f}")
            return True

        elif ctype == 'rotate':
            angle = correction.get('angle_deg', 0.0)
            if abs(angle) < 0.1:
                return False
            self._log(f"    -> ROTATE {target_name} {angle:.2f}deg", verbose)
            self.executor.execute(f"ROTATE {target_name} {angle:.4f}")
            return True

        elif ctype == 'scale':
            factor = correction.get('factor', 1.0)
            if abs(factor - 1.0) < 0.001:
                return False
            self._log(f"    -> SCALE {target_name} {factor:.4f}", verbose)
            self.executor.execute(f"SCALE {target_name} {factor:.6f}")
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
            c = dict(c)  # shallow copy — don't mutate original
            if c.get('type') in ('canvas_size_limit', 'grid_placement'):
                c.setdefault('canvas_w', CANVAS_W)
                c.setdefault('canvas_h', CANVAS_H)
            augmented.append(c)
        return augmented

    def _log(self, msg, verbose=True):
        """Emit a message to the app UI log if verbose is enabled."""
        if not verbose:
            return
        if hasattr(self.executor, 'ui_instance') and self.executor.ui_instance:
            self.executor.ui_instance._log_output(f"    [solver] {msg}")
        else:
            print(f"[solver] {msg}")