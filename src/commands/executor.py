"""
Command executor for Shape Studio.
Executes parsed commands on shapes and canvas.
"""

import os
from src.core.shape import Line, Polygon


class CommandExecutor:
    """Execute commands on shapes and canvas."""
    
    def __init__(self, canvas):
        """
        Initialize executor.
        
        Args:
            canvas: Canvas object to draw on
        """
        self.canvas = canvas
        self.shapes = {}  # Dictionary of name -> Shape
        
        self.command_handlers = {
            'LINE': self._execute_line,
            'POLY': self._execute_poly,
            'MOVE': self._execute_move,
            'ROTATE': self._execute_rotate,
            'SCALE': self._execute_scale,
            'CLEAR': self._execute_clear,
            'SAVE': self._execute_save,
            'LIST': self._execute_list,
        }
    
    def execute(self, parsed_command):
        """
        Execute a parsed command.
        
        Args:
            parsed_command: Dictionary from CommandParser
            
        Returns:
            Success message or error message
        """
        if 'error' in parsed_command:
            return parsed_command['error']
        
        cmd = parsed_command.get('command')
        
        if cmd not in self.command_handlers:
            return f'Unknown command: {cmd}'
        
        try:
            result = self.command_handlers[cmd](parsed_command)
            self._redraw()
            return result
        except Exception as e:
            return f'Execution error: {str(e)}'
    
    def _redraw(self):
        """Redraw all shapes on canvas."""
        self.canvas.clear()
        for shape in self.shapes.values():
            shape.draw(self.canvas)
    
    def _execute_line(self, cmd):
        """Execute LINE command."""
        name = cmd['name']
        
        if name in self.shapes:
            return f'Error: Shape "{name}" already exists'
        
        line = Line(name, cmd['x1'], cmd['y1'], cmd['x2'], cmd['y2'])
        self.shapes[name] = line
        
        return f'Created line "{name}"'
    
    def _execute_poly(self, cmd):
        """Execute POLY command."""
        name = cmd['name']
        
        if name in self.shapes:
            return f'Error: Shape "{name}" already exists'
        
        polygon = Polygon(name, cmd['points'])
        self.shapes[name] = polygon
        
        return f'Created polygon "{name}" with {len(cmd["points"])} vertices'
    
    def _execute_move(self, cmd):
        """Execute MOVE command."""
        name = cmd['name']
        
        if name not in self.shapes:
            return f'Error: Shape "{name}" not found'
        
        self.shapes[name].move(cmd['dx'], cmd['dy'])
        
        return f'Moved "{name}" by ({cmd["dx"]}, {cmd["dy"]})'
    
    def _execute_rotate(self, cmd):
        """Execute ROTATE command."""
        name = cmd['name']
        
        if name not in self.shapes:
            return f'Error: Shape "{name}" not found'
        
        self.shapes[name].rotate(cmd['angle'])
        
        return f'Rotated "{name}" by {cmd["angle"]} degrees'
    
    def _execute_scale(self, cmd):
        """Execute SCALE command."""
        name = cmd['name']
        
        if name not in self.shapes:
            return f'Error: Shape "{name}" not found'
        
        self.shapes[name].scale(cmd['sx'], cmd['sy'])
        
        if cmd['sx'] == cmd['sy']:
            return f'Scaled "{name}" by {cmd["sx"]}'
        else:
            return f'Scaled "{name}" by ({cmd["sx"]}, {cmd["sy"]})'
    
    def _execute_clear(self, cmd):
        """Execute CLEAR command."""
        self.shapes.clear()
        return 'Canvas cleared'
    
    def _execute_save(self, cmd):
        """Execute SAVE command."""
        filename = cmd['filename']
        
        # Ensure .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        # Save to output directory
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        self.canvas.save(filepath)
        
        return f'Saved to {filepath}'
    
    def _execute_list(self, cmd):
        """Execute LIST command."""
        if not self.shapes:
            return 'No shapes on canvas'
        
        shape_list = []
        for name, shape in self.shapes.items():
            shape_type = shape.__class__.__name__
            shape_list.append(f'  {name} ({shape_type})')
        
        return 'Shapes:\n' + '\n'.join(shape_list)
