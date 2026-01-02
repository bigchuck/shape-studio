"""
Command executor for Shape Studio
Executes parsed commands on the canvas
"""
import os
from src.core.shape import Line, Polygon
from src.commands.parser import CommandParser


class CommandExecutor:
    """Execute commands on the canvas"""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.parser = CommandParser()
        self.shapes_by_name = {}
        
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
    def execute(self, command_text):
        """Execute a command string"""
        # Parse the command
        cmd_dict = self.parser.parse(command_text)
        command = cmd_dict['command']
        
        # Execute based on command type
        if command == 'LINE':
            return self._execute_line(cmd_dict)
        elif command == 'POLY':
            return self._execute_poly(cmd_dict)
        elif command == 'MOVE':
            return self._execute_move(cmd_dict)
        elif command == 'ROTATE':
            return self._execute_rotate(cmd_dict)
        elif command == 'SCALE':
            return self._execute_scale(cmd_dict)
        elif command == 'RESIZE':
            return self._execute_resize(cmd_dict)
        elif command == 'CLEAR':
            return self._execute_clear(cmd_dict)
        elif command == 'LIST':
            return self._execute_list(cmd_dict)
        elif command == 'SAVE':
            return self._execute_save(cmd_dict)
        else:
            raise ValueError(f"Unknown command: {command}")
            
    def _execute_line(self, cmd_dict):
        """Execute LINE command"""
        name = cmd_dict['name']
        start = cmd_dict['start']
        end = cmd_dict['end']
        
        if name in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' already exists")
        
        line = Line(name, start, end)
        self.canvas.add_shape(line)
        self.shapes_by_name[name] = line
        
        return f"Created line '{name}'"
        
    def _execute_poly(self, cmd_dict):
        """Execute POLY command"""
        name = cmd_dict['name']
        points = cmd_dict['points']
        
        if name in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' already exists")
        
        poly = Polygon(name, points)
        self.canvas.add_shape(poly)
        self.shapes_by_name[name] = poly
        
        return f"Created polygon '{name}' with {len(points)} points"
        
    def _execute_move(self, cmd_dict):
        """Execute MOVE command"""
        name = cmd_dict['name']
        delta = cmd_dict['delta']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        shape.move(delta[0], delta[1])
        self.canvas.redraw()
        
        return f"Moved '{name}' by {delta}"
        
    def _execute_rotate(self, cmd_dict):
        """Execute ROTATE command"""
        name = cmd_dict['name']
        angle = cmd_dict['angle']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        shape.rotate(angle)
        self.canvas.redraw()
        
        return f"Rotated '{name}' by {angle}°"
        
    def _execute_scale(self, cmd_dict):
        """Execute SCALE command"""
        name = cmd_dict['name']
        factor = cmd_dict['factor']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        shape.scale(factor)
        self.canvas.redraw()
        
        return f"Scaled '{name}' by {factor}x"
        
    def _execute_resize(self, cmd_dict):
        """Execute RESIZE command"""
        name = cmd_dict['name']
        x_factor = cmd_dict['x_factor']
        y_factor = cmd_dict['y_factor']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        
        if not hasattr(shape, 'resize'):
            raise ValueError(f"Shape '{name}' does not support RESIZE")
        
        shape.resize(x_factor, y_factor)
        self.canvas.redraw()
        
        if x_factor == y_factor:
            return f"Resized '{name}' by {x_factor}x"
        else:
            return f"Resized '{name}' by {x_factor}x, {y_factor}x"
        
    def _execute_clear(self, cmd_dict):
        """Execute CLEAR command"""
        self.canvas.clear()
        self.shapes_by_name.clear()
        
        return "Canvas cleared"
        
    def _execute_list(self, cmd_dict):
        """Execute LIST command"""
        if not self.shapes_by_name:
            return "No shapes on canvas"
        
        shapes_info = []
        for name, shape in self.shapes_by_name.items():
            shape_type = type(shape).__name__
            shapes_info.append(f"{name} ({shape_type})")
        
        return "Shapes: " + ", ".join(shapes_info)
        
    def _execute_save(self, cmd_dict):
        """Execute SAVE command"""
        filename = cmd_dict['filename']
        filepath = os.path.join('output', filename)
        
        self.canvas.save(filepath)
        
        return f"Saved to {filepath}"