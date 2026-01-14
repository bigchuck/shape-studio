"""
Color Balance Enhancement Module
Analyzes canvas colors and suggests harmonious colors for shapes
"""
from src.core.enhancement_helpers import (
    get_dominant_colors,
    get_average_color,
    get_color_temperature,
    get_complementary_color,
    get_shape_bounds_on_canvas,
    get_canvas_region_around_shape
)


class ColorBalanceEnhancer:
    """
    Analyzes color harmony on canvas and recommends colors for shapes
    """
    
    # Parameter specification
    PARAM_SPEC = {
        'target': {
            'type': 'choice',
            'choices': ['warm', 'cool', 'neutral', 'complement'],
            'default': 'complement',
            'description': 'Target color temperature or relationship'
        },
        'preserve_hue': {
            'type': 'bool',
            'default': False,
            'description': 'Keep hue, adjust only saturation/value'
        },
        'contrast_boost': {
            'type': 'float',
            'default': 0.5,
            'min': 0.0,
            'max': 1.0,
            'description': 'Contrast adjustment (0=none, 1=maximum)'
        },
        'reference_shapes': {
            'type': 'list',
            'default': [],
            'description': 'Shape names to compare against (comma-separated)'
        },
        'apply_fill': {
            'type': 'bool',
            'default': True,
            'description': 'Also set fill color'
        }
    }
    
    @staticmethod
    def get_metadata():
        """Return metadata about this enhancement method"""
        return {
            'name': 'color_balance',
            'description': 'Analyzes color harmony and suggests complementary colors',
            'param_spec': ColorBalanceEnhancer.PARAM_SPEC,
            'returns': ['color', 'fill', 'alpha'],
            'examples': [
                'ENHANCE color_balance shape1 INTENT="target:warm"',
                'ENHANCE color_balance shape1 INTENT="target:complement,reference_shapes:bg"',
                'ENHANCE color_balance shape1 INTENT="contrast_boost:0.8,apply_fill:true"'
            ]
        }
    
    @staticmethod
    def enhance(canvas, shape, intent_dict):
        """
        Analyze canvas colors and recommend colors for shape
        
        Args:
            canvas: Canvas object with shapes
            shape: Shape object to enhance (or None if analyzing whole canvas)
            intent_dict: Parsed intent parameters
            
        Returns:
            Dict with 'commands' and 'metadata' keys
        """
        # Get canvas as PIL Image for analysis
        canvas_image = canvas.render()
        
        # Extract intent parameters (with defaults from PARAM_SPEC)
        target = intent_dict.get('target', 'complement')
        reference_shapes = intent_dict.get('reference_shapes', [])
        apply_fill = intent_dict.get('apply_fill', True)
        contrast_boost = float(intent_dict.get('contrast_boost', 0.5))
        
        # Analyze dominant canvas colors
        dominant_colors = get_dominant_colors(canvas_image, num_colors=3)
        
        if not dominant_colors:
            # Fallback: no analysis possible
            return {
                'commands': {},
                'metadata': {
                    'success': False,
                    'reasoning': 'Cannot analyze empty canvas',
                    'modified_params': []
                }
            }
        
        # Get most dominant color
        primary_color_hex, _ = dominant_colors[0]
        
        # Determine recommended color based on target
        if target == 'complement':
            recommended_color = get_complementary_color(primary_color_hex)
            reasoning = f"Applied complementary color to contrast with canvas dominant {primary_color_hex}"
        
        elif target == 'warm':
            # Stub: For now, use a warm color
            recommended_color = '#E74C3C'  # Warm red
            reasoning = f"Applied warm color palette"
        
        elif target == 'cool':
            # Stub: For now, use a cool color
            recommended_color = '#3498DB'  # Cool blue
            reasoning = f"Applied cool color palette"
        
        elif target == 'neutral':
            # Stub: Use average canvas color
            recommended_color = get_average_color(canvas_image)
            reasoning = f"Applied neutral color based on canvas average"
        
        else:
            # Fallback
            recommended_color = primary_color_hex
            reasoning = f"Using canvas dominant color"
        
        # Build command dictionary
        commands = {
            'color': recommended_color
        }
        
        if apply_fill:
            # Lighter version for fill (stub: just use same for now)
            commands['fill'] = recommended_color
        
        # Build metadata
        metadata = {
            'success': True,
            'reasoning': reasoning,
            'modified_params': list(commands.keys()),
            'analyzed_colors': [c[0] for c in dominant_colors],
            'target': target
        }
        
        return {
            'commands': commands,
            'metadata': metadata
        }