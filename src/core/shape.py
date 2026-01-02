"""
Shape classes for Shape Studio
Base Shape class and implementations for Line and Polygon
"""
import math


class Shape:
    """Base class for all shapes"""
    
    def __init__(self, name):
        self.name = name
        
    def draw(self, draw_context):
        """Draw the shape - must be implemented by subclasses"""
        raise NotImplementedError
        
    def move(self, dx, dy):
        """Move the shape by dx, dy"""
        raise NotImplementedError
        
    def rotate(self, angle):
        """Rotate the shape by angle degrees"""
        raise NotImplementedError
        
    def scale(self, factor):
        """Scale the shape by factor"""
        raise NotImplementedError
        
    def resize(self, x_factor, y_factor):
        """Resize the shape by x_factor and y_factor"""
        raise NotImplementedError
        
    def get_centroid(self):
        """Get the center point of the shape"""
        raise NotImplementedError


class Line(Shape):
    """A line segment"""
    
    def __init__(self, name, start, end):
        super().__init__(name)
        self.start = start
        self.end = end
        
    def draw(self, draw_context):
        """Draw the line"""
        draw_context.line([self.start, self.end], fill='black', width=2)
        
    def move(self, dx, dy):
        """Move the line"""
        self.start = (self.start[0] + dx, self.start[1] + dy)
        self.end = (self.end[0] + dx, self.end[1] + dy)
        
    def get_centroid(self):
        """Get the midpoint of the line"""
        return (
            (self.start[0] + self.end[0]) / 2,
            (self.start[1] + self.end[1]) / 2
        )
        
    def rotate(self, angle):
        """Rotate the line around its center"""
        center = self.get_centroid()
        self.start = self._rotate_point(self.start, center, angle)
        self.end = self._rotate_point(self.end, center, angle)
        
    def scale(self, factor):
        """Scale the line from its center"""
        center = self.get_centroid()
        self.start = self._scale_point(self.start, center, factor)
        self.end = self._scale_point(self.end, center, factor)
        
    def resize(self, x_factor, y_factor):
        """Resize the line with separate X and Y factors"""
        center = self.get_centroid()
        self.start = self._resize_point(self.start, center, x_factor, y_factor)
        self.end = self._resize_point(self.end, center, x_factor, y_factor)
        
    def _rotate_point(self, point, center, angle):
        """Rotate a point around a center by angle degrees"""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Translate to origin
        x = point[0] - center[0]
        y = point[1] - center[1]
        
        # Rotate
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        
        # Translate back
        return (new_x + center[0], new_y + center[1])
        
    def _scale_point(self, point, center, factor):
        """Scale a point from a center by factor"""
        x = center[0] + (point[0] - center[0]) * factor
        y = center[1] + (point[1] - center[1]) * factor
        return (x, y)
        
    def _resize_point(self, point, center, x_factor, y_factor):
        """Resize a point from a center with separate X and Y factors"""
        x = center[0] + (point[0] - center[0]) * x_factor
        y = center[1] + (point[1] - center[1]) * y_factor
        return (x, y)


class Polygon(Shape):
    """A polygon (closed shape with multiple vertices)"""
    
    def __init__(self, name, points):
        super().__init__(name)
        self.points = points
        
    def draw(self, draw_context):
        """Draw the polygon"""
        if len(self.points) < 2:
            return
        
        # Draw closed polygon
        draw_context.polygon(self.points, outline='black', fill=None, width=2)
        
    def move(self, dx, dy):
        """Move the polygon"""
        self.points = [(x + dx, y + dy) for x, y in self.points]
        
    def get_centroid(self):
        """Get the center point of the polygon"""
        x_sum = sum(p[0] for p in self.points)
        y_sum = sum(p[1] for p in self.points)
        n = len(self.points)
        return (x_sum / n, y_sum / n)
        
    def rotate(self, angle):
        """Rotate the polygon around its center"""
        center = self.get_centroid()
        self.points = [self._rotate_point(p, center, angle) for p in self.points]
        
    def scale(self, factor):
        """Scale the polygon from its center"""
        center = self.get_centroid()
        self.points = [self._scale_point(p, center, factor) for p in self.points]
        
    def resize(self, x_factor, y_factor):
        """Resize the polygon with separate X and Y factors"""
        center = self.get_centroid()
        self.points = [self._resize_point(p, center, x_factor, y_factor) for p in self.points]
        
    def _rotate_point(self, point, center, angle):
        """Rotate a point around a center by angle degrees"""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Translate to origin
        x = point[0] - center[0]
        y = point[1] - center[1]
        
        # Rotate
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        
        # Translate back
        return (new_x + center[0], new_y + center[1])
        
    def _scale_point(self, point, center, factor):
        """Scale a point from a center by factor"""
        x = center[0] + (point[0] - center[0]) * factor
        y = center[1] + (point[1] - center[1]) * factor
        return (x, y)
        
    def _resize_point(self, point, center, x_factor, y_factor):
        """Resize a point from a center with separate X and Y factors"""
        x = center[0] + (point[0] - center[0]) * x_factor
        y = center[1] + (point[1] - center[1]) * y_factor
        return (x, y)