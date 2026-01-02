"""
Canvas management for Shape Studio.
Handles 1024x1024 image creation, grid rendering, and shape drawing.
"""

from PIL import Image, ImageDraw


class Canvas:
    """Manages the 1024x1024 drawing canvas with grid overlay."""
    
    def __init__(self, size=1024, grid_spacing=64, bg_color=(255, 255, 255)):
        """
        Initialize canvas.
        
        Args:
            size: Canvas dimensions (square)
            grid_spacing: Spacing between grid lines in pixels
            bg_color: Background color RGB tuple
        """
        self.size = size
        self.grid_spacing = grid_spacing
        self.bg_color = bg_color
        
        # Create PIL image
        self.image = Image.new('RGB', (size, size), bg_color)
        self.draw = ImageDraw.Draw(self.image)
        
        # Draw initial grid
        self._draw_grid()
    
    def _draw_grid(self):
        """Draw grid lines on canvas."""
        grid_color = (220, 220, 220)  # Light gray
        
        # Vertical lines
        for x in range(0, self.size + 1, self.grid_spacing):
            self.draw.line([(x, 0), (x, self.size)], fill=grid_color, width=1)
        
        # Horizontal lines
        for y in range(0, self.size + 1, self.grid_spacing):
            self.draw.line([(0, y), (self.size, y)], fill=grid_color, width=1)
        
        # Draw axes (darker)
        axis_color = (180, 180, 180)
        center = self.size // 2
        
        # Center vertical line
        self.draw.line([(center, 0), (center, self.size)], fill=axis_color, width=2)
        # Center horizontal line
        self.draw.line([(0, center), (self.size, center)], fill=axis_color, width=2)
    
    def clear(self):
        """Clear canvas and redraw grid."""
        self.image = Image.new('RGB', (self.size, self.size), self.bg_color)
        self.draw = ImageDraw.Draw(self.image)
        self._draw_grid()
    
    def draw_line(self, x1, y1, x2, y2, color=(0, 0, 0), width=2):
        """Draw a line on the canvas."""
        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    
    def draw_polygon(self, points, color=(0, 0, 0), width=2, fill=None):
        """
        Draw a polygon on the canvas.
        
        Args:
            points: List of (x, y) tuples
            color: Outline color
            width: Line width
            fill: Fill color (None for no fill)
        """
        if len(points) < 2:
            return
        
        if fill:
            self.draw.polygon(points, fill=fill, outline=color)
        else:
            self.draw.polygon(points, outline=color, width=width)
    
    def save(self, filepath):
        """Save canvas to PNG file."""
        self.image.save(filepath, 'PNG')
    
    def get_image(self):
        """Return the PIL image object."""
        return self.image
