"""
Command parser for Shape Studio - Phase 5
Parses text commands with persistence support, RUN, and BATCH
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
            'RUN': self._parse_run,
            'BATCH': self._parse_batch,
            'PROC': self._parse_proc,
            'ANIMATE': self._parse_animate,
            'COLOR': self._parse_color,
            'WIDTH': self._parse_width,
            'FILL': self._parse_fill,
            'ALPHA': self._parse_alpha,
            'ZORDER': self._parse_zorder,
            'EXIT': self._parse_exit,
            'QUIT': self._parse_exit,
        }
        
    def parse(self, command_text):
        """Parse a command string into a command dictionary"""
        command_text = command_text.strip()
        
        if not command_text:
            raise ValueError("Empty command")
        
        # Process RAND() and RANDBOOL() functions first
        command_text = self._process_rand_functions(command_text)
        
        # Split into tokens
        parts = command_text.split()
        cmd = parts[0].upper()
        
        if cmd not in self.commands:
            raise ValueError(f"Unknown command: {cmd}")
        
        return self.commands[cmd](parts)
        
    def _process_rand_functions(self, text):
        """Replace RAND(min,max) and RANDBOOL() with random values"""
        # First process RANDBOOL() - simpler pattern
        def replace_randbool(match):
            return str(random.randint(0, 1))
        
        text = re.sub(r'RANDBOOL\(\)', replace_randbool, text)
        
        # Then process RAND(min,max)
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
        """Parse LIST command: LIST [WIP|MAIN|STASH|STORE|GLOBAL|PROC|PRESET]
        
        LIST PROC - List available procedural methods
        LIST PRESET <method> - List presets for a method
        """
        target = None
        method_name = None
        
        if len(parts) >= 2:
            target = parts[1].upper()
            
            # Handle LIST PRESET <method>
            if target == 'PRESET':
                if len(parts) < 3:
                    raise ValueError("LIST PRESET requires method name")
                method_name = parts[2]
                return {
                    'command': 'LIST_PRESET',
                    'method': method_name
                }
            
            # Validate target
            if target not in ['WIP', 'MAIN', 'STASH', 'STORE', 'GLOBAL', 'PROC']:
                raise ValueError("LIST target must be WIP, MAIN, STASH, STORE, GLOBAL, PROC, or PRESET <method>")
        
        return {
            'command': 'LIST',
            'target': target  # None means active canvas
        }
        
    def _parse_info(self, parts):
        """Parse INFO command: INFO <shape> or INFO PROC <method>"""
        if len(parts) < 2:
            raise ValueError("INFO requires: INFO <shape> or INFO PROC <method>")
        
        # Check for INFO PROC <method>
        if parts[1].upper() == 'PROC':
            if len(parts) < 3:
                raise ValueError("INFO PROC requires method name")
            return {
                'command': 'INFO_PROC',
                'method': parts[2]
            }
        
        # Regular shape info
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
    
    def _parse_run(self, parts):
        """Parse RUN command: RUN <scriptfile> [section_name]
        
        For .txt files: RUN script.txt
        For .json files: RUN script.json [section_name]
        """
        if len(parts) < 2:
            raise ValueError("RUN requires: RUN <scriptfile> [section_name]")
        
        scriptfile = parts[1]
        section_name = parts[2] if len(parts) >= 3 else None
        
        return {
            'command': 'RUN',
            'scriptfile': scriptfile,
            'section_name': section_name
        }    

    def _parse_batch(self, parts):
        """Parse BATCH command: BATCH <count> <scriptfile> [section_name] <output_prefix> [WIP|MAIN]
        
        For .txt files: BATCH <count> <scriptfile> <output_prefix> [WIP|MAIN]
        For .json files: BATCH <count> <scriptfile> <section_name> <output_prefix> [WIP|MAIN]
        
        Note: For .json files, section_name is required and goes before output_prefix
        """
        if len(parts) < 4:
            raise ValueError("BATCH requires: BATCH <count> <scriptfile> <output_prefix> [WIP|MAIN] "
                            "(for .json add section_name before output_prefix)")
        
        try:
            count = int(parts[1])
        except ValueError:
            raise ValueError("BATCH count must be an integer")
        
        if count < 1:
            raise ValueError("BATCH count must be at least 1")
        
        scriptfile = parts[2]
        
        # Determine if this is a JSON file
        is_json = scriptfile.endswith('.json')
        
        if is_json:
            # JSON format: BATCH count file.json section_name output_prefix [canvas]
            if len(parts) < 5:
                raise ValueError("BATCH with .json requires: BATCH <count> <file.json> <section_name> <output_prefix> [WIP|MAIN]")
            
            section_name = parts[3]
            output_prefix = parts[4]
            target_canvas = parts[5].upper() if len(parts) >= 6 else 'MAIN'
        else:
            # Text format: BATCH count file.txt output_prefix [canvas]
            section_name = None
            output_prefix = parts[3]
            target_canvas = parts[4].upper() if len(parts) >= 5 else 'MAIN'
        
        if target_canvas not in ['WIP', 'MAIN']:
            raise ValueError("BATCH target canvas must be WIP or MAIN")
        
        return {
            'command': 'BATCH',
            'count': count,
            'scriptfile': scriptfile,
            'section_name': section_name,
            'output_prefix': output_prefix,
            'target_canvas': target_canvas
        }
    
    def _parse_proc(self, parts):
        """Parse PROC command: PROC <method> <name> [PARAM=value ...]
        
        Example: PROC dynamic_polygon shape1 VERTICES=5 BOUNDS=100,100,600,600
        """
        if len(parts) < 3:
            raise ValueError("PROC requires: PROC <method> <name> [PARAM=value ...]")
        
        method_name = parts[1]
        shape_name = parts[2]
        
        # Parse parameter assignments
        params = {}
        for i in range(3, len(parts)):
            part = parts[i]
            if '=' not in part:
                raise ValueError(f"Invalid parameter format: '{part}'. Expected PARAM=value")
            
            key, value = part.split('=', 1)
            params[key.strip().upper()] = value.strip()
        
        return {
            'command': 'PROC',
            'method': method_name,
            'name': shape_name,
            'params': params
        }
    
    def _parse_animate(self, parts):
        """Parse ANIMATE command: ANIMATE <base_name> [FPS=<n>] [LOOP=<true|false>]"""
        if len(parts) < 2:
            raise ValueError("ANIMATE requires: ANIMATE <base_name> [FPS=n] [LOOP=true|false]")
        
        base_name = parts[1]
        fps = 2  # default
        loop = False  # default
        
        # Parse optional parameters
        for i in range(2, len(parts)):
            part = parts[i]
            if '=' not in part:
                raise ValueError(f"Invalid parameter format: '{part}'. Expected PARAM=value")
            
            key, value = part.split('=', 1)
            key = key.strip().upper()
            value = value.strip()
            
            if key == 'FPS':
                try:
                    fps = int(value)
                    if fps < 1 or fps > 10:
                        raise ValueError("FPS must be between 1 and 10")
                except ValueError as e:
                    raise ValueError(f"Invalid FPS value: '{value}'. Must be integer 1-10")
            
            elif key == 'LOOP':
                loop = value.upper() in ['TRUE', '1', 'YES', 'ON']
            
            else:
                raise ValueError(f"Unknown parameter: {key}")
        
        return {
            'command': 'ANIMATE',
            'base_name': base_name,
            'fps': fps,
            'loop': loop
        }

    def _parse_width(self, parts):
        """Parse WIDTH command: WIDTH <n> <width>"""
        if len(parts) < 3:
            raise ValueError("WIDTH requires: WIDTH <n> <width>")
        
        width = int(parts[2])
        if width < 1:
            raise ValueError("Width must be at least 1")
        
        return {
            'command': 'WIDTH',
            'name': parts[1],
            'width': width
        }

    def _parse_color_value(self, color_str):
        """Parse color from various formats to hex or named color
        
        Supports:
            - Named: 'red', 'blue', etc.
            - Hex: '#FF0000' or '#F00'
            - RGB: 'rgb(255,0,0)' or '255,0,0'
            - HSV: 'hsv(360,100,100)' or '360,100,100'
        
        Returns hex string or named color
        """
        import colorsys
        
        color = color_str.strip()
        
        # Hex color
        if color.startswith('#'):
            # Validate hex format
            if len(color) == 4:  # #RGB
                return '#' + ''.join([c*2 for c in color[1:]])  # Convert to #RRGGBB
            elif len(color) == 7:  # #RRGGBB
                return color
            else:
                raise ValueError(f"Invalid hex color format: {color}")
        
        # RGB format: rgb(255,0,0) or 255,0,0
        if color.lower().startswith('rgb(') or (',' in color and not color.lower().startswith('hsv')):
            # Extract numbers
            if color.lower().startswith('rgb('):
                color = color[4:-1]  # Remove 'rgb(' and ')'
            
            parts = [int(x.strip()) for x in color.split(',')]
            if len(parts) != 3:
                raise ValueError("RGB requires 3 values: r,g,b")
            
            r, g, b = parts
            if not all(0 <= v <= 255 for v in [r, g, b]):
                raise ValueError("RGB values must be 0-255")
            
            return f'#{r:02x}{g:02x}{b:02x}'
        
        # HSV format: hsv(360,100,100) or 360,100,100
        if color.lower().startswith('hsv('):
            color = color[4:-1]  # Remove 'hsv(' and ')'
            parts = [float(x.strip()) for x in color.split(',')]
            if len(parts) != 3:
                raise ValueError("HSV requires 3 values: h,s,v")
            
            h, s, v = parts
            if not (0 <= h <= 360):
                raise ValueError("Hue must be 0-360")
            if not (0 <= s <= 100 and 0 <= v <= 100):
                raise ValueError("Saturation and Value must be 0-100")
            
            # Convert to RGB (colorsys expects 0-1 range)
            r, g, b = colorsys.hsv_to_rgb(h/360, s/100, v/100)
            r, g, b = int(r*255), int(g*255), int(b*255)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        
        # Named color - return as-is (PIL will validate)
        return color

    def _parse_color(self, parts):
        """Parse COLOR command: COLOR <n> <color>"""
        if len(parts) < 3:
            raise ValueError("COLOR requires: COLOR <n> <color>")
        
        color = self._parse_color_value(parts[2])
        
        return {
            'command': 'COLOR',
            'name': parts[1],
            'color': color
        }

    def _parse_fill(self, parts):
        """Parse FILL command: FILL <n> <color|NONE>"""
        if len(parts) < 3:
            raise ValueError("FILL requires: FILL <n> <color|NONE>")
        
        fill = parts[2]
        if fill.upper() == 'NONE':
            fill = None
        else:
            fill = self._parse_color_value(fill)
        
        return {
            'command': 'FILL',
            'name': parts[1],
            'fill': fill
        }

    def _parse_alpha(self, parts):
        """Parse ALPHA command: ALPHA <n> <value>"""
        if len(parts) < 3:
            raise ValueError("ALPHA requires: ALPHA <n> <value>")
        
        alpha = float(parts[2])
        if alpha < 0 or alpha > 1:
            raise ValueError("Alpha must be between 0 and 1")
        
        return {
            'command': 'ALPHA',
            'name': parts[1],
            'alpha': alpha
        }

    def _parse_zorder(self, parts):
        """Parse ZORDER command: ZORDER <n> <value>"""
        if len(parts) < 3:
            raise ValueError("ZORDER requires: ZORDER <n> <value>")
        
        return {
            'command': 'ZORDER',
            'name': parts[1],
            'z_coord': int(parts[2])
        }

    def _parse_exit(self, parts):
        """Parse EXIT or QUIT command: EXIT or QUIT"""
        return {
            'command': 'EXIT'
        }