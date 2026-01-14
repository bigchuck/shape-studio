"""
Object Placement Enhancement Module
Analyzes shape positions and suggests adjustments for better composition
"""
from src.core.enhancement_helpers import (
    get_shape_bounds_on_canvas,
    get_shape_centroid
)
import math


class ObjectPlacementEnhancer:
    """
    Analyzes object placement and suggests position/rotation/scale adjustments
    """
    
    # Parameter specification
    PARAM_SPEC = {
        'rule': {
            'type': 'choice',
            'choices': ['thirds', 'center', 'golden', 'balance'],
            'default': 'thirds',
            'description': 'Composition rule to apply'
        },
        'avoid_overlap': {
            'type': 'bool',
            'default': True,
            'description': 'Avoid overlapping other shapes'
        },
        'preserve_orientation': {
            'type': 'bool',
            'default': False,
            'description': 'Keep current rotation angle'
        },
        'reference_shapes': {
            'type': 'list',
            'default': [],
            'description': 'Shape names to balance against (comma-separated)'
        },
        'margin': {
            'type': 'float',
            'default': 50.0,
            'description': 'Safe distance from edges/other shapes'
        },
        'scale_adjust': {
            'type': 'bool',
            'default': False,
            'description': 'Allow scale adjustment for balance'
        }
    }
    
    @staticmethod
    def get_metadata():
        """Return metadata about this enhancement method"""
        return {
            'name': 'object_placement',
            'description': 'Analyzes composition and suggests shape placement adjustments',
            'param_spec': ObjectPlacementEnhancer.PARAM_SPEC,
            'returns': ['move', 'rotate', 'scale'],
            'examples': [
                'ENHANCE object_placement shape1 INTENT="rule:thirds"',
                'ENHANCE object_placement shape1 INTENT="rule:balance,reference_shapes:bg"',
                'ENHANCE object_placement shape1 INTENT="avoid_overlap:true,margin:100"'
            ]
        }
    
    @staticmethod
    def enhance(canvas, shape, intent_dict):
        """
        Analyze shape placement and recommend adjustments
        
        Args:
            canvas: Canvas object with shapes
            shape: Shape object to enhance
            intent_dict: Parsed intent parameters
            
        Returns:
            Dict with 'commands' and 'metadata' keys
        """
        # Extract intent parameters
        rule = intent_dict.get('rule', 'thirds')
        reference_shapes = intent_dict.get('reference_shapes', [])
        avoid_overlap = intent_dict.get('avoid_overlap', True)
        scale_adjust = intent_dict.get('scale_adjust', False)
        margin = float(intent_dict.get('margin', 50.0))
        
        # Get current shape position
        current_centroid = get_shape_centroid(shape)
        if not current_centroid:
            return {
                'commands': {},
                'metadata': {
                    'success': False,
                    'reasoning': 'Cannot determine shape position',
                    'modified_params': []
                }
            }
        
        current_x, current_y = current_centroid
        
        # Calculate target position based on rule
        canvas_width = 768  # TODO: Get from config
        canvas_height = 768
        
        if rule == 'thirds':
            # Rule of thirds: place at 1/3 or 2/3 intersections
            # For stub: move to upper-left third intersection
            target_x = canvas_width / 3
            target_y = canvas_height / 3
            reasoning = "Applied rule of thirds (upper-left intersection)"
        
        elif rule == 'center':
            # Center on canvas
            target_x = canvas_width / 2
            target_y = canvas_height / 2
            reasoning = "Centered shape on canvas"
        
        elif rule == 'golden':
            # Golden ratio: ~0.618 from edge
            target_x = canvas_width * 0.618
            target_y = canvas_height * 0.618
            reasoning = "Applied golden ratio positioning"
        
        elif rule == 'balance':
            # Balance against reference shapes
            if reference_shapes:
                # Stub: Calculate opposite position from first reference shape
                # In real implementation, would calculate center of mass of reference shapes
                target_x = canvas_width - current_x
                target_y = canvas_height - current_y
                reasoning = f"Balanced against reference shapes: {', '.join(reference_shapes)}"
            else:
                # No reference, default to center
                target_x = canvas_width / 2
                target_y = canvas_height / 2
                reasoning = "Centered (no reference shapes for balance)"
        
        else:
            # Unknown rule, no change
            return {
                'commands': {},
                'metadata': {
                    'success': False,
                    'reasoning': f'Unknown rule: {rule}',
                    'modified_params': []
                }
            }
        
        # Calculate movement delta
        dx = target_x - current_x
        dy = target_y - current_y
        
        # Check if movement is significant (> 5 pixels)
        distance = math.sqrt(dx**2 + dy**2)
        if distance < 5:
            return {
                'commands': {},
                'metadata': {
                    'success': True,
                    'reasoning': f'{reasoning}; no adjustment needed (already close)',
                    'modified_params': []
                }
            }
        
        # Build command dictionary
        commands = {
            'move': (dx, dy)
        }
        
        # Optional scale adjustment (stub)
        if scale_adjust:
            # For now, no scaling logic
            pass
        
        # Build metadata
        metadata = {
            'success': True,
            'reasoning': reasoning,
            'modified_params': list(commands.keys()),
            'current_position': (current_x, current_y),
            'target_position': (target_x, target_y),
            'distance_moved': distance
        }
        
        return {
            'commands': commands,
            'metadata': metadata
        }