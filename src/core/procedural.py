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
                    'operations': ['split_offset'],
                    'depth_range': (0.2, 0.6),
                },
                'complex': {
                    'vertices': (8, 12),
                    'iterations': 20,
                    'operations': ['split_offset', 'sawtooth', 'squarewave'],
                    'depth_range': (0.3, 0.9),
                    'weight_decay': 0.3,
                },
                'organic': {
                    'vertices': (6, 10),
                    'iterations': 15,
                    'operations': ['sawtooth'],
                    'depth_range': (0.3, 0.8),
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
                    'type': 'list',
                    'required': False,
                    'default': ['split_offset', 'sawtooth'],
                    'description': 'Allowed modification operations (comma-separated)'
                },
                'depth_range': {
                    'type': 'float_or_range',
                    'required': False,
                    'default': (0.2, 0.8),
                    'description': 'Depth as percentage (float) or range (min,max)'
                },
                'weight_decay': {
                    'type': 'float',
                    'required': False,
                    'default': 0.5,
                    'description': 'Multiplier for split segment weights (0.0-1.0)'
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
                       depth_range=(0.2, 0.8), weight_decay=0.5,
                       max_retries=10, direction_bias='random',
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
            weight_decay: Multiplier for split segment weights (0.0-1.0)
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
        
        # PHASE 3: Initialize segment weights (all segments start equal)
        segment_weights = [1.0] * len(connected_points)
        
        # PHASE 4: Evolution loop
        stats = {
            'successful_modifications': 0,
            'failed_attempts': 0,
            'operations_used': {op: 0 for op in operations}
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
            # Choose depth for this iteration
            depth_pct = random.uniform(*depth_range) if isinstance(depth_range, tuple) else depth_range
            
            # Select a segment using weighted random selection
            segment_idx = self._select_segment(segment_weights)
            
            # Choose a random operation
            operation = random.choice(operations)
            
            # Prepare iteration log entry
            iter_log = None
            if verbose >= 2:
                n = len(current_points)
                p1 = current_points[segment_idx]
                p2 = current_points[(segment_idx + 1) % n]
                seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                total_weight = sum(segment_weights)
                
                iter_log = {
                    'iteration': iteration + 1,
                    'selection': {
                        'segment_idx': segment_idx,
                        'segment_endpoints': [p1, p2] if verbose >= 3 else None,
                        'segment_weight': segment_weights[segment_idx],
                        'segment_length': round(seg_length, 1),
                        'selection_probability': round(segment_weights[segment_idx] / total_weight, 3) if total_weight > 0 else 0
                    },
                    'operation': {
                        'name': operation,
                        'depth_pct': round(depth_pct, 2),
                        'depth_pixels': round(seg_length * depth_pct, 1),
                    }
                }
            
            # Attempt modification with retries
            success = False
            attempt_count = 0
            
            for attempt in range(max_retries):
                attempt_count += 1
                try:
                    # Apply the operation
                    new_points, new_weights = self._apply_operation(
                        current_points, segment_weights, segment_idx,
                        operation, depth_pct, direction_bias, centroid, weight_decay
                    )
                    
                    # Validate: check for self-intersections
                    if self._is_valid_polygon(new_points):
                        # Success! Update state
                        current_points = new_points
                        segment_weights = new_weights
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
                points_before = len(current_points) - (len(current_points) - len(connected_points)) if not success else len(current_points) - 1
                iter_log['result'] = {
                    'points_before': points_before if success else len(current_points),
                    'points_after': len(current_points),
                    'validation_attempts': attempt_count,
                    'validation_result': 'PASS' if success else 'FAIL',
                    'intersection_count': 0 if success else '?',
                    'new_weights': new_weights[:] if verbose >= 3 and success else None
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
                'depth_range': depth_range,
                'weight_decay': weight_decay,
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
    
    def _select_segment(self, weights):
        """Select a segment index using weighted random selection.
        
        Segments with higher weights are more likely to be selected.
        
        Args:
            weights: List of segment weights
            
        Returns:
            Selected segment index (0 to len-1)
        """
        total_weight = sum(weights)
        if total_weight == 0:
            # All weights are zero - uniform random
            return random.randint(0, len(weights) - 1)
        
        # Weighted random selection
        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return i
        
        # Fallback (shouldn't reach here due to floating point)
        return len(weights) - 1
    
    def _apply_operation(self, points, weights, segment_idx, operation,
                        depth_pct, direction_bias, centroid, weight_decay):
        """Apply a modification operation to a segment.
        
        Args:
            points: Current polygon points
            weights: Current segment weights
            segment_idx: Index of segment to modify
            operation: Operation name ('split_offset', 'sawtooth', 'squarewave')
            depth_pct: Depth percentage (0.0-1.0)
            direction_bias: 'inward', 'outward', or 'random'
            centroid: Polygon centroid (cx, cy)
            weight_decay: Multiplier for new segment weights
            
        Returns:
            (new_points, new_weights) tuple
        """
        if operation == 'split_offset':
            return self._op_split_offset(points, weights, segment_idx, depth_pct,
                                        direction_bias, centroid, weight_decay)
        elif operation == 'sawtooth':
            return self._op_sawtooth(points, weights, segment_idx, depth_pct,
                                    direction_bias, centroid, weight_decay)
        elif operation == 'squarewave':
            return self._op_squarewave(points, weights, segment_idx, depth_pct,
                                      direction_bias, centroid, weight_decay)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _op_split_offset(self, points, weights, idx, depth_pct,
                        direction_bias, centroid, weight_decay):
        """Split segment and offset midpoint perpendicular to segment.
        
        Operation: A---B becomes A---M---B where M is offset perpendicular
        
        Args:
            points: Current polygon points
            weights: Current segment weights
            idx: Segment index to modify
            depth_pct: How far to offset (percentage of segment length)
            direction_bias: Direction preference
            centroid: Polygon centroid
            weight_decay: Weight multiplier for new segments
            
        Returns:
            (new_points, new_weights) tuple
        """
        n = len(points)
        p1 = points[idx]
        p2 = points[(idx + 1) % n]
        
        # Compute midpoint
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        
        # Get perpendicular direction
        perp_x, perp_y = self._get_perpendicular_direction(p1, p2, direction_bias, centroid)
        
        # Compute segment length
        seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        # Offset distance
        offset_dist = seg_length * depth_pct
        
        # New midpoint
        new_point = (mx + perp_x * offset_dist, my + perp_y * offset_dist)
        
        # Insert new point
        new_points = points[:idx+1] + [new_point] + points[idx+1:]
        
        # Update weights: original segment split into two
        old_weight = weights[idx]
        new_weight = old_weight * weight_decay
        new_weights = weights[:idx] + [new_weight, new_weight] + weights[idx+1:]
        
        return new_points, new_weights
    
    def _op_sawtooth(self, points, weights, idx, depth_pct,
                    direction_bias, centroid, weight_decay):
        """Create sawtooth pattern on segment.
        
        Operation: A---B becomes A-/\-B (triangular protrusion)
        
        Args:
            points: Current polygon points
            weights: Current segment weights
            idx: Segment index to modify
            depth_pct: How far to offset peak
            direction_bias: Direction preference
            centroid: Polygon centroid
            weight_decay: Weight multiplier for new segments
            
        Returns:
            (new_points, new_weights) tuple
        """
        n = len(points)
        p1 = points[idx]
        p2 = points[(idx + 1) % n]
        
        # Compute 1/3 and 2/3 points along segment
        third_x = p1[0] + (p2[0] - p1[0]) / 3
        third_y = p1[1] + (p2[1] - p1[1]) / 3
        
        two_third_x = p1[0] + 2 * (p2[0] - p1[0]) / 3
        two_third_y = p1[1] + 2 * (p2[1] - p1[1]) / 3
        
        # Midpoint for peak
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        
        # Get perpendicular direction
        perp_x, perp_y = self._get_perpendicular_direction(p1, p2, direction_bias, centroid)
        
        # Segment length
        seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        offset_dist = seg_length * depth_pct
        
        # Peak point
        peak_x = mx + perp_x * offset_dist
        peak_y = my + perp_y * offset_dist
        
        # Insert two new points: 1/3 point and peak
        # A -> A -> 1/3 -> peak -> 2/3 -> B
        # But we want: A -> peak -> B (simplified sawtooth)
        # Actually, proper sawtooth: A -> left_base -> peak -> right_base -> B
        
        # Simplified: just insert peak at midpoint
        new_point = (peak_x, peak_y)
        new_points = points[:idx+1] + [new_point] + points[idx+1:]
        
        # Update weights
        old_weight = weights[idx]
        new_weight = old_weight * weight_decay
        new_weights = weights[:idx] + [new_weight, new_weight] + weights[idx+1:]
        
        return new_points, new_weights
    
    def _op_squarewave(self, points, weights, idx, depth_pct,
                      direction_bias, centroid, weight_decay):
        """Create square wave pattern on segment.
        
        Operation: A---B becomes A-|_|-B (rectangular protrusion)
        
        Args:
            points: Current polygon points
            weights: Current segment weights
            idx: Segment index to modify
            depth_pct: How far to offset the parallel segment
            direction_bias: Direction preference
            centroid: Polygon centroid
            weight_decay: Weight multiplier for new segments
            
        Returns:
            (new_points, new_weights) tuple
        """
        n = len(points)
        p1 = points[idx]
        p2 = points[(idx + 1) % n]
        
        # Compute 1/4 and 3/4 points along segment
        quarter_x = p1[0] + (p2[0] - p1[0]) / 4
        quarter_y = p1[1] + (p2[1] - p1[1]) / 4
        
        three_quarter_x = p1[0] + 3 * (p2[0] - p1[0]) / 4
        three_quarter_y = p1[1] + 3 * (p2[1] - p1[1]) / 4
        
        # Get perpendicular direction
        perp_x, perp_y = self._get_perpendicular_direction(p1, p2, direction_bias, centroid)
        
        # Segment length
        seg_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        offset_dist = seg_length * depth_pct
        
        # Offset the middle segment
        offset_x = perp_x * offset_dist
        offset_y = perp_y * offset_dist
        
        # Create three new points: quarter, quarter+offset, three_quarter+offset
        point1 = (quarter_x, quarter_y)
        point2 = (quarter_x + offset_x, quarter_y + offset_y)
        point3 = (three_quarter_x + offset_x, three_quarter_y + offset_y)
        point4 = (three_quarter_x, three_quarter_y)
        
        # Insert all four corner points
        # A -> p1 -> p2 -> p3 -> p4 -> B
        new_points = points[:idx+1] + [point1, point2, point3, point4] + points[idx+1:]
        
        # Update weights: one segment becomes five
        old_weight = weights[idx]
        new_weight = old_weight * weight_decay
        new_weights = (weights[:idx] + 
                      [new_weight, new_weight, new_weight, new_weight, new_weight] + 
                      weights[idx+1:])
        
        return new_points, new_weights
    
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