"""
Shape Studies - Pre-phase handlers for structured geometric forms.

Shape studies apply a structured geometric pre-phase to a standard dynamic_polygon
before it enters the normal evolution loop. Each shape study defines a specific,
recognizable topological form (U, stingray, future others) that then receives
organic texture through standard iterations.

Architecture:
    - ShapeStudyRegistry dispatches SHAPE=<name_list> to ordered handlers
    - Each handler receives polygon points, centroid, config, and accumulated metadata
    - Handlers return modified points + metadata for downstream handlers
    - The ProceduralGenerators class calls dispatch_shape_studies() between
      vertex connection (Phase 2) and the evolution loop (Phase 4)

Configuration resolution (priority order):
    1. Template shape_parameters block (from template library definition)
    2. config.procedural.shapes.<name> block (from config.json)
    3. Handler's internal defaults (hardcoded fallbacks)

Classes:
    ShapeStudyResult  - Return value from a shape study handler
    ShapeStudyRegistry - Registry and dispatcher for shape study handlers
"""
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable

from src.config import config


# =============================================================================
# ShapeStudyResult
# =============================================================================

@dataclass
class ShapeStudyResult:
    """
    Return value from a shape study pre-phase handler.

    Attributes:
        points: Modified polygon points after the shape study
        metadata: Dictionary of metadata about the transformation, including:
            - 'significant_segments': List of (point_idx_start, point_idx_end) tuples
              marking structurally important segments that downstream handlers
              may want to avoid modifying
            - 'shape_name': Name of the shape study that produced this result
            - 'parameters_used': Dict of actual parameter values used
            - Any shape-specific metadata
        success: Whether the shape study was successfully applied
        message: Human-readable status message
    """
    points: List[Tuple[float, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    message: str = ""


# =============================================================================
# ShapeStudyRegistry
# =============================================================================

class ShapeStudyRegistry:
    """
    Registry and dispatcher for shape study pre-phase handlers.

    Each handler is a callable with signature:
        handler(points, centroid, bounds, shape_config, accumulated_metadata, generator)
            -> ShapeStudyResult

    The generator parameter provides access to validation methods on
    ProceduralGenerators (_is_valid_polygon, _check_segment_clearance, etc.)
    """

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

        # Register built-in shape studies
        self._handlers['u'] = self._pre_phase_u

    def register(self, name: str, handler: Callable):
        """Register a shape study handler by name."""
        self._handlers[name.lower()] = handler

    def get_available(self) -> List[str]:
        """Return list of registered shape study names."""
        return sorted(self._handlers.keys())

    def dispatch(self, shape_names: List[str], points: List[Tuple[float, float]],
                 centroid: Tuple[float, float],
                 bounds: Tuple[float, float, float, float],
                 generator,
                 template_shape_params: Optional[Dict[str, Any]] = None
                 ) -> Tuple[List[Tuple[float, float]], Dict[str, Any]]:
        """
        Execute shape studies in sequence.

        Args:
            shape_names: Ordered list of shape study names to apply
            points: Current polygon points (post-connection, pre-evolution)
            centroid: Polygon centroid computed from initial points
            bounds: Bounding box (x1, y1, x2, y2)
            generator: ProceduralGenerators instance (for validation methods)
            template_shape_params: Optional dict of shape parameter blocks from
                template definition. Keys are shape names (e.g., 'u'), values are
                parameter dicts that override config.json defaults.

        Returns:
            (modified_points, accumulated_metadata) tuple

        Raises:
            ValueError: If a shape study name is not registered or fails
                        after all retries
        """
        accumulated_metadata = {
            'shape_studies_applied': [],
            'significant_segments': [],
        }

        current_points = points[:]

        for shape_name in shape_names:
            name_lower = shape_name.lower()

            # Resolve handler: check direct registration, then template params,
            # then config block for 'handler' field
            handler, handler_name = self._resolve_handler(
                name_lower, template_shape_params
            )
            if handler is None:
                available = ', '.join(self.get_available())
                raise ValueError(
                    f"Unknown shape study '{shape_name}'. "
                    f"No registered handler or config block found. "
                    f"Registered handlers: {available}"
                )

            # Resolve shape config: template params override config.json defaults
            shape_config = self._resolve_shape_config(
                name_lower, template_shape_params
            )

            # Recompute centroid from current state (may have been modified
            # by a previous handler in the pipeline)
            current_centroid = generator._compute_centroid(current_points)

            result = handler(
                current_points, current_centroid, bounds,
                shape_config, accumulated_metadata, generator
            )

            if not result.success:
                raise ValueError(
                    f"Shape study '{shape_name}' failed: {result.message}"
                )

            current_points = result.points

            # Merge metadata
            accumulated_metadata['shape_studies_applied'].append(shape_name)
            if 'significant_segments' in result.metadata:
                accumulated_metadata['significant_segments'].extend(
                    result.metadata['significant_segments']
                )

            # Store per-shape metadata
            accumulated_metadata[f'shape_{name_lower}'] = result.metadata

        return current_points, accumulated_metadata

    # ========================================================================
    # CONFIGURATION RESOLUTION
    # ========================================================================

    def _get_shape_config(self, shape_name: str) -> Dict[str, Any]:
        """
        Retrieve configuration for a shape study from config.procedural.shapes.

        Args:
            shape_name: Lowercase shape study name

        Returns:
            Dictionary of shape-specific parameters

        Raises:
            ValueError: If no config block exists for the shape
        """
        try:
            shapes_node = config.procedural.shapes
            shape_node = getattr(shapes_node, shape_name)
            return shape_node.to_dict()
        except AttributeError:
            raise ValueError(
                f"No configuration block found for shape study '{shape_name}'. "
                f"Expected config.procedural.shapes.{shape_name}"
            )

    def _resolve_handler(self, shape_name: str,
                         template_shape_params: Optional[Dict[str, Any]] = None):
        """
        Resolve a shape name to its handler function.

        Resolution order:
        1. Direct match in _handlers registry (e.g., 'u' -> _pre_phase_u)
        2. Template shape_params: if provided and contains a 'handler' field
        3. Config block lookup: if config.procedural.shapes.<n> exists
           and has a 'handler' field

        Args:
            shape_name: Lowercase shape study name
            template_shape_params: Optional template-provided shape parameters

        Returns:
            (handler_callable, handler_name) or (None, None) if not found
        """
        # Direct registration check
        if shape_name in self._handlers:
            return self._handlers[shape_name], shape_name

        # Check template shape_params for handler field
        if template_shape_params and shape_name in template_shape_params:
            handler_name = template_shape_params[shape_name].get('handler')
            if handler_name and handler_name in self._handlers:
                return self._handlers[handler_name], handler_name

        # Named variant: look up config block for 'handler' field
        try:
            shape_config = self._get_shape_config(shape_name)
            handler_name = shape_config.get('handler')
            if handler_name and handler_name in self._handlers:
                return self._handlers[handler_name], handler_name
        except ValueError:
            pass

        return None, None

    def _resolve_shape_config(self, shape_name: str,
                              template_shape_params: Optional[Dict[str, Any]] = None
                              ) -> Dict[str, Any]:
        """
        Resolve shape configuration with template params overriding config defaults.

        Priority: template shape_params > config.procedural.shapes.<n> > empty dict

        When template params are present, they are merged ON TOP of config defaults
        so that any parameter not specified in the template still gets its config default.

        Args:
            shape_name: Lowercase shape study name
            template_shape_params: Optional template-provided shape parameters

        Returns:
            Merged configuration dictionary
        """
        # Start with config.json defaults (if they exist)
        base_config = {}
        try:
            base_config = self._get_shape_config(shape_name)
        except ValueError:
            # No config block for this exact name - check if handler name
            # has a config block (e.g., template 'u' variant -> config 'u' defaults)
            if template_shape_params and shape_name in template_shape_params:
                handler_name = template_shape_params[shape_name].get('handler')
                if handler_name:
                    try:
                        base_config = self._get_shape_config(handler_name)
                    except ValueError:
                        pass

        # Overlay template params if present
        if template_shape_params and shape_name in template_shape_params:
            merged = base_config.copy()
            merged.update(template_shape_params[shape_name])
            return merged

        if not base_config:
            raise ValueError(
                f"No configuration found for shape study '{shape_name}'. "
                f"Provide shape_parameters in template or add "
                f"config.procedural.shapes.{shape_name}"
            )

        return base_config

    # ========================================================================
    # U-SHAPE PRE-PHASE HANDLER
    # ========================================================================

    def _pre_phase_u(self, points, centroid, bounds, shape_config,
                     accumulated_metadata, generator):
        """
        U-shape pre-phase handler.

        Process:
        1. Find a segment meeting minimum length threshold
        2. Compute reference line parallel to segment through centroid
        3. Apply U-indent: create 6 points / 5 segments
           (foot_A, inner_leg_A, crotch, inner_leg_B, foot_B)
        4. P3/P4 move inward independently with cross-centroid probability
        5. One foot randomly selected for rigid translation (extend/reduce)
        6. Validate against self-intersection, clearance, and angle checks

        Args:
            points: Current polygon points
            centroid: Pre-indent polygon centroid
            bounds: Bounding box (x1, y1, x2, y2)
            shape_config: Merged configuration dict (template over config defaults)
            accumulated_metadata: Metadata from prior shape studies
            generator: ProceduralGenerators instance for validation

        Returns:
            ShapeStudyResult
        """
        # Extract config with defaults
        min_seg_length = shape_config.get('min_segment_length', 100)
        foot_width_min = shape_config.get('foot_width_min', 0.15)
        foot_width_max = shape_config.get('foot_width_max', 0.35)
        indent_min = shape_config.get('indent_min', 0.3)
        indent_max = shape_config.get('indent_max', 0.8)
        cross_centroid_prob = shape_config.get('cross_centroid_prob', 0.3)
        foot_adjust_max = shape_config.get('foot_adjust_max', 0.5)
        foot_extend_prob = shape_config.get('foot_extend_prob', 0.5)
        foot_min_remaining = shape_config.get('foot_min_remaining', 15)
        max_retries = shape_config.get('max_retries', 10)
        polygon_retries = shape_config.get('polygon_retries', 5)
        depth_variation = shape_config.get('depth_variation', 0.3)

        # ----------------------------------------------------------------
        # Step 1: Find qualifying segment
        # ----------------------------------------------------------------
        segment_idx = self._find_qualifying_segment(
            points, min_seg_length, accumulated_metadata
        )

        if segment_idx is None:
            return ShapeStudyResult(
                points=points,
                success=False,
                message=(
                    f"No segment meets minimum length {min_seg_length}px. "
                    f"Polygon needs regeneration."
                )
            )

        n = len(points)
        p1 = points[segment_idx]
        p6 = points[(segment_idx + 1) % n]

        seg_dx = p6[0] - p1[0]
        seg_dy = p6[1] - p1[1]
        seg_length = math.sqrt(seg_dx**2 + seg_dy**2)

        # ----------------------------------------------------------------
        # Step 2: Compute reference line (parallel to segment, through centroid)
        # ----------------------------------------------------------------

        # Segment unit vector
        seg_ux = seg_dx / seg_length
        seg_uy = seg_dy / seg_length

        # Inward perpendicular (toward centroid)
        perp_x, perp_y = generator._get_perpendicular_direction(
            p1, p6, 'inward', centroid
        )

        # Distance from segment midpoint to centroid along perpendicular
        mid_x = (p1[0] + p6[0]) / 2
        mid_y = (p1[1] + p6[1]) / 2
        to_centroid_x = centroid[0] - mid_x
        to_centroid_y = centroid[1] - mid_y
        centroid_distance = abs(
            to_centroid_x * perp_x + to_centroid_y * perp_y
        )

        # ----------------------------------------------------------------
        # Steps 3-5: Apply indent with validation retry loop
        # ----------------------------------------------------------------
        for attempt in range(max_retries):
            try:
                new_points = self._apply_u_indent(
                    points, segment_idx, p1, p6,
                    seg_length, seg_ux, seg_uy, perp_x, perp_y,
                    centroid_distance, centroid,
                    foot_width_min, foot_width_max,
                    indent_min, indent_max, cross_centroid_prob,
                    depth_variation, bounds, generator
                )

                # Step 5: Foot adjustment
                new_points, foot_info = self._apply_foot_adjustment(
                    new_points, segment_idx, perp_x, perp_y,
                    centroid_distance,
                    foot_adjust_max, foot_extend_prob,
                    foot_min_remaining, bounds, generator
                )

                # Full validation
                if not generator._is_valid_polygon(new_points):
                    continue

                if config.procedural.validation.enabled:
                    if not generator._check_segment_clearance(new_points):
                        continue
                    if not generator._check_angles(new_points):
                        continue

                # Success - build metadata
                metadata = {
                    'shape_name': 'u',
                    'segment_idx': segment_idx,
                    'original_segment': (p1, p6),
                    'centroid_distance': centroid_distance,
                    'foot_adjusted': foot_info.get('foot_side', None),
                    'foot_direction': foot_info.get('direction', None),
                    'foot_displacement': foot_info.get('displacement', 0),
                    'parameters_used': {
                        'min_segment_length': min_seg_length,
                        'foot_width_min': foot_width_min,
                        'foot_width_max': foot_width_max,
                        'indent_min': indent_min,
                        'indent_max': indent_max,
                        'cross_centroid_prob': cross_centroid_prob,
                        'foot_adjust_max': foot_adjust_max,
                        'foot_extend_prob': foot_extend_prob,
                    },
                    # Significant segments: the 5 new segments of the U
                    'significant_segments': [
                        (segment_idx, segment_idx + 1),      # foot A: P1-P2
                        (segment_idx + 1, segment_idx + 2),  # inner leg A: P2-P3
                        (segment_idx + 2, segment_idx + 3),  # crotch: P3-P4
                        (segment_idx + 3, segment_idx + 4),  # inner leg B: P4-P5
                        (segment_idx + 4, segment_idx + 5),  # foot B: P5-P6
                    ],
                }

                return ShapeStudyResult(
                    points=new_points,
                    metadata=metadata,
                    success=True,
                    message=f"U-shape applied on segment {segment_idx} "
                            f"(length={seg_length:.0f}px) after {attempt + 1} attempts"
                )

            except ValueError:
                # Bounds violation or other geometric failure - retry
                continue

        # All retries exhausted
        return ShapeStudyResult(
            points=points,
            success=False,
            message=f"U-shape indent failed validation after {max_retries} attempts"
        )

    # ========================================================================
    # U-SHAPE GEOMETRY METHODS
    # ========================================================================

    def _find_qualifying_segment(self, points, min_length, accumulated_metadata):
        """
        Find a segment meeting minimum length, respecting prior shape metadata.

        Prefers the longest qualifying segment. Avoids segments marked as
        structurally significant by earlier shape studies.

        Args:
            points: Polygon points
            min_length: Minimum segment length in pixels
            accumulated_metadata: Metadata from prior shape studies

        Returns:
            Segment index or None if no segment qualifies
        """
        n = len(points)
        significant = set()

        # Build set of segment indices marked significant by prior handlers
        for seg_pair in accumulated_metadata.get('significant_segments', []):
            significant.add(seg_pair[0])

        # Find longest qualifying segment not in significant set
        best_idx = None
        best_length = 0

        for i in range(n):
            if i in significant:
                continue

            p1 = points[i]
            p2 = points[(i + 1) % n]
            length = math.sqrt(
                (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2
            )

            if length >= min_length and length > best_length:
                best_length = length
                best_idx = i

        return best_idx

    def _apply_u_indent(self, points, segment_idx, p1, p6,
                        seg_length, seg_ux, seg_uy, perp_x, perp_y,
                        centroid_distance, centroid,
                        foot_width_min, foot_width_max,
                        indent_min, indent_max, cross_centroid_prob,
                        depth_variation, bounds, generator):
        """
        Apply the U-indent to produce the 6-point / 5-segment structure.

        Original segment P1---P6 becomes:
            P1--P2--P3--P4--P5--P6

        Where:
            P1, P6 = original segment endpoints (unchanged)
            P2 = break point on foot A (on original segment line)
            P5 = break point on foot B (on original segment line)
            P3 = end of inner leg A (projected inward from P2)
            P4 = end of inner leg B (projected inward from P5)

        Segments: foot_A(P1-P2), inner_leg_A(P2-P3), crotch(P3-P4),
                  inner_leg_B(P4-P5), foot_B(P5-P6)

        Returns:
            New points list with indent applied

        Raises:
            ValueError: If any point falls outside bounds
        """
        n = len(points)

        # Compute foot widths (as parametric t values along segment)
        foot_a_width = random.uniform(foot_width_min, foot_width_max)
        foot_b_width = random.uniform(foot_width_min, foot_width_max)

        t_left = foot_a_width          # P2 position
        t_right = 1.0 - foot_b_width   # P5 position

        # Ensure the feet don't overlap (crotch must have positive width)
        if t_left >= t_right:
            raise ValueError("Feet overlap - no room for crotch")

        # P2 and P5 positions on the original segment line
        p2 = generator._round_point((
            p1[0] + t_left * (p6[0] - p1[0]),
            p1[1] + t_left * (p6[1] - p1[1])
        ))

        p5 = generator._round_point((
            p1[0] + t_right * (p6[0] - p1[0]),
            p1[1] + t_right * (p6[1] - p1[1])
        ))

        # Compute indent depth for P3 and P4
        base_depth_frac = random.uniform(indent_min, indent_max)

        # Determine if crossing centroid line is allowed
        can_cross = random.random() < cross_centroid_prob

        # Maximum depth
        if can_cross:
            max_depth = centroid_distance * 1.3
        else:
            max_depth = centroid_distance * 0.9

        base_depth = base_depth_frac * centroid_distance
        base_depth = min(base_depth, max_depth)

        # Independent depths for P3 and P4 (asymmetric crotch)
        variation = depth_variation * base_depth
        depth_p3 = base_depth + random.uniform(-variation, variation)
        depth_p4 = base_depth + random.uniform(-variation, variation)

        # Clamp depths to valid range
        min_depth = centroid_distance * indent_min * 0.5
        depth_p3 = max(min_depth, min(depth_p3, max_depth))
        depth_p4 = max(min_depth, min(depth_p4, max_depth))

        # Project P3 and P4 inward from P2 and P5 respectively
        p3 = generator._round_point((
            p2[0] + perp_x * depth_p3,
            p2[1] + perp_y * depth_p3
        ))

        p4 = generator._round_point((
            p5[0] + perp_x * depth_p4,
            p5[1] + perp_y * depth_p4
        ))

        # Bounds check all new points
        if bounds:
            for point, label in [(p2, 'P2'), (p3, 'P3'), (p4, 'P4'), (p5, 'P5')]:
                if not generator._is_within_bounds(point, bounds):
                    raise ValueError(f"U-indent {label} {point} outside bounds {bounds}")

        # Build new points list
        next_idx = (segment_idx + 1) % n

        if next_idx == 0:
            # Segment wraps around - special case
            new_points = points[:segment_idx + 1] + [p2, p3, p4, p5]
        else:
            new_points = (
                points[:segment_idx + 1] +  # everything up to and including P1
                [p2, p3, p4, p5] +           # the 4 new points
                points[next_idx:]             # P6 onward (already in points)
            )

        return new_points

    def _apply_foot_adjustment(self, points, segment_idx, perp_x, perp_y,
                               centroid_distance,
                               foot_adjust_max, foot_extend_prob,
                               foot_min_remaining, bounds, generator):
        """
        Randomly adjust one foot of the U-shape by rigid translation.

        After the indent, the point layout is:
            ..., P1, P2, P3, P4, P5, P6, ...
                 ^idx

        Foot A = P1, P2  (translate both perpendicular to original segment)
        Foot B = P5, P6  (translate both perpendicular to original segment)

        "Extend" = move outward (away from centroid) - leg gets taller
        "Reduce" = move inward (toward centroid) - leg gets shorter

        Returns:
            (new_points, foot_info_dict) tuple
        """
        # Index positions
        idx_p1 = segment_idx
        idx_p2 = segment_idx + 1
        idx_p3 = segment_idx + 2
        idx_p4 = segment_idx + 3
        idx_p5 = segment_idx + 4
        idx_p6 = segment_idx + 5

        # Current indent depth (average of inner leg lengths)
        p2 = points[idx_p2]
        p3 = points[idx_p3]
        p5_actual = points[idx_p5]

        inner_leg_a_length = math.sqrt(
            (p3[0] - p2[0])**2 + (p3[1] - p2[1])**2
        )
        inner_leg_b_length = math.sqrt(
            (points[idx_p4][0] - p5_actual[0])**2 +
            (points[idx_p4][1] - p5_actual[1])**2
        )
        avg_indent_depth = (inner_leg_a_length + inner_leg_b_length) / 2

        # Choose which foot to adjust
        foot_side = random.choice(['A', 'B'])

        # Choose direction: extend (outward) or reduce (inward)
        extending = random.random() < foot_extend_prob

        # Compute displacement magnitude
        max_displacement = foot_adjust_max * avg_indent_depth
        displacement = random.uniform(0, max_displacement)

        # For reduce: ensure minimum remaining leg length
        if not extending:
            if foot_side == 'A':
                current_leg = inner_leg_a_length
            else:
                current_leg = inner_leg_b_length

            max_reduce = current_leg - foot_min_remaining
            if max_reduce <= 0:
                return points, {
                    'foot_side': foot_side,
                    'direction': 'skipped',
                    'displacement': 0,
                    'reason': 'insufficient_leg_length'
                }
            displacement = min(displacement, max_reduce)

        # Compute displacement vector
        if extending:
            disp_x = -perp_x * displacement
            disp_y = -perp_y * displacement
        else:
            disp_x = perp_x * displacement
            disp_y = perp_y * displacement

        # Apply rigid translation to the chosen foot's two points
        new_points = list(points)

        if foot_side == 'A':
            new_p1 = generator._round_point((
                points[idx_p1][0] + disp_x,
                points[idx_p1][1] + disp_y
            ))
            new_p2 = generator._round_point((
                points[idx_p2][0] + disp_x,
                points[idx_p2][1] + disp_y
            ))

            if bounds:
                if not generator._is_within_bounds(new_p1, bounds):
                    raise ValueError(f"Foot A P1 {new_p1} outside bounds")
                if not generator._is_within_bounds(new_p2, bounds):
                    raise ValueError(f"Foot A P2 {new_p2} outside bounds")

            new_points[idx_p1] = new_p1
            new_points[idx_p2] = new_p2
        else:
            new_p5 = generator._round_point((
                points[idx_p5][0] + disp_x,
                points[idx_p5][1] + disp_y
            ))
            new_p6 = generator._round_point((
                points[idx_p6][0] + disp_x,
                points[idx_p6][1] + disp_y
            ))

            if bounds:
                if not generator._is_within_bounds(new_p5, bounds):
                    raise ValueError(f"Foot B P5 {new_p5} outside bounds")
                if not generator._is_within_bounds(new_p6, bounds):
                    raise ValueError(f"Foot B P6 {new_p6} outside bounds")

            new_points[idx_p5] = new_p5
            new_points[idx_p6] = new_p6

        foot_info = {
            'foot_side': foot_side,
            'direction': 'extend' if extending else 'reduce',
            'displacement': round(displacement, 1),
        }

        return new_points, foot_info


# =============================================================================
# Module-level singleton
# =============================================================================

_registry = ShapeStudyRegistry()


def get_shape_study_registry():
    """Get the global shape study registry."""
    return _registry