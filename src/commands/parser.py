"""
Command parser for Shape Studio.
Parses text commands into structured command objects.
"""

import re
import random


class CommandParser:
    """Parse text commands into structured format."""
    
    def __init__(self):
        """Initialize parser."""
        self.commands = {
            'LINE': self._parse_line,
            'POLY': self._parse_poly,
            'MOVE': self._parse_move,
            'ROTATE': self._parse_rotate,
            'SCALE': self._parse_scale,
            'RESIZE': self._parse_scale,  # Alias for SCALE
            'CLEAR': self._parse_clear,
            'SAVE': self._parse_save,
            'LIST': self._parse_list,
        }
    
    def parse(self, command_text):
        """
        Parse a command string.
        
        Args:
            command_text: Raw command string
            
        Returns:
            dict with 'command' and command-specific parameters
            or dict with 'error' if parsing failed
        """
        if not command_text or not command_text.strip():
            return {'error': 'Empty command'}
        
        # Split into tokens
        tokens = command_text.strip().split()
        
        if not tokens:
            return {'error': 'Empty command'}
        
        cmd = tokens[0].upper()
        
        if cmd not in self.commands:
            return {'error': f'Unknown command: {cmd}'}
        
        try:
            return self.commands[cmd](tokens)
        except Exception as e:
            return {'error': f'Parse error: {str(e)}'}
    
    def _eval_value(self, value_str):
        """
        Evaluate a value that might contain RAND() function.
        
        Args:
            value_str: String that might be a number or RAND(min,max)
            
        Returns:
            Numeric value
        """
        # Check for RAND(min,max) pattern
        rand_match = re.match(r'RAND\((\d+),(\d+)\)', value_str, re.IGNORECASE)
        if rand_match:
            min_val = int(rand_match.group(1))
            max_val = int(rand_match.group(2))
            return random.randint(min_val, max_val)
        
        # Try to parse as float
        return float(value_str)
    
    def _parse_point(self, point_str):
        """Parse a point string like '100,200' into (x, y) tuple."""
        parts = point_str.split(',')
        if len(parts) != 2:
            raise ValueError(f'Invalid point format: {point_str}')
        
        x = self._eval_value(parts[0])
        y = self._eval_value(parts[1])
        
        return (x, y)
    
    def _parse_line(self, tokens):
        """Parse LINE command: LINE name x1,y1 x2,y2"""
        if len(tokens) < 4:
            return {'error': 'LINE requires: name x1,y1 x2,y2'}
        
        name = tokens[1]
        p1 = self._parse_point(tokens[2])
        p2 = self._parse_point(tokens[3])
        
        return {
            'command': 'LINE',
            'name': name,
            'x1': p1[0], 'y1': p1[1],
            'x2': p2[0], 'y2': p2[1]
        }
    
    def _parse_poly(self, tokens):
        """Parse POLY command: POLY name x1,y1 x2,y2 x3,y3 ..."""
        if len(tokens) < 4:
            return {'error': 'POLY requires: name and at least 2 points'}
        
        name = tokens[1]
        points = []
        
        for i in range(2, len(tokens)):
            points.append(self._parse_point(tokens[i]))
        
        return {
            'command': 'POLY',
            'name': name,
            'points': points
        }
    
    def _parse_move(self, tokens):
        """Parse MOVE command: MOVE name dx,dy"""
        if len(tokens) < 3:
            return {'error': 'MOVE requires: name dx,dy'}
        
        name = tokens[1]
        delta = self._parse_point(tokens[2])
        
        return {
            'command': 'MOVE',
            'name': name,
            'dx': delta[0],
            'dy': delta[1]
        }
    
    def _parse_rotate(self, tokens):
        """Parse ROTATE command: ROTATE name angle"""
        if len(tokens) < 3:
            return {'error': 'ROTATE requires: name angle'}
        
        name = tokens[1]
        angle = self._eval_value(tokens[2])
        
        return {
            'command': 'ROTATE',
            'name': name,
            'angle': angle
        }
    
    def _parse_scale(self, tokens):
        """Parse SCALE/RESIZE command: SCALE name factor OR SCALE name sx,sy"""
        if len(tokens) < 3:
            return {'error': 'SCALE requires: name factor or name sx,sy'}
        
        name = tokens[1]
        
        # Check if it's a single value or x,y pair
        if ',' in tokens[2]:
            scale = self._parse_point(tokens[2])
            sx, sy = scale[0], scale[1]
        else:
            sx = sy = self._eval_value(tokens[2])
        
        return {
            'command': 'SCALE',
            'name': name,
            'sx': sx,
            'sy': sy
        }
    
    def _parse_clear(self, tokens):
        """Parse CLEAR command."""
        return {'command': 'CLEAR'}
    
    def _parse_save(self, tokens):
        """Parse SAVE command: SAVE filename"""
        if len(tokens) < 2:
            return {'error': 'SAVE requires: filename'}
        
        return {
            'command': 'SAVE',
            'filename': tokens[1]
        }
    
    def _parse_list(self, tokens):
        """Parse LIST command."""
        return {'command': 'LIST'}
