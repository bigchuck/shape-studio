"""
Composition Balance Enhancement Module
Analyzes overall composition and suggests multi-shape adjustments
"""
from src.core.enhancement_helpers import (
    get_shape_centroid,
    get_shape_bounds_on_canvas
)
import math


class CompositionBalanceEnhancer:
    """
    Analyzes overall composition balance and suggests adjustments
    """
    
    # Parameter specification
    PARAM_SPEC = {
        'target': {
            'type': 'choice',
            'choices': ['symmetric', 'asymmetric', 'dynamic', 'static'],
            'default': 'symmetric',
            'description': 'Target composition style'
        },
        'weight_by_size': {
            'type': 'bool',
            'default': True,
            'description': 'Consider shape size in balance calculations'
        },
        'adjust_all': {
            'type': 'bool',
            'default': False,
            'description': 'Adjust all shapes or just specified shape'
        },
        'balance_axis': {
            'type': 'choice',
            'choices': ['horizontal', 'vertical', 'both', 'radial'],
            'default': 'both',
            'description': 'Axis to balance along'
        }
    }
    
    @staticmethod
    def get_metadata():
        """Return metadata about this enhancement method"""
        return {
            'name': 'composition_balance',
            'description': 'Analyzes overall composition and suggests balance adjustments',
            'param_spec': CompositionBalanceEnhancer.PARAM_SPEC,
            'returns': ['move', 'scale', 'rotate'],
            'examples': [
                'ENHANCE composition_balance shape1 INTENT="target:symmetric"',
                'ENHANCE composition_balance shape1 INTENT="target:asymmetric,balance_axis:horizontal"',
                'ENHANCE composition_balance canvas INTENT="adjust_all:true,target:dynamic"'
            ]
        }
    
    @staticmethod
    def enhance(canvas, shape, intent_dict):
        """
        Analyze composition balance and recommend adjustments
        
        Args:
            canvas: Canvas object with shapes
            shape: Shape object to enhance (or None for canvas-wide analysis)
            intent_dict: Parsed intent parameters
            
        Returns:
            Dict with 'commands' and 'metadata' keys
        """
        # Extract intent parameters
        target = intent_dict.get('target', 'symmetric')
        weight_by_size = intent_dict.get('weight_by_size', True)
        adjust_all = intent_dict.get('adjust_all', False)
        balance_axis = intent_dict.get('balance_axis', 'both')
        
        # Get all shapes on canvas
        all_shapes = canvas.shapes
        
        if not all_shapes:
            return {
                'commands': {},
                'metadata': {
                    'success': False,
                    'reasoning': 'No shapes on canvas to analyze',
                    'modified_params': []
                }
            }
        
        # Calculate composition center of mass
        total_x = 0
        total_y = 0
        total_weight = 0
        
        for s in all_shapes.values():
            centroid = get_shape_centroid(s)
            if not centroid:
                continue
            
            x, y = centroid
            
            # Weight by size if requested
            if weight_by_size:
                bounds = get_shape_bounds_on_canvas(s)
                if bounds:
                    x1, y1, x2, y2 = bounds
                    area = (x2 - x1) * (y2 - y1)
                    weight = max(area, 1)  # Avoid zero weight
                else:
                    weight = 1
            else:
                weight = 1
            
            total_x += x * weight
            total_y += y * weight
            total_weight += weight
        
        if total_weight == 0:
            return {
                'commands': {},
                'metadata': {
                    'success': False,
                    'reasoning': 'Cannot calculate composition balance',
                    'modified_params': []
                }
            }
        
        # Composition center of mass
        com_x = total_x / total_weight
        com_y = total_y / total_weight
        
        # Canvas center
        canvas_width = 768  # TODO: Get from config
        canvas_height = 768
        canvas_center_x = canvas_width / 2
        canvas_center_y = canvas_height / 2
        
        # Calculate offset from ideal center
        offset_x = com_x - canvas_center_x
        offset_y = com_y - canvas_center_y
        
        # Determine if composition is balanced
        distance_from_center = math.sqrt(offset_x**2 + offset_y**2)
        is_balanced = distance_from_center < 50  # Within 50px of center
        
        if is_balanced and target == 'symmetric':
            return {
                'commands': {},
                'metadata': {
                    'success': True,
                    'reasoning': f'Composition already balanced (COM at {com_x:.1f}, {com_y:.1f})',
                    'modified_params': [],
                    'center_of_mass': (com_x, com_y),
                    'canvas_center': (canvas_center_x, canvas_center_y),
                    'distance_from_center': distance_from_center
                }
            }
        
        # For symmetric target, suggest moving the shape to balance composition
        if target == 'symmetric':
            # Move specified shape in opposite direction of imbalance
            # This is a simplification - real implementation would be more sophisticated
            
            if shape is None:
                # Canvas-wide adjustment not supported yet
                return {
                    'commands': {},
                    'metadata': {
                        'success': False,
                        'reasoning': 'Canvas-wide composition adjustment not yet implemented',
                        'modified_params': []
                    }
                }
            
            # Suggest moving shape opposite to imbalance
            # Scale movement by imbalance magnitude
            scale_factor = 0.5  # Move halfway to balance
            
            if balance_axis == 'horizontal':
                move_x = -offset_x * scale_factor
                move_y = 0
            elif balance_axis == 'vertical':
                move_x = 0
                move_y = -offset_y * scale_factor
            elif balance_axis == 'both':
                move_x = -offset_x * scale_factor
                move_y = -offset_y * scale_factor
            else:  # radial
                move_x = -offset_x * scale_factor
                move_y = -offset_y * scale_factor
            
            commands = {
                'move': (move_x, move_y)
            }
            
            reasoning = f'Adjusted to balance composition (COM offset: {distance_from_center:.1f}px)'
        
        else:
            # Other targets (asymmetric, dynamic, static) are stubs
            commands = {}
            reasoning = f'Target "{target}" not yet implemented'
        
        # Build metadata
        metadata = {
            'success': bool(commands),
            'reasoning': reasoning,
            'modified_params': list(commands.keys()),
            'center_of_mass': (com_x, com_y),
            'canvas_center': (canvas_center_x, canvas_center_y),
            'distance_from_center': distance_from_center
        }
        
        return {
            'commands': commands,
            'metadata': metadata
        }