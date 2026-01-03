"""
Procedural generation system for Shape Studio
Provides methods for algorithmic shape creation with parameterized control
"""
import random
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
                       return_mode='single'):
        """
        Generate evolved polygon through iterative segment modification.
        
        This is a STUB implementation. The actual algorithm will be implemented later.
        For now, it creates a simple random polygon as a placeholder.
        
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
            
        Returns:
            Polygon object (or ShapeGroup, or list based on return_mode)
        """
        if operations is None:
            operations = ['split_offset', 'sawtooth']
        
        # Handle range parameters - choose randomly if tuple
        num_vertices = random.randint(*vertices) if isinstance(vertices, tuple) else vertices
        depth_pct = random.uniform(*depth_range) if isinstance(depth_range, tuple) else depth_range
        
        # STUB: Create a simple random polygon in bounds
        x1, y1, x2, y2 = bounds
        points = []
        for i in range(num_vertices):
            x = random.uniform(x1, x2)
            y = random.uniform(y1, y2)
            points.append((x, y))
        
        # Sort by angle from centroid (simple convex approximation)
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        
        import math
        points.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
        
        # Create the polygon
        polygon = Polygon(name, points)
        
        # Add metadata about generation
        polygon.attrs['procedure'] = {
            'method': 'dynamic_polygon',
            'parameters': {
                'vertices': vertices,
                'bounds': bounds,
                'iterations': iterations,
                'operations': operations,
                'connect': connect,
            },
            'actual_iterations': 0,  # STUB: would be filled by actual algorithm
            'successful_modifications': 0,  # STUB
        }
        
        # TODO: Implement actual evolution algorithm here
        # - Connect vertices according to 'connect' method
        # - Iterate 'iterations' times:
        #   - Select segment with weighting
        #   - Apply random operation from 'operations'
        #   - Validate no intersections
        #   - Update weights
        # - Return result
        
        return polygon