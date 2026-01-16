"""
Command executor for Shape Studio - Phase 5
Adds RUN and BATCH commands for script execution and dataset generation
Plus PROC system for procedural generation
"""
import os
import json
import copy
import random
from pathlib import Path
from datetime import datetime
from src.core.shape import Line, Polygon, ShapeGroup
from src.commands.parser import CommandParser
from src.core.procedural import ProceduralGenerators
from src.core.templates import TemplateLibrary, TemplateExecutor
from src.config import config
from src.core.enhancement import EnhancementRegistry

class CommandExecutor:
    """Execute commands on WIP or Main canvas"""
    
    def __init__(self, wip_canvas, main_canvas):
        self.wip_canvas = wip_canvas
        self.main_canvas = main_canvas
        self.active_canvas = wip_canvas  # Start with WIP active
        self.active_canvas_name = 'WIP'
        
        self.parser = CommandParser()
        self.procedural_gen = ProceduralGenerators() 
        self.template_library = TemplateLibrary(project_root='.')
        self.template_executor = TemplateExecutor(self.template_library, self)
        self.enhancement_registry = EnhancementRegistry()
        
        # Separate shape registries for each canvas
        self.wip_shapes = {}
        self.main_shapes = {}
        
        # Global stash for temporary storage
        self.stash = {}

        # Persistence directories
        self.project_store_dir = Path(config.paths.shapes)
        self.global_store_dir = config.paths.global_library
        self.projects_dir = Path(config.paths.projects)
        self.scripts_dir = Path(config.paths.scripts)
        
        # Create directories
        os.makedirs('output', exist_ok=True)
        os.makedirs(self.project_store_dir, exist_ok=True)
        os.makedirs(self.global_store_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        
    def get_active_shapes(self):
        """Get the shapes dictionary for the active canvas"""
        if self.active_canvas_name == 'WIP':
            return self.wip_shapes
        else:
            return self.main_shapes
            
    def _sync_active_canvas(self):
        """Sync active canvas's shape list with executor's registry"""
        if self.active_canvas_name == 'WIP':
            self.wip_canvas.sync_shapes(self.wip_shapes)
        else:
            self.main_canvas.sync_shapes(self.main_shapes)
            
    def execute(self, command_text):
        """Execute a command string"""
        # Parse the command
        cmd_dict = self.parser.parse(command_text)
        command = cmd_dict['command']

        # Route to handler
        handlers = {
            'LINE': self._execute_line,
            'POLY': self._execute_poly,
            'MOVE': self._execute_move,
            'ROTATE': self._execute_rotate,
            'SCALE': self._execute_scale,
            'RESIZE': self._execute_resize,
            'GROUP': self._execute_group,
            'UNGROUP': self._execute_ungroup,
            'EXTRACT': self._execute_extract,
            'DELETE': self._execute_delete,
            'SWITCH': self._execute_switch,
            'PROMOTE': self._execute_promote,
            'UNPROMOTE': self._execute_unpromote,
            'STASH': self._execute_stash,
            'UNSTASH': self._execute_unstash,
            'STORE': self._execute_store,
            'LOAD': self._execute_load,
            'SAVE_PROJECT': self._execute_save_project,
            'LOAD_PROJECT': self._execute_load_project,
            'CLEAR': self._execute_clear,
            'LIST': self._execute_list,
            'INFO': self._execute_info,
            'SAVE': self._execute_save,
            'RUN': self._execute_run,
            'BATCH': self._execute_batch,
            'PROC': self._execute_proc,
            'LIST_PRESET': self._execute_list_preset,
            'INFO_PROC': self._execute_info_proc,
            'ANIMATE': self._execute_animate,
            'COLOR': self._execute_color,
            'WIDTH': self._execute_width,
            'FILL': self._execute_fill,
            'ALPHA': self._execute_alpha,
            'ZORDER': self._execute_zorder,
            'EXIT': self._execute_exit,
            'VALIDATE': self._execute_validate,
            'RESET_ZORDER': self._execute_reset_zorder,
            'ENHANCE': self._execute_enhance,
        }
        
        if command in handlers:
            return handlers[command](cmd_dict, command_text)
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
        
    def _execute_switch(self, cmd_dict, command_text):
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
        
    def _execute_clear(self, cmd_dict, command_text):
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
        
    def _execute_info(self, cmd_dict, command_text):
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
        elif len(cmd_dict) >= 1 and cmd_dict[0].upper() == 'ENHANCE':
            if len(cmd_dict) < 2:
                return "Usage: INFO ENHANCE <method>"
            method_name = cmd_dict[1].lower()
            return self._info_enhance_method(method_name)
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
        info.append(f"Z-Order: {style['z_coord']}")

        # Relationships
        rel = shape.attrs['relationships']
        if rel['group']:
            info.append(f"In group: {rel['group']}")
        
        # Procedural info
        proc = shape.attrs.get('procedure')
        if proc:
            info.append("")
            info.append("Procedural Generation:")
            info.append(f"  Method: {proc.get('method', 'unknown')}")
            
            # Statistics
            stats = proc.get('statistics', {})
            if stats:
                info.append(f"  Successful: {stats.get('successful_modifications', 0)}")
                info.append(f"  Failed: {stats.get('failed_attempts', 0)}")
            
            # Debug log
            debug_log = proc.get('debug_log')
            if debug_log:
                info.append("")
                info.append(self._format_debug_log(debug_log))

        # History (last 5 commands)
        history = shape.attrs['history']
        if history:
            info.append(f"History (last 5):")
            for action_type, command, timestamp in history[-5:]:
                info.append(f"  [{action_type}] {command}")
        
        return "\n".join(info)
        
    def _execute_save(self, cmd_dict, command_text):
        """Execute SAVE command - always saves MAIN canvas"""
        filename = cmd_dict['filename']
        filepath = os.path.join(config.paths.output, filename)
        
        # Always save the MAIN canvas
        self.main_canvas.save(filepath)
        
        return f"Saved MAIN canvas to {filepath}"
    
    def _execute_store(self, cmd_dict, command_text):
        """Execute STORE command - save shape to object store"""
        shape_name = cmd_dict['name']
        scope = cmd_dict['scope']
        
        # Find shape in WIP, MAIN, or stash
        shape = None
        if shape_name in self.wip_shapes:
            shape = self.wip_shapes[shape_name]
        elif shape_name in self.main_shapes:
            shape = self.main_shapes[shape_name]
        elif shape_name in self.stash:
            shape = self.stash[shape_name]
        else:
            raise ValueError(f"Shape '{shape_name}' not found")
        
        # Serialize shape
        shape_data = self._serialize_shape(shape)
        
        # Determine save directory
        if scope == 'global':
            save_dir = self.global_store_dir
        else:
            save_dir = self.project_store_dir
        
        # Save to file
        filepath = save_dir / f"{shape_name}.json"
        with open(filepath, 'w') as f:
            json.dump(shape_data, f, indent=2)
        
        scope_name = "global library" if scope == 'global' else "project store"
        return f"Stored '{shape_name}' to {scope_name}: {filepath}"
    
    def _execute_load(self, cmd_dict, command_text):
        """Execute LOAD command - load shape from object store"""
        shape_name = cmd_dict['name']
        
        shapes = self.get_active_shapes()
        if shape_name in shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on {self.active_canvas_name} canvas")
        
        # Search project store first, then global
        filepath = self.project_store_dir / f"{shape_name}.json"
        source = "project store"
        
        if not filepath.exists():
            filepath = self.global_store_dir / f"{shape_name}.json"
            source = "global library"
        
        if not filepath.exists():
            raise ValueError(f"Shape '{shape_name}' not found in project store or global library")
        
        # Load and deserialize
        with open(filepath, 'r') as f:
            shape_data = json.load(f)
        
        shape = self._deserialize_shape(shape_data)
        shape.add_history('LOAD', command_text)
        
        # Add to active canvas
        self.active_canvas.add_shape(shape)
        shapes[shape_name] = shape
        
        return f"Loaded '{shape_name}' from {source} to {self.active_canvas_name}"
    
    def _execute_save_project(self, cmd_dict, command_text):
        """Execute SAVE_PROJECT command - save entire session"""
        filename = cmd_dict['filename']
        filepath = self.projects_dir / filename
        
        # Build project data
        project_data = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'wip_shapes': {name: self._serialize_shape(shape) 
                          for name, shape in self.wip_shapes.items()},
            'main_shapes': {name: self._serialize_shape(shape) 
                           for name, shape in self.main_shapes.items()},
            'stash': {name: self._serialize_shape(shape) 
                     for name, shape in self.stash.items()},
            'canvas_settings': {
                'show_grid': self.wip_canvas.show_grid,
                'show_rulers': self.wip_canvas.show_rulers
            },
            'active_canvas': self.active_canvas_name
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return f"Saved project to {filepath}"
    
    def _execute_load_project(self, cmd_dict, command_text):
        """Execute LOAD_PROJECT command - load entire session"""
        filename = cmd_dict['filename']
        filepath = self.projects_dir / filename
        
        if not filepath.exists():
            raise ValueError(f"Project file not found: {filepath}")
        
        # Load project data
        with open(filepath, 'r') as f:
            project_data = json.load(f)
        
        # Clear current state
        self.wip_shapes.clear()
        self.main_shapes.clear()
        self.stash.clear()
        self.wip_canvas.clear()
        self.main_canvas.clear()
        
        # Restore WIP shapes
        for name, shape_data in project_data['wip_shapes'].items():
            shape = self._deserialize_shape(shape_data)
            self.wip_shapes[name] = shape
            self.wip_canvas.add_shape(shape)
        
        # Restore MAIN shapes
        for name, shape_data in project_data['main_shapes'].items():
            shape = self._deserialize_shape(shape_data)
            self.main_shapes[name] = shape
            self.main_canvas.add_shape(shape)
        
        # Restore stash
        for name, shape_data in project_data['stash'].items():
            shape = self._deserialize_shape(shape_data)
            self.stash[name] = shape
        
        # Restore canvas settings
        settings = project_data.get('canvas_settings', {})
        self.wip_canvas.show_grid = settings.get('show_grid', True)
        self.wip_canvas.show_rulers = settings.get('show_rulers', True)
        self.main_canvas.show_grid = settings.get('show_grid', True)
        self.main_canvas.show_rulers = settings.get('show_rulers', True)
        
        # Restore active canvas
        active = project_data.get('active_canvas', 'WIP')
        if active == 'MAIN':
            self.active_canvas = self.main_canvas
            self.active_canvas_name = 'MAIN'
        else:
            self.active_canvas = self.wip_canvas
            self.active_canvas_name = 'WIP'
        
        # Redraw both canvases
        self.wip_canvas.redraw()
        self.main_canvas.redraw()
        
        wip_count = len(self.wip_shapes)
        main_count = len(self.main_shapes)
        stash_count = len(self.stash)
        
        return f"Loaded project from {filepath} (WIP: {wip_count}, MAIN: {main_count}, Stash: {stash_count})"
    
    def _execute_run(self, cmd_dict, command_text):
        """Execute RUN command - routes to text or JSON handlers"""
        scriptfile = cmd_dict['scriptfile']
        filepath = self.scripts_dir / scriptfile
        
        if not filepath.exists():
            raise ValueError(f"Script file not found: {filepath}")
        
        
        # Route based on file extension
        if scriptfile.endswith('.txt'):
            # Plain text file - execute line by line
            label = cmd_dict.get('executable')
            return self._execute_run_text(scriptfile, label)
        
        elif scriptfile.endswith('.json'):
            # JSON template file
            section_name = cmd_dict.get('executable')  # May be None
            return self._execute_run_json(scriptfile, section_name)
        
        else:
            # Unknown extension - try to detect format by content
            try:
                with open(filepath, 'r') as f:
                    first_char = f.read(1)
                
                if first_char == '[' or first_char == '{':
                    # Looks like JSON
                    section_name = cmd_dict.get('executable')
                    return self._execute_run_json(scriptfile, section_name)
                else:
                    # Treat as text
                    return self._execute_run_text(scriptfile)
                    
            except Exception as e:
                raise ValueError(f"Could not determine format of {scriptfile}: {e}")

    def _execute_run_text(self, scriptfile, label=None):
        """Execute plain text script file, optionally jumping to a labeled section
        
        Args:
            scriptfile: Name of script file (e.g., 'test.txt')
            label: Optional label to jump to (e.g., 'test2')
            
        File format:
            @label_name       # Label marker (line must start with @)
            command1          # Commands for this section
            command2
            EOF               # End of section marker
            
            @another_label
            command3
            EOF
            
        If no label specified: Executes from start until first EOF or end of file
        If label specified: Executes only that labeled section
        """
        filepath = self.scripts_dir / scriptfile
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Parse file into sections
        sections = self._parse_text_sections(lines)
        
        if label:
            # Execute specific labeled section
            if label not in sections:
                available = list(sections.keys())
                raise ValueError(
                    f"Label '{label}' not found in {scriptfile}\n"
                    f"Available labels: {', '.join(available) if available else '(none)'}\n"
                    f"Use: RUN {scriptfile} <label>"
                )
            
            commands = sections[label]
            section_desc = f"section '{label}'"
        else:
            # Execute default section (unlabeled commands or first section)
            if '' in sections:
                # There are unlabeled commands at the start
                commands = sections['']
                section_desc = "unlabeled section"
            elif sections:
                # Use first labeled section
                first_label = list(sections.keys())[0]
                commands = sections[first_label]
                section_desc = f"section '{first_label}' (first section)"
            else:
                return f"Script '{scriptfile}' contains no commands"
        
        # Execute commands
        results = []
        for i, cmd in enumerate(commands, 1):
            try:
                result = self.execute(cmd)
                results.append(f"  [{i}] {cmd[:60]}{'...' if len(cmd) > 60 else ''} → {result}")
            except Exception as e:
                results.append(f"  [{i}] {cmd[:60]}{'...' if len(cmd) > 60 else ''} → ERROR: {str(e)}")
        
        header = f"Executed {len(commands)} commands from '{scriptfile}' ({section_desc}):"
        return header + "\n" + "\n".join(results)

    def _execute_run_json(self, scriptfile, section_name=None):
        """Execute RUN command with JSON script file"""
        filepath = self.scripts_dir / scriptfile
        
        if not filepath.exists():
            raise ValueError(f"Script file not found: {filepath}")
        
        # Load and validate JSON file
        json_data = self._load_json_file(filepath)
        
        # Select section
        section_data, actual_section_name = self._select_section(json_data, section_name, scriptfile)
        
        # Validate section
        self._validate_section(section_data, actual_section_name)
        
        # Execute commands
        commands = section_data['commands']
        results = []
        
        # Display section info
        results.append(f"Running section '{actual_section_name}' from {scriptfile}")
        
        if 'description' in section_data:
            results.append(f"Description: {section_data['description']}")
        
        results.append("")

        # Execute each command (string or dict)
        for i, cmd in enumerate(commands, 1):
            try:
                if isinstance(cmd, str):
                    # String command - parse and execute as before
                    result = self.execute(cmd)
                    results.append(f"  [{i}] {cmd} → {result}")
                elif isinstance(cmd, dict):
                    # Structured command - convert and execute
                    cmd_display = self._format_structured_command(cmd)
                    result = self._execute_structured_command(cmd)
                    results.append(f"  [{i}] {cmd_display} → {result}")
                else:
                    results.append(f"  [{i}] ERROR: Command must be string or dict, got {type(cmd).__name__}")
            except Exception as e:
                if isinstance(cmd, str):
                    results.append(f"  [{i}] {cmd} → ERROR: {str(e)}")
                else:
                    cmd_display = self._format_structured_command(cmd)
                    results.append(f"  [{i}] {cmd_display} → ERROR: {str(e)}")
        
        return "\n".join(results)

    def _execute_batch(self, cmd_dict, command_text):
        """Execute BATCH command - supports templated executables with randomization"""
        count = cmd_dict['count']
        scriptfile = cmd_dict['scriptfile']
        output_prefix = cmd_dict['output_prefix']
        target_canvas = cmd_dict['target_canvas']
        executable_name = cmd_dict.get('executable')
        
        filepath = self.scripts_dir / scriptfile
        
        if not filepath.exists():
            raise ValueError(f"Script file not found: {filepath}")
        
        # Check if this is templated script
        with open(filepath, 'r') as f:
            first_char = f.read(1)
        
        if first_char == '{':
            # Templated format
            if not executable_name:
                raise ValueError(
                    f"Script {scriptfile} uses template format.\n"
                    f"Specify executable: BATCH <count> {scriptfile} <executable_name> <prefix>"
                )
            
            return self._execute_batch_templated(
                count, filepath, executable_name, output_prefix, target_canvas
            )
        else:
            # Old format - existing behavior
            return self._execute_batch_legacy(
                count, filepath, output_prefix, target_canvas
            )

    def _execute_batch_templated(self, count, filepath, executable_name, 
                                output_prefix, target_canvas):
        """Execute BATCH with templated script
        
        Supports:
        - Single executable: BATCH 100 script.json exec1 prefix
        - Multiple executables: BATCH 100 script.json exec1,exec2,exec3 prefix
        - All executables: BATCH 100 script.json --ALL prefix
        """
        # Load script to get executables
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        executables = data.get('executables', {})
        if not executables:
            raise ValueError(f"No executables found in {filepath}")
        
        # NEW: Determine which executables to run (copied from execute_script logic)
        if executable_name is None or executable_name == '--ALL':
            exec_names = list(executables.keys())
        elif ',' in executable_name:
            # Multiple executables specified
            exec_names = [n.strip() for n in executable_name.split(',')]
        else:
            exec_names = [executable_name]
        
        # NEW: Validate all executables exist before starting
        for name in exec_names:
            if name not in executables:
                available = ', '.join(executables.keys())
                raise ValueError(
                    f"Executable '{name}' not found in {filepath}\n"
                    f"Available: {available}"
                )
        
        # Switch to target canvas
        original_canvas = self.active_canvas_name
        if target_canvas != original_canvas:
            self.execute(f"SWITCH {target_canvas}")
        
        save_canvas = self.wip_canvas if target_canvas == 'WIP' else self.main_canvas
        
        results = []
        successful = 0
        
        # NEW: Outer loop over executables
        for exec_name in exec_names:
            executable = executables[exec_name]
            
            # NEW: Add executable name to prefix if running multiple
            if len(exec_names) > 1:
                exec_prefix = f"{output_prefix}_{exec_name}"
            else:
                exec_prefix = output_prefix
            
            # Inner loop over iterations
            for i in range(1, count + 1):
                try:
                    # Generate randomization values for this iteration
                    randomization = self.template_executor.generate_randomization(executable)
                    
                    # Execute the script with randomization
                    self.template_executor.execute_script(
                        filepath, exec_name,
                        batch_mode=True,
                        randomization_values=randomization
                    )
                    
                    # Save output
                    output_file = f"output/{exec_prefix}_{i:04d}.png"
                    save_canvas.save_png(output_file)
                    successful += 1
                    
                    # Clear for next iteration
                    if target_canvas == 'WIP':
                        self.wip_shapes.clear()
                    else:
                        self.main_shapes.clear()
                    save_canvas.clear()
                    self._sync_active_canvas()
                    
                except Exception as e:
                    results.append(f"  Iteration {i} failed: {e}")
        
        # Switch back to original canvas
        if target_canvas != original_canvas:
            self.execute(f"SWITCH {original_canvas}")
        
        # NEW: Better summary message for multiple executables
        if len(exec_names) > 1:
            total_expected = count * len(exec_names)
            return f"BATCH completed: {successful}/{total_expected} successful across {len(exec_names)} executables"
        else:
            return f"BATCH completed: {successful}/{count} successful"

    def _execute_batch_legacy(self, count, filepath, output_prefix, target_canvas):
        """Execute BATCH with old-style script (existing behavior)"""
        # This is the original BATCH implementation for backwards compatibility
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        commands = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append((line_num, line))
        
        if not commands:
            raise ValueError(f"Script '{filepath}' contains no commands")
        
        original_canvas = self.active_canvas_name
        if target_canvas != original_canvas:
            self.execute(f"SWITCH {target_canvas}")
        
        save_canvas = self.wip_canvas if target_canvas == 'WIP' else self.main_canvas
        
        results = []
        successful = 0
        
        for i in range(1, count + 1):
            try:
                for line_num, cmd in commands:
                    try:
                        self.execute(cmd)
                    except Exception as e:
                        half_point = len(commands) // 2
                        if half_point > 0:
                            recovery_idx = random.randint(0, half_point - 1)
                            recovery_line_num, recovery_cmd = commands[recovery_idx]
                            for j in range(recovery_idx, len(commands)):
                                try:
                                    _, cmd_to_run = commands[j]
                                    self.execute(cmd_to_run)
                                except:
                                    pass
                
                output_filename = f"{output_prefix}_{i:03d}.png"
                output_path = Path('output') / output_filename
                save_canvas.save(str(output_path))
                
                successful += 1
                results.append(f"  [{i}/{count}] Generated {output_filename}")
                
            except Exception as e:
                results.append(f"  [{i}/{count}] FAILED: {str(e)}")
        
        if target_canvas != original_canvas:
            self.execute(f"SWITCH {original_canvas}")
        
        summary = f"BATCH complete: {successful}/{count} successful\n" + "\n".join(results)
        return summary


    def _execute_batch_json(self, count, scriptfile, section_name, output_prefix, target_canvas):
        """Execute BATCH command with JSON script file"""
        filepath = self.scripts_dir / scriptfile
        
        if not filepath.exists():
            raise ValueError(f"Script file not found: {filepath}")
        
        # Section name is required for JSON batch
        if not section_name:
            raise ValueError(f"Section name required for BATCH with JSON files")
        
        # Load and validate JSON file
        json_data = self._load_json_file(filepath)
        
        # Select section
        section_data, actual_section_name = self._select_section(json_data, section_name, scriptfile)
        
        # Validate section
        self._validate_section(section_data, actual_section_name)
        
        # Switch to target canvas for the batch
        original_canvas = self.active_canvas_name
        if target_canvas != original_canvas:
            self.execute(f"SWITCH {target_canvas}")
        
        # Get the canvas to save from
        if target_canvas == 'WIP':
            save_canvas = self.wip_canvas
        else:
            save_canvas = self.main_canvas
        
        # Execute batch iterations
        commands = section_data['commands']
        results = []
        successful = 0
        
        results.append(f"Running section '{actual_section_name}' from {scriptfile} ({count} iterations)")
        
        if 'description' in section_data:
            results.append(f"Description: {section_data['description']}")
        
        results.append("")
        
        for i in range(1, count + 1):
            try:
                # Execute all commands in section (string or dict)
                for cmd in commands:
                    try:
                        if isinstance(cmd, str):
                            self.execute(cmd)
                        elif isinstance(cmd, dict):
                            self._execute_structured_command(cmd)
                    except Exception as e:
                        # On error: randomly branch to a line in first 50% of script
                        half_point = len(commands) // 2
                        if half_point > 0:
                            recovery_idx = random.randint(0, half_point - 1)
                            
                            # Continue from there
                            for j in range(recovery_idx, len(commands)):
                                try:
                                    cmd_to_run = commands[j]
                                    if isinstance(cmd_to_run, str):
                                        self.execute(cmd_to_run)
                                    else:
                                        self._execute_structured_command(cmd_to_run)
                                except:
                                    pass  # Best effort recovery
                        # If recovery fails or not possible, just continue with save
                
                # Save the current state
                output_filename = f"{output_prefix}_{i:03d}.png"
                output_path = Path('output') / output_filename
                save_canvas.save(str(output_path))
                
                successful += 1
                results.append(f"  [{i}/{count}] Generated {output_filename}")
                
            except Exception as e:
                results.append(f"  [{i}/{count}] FAILED: {str(e)}")
        
        # Restore original canvas if changed
        if target_canvas != original_canvas:
            self.execute(f"SWITCH {original_canvas}")
        
        summary = f"\nBATCH complete: {successful}/{count} successful"
        return "\n".join(results) + summary

    def _load_json_file(self, filepath):
        """Load and parse JSON file with basic validation"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath.name}: {str(e)}")
        
        # Validate top level structure
        if not isinstance(data, dict):
            raise ValueError(f"JSON file must contain a dictionary at top level")
        
        if len(data) == 0:
            raise ValueError(f"JSON file contains no sections")
        
        return data

    def _select_section(self, json_data, section_name, scriptfile):
        """Select a section from JSON data
        
        Args:
            json_data: Loaded JSON dictionary
            section_name: Name of section to select (None for auto-select)
            scriptfile: Name of script file (for error messages)
            
        Returns:
            Tuple of (section_data, actual_section_name)
        """
        available_sections = list(json_data.keys())
        
        # If no section specified
        if section_name is None:
            if len(available_sections) == 1:
                # Auto-run single section
                section_name = available_sections[0]
                return json_data[section_name], section_name
            else:
                # Multiple sections - require explicit selection
                sections_list = "\n     - ".join(available_sections)
                raise ValueError(
                    f"Multiple sections found. Specify which to run.\n"
                    f"   Available sections:\n"
                    f"     - {sections_list}\n"
                    f"   Usage: RUN {scriptfile} <section_name>"
                )
        
        # Section name specified - validate it exists
        if section_name not in json_data:
            sections_list = "\n     - ".join(available_sections)
            raise ValueError(
                f"Section '{section_name}' not found in {scriptfile}\n"
                f"   Available sections:\n"
                f"     - {sections_list}"
            )
        
        return json_data[section_name], section_name

    def _validate_section(self, section_data, section_name):
        """Validate section structure (Phase 2: supports string and dict commands)
        
        Args:
            section_data: Section dictionary
            section_name: Name of section (for error messages)
        """
        if not isinstance(section_data, dict):
            raise ValueError(f"Section '{section_name}' must be a dictionary")
        
        # Check for required 'commands' key
        if 'commands' not in section_data:
            raise ValueError(f"Section '{section_name}' missing required 'commands' array")
        
        commands = section_data['commands']
        
        # Validate commands is an array
        if not isinstance(commands, list):
            raise ValueError(f"Section '{section_name}' - 'commands' must be an array")
        
        # Validate array is not empty
        if len(commands) == 0:
            raise ValueError(f"Section '{section_name}' has empty commands array")
        
        # Phase 2: Validate commands are strings or dicts
        for i, cmd in enumerate(commands):
            if not isinstance(cmd, (str, dict)):
                raise ValueError(
                    f"Section '{section_name}' - command {i+1} must be a string or dict "
                    f"(got {type(cmd).__name__})"
                )
            
            # If dict, validate basic structure
            if isinstance(cmd, dict):
                # Skip underscore fields (comments)
                if not any(k for k in cmd.keys() if not k.startswith('_')):
                    raise ValueError(
                        f"Section '{section_name}' - command {i+1} has only underscore fields "
                        f"(all fields ignored)"
                    )
                
                # Must have 'command' field
                if 'command' not in cmd:
                    raise ValueError(
                        f"Section '{section_name}' - command {i+1} (dict) missing 'command' field"
                    )
            
    def _serialize_shape(self, shape):
        """Convert shape to JSON-serializable dict"""
        data = {
            'name': shape.name,
            'type': shape.attrs['type'],
            'attrs': {}
        }
        
        # Deep copy attrs to avoid modifying original
        attrs = copy.deepcopy(shape.attrs)
        
        # Handle geometry - convert ShapeGroup members to names only
        if isinstance(shape, ShapeGroup):
            members = attrs['geometry']['members']
            attrs['geometry']['members'] = [m.name for m in members]
        
        data['attrs'] = attrs
        return data
    
    def _deserialize_shape(self, data):
        """Recreate shape from JSON data"""
        shape_type = data['type']
        name = data['name']
        attrs = data['attrs']
        geom = attrs['geometry']
        
        if shape_type == 'Line':
            shape = Line(name, tuple(geom['start']), tuple(geom['end']))
        elif shape_type == 'Polygon':
            points = [tuple(p) for p in geom['points']]
            shape = Polygon(name, points)
        elif shape_type == 'ShapeGroup':
            # For groups, we'll handle member reconstruction later
            # For now, create empty group (members will be linked in second pass)
            shape = ShapeGroup(name, [])
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
        
        # Restore attrs
        shape.attrs = attrs
        
        return shape
    
    def _execute_list(self, cmd_dict, command_text):
        """Execute LIST command - extended to include stores and PROC"""
        """Execute LIST command - extended to include EXECUTABLES"""
        target = cmd_dict['target']
        
        if target is None:
            target = self.active_canvas_name
        
        if target == 'EXECUTABLES':
            scriptfile = cmd_dict.get('scriptfile')
            if not scriptfile:
                raise ValueError("LIST EXECUTABLES requires scriptfile")
            
            filepath = self.scripts_dir / scriptfile
            if not filepath.exists():
                raise ValueError(f"Script file not found: {filepath}")
            
            return self.template_executor.list_executables(filepath)
        
        if target == 'WIP':
            shapes = self.wip_shapes
        elif target == 'MAIN':
            shapes = self.main_shapes
        elif target == 'STASH':
            shapes = self.stash
        elif target == 'STORE':
            return self._list_store(self.project_store_dir, "project store")
        elif target == 'GLOBAL':
            return self._list_store(self.global_store_dir, "global library")
        elif target == 'PROC':
            # List available procedural methods
            methods = self.procedural_gen.list_methods()
            return "Available procedural methods:\n  " + "\n  ".join(methods)
        elif target == 'ENHANCE':
            return self._list_enhance_methods()
        else:
            raise ValueError(f"Unknown LIST target: {target}")
        
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
    
    def _list_store(self, store_dir, store_name):
        """List shapes in a store directory"""
        json_files = list(store_dir.glob('*.json'))
        
        if not json_files:
            return f"No shapes in {store_name}"
        
        shapes_info = []
        for filepath in sorted(json_files):
            shape_name = filepath.stem
            # Load to get type
            with open(filepath, 'r') as f:
                data = json.load(f)
            shape_type = data['type']
            shapes_info.append(f"{shape_name} ({shape_type})")
        
        return f"{store_name.title()} ({len(json_files)} shapes):\n  " + "\n  ".join(shapes_info)
    
    def _execute_proc(self, cmd_dict, command_text):
        """Execute PROC command - call procedural generation method"""
        method_name = cmd_dict['method']
        shape_name = cmd_dict['name']
        params = cmd_dict['params']
        
        # Call procedural generator
        result = self.procedural_gen.call(method_name, shape_name, params)
        
        shapes = self.get_active_shapes()
        
        # Handle different return types
        if isinstance(result, list):
            # Multiple shapes - add each individually
            snapshot_count = 0
            final_shape = None
            
            for shape in result:
                if shape.name in shapes:
                    raise ValueError(f"Shape '{shape.name}' already exists on {self.active_canvas_name} canvas")
                shapes[shape.name] = shape
                self.active_canvas.add_shape(shape)
                
                # Track snapshots vs final
                if shape.attrs.get('procedure', {}).get('is_snapshot'):
                    snapshot_count += 1
                elif shape.attrs.get('procedure', {}).get('is_final'):
                    snapshot_count += 1
                    final_shape = shape
                else:
                    final_shape = shape
            
            if snapshot_count > 0:
                return (f"Created {shape_name} with {snapshot_count} iteration snapshots on {self.active_canvas_name}\n"
                        f"Use 'INFO {shape_name}' to see generation details\n"
                        f"Snapshots: {shape_name}_iter_0 through {shape_name}_final")
            else:
                shape_names = ', '.join(s.name for s in result)
                return f"Created {len(result)} shapes on {self.active_canvas_name}: {shape_names}"
        
        elif isinstance(result, (Polygon, Line, ShapeGroup)):
            # Single shape
            if shape_name in shapes:
                raise ValueError(f"Shape '{shape_name}' already exists on {self.active_canvas_name} canvas")
            
            shapes[shape_name] = result
            self.active_canvas.add_shape(result)
            
            # Include procedure info if available
            proc_info = result.attrs.get('procedure', {})
            if proc_info:
                method_used = proc_info.get('method', method_name)
                stats = proc_info.get('statistics', {})
                
                msg = f"Created {result.attrs['type']} '{shape_name}' using {method_used} on {self.active_canvas_name}"
                
                # Add stats summary if available
                if stats:
                    successful = stats.get('successful_modifications', 0)
                    total_attempts = successful + stats.get('failed_attempts', 0)
                    msg += f"\n  Modifications: {successful} successful"
                    if total_attempts > successful:
                        msg += f" ({total_attempts - successful} failed attempts)"
                
                # Hint about verbose info
                if proc_info.get('debug_log'):
                    msg += f"\n  Use 'INFO {shape_name}' to see detailed generation log"
                
                return msg
            else:
                return f"Created {result.attrs['type']} '{shape_name}' on {self.active_canvas_name}"
        
        else:
            raise ValueError(f"Unexpected return type from {method_name}: {type(result)}")    
    
    def _execute_list_preset(self, cmd_dict, command_text):
        """Execute LIST PRESET command - show presets for a method"""
        method_name = cmd_dict['method']
        return self.procedural_gen.list_presets(method_name)
    
    def _execute_info_proc(self, cmd_dict, command_text):
        """Execute INFO PROC command - show details about a procedural method"""
        method_name = cmd_dict['method']
        return self.procedural_gen.get_method_info(method_name)
    
    def _format_debug_log(self, debug_log):
        """Format debug log for display"""
        verbose = debug_log.get('verbose_level', 0)
        lines = []
        
        lines.append("=== PROCEDURAL GENERATION DEBUG LOG ===")
        lines.append("")
        
        # Initial state
        init = debug_log.get('initial_state', {})
        lines.append("Initial State:")
        lines.append(f"  Vertices: {init.get('vertex_count', '?')}")
        lines.append(f"  Bounds: {init.get('bounds', '?')}")
        if init.get('centroid'):
            cx, cy = init['centroid']
            lines.append(f"  Centroid: ({round(cx, 1)}, {round(cy, 1)})")
        lines.append(f"  Connection: {init.get('connection_method', '?')}")
        
        if verbose >= 3 and init.get('points'):
            lines.append(f"  Points: {init['points']}")
        
        lines.append("")
        
        # Iterations
        iterations = debug_log.get('iterations', [])
        for iter_data in iterations:
            lines.append(f"--- Iteration {iter_data['iteration']} ---")
            
            # Selection
            sel = iter_data.get('selection', {})
            lines.append("Selection:")
            lines.append(f"  Segment: {sel.get('segment_idx', '?')}")
            if sel.get('segment_endpoints') and verbose >= 3:
                lines.append(f"  Endpoints: {sel['segment_endpoints']}")
            lines.append(f"  Length: {sel.get('segment_length', '?')}px")
            if sel.get('selection_probability'):
                lines.append(f"  Probability: {sel['selection_probability']:.1%}")            
            
            lines.append("")
            
            # Operation
            op = iter_data.get('operation', {})
            lines.append(f"Operation: {op.get('name', '?')}")
            if op.get('direction'):
                lines.append(f"  Direction: {op['direction']}")
            if op.get('direction_vector') and verbose >= 3:
                lines.append(f"  Direction vector: {op['direction_vector']}")
            if op.get('new_point') and verbose >= 3:
                lines.append(f"  New point: {op['new_point']}")
            
            lines.append("")
            
            # Result
            res = iter_data.get('result', {})
            lines.append("Result:")
            lines.append(f"  Points: {res.get('points_before', '?')} -> {res.get('points_after', '?')}")
            
            # Build validation line with ASCII-safe symbols
            validation_text = f"  Validation: {res.get('validation_result', '?')}"
            if res.get('validation_result') == 'PASS':
                validation_text += " [OK]"
            else:
                validation_text += " [FAIL]"
            lines.append(validation_text)
            
            if res.get('validation_attempts', 1) > 1:
                lines.append(f"  Attempts: {res['validation_attempts']}")
            
            if res.get('intersection_count') is not None:
                lines.append(f"  Intersections: {res['intersection_count']}")
            
            if res.get('new_weights') and verbose >= 3:
                lines.append(f"  New weights: {res['new_weights']}")
            
            lines.append("")
        
        # Summary
        summary = debug_log.get('summary', {})
        lines.append("Final Statistics:")
        lines.append(f"  Successful modifications: {summary.get('successful_modifications', 0)}")
        lines.append(f"  Failed attempts: {summary.get('failed_attempts', 0)}")
        
        ops_used = summary.get('operations_used', {})
        if ops_used:
            lines.append("  Operations used:")
            for op, count in ops_used.items():
                lines.append(f"    {op}: {count}")
        
        return "\n".join(lines)
     
    def _find_snapshots(self, base_name):
        """
        Find all iteration snapshots for a base shape name
        
        Args:
            base_name: Base shape name (e.g., "demo1")
            
        Returns:
            List of snapshot shapes sorted by iteration number,
            or empty list if no snapshots found
        """
        snapshots = []
        
        # Search in WIP shapes (where SAVE_ITERATIONS creates them)
        for name, shape in self.wip_shapes.items():
            # Only check shapes that match the naming pattern
            # This is much faster than checking all shapes
            if not (name.startswith(f"{base_name}_iter_") or name == f"{base_name}_final"):
                continue
            
            proc = shape.attrs.get('procedure')
            
            # Skip shapes without procedure metadata
            if not proc:
                continue
            
            # Check if it's a snapshot (has snapshot_of matching base_name)
            is_iteration_snapshot = proc.get('snapshot_of') == base_name
            
            # Check if it's the final snapshot (name matches and has is_final flag)
            is_final_snapshot = (name == f"{base_name}_final" and proc.get('is_final'))
            
            if is_iteration_snapshot or is_final_snapshot:
                # Extract iteration number from name
                # Names like: demo1_iter_0, demo1_iter_1, ..., demo1_final
                if '_iter_' in name:
                    try:
                        iter_num = int(name.split('_iter_')[1])
                        snapshots.append((iter_num, shape))
                    except (ValueError, IndexError):
                        pass
                elif name == f"{base_name}_final":
                    # Final snapshot - use large number to sort last
                    snapshots.append((999999, shape))
        
        # Sort by iteration number
        snapshots.sort(key=lambda x: x[0])
        
        # Return just the shape objects
        return [shape for _, shape in snapshots]

    def _execute_animate(self, cmd_dict, command_text):
        """Execute ANIMATE command - launch preview window for iteration snapshots"""
        base_name = cmd_dict['base_name']
        fps = cmd_dict['fps']
        loop = cmd_dict['loop']
        
        # Find all snapshots
        snapshots = self._find_snapshots(base_name)
        
        if not snapshots:
            raise ValueError(
                f"No iteration snapshots found for '{base_name}'.\n"
                f"Did you use SAVE_ITERATIONS=true when creating it?\n"
                f"Example: PROC dynamic_polygon {base_name} ... SAVE_ITERATIONS=true"
            )
        
        if len(snapshots) < 2:
            raise ValueError(
                f"Only {len(snapshots)} snapshot(s) found for '{base_name}'.\n"
                f"Animation requires at least 2 iterations."
            )
        
        # Launch preview window
        from ui.animation_preview import AnimationPreview
        
        # Need to get the root window from UI
        # Assuming self has a reference to UI or root window
        # This will need to be passed when CommandExecutor is created
        AnimationPreview(self.ui_root, snapshots, base_name, fps, loop, self, self.ui_instance)
        
        return f"Animation preview opened for '{base_name}' ({len(snapshots)} frames, {fps} FPS)"

    def _execute_color(self, cmd_dict, command_text):
        """Execute COLOR command - set shape outline color"""
        name = cmd_dict['name']
        color = cmd_dict['color']
        
        shapes = self.get_active_shapes()
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        shape.attrs['style']['color'] = color
        shape.add_history('STYLE', command_text)
        self.active_canvas.redraw()
        
        return f"Set color of '{name}' to {color}"

    def _execute_width(self, cmd_dict, command_text):
        """Execute WIDTH command - set shape line width"""
        name = cmd_dict['name']
        width = cmd_dict['width']
        
        shapes = self.get_active_shapes()
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        shape.attrs['style']['width'] = width
        shape.add_history('STYLE', command_text)
        self.active_canvas.redraw()
        
        return f"Set width of '{name}' to {width}"

    def _execute_fill(self, cmd_dict, command_text):
        """Execute FILL command - set shape fill color"""
        name = cmd_dict['name']
        fill = cmd_dict['fill']
        
        shapes = self.get_active_shapes()
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        shape.attrs['style']['fill'] = fill
        shape.add_history('STYLE', command_text)
        self.active_canvas.redraw()
        
        if fill is None:
            return f"Removed fill from '{name}'"
        return f"Set fill of '{name}' to {fill}"

    def _execute_alpha(self, cmd_dict, command_text):
        """Execute ALPHA command - set shape transparency"""
        name = cmd_dict['name']
        alpha = cmd_dict['alpha']
        
        shapes = self.get_active_shapes()
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        shape.attrs['style']['transparency'] = alpha
        shape.add_history('STYLE', command_text)
        self.active_canvas.redraw()
        
        return f"Set transparency of '{name}' to {alpha}"

    def _execute_zorder(self, cmd_dict, command_text):
        """Execute ZORDER command - set shape z-coordinate for layering"""
        name = cmd_dict['name']
        z_coord = cmd_dict['z_coord']
        
        shapes = self.get_active_shapes()
        if name not in shapes:
            raise ValueError(f"Shape '{name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[name]
        shape.attrs['style']['z_coord'] = z_coord
        shape.add_history('STYLE', command_text)
        self.active_canvas.redraw()
        
        return f"Set z-order of '{name}' to {z_coord}"
    
    def _execute_exit(self, cmd_dict, command_text):
        """Execute EXIT command - quit the application"""
        # Close the UI window if available
        if hasattr(self, 'ui_root') and self.ui_root:
            self.ui_root.quit()
        return "Exiting Shape Studio..."
    
    def _execute_structured_command(self, cmd_dict):
        """Execute a structured command (dictionary format)
        
        Args:
            cmd_dict: Dictionary with command structure matching parser output
            
        Returns:
            Result string from command execution
        """
        # Filter out underscore fields (comments)
        filtered_dict = {k: v for k, v in cmd_dict.items() if not k.startswith('_')}
        
        # Normalize command name (uppercase)
        if 'command' not in filtered_dict:
            raise ValueError("Structured command missing 'command' field")
        
        filtered_dict['command'] = filtered_dict['command'].upper()
        
        # Process RAND() in all string values
        filtered_dict = self._process_rand_in_dict(filtered_dict)
        
        # Convert flexible types (arrays, numbers) to strings
        filtered_dict = self._convert_param_types(filtered_dict)
        
        # Pass to existing command handlers via execute dispatcher
        return self._execute_from_dict(filtered_dict)

    def _execute_from_dict(self, cmd_dict):
        """Execute command directly from dictionary (bypassing parser)
        
        Args:
            cmd_dict: Dictionary matching parser output format
            
        Returns:
            Result string from command execution
        """
        command = cmd_dict['command']
        
        # Create a dummy command_text for history tracking
        command_text = self._format_structured_command(cmd_dict)
        
        # Route to existing handlers (same as execute method)
        handlers = {
            'LINE': self._execute_line,
            'POLY': self._execute_poly,
            'MOVE': self._execute_move,
            'ROTATE': self._execute_rotate,
            'SCALE': self._execute_scale,
            'RESIZE': self._execute_resize,
            'GROUP': self._execute_group,
            'UNGROUP': self._execute_ungroup,
            'EXTRACT': self._execute_extract,
            'DELETE': self._execute_delete,
            'SWITCH': self._execute_switch,
            'PROMOTE': self._execute_promote,
            'UNPROMOTE': self._execute_unpromote,
            'STASH': self._execute_stash,
            'UNSTASH': self._execute_unstash,
            'STORE': self._execute_store,
            'LOAD': self._execute_load,
            'SAVE_PROJECT': self._execute_save_project,
            'LOAD_PROJECT': self._execute_load_project,
            'CLEAR': self._execute_clear,
            'LIST': self._execute_list,
            'INFO': self._execute_info,
            'SAVE': self._execute_save,
            'RUN': self._execute_run,
            'BATCH': self._execute_batch,
            'PROC': self._execute_proc,
            'ANIMATE': self._execute_animate,
            'COLOR': self._execute_color,
            'WIDTH': self._execute_width,
            'FILL': self._execute_fill,
            'ALPHA': self._execute_alpha,
            'ZORDER': self._execute_zorder,
            'EXIT': self._execute_exit,
        }
        
        if command in handlers:
            return handlers[command](cmd_dict, command_text)
        else:
            raise ValueError(f"Unknown command: {command}")

    def _process_rand_in_dict(self, cmd_dict):
        """Recursively process RAND() functions in all string values
        
        Args:
            cmd_dict: Command dictionary
            
        Returns:
            Dictionary with RAND() functions evaluated
        """
        import re
        
        result = {}
        for key, value in cmd_dict.items():
            if isinstance(value, str):
                # Process RAND() in string values
                result[key] = self.parser._process_rand_functions(value)
            elif isinstance(value, dict):
                # Recurse into nested dicts
                result[key] = self._process_rand_in_dict(value)
            else:
                # Keep other types as-is
                result[key] = value
        
        return result

    def _convert_param_types(self, cmd_dict):
        """Convert flexible parameter types to proper formats
        
        Handles:
        - Nested arrays (POLY points) [[x,y], [x,y]] -> [(x,y), (x,y)]
        - Flat arrays [1,2,3] -> "1,2,3" 
        - Coordinate pairs (start, end, delta) [x, y] -> (x, y)
        - String lists (members) -> KEEP AS LIST
        - PROC params dict -> all values to strings
        - Other numbers/booleans -> KEEP AS-IS
        - Filters underscore fields (comments) at all levels
        
        Args:
            cmd_dict: Command dictionary
            
        Returns:
            Dictionary with converted values (underscore fields removed)
        """
        result = {}
        
        for key, value in cmd_dict.items():
            # Skip underscore fields (comments) at any level
            if key.startswith('_'):
                continue
                
            # Don't convert the 'command' field itself
            if key == 'command':
                result[key] = value
                continue
            
            # Special handling for PROC params - convert everything to strings
            if key == 'params' and isinstance(value, dict):
                result[key] = self._convert_params_to_strings(value)
                continue
            
            # Handle arrays
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], list):
                    # Nested array -> list of tuples for coordinates
                    result[key] = [tuple(coord) for coord in value]
                elif len(value) == 2 and key.lower() in ['start', 'end', 'delta']:
                    # Coordinate pair -> tuple (x, y)
                    result[key] = tuple(value)
                elif key.lower() in ['members']:
                    # String lists that should stay as lists
                    result[key] = value
                else:
                    # Flat array -> comma-separated string
                    result[key] = ','.join(str(v) for v in value)
            
            # Handle nested dicts (recurse - will filter underscores recursively)
            elif isinstance(value, dict):
                result[key] = self._convert_param_types(value)
            
            # Keep numbers and booleans as-is for non-PROC params
            else:
                result[key] = value
        
        return result

    def _convert_params_to_strings(self, params_dict):
        """Convert all values in PROC params dict to strings
        
        PROC params go through param_converters which expect strings.
        
        Args:
            params_dict: Dictionary of PROC parameters
            
        Returns:
            Dictionary with all values as strings (underscore fields removed)
        """
        result = {}
        
        for key, value in params_dict.items():
            # Skip underscore fields
            if key.startswith('_'):
                continue
            
            # Convert booleans FIRST (before int check, since bool is subclass of int)
            if isinstance(value, bool):
                result[key] = str(value).lower()  # true/false
            # Convert arrays to comma-separated strings
            elif isinstance(value, list):
                # Round floats to integers for bounds/coordinates
                if key.upper() in ['BOUNDS', 'VERTICES']:
                    result[key] = ','.join(str(int(round(v))) if isinstance(v, float) else str(v) for v in value)
                else:
                    result[key] = ','.join(str(v) for v in value)
            # Convert floats to rounded ints for specific params
            elif isinstance(value, float) and key.upper() in ['VERTICES', 'ITERATIONS', 'MAX_RETRIES', 'SNAPSHOT_INTERVAL', 'VERBOSE']:
                result[key] = str(int(round(value)))
            # Convert numbers to strings
            elif isinstance(value, (int, float)):
                result[key] = str(value)
            # Keep strings as-is
            else:
                result[key] = value
        
        return result

    def _format_structured_command(self, cmd_dict):
        """Format structured command for display (compact representation)
        
        Args:
            cmd_dict: Command dictionary
            
        Returns:
            String representation for logging
        """
        # Filter underscore fields
        filtered = {k: v for k, v in cmd_dict.items() if not k.startswith('_')}
        
        command = filtered.get('command', '?').upper()
        
        # Format based on command type
        if command == 'PROC':
            method = filtered.get('method', '?')
            name = filtered.get('name', '?')
            params = filtered.get('params', {})
            param_str = ' '.join(f"{k}={v}" for k, v in params.items() if not k.startswith('_'))
            return f"PROC {method} {name} {param_str}"
        
        elif command == 'POLY':
            name = filtered.get('name', '?')
            points = filtered.get('points', [])
            return f"POLY {name} ({len(points)} points)"
        
        elif command == 'LINE':
            name = filtered.get('name', '?')
            start = filtered.get('start', '?')
            end = filtered.get('end', '?')
            return f"LINE {name} {start} {end}"
        
        elif command == 'COLOR':
            name = filtered.get('name', '?')
            color = filtered.get('color', '?')
            return f"COLOR {name} {color}"
        
        elif command == 'FILL':
            name = filtered.get('name', '?')
            fill = filtered.get('fill', '?')
            return f"FILL {name} {fill}"
        
        elif command == 'WIDTH':
            name = filtered.get('name', '?')
            width = filtered.get('width', '?')
            return f"WIDTH {name} {width}"
        
        elif command in ['MOVE', 'ROTATE', 'SCALE', 'RESIZE']:
            name = filtered.get('name', '?')
            return f"{command} {name} ..."
        
        else:
            # Generic format
            parts = [command]
            for k, v in filtered.items():
                if k != 'command' and not isinstance(v, dict):
                    parts.append(f"{v}")
            return ' '.join(parts)
        
    def _execute_validate(self, cmd_dict, command_text):
        """Execute VALIDATE command - validate script without executing"""
        scriptfile = cmd_dict['scriptfile']
        filepath = self.scripts_dir / scriptfile
        
        if not filepath.exists():
            raise ValueError(f"Script file not found: {filepath}")
        
        # Validate using template executor
        is_valid, messages = self.template_executor.validate_script(filepath)
        
        result = f"Validation of '{scriptfile}':\n" + '\n'.join(messages)
        
        if not is_valid:
            raise ValueError(result)
        
        return result

    def _execute_reset_zorder(self, cmd_dict, command_text):
        """Execute RESET_ZORDER command - reset canvas z-order counter
        
        Resets the active canvas's z-order counter to initial value or specified value.
        This is useful when you want to restart z-order numbering in the middle of a session.
        """
        from src.config import config
        
        value = cmd_dict.get('value')
        
        if value is None:
            # Use config default
            value = config.canvas.zorder_initial
        
        # Reset the active canvas counter
        old_value = self.active_canvas.next_z_coord
        self.active_canvas.next_z_coord = value
        
        return f"Reset z-order counter from {old_value} to {value} on {self.active_canvas_name} canvas"

    def _parse_text_sections(self, lines):
        """Parse text file lines into labeled sections
        
        Returns:
            dict mapping label → list of commands
            
        Example:
            {
                '': ['POLY shape1 ...', 'POLY shape2 ...'],  # Unlabeled section
                'test1': ['CLEAR WIP ALL', 'POLY ...'],
                'test2': ['PROC ...', 'COLOR ...']
            }
        """
        sections = {}
        current_label = ''  # Unlabeled section (before any @label)
        current_commands = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for label marker
            if line.startswith('@'):
                # Save previous section if it has commands
                if current_commands:
                    sections[current_label] = current_commands
                
                # Start new section
                current_label = line[1:].strip()  # Remove @ and whitespace
                current_commands = []
                continue
            
            # Check for EOF marker (ends current section)
            if line.upper() == 'EOF':
                if current_commands:
                    sections[current_label] = current_commands
                current_label = ''  # Reset to unlabeled
                current_commands = []
                continue
            
            # Regular command line
            current_commands.append(line)
        
        # Save final section if it has commands
        if current_commands:
            sections[current_label] = current_commands
        
        return sections
    
    def _execute_enhance(self, cmd_dict, command_text):
        """Execute ENHANCE command"""
        method = cmd_dict['method']
        shape_name = cmd_dict['shape']
        intent_dict = cmd_dict['intent']
        
        canvas = self.wip_canvas if self.active_canvas_name == 'WIP' else self.main_canvas

        # Validate
        if method not in self.enhancement_registry.list_methods():
            available = ', '.join(self.enhancement_registry.list_methods())
            raise ValueError(f"Unknown method '{method}'. Available: {available}")
        
        shape = canvas.get_shape_by_name(shape_name) if shape_name.lower() != 'canvas' else None
        
        if shape_name.lower() != 'canvas' and shape is None:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name}")
        
        # Get the enhancer instance from registry
        enhancer = self.enhancement_registry.get(method)
        if enhancer is None:
            raise ValueError(f"Unknown enhancement method: {method}")
        
        is_valid, error = enhancer.validate_intent(intent_dict)
        if not is_valid:
            raise ValueError(f"Intent validation failed: {error}")
        
        # Execute
        result = enhancer.enhance(canvas, shape, intent_dict)
        commands = result.get('commands', {})
        metadata = result.get('metadata', {})
        
        if not metadata.get('success', False):
            return f"Enhancement failed: {metadata.get('reasoning', 'Unknown error')}"
        
        # Apply commands by delegating to existing command handlers
        applied = []
        if shape and commands:
            for cmd_type, cmd_value in commands.items():
                if cmd_type == 'color':
                    color_cmd = {
                        'command': 'COLOR',
                        'name': shape_name,
                        'color': cmd_value
                    }
                    self._execute_color(color_cmd, f"COLOR {shape_name} {cmd_value}")
                    applied.append(f"color → {cmd_value}")
                
                elif cmd_type == 'fill':
                    fill_cmd = {
                        'command': 'FILL',
                        'name': shape_name,
                        'fill': cmd_value
                    }
                    self._execute_fill(fill_cmd, f"FILL {shape_name} {cmd_value}")
                    applied.append(f"fill → {cmd_value}")
                
                elif cmd_type == 'move':
                    dx, dy = cmd_value
                    move_cmd = {
                        'command': 'MOVE',
                        'name': shape_name,
                        'delta': (dx, dy)
                    }
                    self._execute_move(move_cmd, f"MOVE {shape_name} {dx},{dy}")
                    applied.append(f"moved ({dx:.1f}, {dy:.1f})")
        
        reasoning = metadata.get('reasoning', '')
        recommendation = metadata.get('recommendation', '')
        
        if applied:
            return f"Enhanced '{shape_name}' using {method}  Applied: {', '.join(applied)}  Reasoning: {reasoning}"
        else:
            return f"Enhancement analyzed  Recommendation: {recommendation}"

    def _list_enhance_methods(self):
        """
        List available enhancement methods
        
        Returns:
            Formatted string of method names
        """
        methods = self.enhancement_registry.list_methods()
        
        result = ["Available enhancement methods:"]
        for method in methods:
            info = self.enhancement_registry.get_method_info(method)
            if info:
                desc = info.get('description', 'No description')
                result.append(f"  {method} - {desc}")
        
        result.append("\\nUse 'INFO ENHANCE <method>' for details")
        return '\\n'.join(result)
    
    def _info_enhance_method(self, method_name):
        """
        Show detailed information about an enhancement method
        
        Args:
            method_name: Name of method
            
        Returns:
            Formatted string with method details
        """
        info = self.enhancement_registry.get_method_info(method_name)
        
        if not info:
            available = ', '.join(self.enhancement_registry.list_methods())
            return f"Unknown enhancement method '{method_name}'\\nAvailable: {available}"
        
        result = [
            f"Enhancement Method: {info['name']}",
            f"Description: {info['description']}",
            "",
            "Intent Parameters:",
        ]
        
        param_spec = info.get('param_spec', {})
        for param_name, param_config in param_spec.items():
            param_type = param_config.get('type', 'unknown')
            desc = param_config.get('description', 'No description')
            default = param_config.get('default')
            
            param_line = f"  {param_name} ({param_type})"
            if default is not None:
                param_line += f" [default: {default}]"
            param_line += f" - {desc}"
            
            # Add choices if applicable
            if param_type == 'choice':
                choices = param_config.get('choices', [])
                param_line += f"\\n    Choices: {', '.join(str(c) for c in choices)}"
            
            # Add range if applicable
            if 'min' in param_config or 'max' in param_config:
                range_info = []
                if 'min' in param_config:
                    range_info.append(f"min: {param_config['min']}")
                if 'max' in param_config:
                    range_info.append(f"max: {param_config['max']}")
                param_line += f"\\n    Range: {', '.join(range_info)}"
            
            result.append(param_line)
        
        result.append("")
        result.append("Returns:")
        returns = info.get('returns', [])
        for ret in returns:
            result.append(f"  {ret}")
        
        result.append("")
        result.append("Examples:")
        examples = info.get('examples', [])
        for example in examples:
            result.append(f"  {example}")
        
        return '\\n'.join(result)