"""
Procedural generation system for Shape Studio
Provides methods for algorithmic shape creation with parameterized control
"""
import random
import math
from src.core.shape import Polygon, Line, ShapeGroup
from src.core.param_converters import CONVERTERS, choice_converter


class ProceduralGenerators:
    """Registry and dispatcher for procedural generation methods"""
    
    def __init__(self):
        # Registry maps method names to implementation functions
        self.registry = {
            'dynamic_polygon': self.dynamic_polygon,
            # Add more methods here as they're implemented:
            # 'voronoi': self.voronoi_cells,
            # 'fractal_tree': self.fractal_tree,
        }
        
        # Presets for common configurations
        self.presets = {
            'dynamic_polygon': {
                'simple': {
                    'vertices': (5, 8),
                    'iterations': 5,
                    'operations': [['split_offset', 1]],
                    'break_margin': 0.2,
                    'break_width_max': 0.3,
                    'projection_max': 1.5,
                },
                'complex': {
                    'vertices': (8, 12),
                    'iterations': 20,
                    'operations': [['split_offset', 1], ['sawtooth', 1], ['squarewave', 1]],
                    'break_margin': 0.15,
                    'break_width_max': 0.6,
                    'projection_max': 2.5,
                    'squarewave_independent_directions': True,
                    'squarewave_opposite_direction_prob': 0.3,
                },
                'organic': {
                    'vertices': (6, 10),
                    'iterations': 12,
                    'operations': [['sawtooth', 1]],
                    'break_margin': 0.2,
                    'break_width_max': 0.5,
                    'projection_max': 2.0,
                    'direction_bias': 'inward',
                },
            },
        }
        
        # Parameter specifications for each method
        self.param_specs = {
            'dynamic_polygon': {
                'vertices': {
                    'type': 'int_or_range',
                    'required': True,
                    'default': (5, 8),
                    'description': 'Number of initial vertices (int) or range (min,max)'
                },
                'bounds': {
                    'type': 'bounds',
                    'required': True,
                    'description': 'Bounding box as x1,y1,x2,y2'
                },
                'iterations': {
                    'type': 'int',
                    'required': False,
                    'default': 10,
                    'description': 'Number of evolution iterations'
                },
                'connect': {
                    'type': 'choice',
                    'choices': ['angle_sort', 'convex_hull'],
                    'required': False,
                    'default': 'angle_sort',
                    'description': 'Method for connecting initial vertices'
                },
                'operations': {
                    'type': 'weighted_list',
                    'default': [['split_offset', 1], ['sawtooth', 1], ['squarewave', 0], ['remove_point', 0], ['distort_original', 0]],
                    'choices': ['split_offset', 'sawtooth', 'squarewave', 'remove_point', 'distort_original'],
                    'description': 'List of operations with optional weights [[op, weight], ...]'
                },
                'break_margin': {
                    'type': 'float',
                    'required': False,
                    'default': 0.15,
                    'description': 'Minimum distance from segment endpoints (0.0-0.5)'
                },
                'break_width_max': {
                    'type': 'float',
                    'required': False,
                    'default': 0.5,
                    'description': 'Maximum break width as fraction of segment length (0.0-1.0)'
                },
                'projection_max': {
                    'type': 'float',
                    'required': False,
                    'default': 2.0,
                    'description': 'Maximum projection distance multiplier (0.5-5.0)'
                },
                'min_segment_length': {
                    'type': 'int',
                    'required': False,
                    'default': 10,
                    'description': 'Minimum segment length to consider for modification (pixels)'
                },
                'squarewave_independent_directions': {
                    'type': 'bool',
                    'required': False,
                    'default': False,
                    'description': 'Allow independent projection directions in squarewave'
                },
                'squarewave_opposite_direction_prob': {
                    'type': 'float',
                    'required': False,
                    'default': 0.2,
                    'description': 'Probability of opposite direction in squarewave (0.0-1.0)'
                },
                'max_retries': {
                    'type': 'int',
                    'required': False,
                    'default': 10,
                    'description': 'Max attempts per modification before skipping'
                },
                'direction_bias': {
                    'type': 'choice',
                    'choices': ['inward', 'outward', 'random'],
                    'required': False,
                    'default': 'random',
                    'description': 'Preferred direction for modifications'
                },
                'return_mode': {
                    'type': 'choice',
                    'choices': ['single', 'group', 'individual'],
                    'required': False,
                    'default': 'single',
                    'description': 'How to return result (single shape, group, or individual shapes)'
                },
                'verbose': {
                    'type': 'int',
                    'required': False,
                    'default': 0,
                    'description': 'Debug verbosity: 0=silent, 1=summary, 2=detailed, 3=full geometry'
                },
                'save_iterations': {
                    'type': 'bool',
                    'required': False,
                    'default': False,
                    'description': 'Create snapshot polygons for each iteration'
                },
                'snapshot_interval': {
                    'type': 'int',
                    'required': False,
                    'default': 1,
                    'description': 'Save every Nth iteration (use with save_iterations)'
                },
            },
        }
        
        # Documentation for each method
        self.method_docs = {
            'dynamic_polygon': {
                'description': 'Generate evolved polygon through iterative segment modification',
                'examples': [
                    'PROC dynamic_polygon shape1 VERTICES=5,8 BOUNDS=100,100,600,600',
                    'PROC dynamic_polygon shape1 PRESET=organic BOUNDS=0,0,768,768',
                    'PROC dynamic_polygon shape1 VERTICES=RAND(5,8) BOUNDS=100,100,600,600 ITERS=15',
                ],
            },
        }
    
    def call(self, method_name, shape_name, raw_params):
        """
        Generic dispatcher for procedural methods
        
        Args:
            method_name: Name of procedural method to call
            shape_name: Name (or prefix) for created shape(s)
            raw_params: Dictionary of string parameter values from script
            
        Returns:
            Single shape, ShapeGroup, or list of shapes
            
        Raises:
            ValueError: If method unknown, params invalid, or execution fails
        """
        # Validate method exists
        if method_name not in self.registry:
            available = ', '.join(sorted(self.registry.keys()))
            raise ValueError(
                f"Unknown procedural method '{method_name}'.\n"
                f"Available methods: {available}\n"
                f"Use 'LIST PROC' to see all methods."
            )
        
        # Get preset if specified (will be used as defaults)
        preset_values = {}
        if 'PRESET' in raw_params:
            preset_name = raw_params.pop('PRESET').lower()
            preset_values = self._get_preset(method_name, preset_name)
            # preset_values are already Python types, not strings
        
        # Convert and validate parameters
        spec = self.param_specs[method_name]
        converted_params = {}
        errors = []
        
        for param_name, param_config in spec.items():
            # Look for parameter in raw_params (case insensitive)
            raw_value = None
            for key in raw_params:
                if key.upper() == param_name.upper():
                    raw_value = raw_params[key]
                    break
            
            if raw_value is not None:
                # Explicit parameter provided - convert it
                try:
                    param_type = param_config['type']
                    
                    # Handle choice type specially (needs choices list)
                    if param_type == 'choice':
                        choices = param_config['choices']
                        converted_params[param_name] = choice_converter(raw_value, choices)
                    else:
                        converter = CONVERTERS[param_type]
                        converted_params[param_name] = converter(raw_value)
                        
                except Exception as e:
                    errors.append(f"Invalid value for {param_name}: '{raw_value}' ({str(e)})")
            
            elif param_name in preset_values:
                # Use preset value (already converted)
                converted_params[param_name] = preset_values[param_name]
            
            elif param_config['required']:
                # No value and no preset - required param missing
                errors.append(f"Missing required parameter: {param_name}")
            
            else:
                # Use default from spec
                converted_params[param_name] = param_config['default']
        
        # Check for unknown parameters
        known_params = set(p.upper() for p in spec.keys())
        for key in raw_params:
            if key.upper() not in known_params and key.upper() != 'PRESET':
                errors.append(f"Unknown parameter: {key}")
        
        if errors:
            raise ValueError(
                f"Parameter errors for {method_name}:\n  " + "\n  ".join(errors)
            )
        
        # Call the method
        method = self.registry[method_name]
        return method(shape_name, **converted_params)
    
    def _get_preset(self, method_name, preset_name):
        """Get preset configuration for a method"""
        if method_name not in self.presets:
            raise ValueError(f"No presets available for method '{method_name}'")
        
        if preset_name not in self.presets[method_name]:
            available = ', '.join(self.presets[method_name].keys())
            raise ValueError(
                f"Unknown preset '{preset_name}' for {method_name}.\n"
                f"Available presets: {available}"
            )
        
        return self.presets[method_name][preset_name].copy()
    
    def list_methods(self):
        """Return list of available methods with descriptions"""
        methods = []
        for name in sorted(self.registry.keys()):
            doc = self.method_docs.get(name, {})
            desc = doc.get('description', 'No description available')
            methods.append(f"{name}: {desc}")
        return methods
    
    def get_method_info(self, method_name):
        """Return detailed information about a method"""
        if method_name not in self.registry:
            raise ValueError(f"Unknown method: {method_name}")
        
        doc = self.method_docs.get(method_name, {})
        spec = self.param_specs.get(method_name, {})
        
        info = []
        info.append(f"Method: {method_name}")
        info.append(f"Description: {doc.get('description', 'No description')}")
        info.append("")
        info.append("Parameters:")
        
        for param_name, param_config in spec.items():
            required = "REQUIRED" if param_config['required'] else f"optional (default: {param_config['default']})"
            info.append(f"  {param_name}: {param_config['description']} [{required}]")
        
        if 'examples' in doc:
            info.append("")
            info.append("Examples:")
            for example in doc['examples']:
                info.append(f"  {example}")
        
        return "\n".join(info)
    
    def list_presets(self, method_name):
        """Return list of presets for a method"""
        if method_name not in self.presets:
            return f"No presets available for {method_name}"
        
        presets_info = []
        presets_info.append(f"Presets for {method_name}:")
        
        for preset_name, preset_config in self.presets[method_name].items():
            presets_info.append(f"  {preset_name}:")
            for key, value in preset_config.items():
                presets_info.append(f"    {key}: {value}")
        
        return "\n".join(presets_info)
    
    # ========================================================================
    # PROCEDURAL METHOD IMPLEMENTATIONS
    # ========================================================================
    
    def dynamic_polygon(self, name, vertices, bounds, iterations=10,
                       connect='angle_sort', operations=None,
                       break_margin=0.15, break_width_max=0.5, projection_max=2.0,
                       max_retries=15, direction_bias='random',
                       squarewave_independent_directions=False,
                       squarewave_opposite_direction_prob=0.2,
                       min_segment_length=10,
                       return_mode='single', verbose=0,
                       save_iterations=False, snapshot_interval=1):
        """
        Generate evolved polygon through iterative segment modification.
        
        Algorithm:
        1. Generate random vertices in bounds
        2. Connect them via angle_sort or convex_hull
        3. Initialize segment weights (all equal)
        4. For each iteration:
           - Select segment (weighted random)
           - Choose operation (random from allowed list)
           - Apply operation with retries until valid
           - Update weights (new segments get reduced weight)
        5. Return final polygon with metadata
        
        Args:
            name: Shape name (or prefix if return_mode='individual')
            vertices: Number of vertices (int) or range (tuple)
            bounds: Bounding box (x1, y1, x2, y2)
            iterations: Number of evolution steps
            connect: Initial connection method ('angle_sort' or 'convex_hull')
            operations: List of allowed operations
            depth_range: Depth as percentage (float) or range (tuple)
            max_retries: Max attempts per modification
            direction_bias: Preferred direction ('inward', 'outward', 'random')
            return_mode: How to return ('single', 'group', 'individual')
            verbose: Debug verbosity (0=silent, 1=summary, 2=detailed, 3=full)
            save_iterations: Create snapshot polygons for each iteration
            snapshot_interval: Save every Nth iteration
            
        Returns:
            Polygon object or list of Polygons (if save_iterations=True)
        """
        if operations is None:
            operations = ['split_offset', 'sawtooth']
        
        # Handle range parameters - choose randomly if tuple
        num_vertices = random.randint(*vertices) if isinstance(vertices, tuple) else vertices
        
        # PHASE 1: Generate initial vertices
        initial_points = self._generate_initial_vertices(num_vertices, bounds)
        
        # PHASE 2: Connect vertices into polygon
        connected_points = self._connect_vertices(initial_points, connect)
        
        # Round all initial points to integer pixel coordinates
        connected_points = [self._round_point(p) for p in connected_points]
        
        # Track original vertices for distort_original operation
        # This is a separate list that only contains vertices from initial construction
        distortable_points = connected_points[:]  # Independent copy
        
        # Initialize debug log
        debug_log = None
        if verbose > 0:
            debug_log = {
                'verbose_level': verbose,
                'initial_state': {
                    'vertex_count': num_vertices,
                    'bounds': bounds,
                    'points': connected_points[:] if verbose >= 3 else None,
                    'centroid': self._compute_centroid(connected_points),
                    'connection_method': connect
                },
                'iterations': [],
                'summary': {
                    'successful_modifications': 0,
                    'failed_attempts': 0,
                    'operations_used': {op: 0 for op in operations}
                }
            }
        
        # PHASE 3: Evolution loop (segment selection now based on length)        
        
        # PHASE 4: Evolution loop
        stats = {
            'successful_modifications': 0,
            'failed_attempts': 0,
            'operations_used': {op: 0 for op, weight in operations}
        }
        
        current_points = connected_points[:]
        centroid = self._compute_centroid(current_points)
        
        # For snapshots
        snapshots = []
        if save_iterations:
            # Save initial state as iteration 0
            snapshot = Polygon(f"{name}_iter_0", current_points[:])
            snapshot.attrs['procedure'] = {
                'method': 'dynamic_polygon',
                'is_snapshot': True,
                'snapshot_of': name,
                'iteration': 0,
                'stats': stats.copy()
            }
            snapshots.append(snapshot)
        
        for iteration in range(iterations):
            # Select a segment using length-based selection (skip too-short segments)
            segment_idx = self._select_segment(current_points, min_segment_length)
            
            # WEIGHTED OPERATION SELECTION
            # operations is now a list of [operation_name, weight] pairs
            # Filter to only operations with positive weights
            eligible_ops = [(op, weight) for op, weight in operations if weight > 0]

            if not eligible_ops:
                raise ValueError("No operations with positive weights available")

            # Weighted random selection
            op_names = [op for op, weight in eligible_ops]
            op_weights = [weight for op, weight in eligible_ops]
            operation = random.choices(op_names, weights=op_weights)[0]

            # Prepare iteration log entry
            iter_log = None
            if verbose >= 2:
                n = len(current_points)
                p1 = current_points[segment_idx]
                p2 = current_points[(segment_idx + 1) % n]
                seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                
                # Compute total perimeter for probability calculation
                total_perimeter = sum(
                    math.sqrt((current_points[i][0] - current_points[(i+1)%n][0])**2 +
                             (current_points[i][1] - current_points[(i+1)%n][1])**2)
                    for i in range(n)
                )
                
                iter_log = {
                    'iteration': iteration + 1,
                    'selection': {
                        'segment_idx': segment_idx,
                        'segment_endpoints': [p1, p2] if verbose >= 3 else None,
                        'segment_length': round(seg_length, 1),
                        'selection_probability': round(seg_length / total_perimeter, 3) if total_perimeter > 0 else 0
                    },
                    'operation': {
                        'name': operation,
                    }
                }

            # Attempt modification with retries
            success = False
            attempt_count = 0
            points_before_op = len(current_points)
            
            for attempt in range(max_retries):
                attempt_count += 1
                try:
                    # Apply the operation (returns pair)
                    new_points, new_distortable = self._apply_operation(
                        current_points, segment_idx,
                        operation, break_margin, break_width_max, projection_max,
                        direction_bias, centroid, bounds, distortable_points,
                        squarewave_independent_directions, squarewave_opposite_direction_prob
                    )
                    
                    # Validate: check for self-intersections
                    if self._is_valid_polygon(new_points):
                        # Success! Update state
                        current_points = new_points
                        distortable_points = new_distortable

                        centroid = self._compute_centroid(current_points)  # Update centroid
                        stats['successful_modifications'] += 1
                        stats['operations_used'][operation] += 1
                        success = True
                        
                        # Log successful operation details
                        if verbose >= 2 and iter_log:
                            # Get the new point(s) that were added
                            if operation == 'split_offset':
                                new_point = current_points[segment_idx + 1]
                                iter_log['operation']['new_point'] = new_point if verbose >= 3 else None
                            
                            # Add result info
                            if verbose >= 3:
                                iter_log['result'] = {
                                    'point_count': len(new_points),
                                    'validation': 'PASS',
                                    'new_points': new_points[:] if verbose >= 3 else None,
                                }                        
                            
                            # Add direction info
                            n = len(current_points) - (len(current_points) - len(new_points))
                            if segment_idx < len(current_points) - 1:
                                perp_x, perp_y = self._get_perpendicular_direction(
                                    current_points[segment_idx], 
                                    current_points[segment_idx + 1],
                                    direction_bias, 
                                    centroid
                                )
                                # Determine if it's inward or outward
                                p1 = current_points[segment_idx]
                                p2 = current_points[segment_idx + 1]
                                mx = (p1[0] + p2[0]) / 2
                                my = (p1[1] + p2[1]) / 2
                                to_mid_x = mx - centroid[0]
                                to_mid_y = my - centroid[1]
                                dot = perp_x * to_mid_x + perp_y * to_mid_y
                                
                                iter_log['operation']['direction'] = 'outward' if dot > 0 else 'inward'
                                if verbose >= 3:
                                    iter_log['operation']['direction_vector'] = (round(perp_x, 2), round(perp_y, 2))
                        
                        break
                    else:
                        stats['failed_attempts'] += 1
                        
                except Exception as e:
                    # Operation failed (e.g., degenerate geometry)
                    stats['failed_attempts'] += 1
            
            # Log iteration result
            if verbose >= 2 and iter_log:
                iter_log['result'] = {
                    'points_before': points_before_op if success else len(current_points),
                    'points_after': len(current_points),
                    'validation_attempts': attempt_count,
                    'validation_result': 'PASS' if success else 'FAIL',
                    'intersection_count': 0 if success else '?',
                }
                debug_log['iterations'].append(iter_log)
            
            # Update summary stats in debug log
            if verbose > 0:
                debug_log['summary'] = stats.copy()
            
            # Save iteration snapshot
            if save_iterations and ((iteration + 1) % snapshot_interval == 0):
                snapshot = Polygon(f"{name}_iter_{iteration + 1}", current_points[:])
                snapshot.attrs['procedure'] = {
                    'method': 'dynamic_polygon',
                    'is_snapshot': True,
                    'snapshot_of': name,
                    'iteration': iteration + 1,
                    'stats': stats.copy()
                }
                snapshots.append(snapshot)
        
        # PHASE 5: Create final polygon
        polygon = Polygon(name, current_points)
        
        # Add metadata about generation
        polygon.attrs['procedure'] = {
            'method': 'dynamic_polygon',
            'parameters': {
                'vertices': vertices,
                'bounds': bounds,
                'iterations': iterations,
                'operations': operations,
                'connect': connect,
                'break_margin': break_margin,
                'break_width_max': break_width_max,
                'projection_max': projection_max,
                'min_segment_length': min_segment_length,
                'squarewave_independent_directions': squarewave_independent_directions,
                'squarewave_opposite_direction_prob': squarewave_opposite_direction_prob,
                'direction_bias': direction_bias,
                'verbose': verbose,
                'save_iterations': save_iterations,
            },
            'statistics': stats
        }
        
        # Add debug log if verbose
        if debug_log:
            polygon.attrs['procedure']['debug_log'] = debug_log
        
        # Return based on save_iterations
        if save_iterations:
            # Add final snapshot
            final_snapshot = Polygon(f"{name}_final", current_points[:])
            final_snapshot.attrs = polygon.attrs.copy()
            final_snapshot.attrs['procedure']['is_final'] = True
            snapshots.append(final_snapshot)
            
            # Return list: snapshots + main polygon
            return snapshots + [polygon]
        else:
            return polygon
    
    # ========================================================================
    # DYNAMIC POLYGON HELPER METHODS
    # ========================================================================
    
    def _generate_initial_vertices(self, count, bounds):
        """Generate random points within bounds.
        
        Args:
            count: Number of vertices to generate
            bounds: (x1, y1, x2, y2) bounding box
            
        Returns:
            List of (x, y) tuples
        """
        x1, y1, x2, y2 = bounds
        points = []
        for i in range(count):
            x = random.uniform(x1, x2)
            y = random.uniform(y1, y2)
            points.append((x, y))
        return points
    
    def _connect_vertices(self, points, method):
        """Connect vertices into a polygon using specified method.
        
        Args:
            points: List of (x, y) tuples
            method: 'angle_sort' or 'convex_hull'
            
        Returns:
            Ordered list of points forming a polygon
        """
        if method == 'angle_sort':
            return self._connect_angle_sort(points)
        elif method == 'convex_hull':
            return self._connect_convex_hull(points)
        else:
            raise ValueError(f"Unknown connection method: {method}")
    
    def _connect_angle_sort(self, points):
        """Sort points by angle from centroid.
        
        This creates a star-like polygon that may be concave.
        
        Args:
            points: List of (x, y) tuples
            
        Returns:
            Sorted list of points
        """
        # Compute centroid
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        
        # Sort by angle from centroid
        sorted_points = sorted(points, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
        
        return sorted_points
    
    def _connect_convex_hull(self, points):
        """Connect points using convex hull algorithm (Graham scan).
        
        This creates a convex polygon.
        
        Args:
            points: List of (x, y) tuples
            
        Returns:
            Points forming convex hull
        """
        # TODO: Implement full Graham scan
        # For now, use angle sort (which approximates convex hull for random points)
        return self._connect_angle_sort(points)
    
    def _compute_centroid(self, points):
        """Compute centroid of polygon.
        
        Args:
            points: List of (x, y) tuples
            
        Returns:
            (cx, cy) tuple
        """
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        return (cx, cy)
    
    def _select_segment(self, points, min_segment_length=10):
        """Select a segment index using length-based weighted random selection.
        
        Longer segments are more likely to be selected, creating natural
        spreading behavior as long segments get split into shorter ones.
        Segments shorter than min_segment_length are excluded from selection.
        
        Args:
            points: List of (x, y) polygon vertices
            min_segment_length: Minimum segment length to consider (pixels)
            
        Returns:
            Selected segment index (0 to len-1)
            
        Raises:
            ValueError: If no segments meet minimum length requirement
        """
        # Compute all segment lengths
        n = len(points)
        lengths = []
        eligible_indices = []
        
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            lengths.append(length)
            
            # Track segments that meet minimum length
            if length >= min_segment_length:
                eligible_indices.append(i)
        
        # If no segments meet minimum, use all segments
        if not eligible_indices:
            eligible_indices = list(range(n))
        
        # Weighted random selection by length (only from eligible segments)
        eligible_lengths = [lengths[i] for i in eligible_indices]
        total_length = sum(eligible_lengths)
        
        if total_length == 0:
            # All segments have zero length (degenerate case)
            return random.randint(0, n - 1)
        
        r = random.uniform(0, total_length)
        cumulative = 0
        for idx, length in zip(eligible_indices, eligible_lengths):
            cumulative += length
            if r <= cumulative:
                return idx
        
        # Fallback
        return eligible_indices[-1] if eligible_indices else n - 1
    
    def _apply_operation(self, points, segment_idx, operation,
                        break_margin, break_width_max, projection_max,
                        direction_bias, centroid, bounds=None,
                        distortable_points=None,
                        squarewave_independent_directions=False,
                        squarewave_opposite_prob=0.2):
        """Apply a modification operation to a segment.
        
        Args:
            points: Current polygon points
            segment_idx: Index of segment to modify
            operation: Operation name
            break_margin: Minimum distance from endpoints (0.0-0.5)
            break_width_max: Maximum break width as fraction of segment
            projection_max: Maximum projection distance multiplier
            direction_bias: 'inward', 'outward', or 'random'
            centroid: Polygon centroid (cx, cy)
            bounds: Bounding box (x1, y1, x2, y2) for validation
            distortable_points: List of original vertices (for distort_original)
            squarewave_independent_directions: Allow independent directions in squarewave
            squarewave_opposite_prob: Probability of opposite direction
            
        Returns:
            (new_points, new_distortable_points) tuple
        """
        if operation == 'split_offset':
            new_points = self._op_split_offset(points, segment_idx, 
                                        break_margin, break_width_max, projection_max,
                                        direction_bias, centroid, bounds)
            return new_points, distortable_points
            
        elif operation == 'sawtooth':
            new_points = self._op_sawtooth(points, segment_idx,
                                    break_margin, break_width_max, projection_max,
                                    direction_bias, centroid, bounds)
            return new_points, distortable_points
            
        elif operation == 'squarewave':
            new_points = self._op_squarewave(points, segment_idx,
                                      break_margin, break_width_max, projection_max,
                                      direction_bias, centroid, bounds,
                                      squarewave_independent_directions,
                                      squarewave_opposite_prob)
            return new_points, distortable_points
        
        elif operation == 'remove_point':
            return self._op_remove_point(points, segment_idx, 
                                         break_margin, break_width_max, projection_max,
                                         direction_bias, centroid, bounds,
                                         distortable_points)
                                         
        elif operation == 'distort_original':
            return self._op_distort_original(points, segment_idx,
                                             break_margin, break_width_max, projection_max,
                                             direction_bias, centroid, bounds,
                                             distortable_points)
    
    def _op_split_offset(self, points, idx, break_margin, break_width_max, 
                        projection_max, direction_bias, centroid, bounds=None):
        """Split segment and offset a random point perpendicular to segment.
        
        Operation: A---B becomes A---M---B where M is at random position, offset perpendicular
        
        Args:
            points: Current polygon points
            idx: Segment index to modify
            break_margin: Minimum distance from endpoints (0.0-0.5)
            break_width_max: Maximum break width as fraction of segment (unused for single point)
            projection_max: Maximum projection distance multiplier
            direction_bias: Direction preference
            centroid: Polygon centroid
            bounds: Optional bounding box (x1, y1, x2, y2) for validation
            
        Returns:
            new_points list
            
        Raises:
            ValueError: If new point is outside bounds
        """
        n = len(points)
        p1 = points[idx]
        p2 = points[(idx + 1) % n]
        
        # Compute segment length
        seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        # Random break position (respecting margins)
        t = random.uniform(break_margin, 1.0 - break_margin)
        break_x = p1[0] + t * (p2[0] - p1[0])
        break_y = p1[1] + t * (p2[1] - p1[1])
        
        # Get perpendicular direction
        perp_x, perp_y = self._get_perpendicular_direction(p1, p2, direction_bias, centroid)
        
        # Random break width (for depth calculation)
        break_width = random.uniform(0, break_width_max * seg_length)
        
        # Random projection distance (up to projection_max times break_width)
        offset_dist = random.uniform(0, projection_max * max(break_width, seg_length * 0.1))

        # New point offset perpendicular from break position
        new_x = break_x + perp_x * offset_dist
        new_y = break_y + perp_y * offset_dist
        new_point = (new_x, new_y)

        # Round to integer pixel coordinates
        new_point = self._round_point(new_point)
        
        # Check bounds if provided
        if bounds and not self._is_within_bounds(new_point, bounds):
            raise ValueError(f"Point {new_point} outside bounds {bounds}")
        
        # Insert new point
        new_points = points[:idx+1] + [new_point] + points[idx+1:]
        
        return new_points
    
    def _op_sawtooth(self, points, idx, break_margin, break_width_max,
                    projection_max, direction_bias, centroid, bounds=None):
        """Create sawtooth pattern with randomized position, width, and depth.
        
        Operation: triangular protrusion with variable characteristics
        
        Creates a triangular tooth with:
        - Random center position (within margins)
        - Random base width (up to break_width_max)
        - Random peak projection (up to projection_max * break_width)
        
        Args:
            points: Current polygon points
            idx: Segment index to modify
            break_margin: Minimum distance from endpoints (0.0-0.5)
            break_width_max: Maximum break width as fraction of segment length
            projection_max: Maximum projection distance multiplier
            direction_bias: Direction preference ('inward', 'outward', 'random')
            centroid: Polygon centroid (cx, cy)
            bounds: Optional bounding box (x1, y1, x2, y2) for validation
            
        Returns:
            new_points list
            
        Raises:
            ValueError: If any new point is outside bounds
        """
        n = len(points)
        p1 = points[idx]
        p2 = points[(idx + 1) % n]
        
        # Compute segment length
        seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        # Random break center position (respecting margins)
        t_center = random.uniform(break_margin, 1.0 - break_margin)
        center_x = p1[0] + t_center * (p2[0] - p1[0])
        center_y = p1[1] + t_center * (p2[1] - p1[1])
        
        # Random break width (clamped to available space)
        max_width = min(break_width_max * seg_length, 
                       min(t_center, 1.0 - t_center) * seg_length * 2)
        break_width = random.uniform(0, max_width)
        half_width = break_width / 2
        
        # Base points at center +/- half_width
        # Convert half_width to parametric distance
        t_delta = half_width / seg_length
        t_left = t_center - t_delta
        t_right = t_center + t_delta
        
        base_left_x = p1[0] + t_left * (p2[0] - p1[0])
        base_left_y = p1[1] + t_left * (p2[1] - p1[1])
        base_left = (base_left_x, base_left_y)
        
        base_right_x = p1[0] + t_right * (p2[0] - p1[0])
        base_right_y = p1[1] + t_right * (p2[1] - p1[1])
        base_right = (base_right_x, base_right_y)
        
        # Get perpendicular direction
        perp_x, perp_y = self._get_perpendicular_direction(p1, p2, direction_bias, centroid)
        
        # Random projection distance (up to projection_max * break_width)
        # Ensure minimum projection even with small break_width
        min_projection = seg_length * 0.05
        max_projection = projection_max * max(break_width, min_projection)
        offset_dist = random.uniform(min_projection, max_projection)
        
        # Peak point (offset perpendicular from center)
        peak_x = center_x + perp_x * offset_dist
        peak_y = center_y + perp_y * offset_dist
        peak = (peak_x, peak_y)
        
        # Round all points to integer pixel coordinates
        base_left = self._round_point(base_left)
        peak = self._round_point(peak)
        base_right = self._round_point(base_right)
        
        # Check bounds if provided
        if bounds:
            for point in [base_left, peak, base_right]:
                if not self._is_within_bounds(point, bounds):
                    raise ValueError(f"Point {point} outside bounds {bounds}")
        
        # Insert THREE points: left base, peak, right base
        new_points = points[:idx+1] + [base_left, peak, base_right] + points[idx+1:]
        
        return new_points
    
    def _op_squarewave(self, points, idx, break_margin, break_width_max,
                      projection_max, direction_bias, centroid, bounds=None,
                      independent_directions=False, opposite_prob=0.2):
        """Create square wave pattern with randomized characteristics and optional asymmetry.
        
        Operation: A---B becomes A--[_]--B (rectangular/trapezoidal protrusion)
        
        Creates a rectangular or trapezoidal shape with:
        - Random center position (within margins)
        - Random base width (up to break_width_max)
        - Two independent projection points (optionally different directions/depths)
        
        The top points are connected to the nearest base points, preventing self-intersection.
        
        Args:
            points: Current polygon points
            idx: Segment index to modify
            break_margin: Minimum distance from endpoints (0.0-0.5)
            break_width_max: Maximum break width as fraction of segment length
            projection_max: Maximum projection distance multiplier
            direction_bias: Direction preference (baseline for both projections)
            centroid: Polygon centroid (cx, cy)
            bounds: Optional bounding box (x1, y1, x2, y2) for validation
            independent_directions: If True, each projection can have different direction
            opposite_prob: Probability of opposite direction when independent (0.0-1.0)
            
        Returns:
            new_points list
            
        Raises:
            ValueError: If any new point is outside bounds
        """
        n = len(points)
        p1 = points[idx]
        p2 = points[(idx + 1) % n]
        
        # Compute segment length
        seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        # Random break center position (respecting margins)
        t_center = random.uniform(break_margin, 1.0 - break_margin)
        center_x = p1[0] + t_center * (p2[0] - p1[0])
        center_y = p1[1] + t_center * (p2[1] - p1[1])
        
        # Random break width (clamped to available space)
        max_width = min(break_width_max * seg_length, 
                       min(t_center, 1.0 - t_center) * seg_length * 2)
        break_width = random.uniform(0, max_width)
        half_width = break_width / 2
        
        # Base points at center +/- half_width
        t_delta = half_width / seg_length
        t_left = t_center - t_delta
        t_right = t_center + t_delta
        
        base_left_x = p1[0] + t_left * (p2[0] - p1[0])
        base_left_y = p1[1] + t_left * (p2[1] - p1[1])
        
        base_right_x = p1[0] + t_right * (p2[0] - p1[0])
        base_right_y = p1[1] + t_right * (p2[1] - p1[1])
        
        # Get base perpendicular direction
        perp_x, perp_y = self._get_perpendicular_direction(p1, p2, direction_bias, centroid)
        
        # Determine directions for each projection
        if independent_directions:
            # Left projection direction
            if random.random() < opposite_prob:
                left_perp_x, left_perp_y = -perp_x, -perp_y
            else:
                left_perp_x, left_perp_y = perp_x, perp_y
            
            # Right projection direction
            if random.random() < opposite_prob:
                right_perp_x, right_perp_y = -perp_x, -perp_y
            else:
                right_perp_x, right_perp_y = perp_x, perp_y
        else:
            # Both projections use same direction
            left_perp_x, left_perp_y = perp_x, perp_y
            right_perp_x, right_perp_y = perp_x, perp_y
        
        # Random projection distances (independent for each side)
        min_projection = seg_length * 0.05
        max_projection = projection_max * max(break_width, min_projection)
        
        left_offset = random.uniform(min_projection, max_projection)
        right_offset = random.uniform(min_projection, max_projection)
        
        # Projected points
        top_left_x = base_left_x + left_perp_x * left_offset
        top_left_y = base_left_y + left_perp_y * left_offset
        
        top_right_x = base_right_x + right_perp_x * right_offset
        top_right_y = base_right_y + right_perp_y * right_offset
        
        # Create all four corner points
        # Order: base_left -> top_left -> top_right -> base_right
        # This creates proper connections (left base to left top, right top to right base)
        base_left = (base_left_x, base_left_y)
        top_left = (top_left_x, top_left_y)
        top_right = (top_right_x, top_right_y)
        base_right = (base_right_x, base_right_y)
        
        # Round all points to integer pixel coordinates
        base_left = self._round_point(base_left)
        top_left = self._round_point(top_left)
        top_right = self._round_point(top_right)
        base_right = self._round_point(base_right)
        
        # Check bounds if provided
        if bounds:
            for point in [base_left, top_left, top_right, base_right]:
                if not self._is_within_bounds(point, bounds):
                    raise ValueError(f"Point {point} outside bounds {bounds}")
        
        # Insert all four corner points in proper order
        new_points = points[:idx+1] + [base_left, top_left, top_right, base_right] + points[idx+1:]
        
        return new_points
    
    def _op_remove_point(self, points, idx, break_margin, break_width_max, projection_max,
                        direction_bias, centroid, bounds=None,
                        distortable_points=None):
        """Remove a vertex, merging two adjacent segments into one.
        
        Operation: A---B---C becomes A-------C (removes B)
        
        Args:
            points: Current polygon points
            idx: Vertex index to remove (selected by weighted random)
            depth_pct: Unused (for signature compatibility)
            direction_bias: Unused (for signature compatibility)
            centroid: Unused (for signature compatibility)
            bounds: Unused (for signature compatibility)
            distortable_points: List of original vertices (will be updated if removed point is original)
            
        Returns:
            (new_points, new_distortable_points) tuple
            
        Raises:
            ValueError: If polygon would have too few vertices
        """
        if len(points) <= 3:
            raise ValueError("Cannot remove point - polygon must have at least 3 vertices")
        
        # Get the point being removed
        removed_point = points[idx]
        
        # Remove the vertex from points
        new_points = points[:idx] + points[idx+1:]
        
        # Update distortable_points if this was an original vertex
        new_distortable = distortable_points[:] if distortable_points else []
        if removed_point in new_distortable:
            new_distortable.remove(removed_point)
        
        return new_points, new_distortable
    
    def _op_distort_original(self, points, idx, break_margin, break_width_max, projection_max,
                            direction_bias, centroid, bounds=None,
                            distortable_points=None):
        """Move an original vertex toward or away from centroid.
        
        This operation only works on vertices from the initial polygon construction.
        The vertex moves along the line from centroid to its current position.
        
        Args:
            points: Current polygon points
            idx: IGNORED - we select randomly from distortable_points instead
            break_margin: IGNORED - not applicable to this operation
            break_width_max: IGNORED - not applicable to this operation
            projection_max: Controls movement distance (as fraction of centroid distance)
            direction_bias: 'inward' (toward centroid) or 'outward' (away from centroid)
            centroid: Polygon centroid
            bounds: Bounding box (x1, y1, x2, y2) for validation
            distortable_points: List of original vertices (REQUIRED)
            
        Returns:
            (new_points, new_distortable_points) tuple
            
        Raises:
            ValueError: If no distortable points available or new point outside bounds
        """
        if not distortable_points or len(distortable_points) == 0:
            raise ValueError("No distortable points available")
        
        # Select a random point from distortable_points
        old_coord = random.choice(distortable_points)
        
        # Find this point in the current points list
        try:
            point_idx = points.index(old_coord)
        except ValueError:
            raise ValueError(f"Distortable point {old_coord} not found in current polygon")
        
        # Vector from centroid to point
        dx = old_coord[0] - centroid[0]
        dy = old_coord[1] - centroid[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            # Point is at centroid - can't move
            return points[:], distortable_points[:]
        
        # Normalize direction
        dir_x = dx / distance
        dir_y = dy / distance
        
        # Movement distance - use projection_max to control distortion amount
        # Scale by random factor (10-30% of distance) times projection_max
        move_fraction = random.uniform(0.1, 0.3) * projection_max
        move_dist = distance * move_fraction
        
        # Apply direction bias
        if direction_bias == 'inward':
            # Move toward centroid (negative direction)
            new_x = old_coord[0] - dir_x * move_dist
            new_y = old_coord[1] - dir_y * move_dist
        else:  # outward or random
            # Move away from centroid (positive direction)
            new_x = old_coord[0] + dir_x * move_dist
            new_y = old_coord[1] + dir_y * move_dist
        
        new_coord = (new_x, new_y)
        
        # Round to integer pixel coordinates
        new_coord = self._round_point(new_coord)
        
        # Check bounds if provided
        if bounds and not self._is_within_bounds(new_coord, bounds):
            raise ValueError(f"Point {new_coord} outside bounds {bounds}")
        
        # Update points list
        new_points = list(points)
        new_points[point_idx] = new_coord

        # Update distortable_points - replace old coord with new coord
        distort_idx = distortable_points.index(old_coord)
        new_distortable = distortable_points[:distort_idx] + [new_coord] + distortable_points[distort_idx+1:]
        
        return new_points, new_distortable
    
    def _is_valid_polygon(self, points):
        """Check if polygon is valid (no self-intersections).
        
        Args:
            points: List of (x, y) tuples
            
        Returns:
            True if valid, False if self-intersecting
        """
        n = len(points)
        if n < 3:
            return False
        
        # Check each edge against all non-adjacent edges
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            
            # Check against all edges that are not adjacent
            for j in range(i + 2, n):
                # Skip if we're checking the last edge against the first
                if i == 0 and j == n - 1:
                    continue
                    
                p3 = points[j]
                p4 = points[(j + 1) % n]
                
                if self._segments_intersect(p1, p2, p3, p4):
                    return False
        
        return True
    
    def _segments_intersect(self, p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects p3-p4.
        
        Uses cross product method to determine intersection.
        
        Args:
            p1, p2: Endpoints of first segment
            p3, p4: Endpoints of second segment
            
        Returns:
            True if segments intersect (excluding endpoint touches)
        """
        def ccw(A, B, C):
            """Check if three points are in counter-clockwise order"""
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        # Segments intersect if endpoints are on opposite sides
        return (ccw(p1, p3, p4) != ccw(p2, p3, p4) and 
                ccw(p1, p2, p3) != ccw(p1, p2, p4))
    
    def _get_perpendicular_direction(self, p1, p2, bias, centroid):
        """Get perpendicular direction vector for a segment.
        
        Args:
            p1, p2: Segment endpoints
            bias: 'inward', 'outward', or 'random'
            centroid: Polygon centroid
            
        Returns:
            (dx, dy) normalized perpendicular vector
        """
        # Segment direction
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        # Perpendicular (rotate 90 degrees counter-clockwise)
        perp_x = -dy
        perp_y = dx
        
        # Normalize
        length = math.sqrt(perp_x**2 + perp_y**2)
        if length > 0:
            perp_x /= length
            perp_y /= length
        
        # Segment midpoint
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        
        # Vector from centroid to midpoint
        to_mid_x = mx - centroid[0]
        to_mid_y = my - centroid[1]
        
        # Dot product tells us if perpendicular points outward or inward
        dot = perp_x * to_mid_x + perp_y * to_mid_y
        
        # Apply bias
        if bias == 'inward':
            # Want to point toward centroid (negative dot product)
            if dot > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        elif bias == 'outward':
            # Want to point away from centroid (positive dot product)
            if dot < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        elif bias == 'random':
            # 50/50 chance to flip
            if random.random() < 0.5:
                perp_x = -perp_x
                perp_y = -perp_y
        
        return (perp_x, perp_y)
    
    def _round_point(self, point):
        """Round point to integer pixel coordinates.
        
        Points are stored as floats for intermediate calculations,
        but represent integer pixel positions.
        
        Args:
            point: (x, y) tuple with float values
            
        Returns:
            (x, y) tuple with values rounded to nearest integer (as floats)
        """
        return (round(point[0]), round(point[1]))
    
    def _is_within_bounds(self, point, bounds):
        """Check if point is within bounding rectangle.
        
        Args:
            point: (x, y) tuple
            bounds: (x1, y1, x2, y2) rectangle
            
        Returns:
            True if point is inside bounds
        """
        x, y = point
        x1, y1, x2, y2 = bounds
        return x1 <= x <= x2 and y1 <= y <= y2