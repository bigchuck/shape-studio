"""
Shape classes for Shape Studio - Phase 2 with Attributes Dictionary
Base Shape class and implementations for Line, Polygon, and ShapeGroup
"""
import math
from datetime import datetime


class Shape:
    """Base class for all shapes with dictionary-based attributes"""
    
    def __init__(self, name, shape_type):
        self.name = name  # Direct attribute - core identity
        self.attrs = {
            'type': shape_type,
            'geometry': {},      # Shape-specific: points, start/end, members
            'style': {
                'color': 'black',
                'width': 2,
                'transparency': 1.0,
                'z_coord': 0,
                'fill': None
            },
            'history': [],       # List of (action_type, command, timestamp)
            'procedure': None,   # Optional: template info
            'relationships': {
                'group': None,       # Parent group if any
                'attached_to': [],   # Shapes that track this one
                'tracking': []       # Shapes this one tracks
            },
            'metadata': {
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'tags': []
            }
        }
        
    def add_history(self, action_type, command):
        """Add entry to command history"""
        entry = (action_type, command, datetime.now().isoformat())
        self.attrs['history'].append(entry)
        self.attrs['metadata']['modified'] = datetime.now().isoformat()

    def _apply_alpha(self, color, alpha):
        """Convert color to RGBA tuple with alpha applied
        
        Args:
            color: Named color or hex string
            alpha: Transparency (0.0-1.0)
        
        Returns:
            RGBA tuple (r, g, b, a)
        """
        from PIL import ImageColor
        
        # Convert named/hex color to RGB
        if isinstance(color, str):
            rgb = ImageColor.getrgb(color)
        else:
            rgb = color
        
        # Add alpha channel (0-255)
        a = int(alpha * 255)
        return (rgb[0], rgb[1], rgb[2], a)

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
        super().__init__(name, 'Line')
        self.attrs['geometry'] = {
            'start': start,
            'end': end
        }
        
    def draw(self, draw_context):
        """Draw the line using style attributes"""
        geom = self.attrs['geometry']
        style = self.attrs['style']
        color = self._apply_alpha(style['color'], style['transparency'])
        draw_context.line(
            [geom['start'], geom['end']], 
            fill=color, 
            width=style['width']
        )
        
    def move(self, dx, dy):
        """Move the line"""
        geom = self.attrs['geometry']
        geom['start'] = (geom['start'][0] + dx, geom['start'][1] + dy)
        geom['end'] = (geom['end'][0] + dx, geom['end'][1] + dy)
        
    def get_centroid(self):
        """Get the midpoint of the line"""
        geom = self.attrs['geometry']
        return (
            (geom['start'][0] + geom['end'][0]) / 2,
            (geom['start'][1] + geom['end'][1]) / 2
        )
        
    def rotate(self, angle):
        """Rotate the line around its center"""
        center = self.get_centroid()
        geom = self.attrs['geometry']
        geom['start'] = self._rotate_point(geom['start'], center, angle)
        geom['end'] = self._rotate_point(geom['end'], center, angle)
        
    def scale(self, factor):
        """Scale the line from its center"""
        center = self.get_centroid()
        geom = self.attrs['geometry']
        geom['start'] = self._scale_point(geom['start'], center, factor)
        geom['end'] = self._scale_point(geom['end'], center, factor)
        
    def resize(self, x_factor, y_factor):
        """Resize the line with separate X and Y factors"""
        center = self.get_centroid()
        geom = self.attrs['geometry']
        geom['start'] = self._resize_point(geom['start'], center, x_factor, y_factor)
        geom['end'] = self._resize_point(geom['end'], center, x_factor, y_factor)
        
    def _rotate_point(self, point, center, angle):
        """Rotate a point around a center by angle degrees"""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        x = point[0] - center[0]
        y = point[1] - center[1]
        
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        
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
        super().__init__(name, 'Polygon')
        self.attrs['geometry'] = {
            'points': points
        }
        
    def draw(self, draw_context):
        """Draw the polygon using style attributes"""
        geom = self.attrs['geometry']
        style = self.attrs['style']
        
        if len(geom['points']) < 2:
            return
        
        outline_color = self._apply_alpha(style['color'], style['transparency'])
        fill_color = None
        if style['fill']:
            fill_color = self._apply_alpha(style['fill'], style['transparency'])

        draw_context.polygon(
            geom['points'], 
            outline=outline_color,
            fill=fill_color,
            width=style['width']
        )
        
    def move(self, dx, dy):
        """Move the polygon"""
        geom = self.attrs['geometry']
        geom['points'] = [(x + dx, y + dy) for x, y in geom['points']]
        
    def get_centroid(self):
        """Get the center point of the polygon"""
        geom = self.attrs['geometry']
        points = geom['points']
        x_sum = sum(p[0] for p in points)
        y_sum = sum(p[1] for p in points)
        n = len(points)
        return (x_sum / n, y_sum / n)
        
    def rotate(self, angle):
        """Rotate the polygon around its center"""
        center = self.get_centroid()
        geom = self.attrs['geometry']
        geom['points'] = [self._rotate_point(p, center, angle) for p in geom['points']]
        
    def scale(self, factor):
        """Scale the polygon from its center"""
        center = self.get_centroid()
        geom = self.attrs['geometry']
        geom['points'] = [self._scale_point(p, center, factor) for p in geom['points']]
        
    def resize(self, x_factor, y_factor):
        """Resize the polygon with separate X and Y factors"""
        center = self.get_centroid()
        geom = self.attrs['geometry']
        geom['points'] = [self._resize_point(p, center, x_factor, y_factor) for p in geom['points']]
        
    def _rotate_point(self, point, center, angle):
        """Rotate a point around a center by angle degrees"""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        x = point[0] - center[0]
        y = point[1] - center[1]
        
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        
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


class ShapeGroup(Shape):
    """A group of shapes that can be manipulated as a unit"""
    
    def __init__(self, name, members):
        super().__init__(name, 'ShapeGroup')
        self.attrs['geometry'] = {
            'members': members  # List of Shape objects (can include other ShapeGroups)
        }
        
        # Mark all members as belonging to this group
        for member in members:
            member.attrs['relationships']['group'] = name
            
    def draw(self, draw_context):
        """Draw all member shapes, respecting their z-order within the group"""
        members = self.attrs['geometry']['members']
        
        # Sort members by z_coord before drawing
        sorted_members = sorted(members, key=lambda m: m.attrs['style']['z_coord'])
        
        for member in sorted_members:
            member.draw(draw_context)

    def move(self, dx, dy):
        """Move all members together"""
        members = self.attrs['geometry']['members']
        for member in members:
            member.move(dx, dy)
            
    def get_centroid(self):
        """Get the collective centroid of all members"""
        members = self.attrs['geometry']['members']
        centroids = [member.get_centroid() for member in members]
        x_sum = sum(c[0] for c in centroids)
        y_sum = sum(c[1] for c in centroids)
        n = len(centroids)
        return (x_sum / n, y_sum / n)
        
    def rotate(self, angle):
        """Rotate all members around the group's collective centroid"""
        group_center = self.get_centroid()
        members = self.attrs['geometry']['members']
        
        for member in members:
            # First, rotate the member's own center around the group center
            member_center = member.get_centroid()
            new_center = self._rotate_point(member_center, group_center, angle)
            
            # Move member so its center is at the new position
            dx = new_center[0] - member_center[0]
            dy = new_center[1] - member_center[1]
            member.move(dx, dy)
            
            # Then rotate the member around its own center
            member.rotate(angle)
            
    def scale(self, factor):
        """Scale all members from the group's collective centroid"""
        group_center = self.get_centroid()
        members = self.attrs['geometry']['members']
        
        for member in members:
            # Scale member's position relative to group center
            member_center = member.get_centroid()
            new_center = self._scale_point(member_center, group_center, factor)
            
            dx = new_center[0] - member_center[0]
            dy = new_center[1] - member_center[1]
            member.move(dx, dy)
            
            # Scale the member itself
            member.scale(factor)
            
    def resize(self, x_factor, y_factor):
        """Resize all members with separate X and Y factors"""
        group_center = self.get_centroid()
        members = self.attrs['geometry']['members']
        
        for member in members:
            # Resize member's position relative to group center
            member_center = member.get_centroid()
            new_center = self._resize_point(member_center, group_center, x_factor, y_factor)
            
            dx = new_center[0] - member_center[0]
            dy = new_center[1] - member_center[1]
            member.move(dx, dy)
            
            # Resize the member itself
            member.resize(x_factor, y_factor)
            
    def get_members(self, recursive=False):
        """Get list of member shapes
        
        Args:
            recursive: If True, recursively get all members from nested groups
        """
        members = self.attrs['geometry']['members']
        
        if not recursive:
            return members
            
        # Recursively collect all members
        all_members = []
        for member in members:
            if isinstance(member, ShapeGroup):
                all_members.extend(member.get_members(recursive=True))
            else:
                all_members.append(member)
        return all_members
        
    def _rotate_point(self, point, center, angle):
        """Rotate a point around a center by angle degrees"""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        x = point[0] - center[0]
        y = point[1] - center[1]
        
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        
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