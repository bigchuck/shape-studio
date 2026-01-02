"""
Command executor for Shape Studio - Phase 2
Executes parsed commands on the canvas with GROUP/UNGROUP and history tracking
"""
import os
from src.core.shape import Line, Polygon, ShapeGroup
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
            return self._execute_line(cmd_dict, command_text)
        elif command == 'POLY':
            return self._execute_poly(cmd_dict, command_text)
        elif command == 'MOVE':
            return self._execute_move(cmd_dict, command_text)
        elif command == 'ROTATE':
            return self._execute_rotate(cmd_dict, command_text)
        elif command == 'SCALE':
            return self._execute_scale(cmd_dict, command_text)
        elif command == 'RESIZE':
            return self._execute_resize(cmd_dict, command_text)
        elif command == 'GROUP':
            return self._execute_group(cmd_dict, command_text)
        elif command == 'UNGROUP':
            return self._execute_ungroup(cmd_dict, command_text)
        elif command == 'CLEAR':
            return self._execute_clear(cmd_dict)
        elif command == 'LIST':
            return self._execute_list(cmd_dict)
        elif command == 'SAVE':
            return self._execute_save(cmd_dict)
        else:
            raise ValueError(f"Unknown command: {command}")
            
    def _execute_line(self, cmd_dict, command_text):
        """Execute LINE command"""
        name = cmd_dict['name']
        start = cmd_dict['start']
        end = cmd_dict['end']
        
        if name in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' already exists")
        
        line = Line(name, start, end)
        line.add_history('CREATE', command_text)
        self.canvas.add_shape(line)
        self.shapes_by_name[name] = line
        
        return f"Created line '{name}'"
        
    def _execute_poly(self, cmd_dict, command_text):
        """Execute POLY command"""
        name = cmd_dict['name']
        points = cmd_dict['points']
        
        if name in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' already exists")
        
        poly = Polygon(name, points)
        poly.add_history('CREATE', command_text)
        self.canvas.add_shape(poly)
        self.shapes_by_name[name] = poly
        
        return f"Created polygon '{name}' with {len(points)} points"
        
    def _execute_move(self, cmd_dict, command_text):
        """Execute MOVE command"""
        name = cmd_dict['name']
        delta = cmd_dict['delta']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        
        # Check if shape is in a group
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group or UNGROUP first.")
        
        shape.move(delta[0], delta[1])
        shape.add_history('TRANSFORM', command_text)
        self.canvas.redraw()
        
        return f"Moved '{name}' by {delta}"
        
    def _execute_rotate(self, cmd_dict, command_text):
        """Execute ROTATE command"""
        name = cmd_dict['name']
        angle = cmd_dict['angle']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        
        # Check if shape is in a group
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group or UNGROUP first.")
        
        shape.rotate(angle)
        shape.add_history('TRANSFORM', command_text)
        self.canvas.redraw()
        
        return f"Rotated '{name}' by {angle}°"
        
    def _execute_scale(self, cmd_dict, command_text):
        """Execute SCALE command"""
        name = cmd_dict['name']
        factor = cmd_dict['factor']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        
        # Check if shape is in a group
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group or UNGROUP first.")
        
        shape.scale(factor)
        shape.add_history('TRANSFORM', command_text)
        self.canvas.redraw()
        
        return f"Scaled '{name}' by {factor}x"
        
    def _execute_resize(self, cmd_dict, command_text):
        """Execute RESIZE command"""
        name = cmd_dict['name']
        x_factor = cmd_dict['x_factor']
        y_factor = cmd_dict['y_factor']
        
        if name not in self.shapes_by_name:
            raise ValueError(f"Shape '{name}' not found")
        
        shape = self.shapes_by_name[name]
        
        # Check if shape is in a group
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group or UNGROUP first.")
        
        if not hasattr(shape, 'resize'):
            raise ValueError(f"Shape '{name}' does not support RESIZE")
        
        shape.resize(x_factor, y_factor)
        shape.add_history('TRANSFORM', command_text)
        self.canvas.redraw()
        
        if x_factor == y_factor:
            return f"Resized '{name}' by {x_factor}x"
        else:
            return f"Resized '{name}' by {x_factor}x, {y_factor}x"
            
    def _execute_group(self, cmd_dict, command_text):
        """Execute GROUP command"""
        group_name = cmd_dict['name']
        member_names = cmd_dict['members']
        
        if group_name in self.shapes_by_name:
            raise ValueError(f"Shape '{group_name}' already exists")
        
        # Collect member shapes
        members = []
        for member_name in member_names:
            if member_name not in self.shapes_by_name:
                raise ValueError(f"Shape '{member_name}' not found")
            
            shape = self.shapes_by_name[member_name]
            
            # Check if already in a group
            if shape.attrs['relationships']['group']:
                raise ValueError(f"Shape '{member_name}' is already in group "
                               f"'{shape.attrs['relationships']['group']}'")
            
            members.append(shape)
        
        # Create the group
        group = ShapeGroup(group_name, members)
        group.add_history('CREATE', command_text)
        self.shapes_by_name[group_name] = group
        
        # Note: Members stay in shapes_by_name but can't be transformed individually
        # Canvas will still draw them (through the group)
        self.canvas.redraw()
        
        return f"Created group '{group_name}' with {len(members)} members"
        
    def _execute_ungroup(self, cmd_dict, command_text):
        """Execute UNGROUP command"""
        group_name = cmd_dict['name']
        
        if group_name not in self.shapes_by_name:
            raise ValueError(f"Group '{group_name}' not found")
        
        shape = self.shapes_by_name[group_name]
        
        if not isinstance(shape, ShapeGroup):
            raise ValueError(f"'{group_name}' is not a group")
        
        # Get members and clear their group relationship
        members = shape.attrs['geometry']['members']
        for member in members:
            member.attrs['relationships']['group'] = None
            member.add_history('UNGROUP', command_text)
        
        # Remove the group from registry
        del self.shapes_by_name[group_name]
        
        # Members are still in shapes_by_name and canvas, so just redraw
        self.canvas.redraw()
        
        return f"Ungrouped '{group_name}' ({len(members)} members now independent)"
        
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
            shape_type = shape.attrs['type']
            
            # Show group info
            if isinstance(shape, ShapeGroup):
                member_count = len(shape.attrs['geometry']['members'])
                shapes_info.append(f"{name} (Group: {member_count} members)")
            else:
                # Show if part of a group
                group = shape.attrs['relationships']['group']
                if group:
                    shapes_info.append(f"{name} ({shape_type}, in group '{group}')")
                else:
                    shapes_info.append(f"{name} ({shape_type})")
        
        return "Shapes:\n  " + "\n  ".join(shapes_info)
        
    def _execute_save(self, cmd_dict):
        """Execute SAVE command"""
        filename = cmd_dict['filename']
        filepath = os.path.join('output', filename)
        
        self.canvas.save(filepath)
        
        return f"Saved to {filepath}"