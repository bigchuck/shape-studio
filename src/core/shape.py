"""
Shape definitions for Shape Studio.
Base Shape class and specific shape implementations.
"""

import math
from typing import List, Tuple


class Shape:
    """Base class for all shapes."""
    
    def __init__(self, name, color=(0, 0, 0), width=2):
        """
        Initialize shape.
        
        Args:
            name: Unique identifier for the shape
            color: RGB color tuple
            width: Line width
        """
        self.name = name
        self.color = color
        self.width = width
        self.points = []
    
    def get_center(self):
        """Calculate centroid of the shape."""
        if not self.points:
            return (0, 0)
        
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        
        return (center_x, center_y)
    
    def move(self, dx, dy):
        """Translate shape by dx, dy."""
        self.points = [(x + dx, y + dy) for x, y in self.points]
    
    def scale(self, sx, sy=None):
        """
        Scale shape around its center.
        
        Args:
            sx: X scale factor
            sy: Y scale factor (defaults to sx for uniform scaling)
        """
        if sy is None:
            sy = sx
        
        center_x, center_y = self.get_center()
        
        # Translate to origin, scale, translate back
        self.points = [
            (
                center_x + (x - center_x) * sx,
                center_y + (y - center_y) * sy
            )
            for x, y in self.points
        ]
    
    def rotate(self, angle_degrees):
        """Rotate shape around its center by angle in degrees."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        center_x, center_y = self.get_center()
        
        # Rotate around center
        rotated_points = []
        for x, y in self.points:
            # Translate to origin
            tx = x - center_x
            ty = y - center_y
            
            # Rotate
            rx = tx * cos_a - ty * sin_a
            ry = tx * sin_a + ty * cos_a
            
            # Translate back
            rotated_points.append((rx + center_x, ry + center_y))
        
        self.points = rotated_points
    
    def draw(self, canvas):
        """Draw shape on canvas. To be implemented by subclasses."""
        raise NotImplementedError


class Line(Shape):
    """Line shape defined by two points."""
    
    def __init__(self, name, x1, y1, x2, y2, color=(0, 0, 0), width=2):
        """Create a line from (x1, y1) to (x2, y2)."""
        super().__init__(name, color, width)
        self.points = [(x1, y1), (x2, y2)]
    
    def draw(self, canvas):
        """Draw line on canvas."""
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]
        canvas.draw_line(x1, y1, x2, y2, self.color, self.width)


class Polygon(Shape):
    """Polygon shape defined by a list of vertices."""
    
    def __init__(self, name, points, color=(0, 0, 0), width=2, fill=None):
        """
        Create a polygon from a list of points.
        
        Args:
            name: Shape identifier
            points: List of (x, y) tuples
            color: Outline color
            width: Line width
            fill: Fill color (None for no fill)
        """
        super().__init__(name, color, width)
        self.points = list(points)
        self.fill = fill
    
    def draw(self, canvas):
        """Draw polygon on canvas."""
        canvas.draw_polygon(self.points, self.color, self.width, self.fill)
    
    def add_vertex(self, x, y):
        """Add a vertex to the polygon."""
        self.points.append((x, y))
