"""
Command parser for Shape Studio - Phase 5
Parses text commands with persistence and style support
"""
import re
import random
import colorsys


class ColorParser:
    """Parse various color formats into PIL-compatible format"""
    
    @staticmethod
    def parse(color_str):
        """Parse color string into PIL-compatible format
        
        Supports:
        - Named colors: 'red', 'blue', etc.
        - RGB: rgb(255,0,0)
        - RGBA: rgba(255,0,0,128) or rgba(255,0,0,0.5)
        - HSL: hsl(0,100%,50%)
        - HSLA: hsla(0,100%,50%,0.5)
        - Hex: #FF0000 or #FF0000FF
        """
        color_str = color_str.strip().lower()
        
        # Check for None/NONE
        if color_str in ['none', 'null']:
            return None
        
        # Check for RGB/RGBA
        rgb_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+(?:\.\d+)?))?\)', color_str)
        if rgb_match:
            r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
            if rgb_match.group(4):
                a = float(rgb_match.group(4))
                # If alpha is 0-1 range, convert to 0-255
                if a <= 1.0:
                    a = int(a * 255)
                else:
                    a = int(a)
                return (r, g, b, a)
            return (r, g, b)
        
        # Check for HSL/HSLA
        hsl_match = re.match(r'hsla?\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)%?,\s*(\d+(?:\.\d+)?)%?(?:,\s*(\d+(?:\.\d+)?))?\)', color_str)
        if hsl_match:
            h = float(hsl_match.group(1)) / 360.0  # Convert to 0-1
            s = float(hsl_match.group(2)) / 100.0  # Convert to 0-1
            l = float(hsl_match.group(3)) / 100.0  # Convert to 0-1
            
            # Convert HSL to RGB
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            
            if hsl_match.group(4):
                a = float(hsl_match.group(4))
                if a <= 1.0:
                    a = int(a * 255)
                else:
                    a = int(a)
                return (r, g, b, a)
            return (r, g, b)
        
        # Check for hex color
        hex_match = re.match(r'#?([0-9a-f]{6})([0-9a-f]{2})?', color_str)
        if hex_match:
            hex_val = hex_match.group(1)
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            if hex_match.group(2):
                a = int(hex_match.group(2), 16)
                return (r, g, b, a)
            return f'#{hex_val}'
        
        # Assume it's a named color - PIL will validate
        return color_str


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
            'EXTRACT': self._parse_extract,
            'DELETE': self._parse_delete,
            'SWITCH': self._parse_switch,
            'PROMOTE': self._parse_promote,
            'UNPROMOTE': self._parse_unpromote,
            'STASH': self._parse_stash,
            'UNSTASH': self._parse_unstash,
            'STORE': self._parse_store,
            'LOAD': self._parse_load,
            'SAVE_PROJECT': self._parse_save_project,
            'LOAD_PROJECT': self._parse_load_project,
            'CLEAR': self._parse_clear,
            'LIST': self._parse_list,
            'INFO': self._parse_info,
            'SAVE': self._parse_save,
            # Phase 5: Style commands
            'COLOR': self._parse_color,
            'WIDTH': self._parse_width,
            'FILL': self._parse_fill,
            'ALPHA': self._parse_alpha,
            'BRING_FORWARD': self._parse_bring_forward,
            'SEND_BACKWARD': self._parse_send_backward,
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
    
    def _parse_shape_list(self, shape_names_str):
        """Parse comma-separated list of shape names"""
        return [name.strip() for name in shape_names_str.split(',')]
        
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
        """Parse RESIZE command: RESIZE <n> <x_factor> [y_factor]"""
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
        """Parse GROUP command: GROUP <group_name> <shape1> <shape2> ..."""
        if len(parts) < 3:
            raise ValueError("GROUP requires: GROUP <group_name> <shape1> [shape2 ...]")
        
        group_name = parts[1]
        member_names = parts[2:]
        
        return {
            'command': 'GROUP',
            'name': group_name,
            'members': member_names
        }
        
    def _parse_ungroup(self, parts):
        """Parse UNGROUP command: UNGROUP <group_name>"""
        if len(parts) < 2:
            raise ValueError("UNGROUP requires: UNGROUP <group_name>")
        
        group_name = parts[1]
        
        return {
            'command': 'UNGROUP',
            'name': group_name
        }
        
    def _parse_extract(self, parts):
        """Parse EXTRACT command: EXTRACT <member> FROM <group>"""
        if len(parts) < 4:
            raise ValueError("EXTRACT requires: EXTRACT <member> FROM <group>")
        
        if parts[2].upper() != 'FROM':
            raise ValueError("EXTRACT syntax: EXTRACT <member> FROM <group>")
        
        member_name = parts[1]
        group_name = parts[3]
        
        return {
            'command': 'EXTRACT',
            'member': member_name,
            'group': group_name
        }
        
    def _parse_delete(self, parts):
        """Parse DELETE command: DELETE <shape_name> [CONFIRM]"""
        if len(parts) < 2:
            raise ValueError("DELETE requires: DELETE <shape>")
        
        shape_name = parts[1]
        
        # Check for CONFIRM flag
        confirm = False
        if len(parts) >= 3 and parts[2].upper() == 'CONFIRM':
            confirm = True
        
        return {
            'command': 'DELETE',
            'name': shape_name,
            'confirm': confirm
        }
        
    def _parse_switch(self, parts):
        """Parse SWITCH command: SWITCH WIP|MAIN"""
        if len(parts) < 2:
            raise ValueError("SWITCH requires: SWITCH WIP|MAIN")
        
        target = parts[1].upper()
        
        if target not in ['WIP', 'MAIN']:
            raise ValueError("SWITCH target must be WIP or MAIN")
        
        return {
            'command': 'SWITCH',
            'target': target
        }
        
    def _parse_promote(self, parts):
        """Parse PROMOTE command: PROMOTE [COPY] <shape>"""
        if len(parts) < 2:
            raise ValueError("PROMOTE requires: PROMOTE [COPY] <shape>")
        
        # Check for COPY modifier
        if parts[1].upper() == 'COPY':
            if len(parts) < 3:
                raise ValueError("PROMOTE COPY requires shape name")
            mode = 'copy'
            shape_name = parts[2]
        else:
            mode = 'move'
            shape_name = parts[1]
        
        return {
            'command': 'PROMOTE',
            'name': shape_name,
            'mode': mode
        }
        
    def _parse_unpromote(self, parts):
        """Parse UNPROMOTE command: UNPROMOTE [COPY] <shape>"""
        if len(parts) < 2:
            raise ValueError("UNPROMOTE requires: UNPROMOTE [COPY] <shape>")
        
        # Check for COPY modifier
        if parts[1].upper() == 'COPY':
            if len(parts) < 3:
                raise ValueError("UNPROMOTE COPY requires shape name")
            mode = 'copy'
            shape_name = parts[2]
        else:
            mode = 'move'
            shape_name = parts[1]
        
        return {
            'command': 'UNPROMOTE',
            'name': shape_name,
            'mode': mode
        }
        
    def _parse_stash(self, parts):
        """Parse STASH command: STASH <shape>"""
        if len(parts) < 2:
            raise ValueError("STASH requires: STASH <shape>")
        
        shape_name = parts[1]
        
        return {
            'command': 'STASH',
            'name': shape_name
        }
        
    def _parse_unstash(self, parts):
        """Parse UNSTASH command: UNSTASH [MOVE] <shape>"""
        if len(parts) < 2:
            raise ValueError("UNSTASH requires: UNSTASH [MOVE] <shape>")
        
        # Check for MOVE modifier
        if parts[1].upper() == 'MOVE':
            if len(parts) < 3:
                raise ValueError("UNSTASH MOVE requires shape name")
            mode = 'move'
            shape_name = parts[2]
        else:
            mode = 'copy'  # Default: keep in stash
            shape_name = parts[1]
        
        return {
            'command': 'UNSTASH',
            'name': shape_name,
            'mode': mode
        }
        
    def _parse_store(self, parts):
        """Parse STORE command: STORE [GLOBAL] <shape>
        
        STORE <shape> - Save to project store
        STORE GLOBAL <shape> - Save to global library
        """
        if len(parts) < 2:
            raise ValueError("STORE requires: STORE [GLOBAL] <shape>")
        
        # Check for GLOBAL modifier
        if parts[1].upper() == 'GLOBAL':
            if len(parts) < 3:
                raise ValueError("STORE GLOBAL requires shape name")
            scope = 'global'
            shape_name = parts[2]
        else:
            scope = 'project'
            shape_name = parts[1]
        
        return {
            'command': 'STORE',
            'name': shape_name,
            'scope': scope
        }
        
    def _parse_load(self, parts):
        """Parse LOAD command: LOAD <shape>
        
        Searches project store first, then global library
        """
        if len(parts) < 2:
            raise ValueError("LOAD requires: LOAD <shape>")
        
        shape_name = parts[1]
        
        return {
            'command': 'LOAD',
            'name': shape_name
        }
        
    def _parse_save_project(self, parts):
        """Parse SAVE_PROJECT command: SAVE_PROJECT <filename>"""
        if len(parts) < 2:
            raise ValueError("SAVE_PROJECT requires: SAVE_PROJECT <filename>")
        
        filename = parts[1]
        if not filename.endswith('.shapestudio'):
            filename += '.shapestudio'
        
        return {
            'command': 'SAVE_PROJECT',
            'filename': filename
        }
        
    def _parse_load_project(self, parts):
        """Parse LOAD_PROJECT command: LOAD_PROJECT <filename>"""
        if len(parts) < 2:
            raise ValueError("LOAD_PROJECT requires: LOAD_PROJECT <filename>")
        
        filename = parts[1]
        if not filename.endswith('.shapestudio'):
            filename += '.shapestudio'
        
        return {
            'command': 'LOAD_PROJECT',
            'filename': filename
        }
        
    def _parse_clear(self, parts):
        """Parse CLEAR command: CLEAR [WIP|MAIN|STASH] [ALL]"""
        target = None
        require_all = False
        
        if len(parts) >= 2:
            token = parts[1].upper()
            if token in ['WIP', 'MAIN', 'STASH']:
                target = token
                # Check for ALL in third position
                if len(parts) >= 3 and parts[2].upper() == 'ALL':
                    require_all = True
            elif token == 'ALL':
                # CLEAR ALL - clears active canvas
                require_all = True
        
        return {
            'command': 'CLEAR',
            'target': target,  # None means active canvas
            'all': require_all
        }
        
    def _parse_list(self, parts):
        """Parse LIST command: LIST [WIP|MAIN|STASH|STORE|GLOBAL]"""
        target = None
        if len(parts) >= 2:
            target = parts[1].upper()
            if target not in ['WIP', 'MAIN', 'STASH', 'STORE', 'GLOBAL']:
                raise ValueError("LIST target must be WIP, MAIN, STASH, STORE, or GLOBAL")
        
        return {
            'command': 'LIST',
            'target': target  # None means active canvas
        }
        
    def _parse_info(self, parts):
        """Parse INFO command: INFO <shape>"""
        if len(parts) < 2:
            raise ValueError("INFO requires: INFO <shape>")
        
        shape_name = parts[1]
        
        return {
            'command': 'INFO',
            'name': shape_name
        }
        
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
    
    # ============= Phase 5: Style Commands =============
    
    def _parse_color(self, parts):
        """Parse COLOR command: COLOR <shape1>[,<shape2>,...] <color>
        
        Examples:
        COLOR tri1 red
        COLOR tri1,tri2,tri3 rgb(255,0,0)
        COLOR square1 hsl(120,100%,50%)
        """
        if len(parts) < 3:
            raise ValueError("COLOR requires: COLOR <shape(s)> <color>")
        
        # Parse shape names (comma-separated)
        shape_names = self._parse_shape_list(parts[1])
        
        # Rest is the color (may contain spaces or commas)
        color_str = ' '.join(parts[2:])
        
        # Parse the color
        try:
            color = ColorParser.parse(color_str)
        except Exception as e:
            raise ValueError(f"Invalid color format: {color_str} ({e})")
        
        return {
            'command': 'COLOR',
            'shapes': shape_names,
            'color': color
        }
    
    def _parse_width(self, parts):
        """Parse WIDTH command: WIDTH <shape1>[,<shape2>,...] <pixels>
        
        Examples:
        WIDTH tri1 5
        WIDTH tri1,tri2 3
        """
        if len(parts) < 3:
            raise ValueError("WIDTH requires: WIDTH <shape(s)> <pixels>")
        
        # Parse shape names
        shape_names = self._parse_shape_list(parts[1])
        
        # Parse width
        try:
            width = int(parts[2])
            if width < 1:
                raise ValueError("Width must be >= 1")
        except ValueError:
            raise ValueError(f"Invalid width value: {parts[2]}")
        
        return {
            'command': 'WIDTH',
            'shapes': shape_names,
            'width': width
        }
    
    def _parse_fill(self, parts):
        """Parse FILL command: FILL <shape1>[,<shape2>,...] <color|NONE>
        
        Examples:
        FILL tri1 red
        FILL square1 NONE
        FILL tri1,tri2 rgba(255,0,0,128)
        """
        if len(parts) < 3:
            raise ValueError("FILL requires: FILL <shape(s)> <color|NONE>")
        
        # Parse shape names
        shape_names = self._parse_shape_list(parts[1])
        
        # Rest is the color
        color_str = ' '.join(parts[2:])
        
        # Parse the color (NONE is handled in ColorParser)
        try:
            color = ColorParser.parse(color_str)
        except Exception as e:
            raise ValueError(f"Invalid color format: {color_str} ({e})")
        
        return {
            'command': 'FILL',
            'shapes': shape_names,
            'fill': color
        }
    
    def _parse_alpha(self, parts):
        """Parse ALPHA command: ALPHA <shape1>[,<shape2>,...] <0.0-1.0>
        
        Examples:
        ALPHA tri1 0.5
        ALPHA tri1,tri2 0.75
        """
        if len(parts) < 3:
            raise ValueError("ALPHA requires: ALPHA <shape(s)> <0.0-1.0>")
        
        # Parse shape names
        shape_names = self._parse_shape_list(parts[1])
        
        # Parse alpha value
        try:
            alpha = float(parts[2])
            if not 0.0 <= alpha <= 1.0:
                raise ValueError("Alpha must be between 0.0 and 1.0")
        except ValueError:
            raise ValueError(f"Invalid alpha value: {parts[2]}")
        
        return {
            'command': 'ALPHA',
            'shapes': shape_names,
            'alpha': alpha
        }
    
    def _parse_bring_forward(self, parts):
        """Parse BRING_FORWARD command: BRING_FORWARD <shape> [<n>]
        
        Examples:
        BRING_FORWARD tri1
        BRING_FORWARD tri1 5
        """
        if len(parts) < 2:
            raise ValueError("BRING_FORWARD requires: BRING_FORWARD <shape> [<n>]")
        
        shape_name = parts[1]
        
        # Default to 1 step
        steps = 1
        if len(parts) >= 3:
            try:
                steps = int(parts[2])
                if steps < 1:
                    raise ValueError("Steps must be >= 1")
            except ValueError:
                raise ValueError(f"Invalid step count: {parts[2]}")
        
        return {
            'command': 'BRING_FORWARD',
            'name': shape_name,
            'steps': steps
        }
    
    def _parse_send_backward(self, parts):
        """Parse SEND_BACKWARD command: SEND_BACKWARD <shape> [<n>]
        
        Examples:
        SEND_BACKWARD tri1
        SEND_BACKWARD tri1 5
        """
        if len(parts) < 2:
            raise ValueError("SEND_BACKWARD requires: SEND_BACKWARD <shape> [<n>]")
        
        shape_name = parts[1]
        
        # Default to 1 step
        steps = 1
        if len(parts) >= 3:
            try:
                steps = int(parts[2])
                if steps < 1:
                    raise ValueError("Steps must be >= 1")
            except ValueError:
                raise ValueError(f"Invalid step count: {parts[2]}")
        
        return {
            'command': 'SEND_BACKWARD',
            'name': shape_name,
            'steps': steps
        }