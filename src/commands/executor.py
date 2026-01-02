"""
Command executor for Shape Studio - Phase 3 Enhanced + Canvas Sync Fix
Properly syncs canvas shape list with executor registry
"""
import os
import copy
from src.core.shape import Line, Polygon, ShapeGroup
from src.commands.parser import CommandParser


class CommandExecutor:
    """Execute commands on WIP or Main canvas"""
    
    def __init__(self, wip_canvas, main_canvas):
        self.wip_canvas = wip_canvas
        self.main_canvas = main_canvas
        self.active_canvas = wip_canvas  # Start with WIP active
        self.active_canvas_name = 'WIP'
        
        self.parser = CommandParser()
        
        # Separate shape registries for each canvas
        self.wip_shapes = {}
        self.main_shapes = {}
        
        # Global stash for temporary storage
        self.stash = {}
        
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
    def get_active_shapes(self):
        """Get the shapes dictionary for the active canvas"""
        if self.active_canvas_name == 'WIP':
            return self.wip_shapes
        else:
            return self.main_shapes
            
    def _sync_active_canvas(self):
        """Sync active canvas's shape list with executor's registry
        
        This is THE FIX for ghost shapes. After any operation that changes
        the registry (delete, stash, promote, etc.), we must sync the canvas.
        """
        if self.active_canvas_name == 'WIP':
            self.wip_canvas.sync_shapes(self.wip_shapes)
        else:
            self.main_canvas.sync_shapes(self.main_shapes)
            
    def execute(self, command_text):
        """Execute a command string"""
        # Parse the command
        cmd_dict = self.parser.parse(command_text)
        command = cmd_dict['command']
        
        # Route to appropriate handler
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
        elif command == 'EXTRACT':
            return self._execute_extract(cmd_dict, command_text)
        elif command == 'DELETE':
            return self._execute_delete(cmd_dict, command_text)
        elif command == 'SWITCH':
            return self._execute_switch(cmd_dict)
        elif command == 'PROMOTE':
            return self._execute_promote(cmd_dict, command_text)
        elif command == 'UNPROMOTE':
            return self._execute_unpromote(cmd_dict, command_text)
        elif command == 'STASH':
            return self._execute_stash(cmd_dict, command_text)
        elif command == 'UNSTASH':
            return self._execute_unstash(cmd_dict, command_text)
        elif command == 'CLEAR':
            return self._execute_clear(cmd_dict)
        elif command == 'LIST':
            return self._execute_list(cmd_dict)
        elif command == 'INFO':
            return self._execute_info(cmd_dict)
        elif command == 'SAVE':
            return self._execute_save(cmd_dict)
        else:
            raise ValueError(f"Unknown command: {command}")
            
    def _execute_line(self, cmd_dict, command_text):
        """Execute LINE command on active canvas"""
        name = cmd_dict['name']
        start = cmd_dict['start']
        end = cmd_dict['end']
        
        shapes = self.get_active_shapes()
        
        if name in shapes:
            raise ValueError(f"Shape '{name}' already exists on {self.active_canvas_name} canvas")
        
        line = Line(name, start, end)
        line.add_history('CREATE', command_text)
        self.active_canvas.add_shape(line)
        shapes[name] = line
        
        return f"Created line '{name}' on {self.active_canvas_name}"
        
    def _execute_poly(self, cmd_dict, command_text):
        """Execute POLY command on active canvas"""
        name = cmd_dict['name']
        points = cmd_dict['points']
        
        shapes = self.get_active_shapes()
        
        if name in shapes:
            raise ValueError(f"Shape '{name}' already exists on {self.active_canvas_name} canvas")
        
        poly = Polygon(name, points)
        poly.add_history('CREATE', command_text)
        self.active_canvas.add_shape(poly)
        shapes[name] = poly
        
        return f"Created polygon '{name}' on {self.active_canvas_name} ({len(points)} points)"
        
    def _execute_move(self, cmd_dict, command_text):
        """Execute MOVE command on active canvas"""
        name = cmd_dict['name']
        delta = cmd_dict['delta']
        
        shapes = self.get_active_shapes()
        
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group, EXTRACT it, or UNGROUP first.")
        
        shape.move(delta[0], delta[1])
        shape.add_history('TRANSFORM', command_text)
        self.active_canvas.redraw()
        
        return f"Moved '{name}' by {delta}"
        
    def _execute_rotate(self, cmd_dict, command_text):
        """Execute ROTATE command on active canvas"""
        name = cmd_dict['name']
        angle = cmd_dict['angle']
        
        shapes = self.get_active_shapes()
        
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group, EXTRACT it, or UNGROUP first.")
        
        shape.rotate(angle)
        shape.add_history('TRANSFORM', command_text)
        self.active_canvas.redraw()
        
        return f"Rotated '{name}' by {angle}°"
        
    def _execute_scale(self, cmd_dict, command_text):
        """Execute SCALE command on active canvas"""
        name = cmd_dict['name']
        factor = cmd_dict['factor']
        
        shapes = self.get_active_shapes()
        
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group, EXTRACT it, or UNGROUP first.")
        
        shape.scale(factor)
        shape.add_history('TRANSFORM', command_text)
        self.active_canvas.redraw()
        
        return f"Scaled '{name}' by {factor}x"
        
    def _execute_resize(self, cmd_dict, command_text):
        """Execute RESIZE command on active canvas"""
        name = cmd_dict['name']
        x_factor = cmd_dict['x_factor']
        y_factor = cmd_dict['y_factor']
        
        shapes = self.get_active_shapes()
        
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "Transform the group, EXTRACT it, or UNGROUP first.")
        
        shape.resize(x_factor, y_factor)
        shape.add_history('TRANSFORM', command_text)
        self.active_canvas.redraw()
        
        if x_factor == y_factor:
            return f"Resized '{name}' by {x_factor}x"
        else:
            return f"Resized '{name}' by {x_factor}x, {y_factor}x"
            
    def _execute_group(self, cmd_dict, command_text):
        """Execute GROUP command on active canvas"""
        group_name = cmd_dict['name']
        member_names = cmd_dict['members']
        
        shapes = self.get_active_shapes()
        
        if group_name in shapes:
            raise ValueError(f"Shape '{group_name}' already exists on {self.active_canvas_name} canvas")
        
        # Collect member shapes
        members = []
        for member_name in member_names:
            if member_name not in shapes:
                raise ValueError(f"Shape '{member_name}' not found on {self.active_canvas_name} canvas")
            
            shape = shapes[member_name]
            
            if shape.attrs['relationships']['group']:
                raise ValueError(f"Shape '{member_name}' is already in group "
                               f"'{shape.attrs['relationships']['group']}'")
            
            members.append(shape)
        
        # Create the group
        group = ShapeGroup(group_name, members)
        group.add_history('CREATE', command_text)
        shapes[group_name] = group
        
        self.active_canvas.redraw()
        
        return f"Created group '{group_name}' with {len(members)} members on {self.active_canvas_name}"
        
    def _execute_ungroup(self, cmd_dict, command_text):
        """Execute UNGROUP command on active canvas"""
        group_name = cmd_dict['name']
        
        shapes = self.get_active_shapes()
        
        if group_name not in shapes:
            raise ValueError(f"Group '{group_name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[group_name]
        
        if not isinstance(shape, ShapeGroup):
            raise ValueError(f"'{group_name}' is not a group")
        
        # Get members and clear their group relationship
        members = shape.attrs['geometry']['members']
        for member in members:
            member.attrs['relationships']['group'] = None
            member.add_history('UNGROUP', command_text)
        
        # Remove the group from registry
        del shapes[group_name]
        
        # SYNC: Rebuild canvas shape list from registry
        self._sync_active_canvas()
        
        return f"Ungrouped '{group_name}' ({len(members)} members now independent)"
        
    def _execute_extract(self, cmd_dict, command_text):
        """Execute EXTRACT command - remove single member from group"""
        member_name = cmd_dict['member']
        group_name = cmd_dict['group']
        
        shapes = self.get_active_shapes()
        
        # Check group exists
        if group_name not in shapes:
            raise ValueError(f"Group '{group_name}' not found on {self.active_canvas_name} canvas")
        
        group = shapes[group_name]
        
        if not isinstance(group, ShapeGroup):
            raise ValueError(f"'{group_name}' is not a group")
        
        # Check member exists in group
        if member_name not in shapes:
            raise ValueError(f"Shape '{member_name}' not found on {self.active_canvas_name} canvas")
        
        member = shapes[member_name]
        
        if member.attrs['relationships']['group'] != group_name:
            raise ValueError(f"Shape '{member_name}' is not in group '{group_name}'")
        
        # Remove member from group
        members = group.attrs['geometry']['members']
        members.remove(member)
        
        # Clear member's group relationship
        member.attrs['relationships']['group'] = None
        member.add_history('EXTRACT', command_text)
        
        # If group is now empty or has only 1 member, delete it
        if len(members) == 0:
            del shapes[group_name]
            self._sync_active_canvas()
            return f"Extracted '{member_name}' from '{group_name}' (group now empty, deleted)"
        elif len(members) == 1:
            last_member = members[0]
            last_member.attrs['relationships']['group'] = None
            del shapes[group_name]
            self._sync_active_canvas()
            return f"Extracted '{member_name}' from '{group_name}' (group dissolved, '{last_member.name}' now independent)"
        
        self.active_canvas.redraw()
        return f"Extracted '{member_name}' from '{group_name}' ({len(members)} members remaining)"
        
    def _execute_delete(self, cmd_dict, command_text):
        """Execute DELETE command - remove shape from active canvas"""
        shape_name = cmd_dict['name']
        confirm = cmd_dict['confirm']
        
        shapes = self.get_active_shapes()
        
        if shape_name not in shapes:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[shape_name]
        
        # Check if shape is in a group
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{shape_name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "EXTRACT it first or UNGROUP the group.")
        
        # Safety check: If it's a group with members, require CONFIRM
        if isinstance(shape, ShapeGroup):
            members = shape.attrs['geometry']['members']
            if len(members) > 0 and not confirm:
                raise ValueError(f"'{shape_name}' is a group with {len(members)} members. "
                               f"Use 'DELETE {shape_name} CONFIRM' to delete it and free its members.")
            
            # Free all members
            for member in members:
                member.attrs['relationships']['group'] = None
        
        # Remove from registry
        del shapes[shape_name]
        
        # SYNC FIX: Rebuild canvas shape list from registry
        self._sync_active_canvas()
        
        return f"Deleted '{shape_name}' from {self.active_canvas_name}"
        
    def _execute_switch(self, cmd_dict):
        """Execute SWITCH command - change active canvas"""
        target = cmd_dict['target']
        
        if target == 'WIP':
            self.active_canvas = self.wip_canvas
            self.active_canvas_name = 'WIP'
        else:  # MAIN
            self.active_canvas = self.main_canvas
            self.active_canvas_name = 'MAIN'
        
        return f"Switched to {self.active_canvas_name} canvas"
        
    def _execute_promote(self, cmd_dict, command_text):
        """Execute PROMOTE command - move/copy shape from WIP to Main"""
        shape_name = cmd_dict['name']
        mode = cmd_dict['mode']
        
        # Check shape exists on WIP
        if shape_name not in self.wip_shapes:
            raise ValueError(f"Shape '{shape_name}' not found on WIP canvas")
        
        # Check shape doesn't already exist on Main
        if shape_name in self.main_shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on MAIN canvas")
        
        shape = self.wip_shapes[shape_name]
        
        # Deep copy the shape
        promoted_shape = copy.deepcopy(shape)
        promoted_shape.add_history('PROMOTE', command_text)
        
        # Add to Main canvas
        self.main_canvas.add_shape(promoted_shape)
        self.main_shapes[shape_name] = promoted_shape
        
        # If move mode, remove from WIP
        if mode == 'move':
            del self.wip_shapes[shape_name]
            # SYNC FIX: Rebuild WIP canvas shape list from registry
            self.wip_canvas.sync_shapes(self.wip_shapes)
            return f"Promoted '{shape_name}' from WIP to MAIN (moved)"
        else:  # copy mode
            return f"Promoted '{shape_name}' from WIP to MAIN (copied)"
        
    def _execute_unpromote(self, cmd_dict, command_text):
        """Execute UNPROMOTE command - move/copy shape from Main to WIP"""
        shape_name = cmd_dict['name']
        mode = cmd_dict['mode']
        
        # Check shape exists on Main
        if shape_name not in self.main_shapes:
            raise ValueError(f"Shape '{shape_name}' not found on MAIN canvas")
        
        # Check shape doesn't already exist on WIP
        if shape_name in self.wip_shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on WIP canvas")
        
        shape = self.main_shapes[shape_name]
        
        # Deep copy the shape
        unpromoted_shape = copy.deepcopy(shape)
        unpromoted_shape.add_history('UNPROMOTE', command_text)
        
        # Add to WIP canvas
        self.wip_canvas.add_shape(unpromoted_shape)
        self.wip_shapes[shape_name] = unpromoted_shape
        
        # If move mode, remove from Main
        if mode == 'move':
            del self.main_shapes[shape_name]
            # SYNC FIX: Rebuild Main canvas shape list from registry
            self.main_canvas.sync_shapes(self.main_shapes)
            return f"Unpromoted '{shape_name}' from MAIN to WIP (moved)"
        else:  # copy mode
            return f"Unpromoted '{shape_name}' from MAIN to WIP (copied)"
            
    def _execute_stash(self, cmd_dict, command_text):
        """Execute STASH command - move shape to temporary storage"""
        shape_name = cmd_dict['name']
        
        shapes = self.get_active_shapes()
        
        if shape_name not in shapes:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
        
        if shape_name in self.stash:
            raise ValueError(f"Shape '{shape_name}' already in stash")
        
        shape = shapes[shape_name]
        
        # Check if shape is in a group
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{shape_name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "EXTRACT it first or UNGROUP the group.")
        
        # Deep copy and add to stash
        stashed_shape = copy.deepcopy(shape)
        stashed_shape.add_history('STASH', command_text)
        self.stash[shape_name] = stashed_shape
        
        # Remove from active canvas
        del shapes[shape_name]
        
        # SYNC FIX: Rebuild canvas shape list from registry
        self._sync_active_canvas()
        
        return f"Stashed '{shape_name}' from {self.active_canvas_name}"
        
    def _execute_unstash(self, cmd_dict, command_text):
        """Execute UNSTASH command - restore shape from stash to active canvas"""
        shape_name = cmd_dict['name']
        mode = cmd_dict['mode']
        
        if shape_name not in self.stash:
            raise ValueError(f"Shape '{shape_name}' not found in stash")
        
        shapes = self.get_active_shapes()
        
        if shape_name in shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on {self.active_canvas_name} canvas")
        
        # Deep copy from stash
        unstashed_shape = copy.deepcopy(self.stash[shape_name])
        unstashed_shape.add_history('UNSTASH', command_text)
        
        # Add to active canvas
        self.active_canvas.add_shape(unstashed_shape)
        shapes[shape_name] = unstashed_shape
        
        # Only remove from stash if MOVE mode
        if mode == 'move':
            del self.stash[shape_name]
            return f"Unstashed '{shape_name}' to {self.active_canvas_name} (removed from stash)"
        else:
            return f"Unstashed '{shape_name}' to {self.active_canvas_name} (kept in stash)"
        
    def _execute_clear(self, cmd_dict):
        """Execute CLEAR command on specified or active canvas"""
        target = cmd_dict['target']
        all_flag = cmd_dict['all']
        
        if target is None:
            target = self.active_canvas_name
        
        # STASH doesn't require ALL (it's meant for temporary storage)
        if target == 'STASH':
            self.stash.clear()
            return "Stash cleared"
        
        # Canvas clearing requires ALL for safety
        if not all_flag:
            raise ValueError(f"Clearing {target} canvas requires ALL keyword for safety. "
                           f"Use: CLEAR {target} ALL")
        
        if target == 'WIP':
            self.wip_canvas.clear()
            self.wip_shapes.clear()
            return "WIP canvas cleared"
        else:  # MAIN
            self.main_canvas.clear()
            self.main_shapes.clear()
            return "MAIN canvas cleared"
        
    def _execute_list(self, cmd_dict):
        """Execute LIST command on specified or active canvas"""
        target = cmd_dict['target']
        
        if target is None:
            target = self.active_canvas_name
        
        if target == 'WIP':
            shapes = self.wip_shapes
        elif target == 'MAIN':
            shapes = self.main_shapes
        else:  # STASH
            shapes = self.stash
        
        if not shapes:
            return f"No shapes in {target}"
        
        shapes_info = []
        for name, shape in shapes.items():
            shape_type = shape.attrs['type']
            
            if isinstance(shape, ShapeGroup):
                member_count = len(shape.attrs['geometry']['members'])
                shapes_info.append(f"{name} (Group: {member_count} members)")
            else:
                group = shape.attrs['relationships']['group']
                if group:
                    shapes_info.append(f"{name} ({shape_type}, in group '{group}')")
                else:
                    shapes_info.append(f"{name} ({shape_type})")
        
        if target in ['WIP', 'MAIN']:
            return f"{target} canvas shapes:\n  " + "\n  ".join(shapes_info)
        else:
            return f"Stash:\n  " + "\n  ".join(shapes_info)
            
    def _execute_info(self, cmd_dict):
        """Execute INFO command - show detailed shape information"""
        shape_name = cmd_dict['name']
        
        # Search for shape in WIP, MAIN, and stash
        shape = None
        location = None
        
        if shape_name in self.wip_shapes:
            shape = self.wip_shapes[shape_name]
            location = 'WIP'
        elif shape_name in self.main_shapes:
            shape = self.main_shapes[shape_name]
            location = 'MAIN'
        elif shape_name in self.stash:
            shape = self.stash[shape_name]
            location = 'STASH'
        else:
            raise ValueError(f"Shape '{shape_name}' not found on any canvas or stash")
        
        # Build info string
        info = [f"Shape: {shape_name}"]
        info.append(f"Location: {location}")
        info.append(f"Type: {shape.attrs['type']}")
        
        # Geometry info
        geom = shape.attrs['geometry']
        if shape.attrs['type'] == 'Line':
            info.append(f"Start: {geom['start']}")
            info.append(f"End: {geom['end']}")
        elif shape.attrs['type'] == 'Polygon':
            info.append(f"Vertices: {len(geom['points'])}")
            info.append(f"Points: {geom['points']}")
        elif shape.attrs['type'] == 'ShapeGroup':
            members = geom['members']
            info.append(f"Members ({len(members)}): {[m.name for m in members]}")
        
        # Style info
        style = shape.attrs['style']
        info.append(f"Color: {style['color']}")
        info.append(f"Width: {style['width']}")
        
        # Relationships
        rel = shape.attrs['relationships']
        if rel['group']:
            info.append(f"In group: {rel['group']}")
        
        # History (last 5 commands)
        history = shape.attrs['history']
        if history:
            info.append(f"History (last 5):")
            for action_type, command, timestamp in history[-5:]:
                info.append(f"  [{action_type}] {command}")
        
        return "\n".join(info)
        
    def _execute_save(self, cmd_dict):
        """Execute SAVE command - always saves MAIN canvas"""
        filename = cmd_dict['filename']
        filepath = os.path.join('output', filename)
        
        # Always save the MAIN canvas
        self.main_canvas.save(filepath)
        
        return f"Saved MAIN canvas to {filepath}"