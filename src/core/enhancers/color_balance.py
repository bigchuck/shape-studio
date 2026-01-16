"""
Color Balance Enhancer

Analyzes canvas color distribution and recommends harmonious colors
for new shapes based on color theory principles.
"""
from typing import Dict, List, Any
from src.core.enhancement import EnhancementMethod
from src.core.enhancement_helpers import (
    get_dominant_colors,
    get_average_color,
    get_color_temperature,
    get_complementary_color,
    get_shape_bounds_on_canvas,
    get_canvas_region_around_shape
)


class ColorBalanceEnhancer(EnhancementMethod):
    """
    Analyzes color balance on canvas and recommends harmonious colors.
    
    Uses color theory principles:
    - Complementary colors
    - Analogous colors
    - Triadic harmony
    - Color temperature balance
    """
    
    @property
    def name(self) -> str:
        return "color_balance"
    
    @property
    def description(self) -> str:
        return "Analyzes canvas color distribution and recommends harmonious colors"
    
    @property
    def intent_spec(self) -> Dict[str, Any]:
        """Define what intent parameters this method accepts"""
        return {
            'mode': {
                'type': 'choice',
                'choices': ['complement', 'analogous', 'triadic', 'auto'],
                'default': 'auto',
                'description': 'Color harmony mode'
            },
            'apply': {
                'type': 'bool',
                'default': False,
                'description': 'Whether to apply suggestions directly'
            },
            'sample_rate': {
                'type': 'int',
                'default': 10,
                'description': 'Pixel sampling rate for analysis'
            },
            'top_n': {
                'type': 'int',
                'default': 5,
                'description': 'Number of dominant colors to identify'
            }
        }
    
    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """Extended metadata about this enhancement method"""
        return {
            'name': 'color_balance',
            'description': 'Analyzes canvas color distribution and recommends harmonious colors',
            'parameters': {
                'analyze': {
                    'sample_rate': 'Pixel sampling rate (default: 10)',
                    'top_n': 'Number of dominant colors to identify (default: 5)',
                },
                'enhance': {
                    'mode': 'Color harmony mode: complement, analogous, triadic, auto (default: auto)',
                    'apply': 'Whether to apply suggestions directly (default: False)',
                }
            },
            'modes': ['complement', 'analogous', 'triadic', 'auto'],
            'returns': {
                'analyze': ['dominant_colors', 'color_temperature', 'saturation_level', 'recommendations'],
                'enhance': ['modified', 'changes', 'recommendations'],
            }
        }
    
    def analyze(self, canvas, **kwargs) -> Dict[str, Any]:
        """
        Analyze color distribution on canvas.

        Args:
            canvas: Canvas object to analyze
            **kwargs: 
                - sample_size: int (pixel sampling for dominant colors, default 1000)
                - num_colors: int (number of top colors to return, default 5)

        Returns:
            Dict with color analysis
        """
        sample_size = kwargs.get('sample_size', 1000)
        num_colors = kwargs.get('num_colors', 5)

        # Get rendered canvas as PIL Image
        image = canvas.render()

        # Use helper functions with correct parameters
        dominant = get_dominant_colors(image, num_colors=num_colors, sample_size=sample_size)
        avg_hex = get_average_color(image)  # No sample_rate parameter!

        # Convert hex to RGB tuple for temperature analysis
        avg_hex_clean = avg_hex.lstrip('#')
        avg_color = tuple(int(avg_hex_clean[i:i+2], 16) for i in (0, 2, 4))

        temperature = get_color_temperature(avg_hex)

        # Generate recommendations
        recommendations = self._generate_recommendations(dominant, temperature)

        return {
            'dominant_colors': dominant,
            'color_temperature': temperature,
            'average_color': avg_color,  # Now returns RGB tuple
            'average_color_hex': avg_hex,  # Also provide hex
            'recommendations': recommendations,
        }
    
    def validate_intent(self, intent_dict):
        is_valid = False
        error = "not implemented yet"
        if "mode" in intent_dict:
            mode = intent_dict["mode"]
            if mode not in ['complement', 'analogous', 'triadic', 'auto']:
                error = f"mode ({mode}) not valid"
                return is_valid, error
        is_valid = True
        return is_valid, error

    def enhance(self, canvas, shape, intent) -> Dict[str, Any]:
        """Suggest color enhancements for a shape based on canvas state."""
        
        mode = intent.get('mode', 'auto')
        apply = self._parse_bool(intent.get('apply'), default=False)
        outline = self._parse_bool(intent.get('outline'), default=True)

        # Analyze current canvas
        analysis = self.analyze(canvas)
        
        # Get average color as RGB tuple
        avg_color = analysis['average_color']
        temperature = analysis['color_temperature']
        
        # Convert avg_color to hex for complementary calculation
        avg_hex = f'#{avg_color[0]:02x}{avg_color[1]:02x}{avg_color[2]:02x}'
        
        # Generate suggestion based on mode
        if mode == 'complement' or (mode == 'auto' and temperature == 'warm'):
            comp_hex = get_complementary_color(avg_hex)
            # Convert back to RGB tuple
            comp_clean = comp_hex.lstrip('#')
            suggested_color = tuple(int(comp_clean[i:i+2], 16) for i in (0, 2, 4))
        elif mode == 'analogous' or (mode == 'auto' and temperature == 'cool'):
            r, g, b = avg_color
            suggested_color = (min(255, r + 30), max(0, g - 15), min(255, b + 15))
        elif mode == 'triadic':
            r, g, b = avg_color
            suggested_color = (b, r, g)
        else:
            comp_hex = get_complementary_color(avg_hex)
            comp_clean = comp_hex.lstrip('#')
            suggested_color = tuple(int(comp_clean[i:i+2], 16) for i in (0, 2, 4))
        
        # Convert suggested color to hex
        suggested_hex = f'#{suggested_color[0]:02x}{suggested_color[1]:02x}{suggested_color[2]:02x}'
        
        # Build result in expected format
        commands = {}
        if apply:
            commands['fill'] = suggested_hex
            if outline:
                commands['color'] = suggested_hex
        
        return {
            'commands': commands,
            'metadata': {
                'success': True,
                'reasoning': f"Suggested {mode} color {suggested_hex} to complement {temperature} palette (avg: {avg_hex})",
                'analysis': {
                    'average_color': avg_color,
                    'temperature': temperature,
                    'mode': mode,
                },
                'recommendation': analysis['recommendations'],
            }
        }
    
    def _generate_recommendations(self, dominant_colors: List, temperature: str) -> List[str]:
        """Generate color recommendations based on analysis"""
        recommendations = []
        
        if not dominant_colors:
            recommendations.append("Canvas is empty - any color works well")
            return recommendations
        
        # Temperature-based recommendations
        if temperature == 'warm':
            recommendations.append("Consider cool blues or greens for contrast")
            recommendations.append("Use complementary colors to balance warm tones")
        elif temperature == 'cool':
            recommendations.append("Consider warm reds or oranges for contrast")
            recommendations.append("Use analogous colors to maintain cool harmony")
        else:
            recommendations.append("Balanced palette - maintain harmony or add accent")
        
        # Dominant color recommendations
        num_dominant = len(dominant_colors)
        if num_dominant <= 2:
            recommendations.append("Limited palette - good for bold statements")
        elif num_dominant >= 4:
            recommendations.append("Varied palette - consider limiting new colors")
        
        return recommendations