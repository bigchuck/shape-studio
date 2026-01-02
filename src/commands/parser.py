"""
Command parser for Shape Studio - Phase 2
Parses text commands into structured data with GROUP/UNGROUP support
"""
import re
import random


class CommandParser:
    """Parse text commands into structured command dictionaries"""
    
    def __init__(self):
        self.commands = {
            'LINE': self._parse_line,
            'POLY': self._parse_poly,
            'MOVE': self._parse_move,
            'ROTATE': self._parse_rotate,
            'SCALE': self._parse_scale,
            'RESIZE': self._parse_resize,
            'GROUP': self._parse_group,
            'UNGROUP': self._parse_ungroup,
            'CLEAR': self._parse_clear,
            'LIST': self._parse_list,
            'SAVE': self._parse_save,
        }
        
    def parse(self, command_text):
        """Parse a command string into a command dictionary"""
        command_text = command_text.strip()
        
        if not command_text:
            raise ValueError("Empty command")
        
        # Process RAND() functions first
        command_text = self._process_rand_functions(command_text)
        
        # Split into tokens
        parts = command_text.split()
        cmd = parts[0].upper()
        
        if cmd not in self.commands:
            raise ValueError(f"Unknown command: {cmd}")
        
        return self.commands[cmd](parts)
        
    def _process_rand_functions(self, text):
        """Replace RAND(min,max) with random values"""
        pattern = r'RAND\((-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\)'
        
        def replace_rand(match):
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            value = random.uniform(min_val, max_val)
            # Return as int if both bounds are integers
            if min_val == int(min_val) and max_val == int(max_val):
                return str(int(value))
            return str(value)
        
        return re.sub(pattern, replace_rand, text)
        
    def _parse_line(self, parts):
        """Parse LINE command: LINE <n> <x1>,<y1> <x2>,<y2>"""
        if len(parts) < 4:
            raise ValueError("LINE requires: LINE <n> <x1>,<y1> <x2>,<y2>")
        
        name = parts[1]
        
        # Parse start point
        start_parts = parts[2].split(',')
        if len(start_parts) != 2:
            raise ValueError("Invalid start point format")
        x1, y1 = float(start_parts[0]), float(start_parts[1])
        
        # Parse end point
        end_parts = parts[3].split(',')
        if len(end_parts) != 2:
            raise ValueError("Invalid end point format")
        x2, y2 = float(end_parts[0]), float(end_parts[1])
        
        return {
            'command': 'LINE',
            'name': name,
            'start': (x1, y1),
            'end': (x2, y2)
        }
        
    def _parse_poly(self, parts):
        """Parse POLY command: POLY <n> <x1>,<y1> <x2>,<y2> ..."""
        if len(parts) < 4:
            raise ValueError("POLY requires at least 3 points")
        
        name = parts[1]
        points = []
        
        for i in range(2, len(parts)):
            point_parts = parts[i].split(',')
            if len(point_parts) != 2:
                raise ValueError(f"Invalid point format: {parts[i]}")
            x, y = float(point_parts[0]), float(point_parts[1])
            points.append((x, y))
        
        if len(points) < 3:
            raise ValueError("POLY requires at least 3 points")
        
        return {
            'command': 'POLY',
            'name': name,
            'points': points
        }
        
    def _parse_move(self, parts):
        """Parse MOVE command: MOVE <n> <dx>,<dy>"""
        if len(parts) < 3:
            raise ValueError("MOVE requires: MOVE <n> <dx>,<dy>")
        
        name = parts[1]
        delta_parts = parts[2].split(',')
        if len(delta_parts) != 2:
            raise ValueError("Invalid delta format")
        
        dx, dy = float(delta_parts[0]), float(delta_parts[1])
        
        return {
            'command': 'MOVE',
            'name': name,
            'delta': (dx, dy)
        }
        
    def _parse_rotate(self, parts):
        """Parse ROTATE command: ROTATE <n> <angle>"""
        if len(parts) < 3:
            raise ValueError("ROTATE requires: ROTATE <n> <angle>")
        
        name = parts[1]
        angle = float(parts[2])
        
        return {
            'command': 'ROTATE',
            'name': name,
            'angle': angle
        }
        
    def _parse_scale(self, parts):
        """Parse SCALE command: SCALE <n> <factor>"""
        if len(parts) < 3:
            raise ValueError("SCALE requires: SCALE <n> <factor>")
        
        name = parts[1]
        factor = float(parts[2])
        
        return {
            'command': 'SCALE',
            'name': name,
            'factor': factor
        }
        
    def _parse_resize(self, parts):
        """Parse RESIZE command: RESIZE <n> <x_factor> [y_factor]
        - RESIZE <n> <factor> - uniform resize
        - RESIZE <n> <x_factor> <y_factor> - anisotropic resize
        """
        if len(parts) < 3:
            raise ValueError("RESIZE requires: RESIZE <n> <x_factor> [y_factor]")
        
        name = parts[1]
        x_factor = float(parts[2])
        
        # Check if y_factor is provided
        if len(parts) >= 4:
            y_factor = float(parts[3])
        else:
            y_factor = x_factor  # Uniform scaling
        
        return {
            'command': 'RESIZE',
            'name': name,
            'x_factor': x_factor,
            'y_factor': y_factor
        }
        
    def _parse_group(self, parts):
        """Parse GROUP command: GROUP <group_name> <shape1> <shape2> ...
        
        Creates a new group containing the specified shapes.
        """
        if len(parts) < 3:
            raise ValueError("GROUP requires: GROUP <group_name> <shape1> [shape2 ...]")
        
        group_name = parts[1]
        member_names = parts[2:]  # All remaining args are shape names
        
        return {
            'command': 'GROUP',
            'name': group_name,
            'members': member_names
        }
        
    def _parse_ungroup(self, parts):
        """Parse UNGROUP command: UNGROUP <group_name>
        
        Dissolves a group, making its members independent again.
        """
        if len(parts) < 2:
            raise ValueError("UNGROUP requires: UNGROUP <group_name>")
        
        group_name = parts[1]
        
        return {
            'command': 'UNGROUP',
            'name': group_name
        }
        
    def _parse_clear(self, parts):
        """Parse CLEAR command"""
        return {'command': 'CLEAR'}
        
    def _parse_list(self, parts):
        """Parse LIST command"""
        return {'command': 'LIST'}
        
    def _parse_save(self, parts):
        """Parse SAVE command: SAVE <filename>"""
        if len(parts) < 2:
            raise ValueError("SAVE requires: SAVE <filename>")
        
        filename = parts[1]
        if not filename.endswith('.png'):
            filename += '.png'
        
        return {
            'command': 'SAVE',
            'filename': filename
        }