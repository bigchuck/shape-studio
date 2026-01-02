"""
Command executor for Shape Studio - Phase 5
Executes commands with style support
"""
import os
import json
import copy
from pathlib import Path
from datetime import datetime
from src.core.shape import Line, Polygon, ShapeGroup
from src.commands.parser import CommandParser

class CommandExecutor:
    """Execute commands on WIP or Main canvas"""
    
    def __init__(self, wip_canvas, main_canvas):
        self.wip_canvas = wip_canvas
        self.main_canvas = main_canvas
        self.active_canvas = wip_canvas
        self.active_canvas_name = 'WIP'
        
        self.parser = CommandParser()
        
        self.wip_shapes = {}
        self.main_shapes = {}
        self.stash = {}

        self.project_store_dir = Path('shapes')
        self.global_store_dir = Path.home() / '.shapestudio' / 'shapes'
        self.projects_dir = Path('projects')
        
        os.makedirs('output', exist_ok=True)
        os.makedirs(self.project_store_dir, exist_ok=True)
        os.makedirs(self.global_store_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        
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
        cmd_dict = self.parser.parse(command_text)
        command = cmd_dict['command']

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
            'COLOR': self._execute_color,
            'WIDTH': self._execute_width,
            'FILL': self._execute_fill,
            'ALPHA': self._execute_alpha,
            'BRING_FORWARD': self._execute_bring_forward,
            'SEND_BACKWARD': self._execute_send_backward,
        }
        
        if command in handlers:
            return handlers[command](cmd_dict, command_text)
        else:
            raise ValueError(f"Unknown command: {command}")
            
    def _execute_line(self, cmd_dict, command_text):
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
        group_name = cmd_dict['name']
        member_names = cmd_dict['members']
        
        shapes = self.get_active_shapes()
        
        if group_name in shapes:
            raise ValueError(f"Shape '{group_name}' already exists on {self.active_canvas_name} canvas")
        
        members = []
        for member_name in member_names:
            if member_name not in shapes:
                raise ValueError(f"Shape '{member_name}' not found on {self.active_canvas_name} canvas")
            
            shape = shapes[member_name]
            
            if shape.attrs['relationships']['group']:
                raise ValueError(f"Shape '{member_name}' is already in group "
                               f"'{shape.attrs['relationships']['group']}'")
            
            members.append(shape)
        
        group = ShapeGroup(group_name, members)
        group.add_history('CREATE', command_text)
        shapes[group_name] = group
        
        self.active_canvas.redraw()
        
        return f"Created group '{group_name}' with {len(members)} members on {self.active_canvas_name}"
        
    def _execute_ungroup(self, cmd_dict, command_text):
        group_name = cmd_dict['name']
        
        shapes = self.get_active_shapes()
        
        if group_name not in shapes:
            raise ValueError(f"Group '{group_name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[group_name]
        
        if not isinstance(shape, ShapeGroup):
            raise ValueError(f"'{group_name}' is not a group")
        
        members = shape.attrs['geometry']['members']
        for member in members:
            member.attrs['relationships']['group'] = None
            member.add_history('UNGROUP', command_text)
        
        del shapes[group_name]
        self._sync_active_canvas()
        
        return f"Ungrouped '{group_name}' ({len(members)} members now independent)"
        
    def _execute_extract(self, cmd_dict, command_text):
        member_name = cmd_dict['member']
        group_name = cmd_dict['group']
        
        shapes = self.get_active_shapes()
        
        if group_name not in shapes:
            raise ValueError(f"Group '{group_name}' not found on {self.active_canvas_name} canvas")
        
        group = shapes[group_name]
        
        if not isinstance(group, ShapeGroup):
            raise ValueError(f"'{group_name}' is not a group")
        
        if member_name not in shapes:
            raise ValueError(f"Shape '{member_name}' not found on {self.active_canvas_name} canvas")
        
        member = shapes[member_name]
        
        if member.attrs['relationships']['group'] != group_name:
            raise ValueError(f"Shape '{member_name}' is not in group '{group_name}'")
        
        members = group.attrs['geometry']['members']
        members.remove(member)
        
        member.attrs['relationships']['group'] = None
        member.add_history('EXTRACT', command_text)
        
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
        shape_name = cmd_dict['name']
        confirm = cmd_dict['confirm']
        
        shapes = self.get_active_shapes()
        
        if shape_name not in shapes:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[shape_name]
        
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{shape_name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "EXTRACT it first or UNGROUP the group.")
        
        if isinstance(shape, ShapeGroup):
            members = shape.attrs['geometry']['members']
            if len(members) > 0 and not confirm:
                raise ValueError(f"'{shape_name}' is a group with {len(members)} members. "
                               f"Use 'DELETE {shape_name} CONFIRM' to delete it and free its members.")
            
            for member in members:
                member.attrs['relationships']['group'] = None
        
        del shapes[shape_name]
        self._sync_active_canvas()
        
        return f"Deleted '{shape_name}' from {self.active_canvas_name}"
        
    def _execute_switch(self, cmd_dict, command_text):
        target = cmd_dict['target']
        
        if target == 'WIP':
            self.active_canvas = self.wip_canvas
            self.active_canvas_name = 'WIP'
        else:
            self.active_canvas = self.main_canvas
            self.active_canvas_name = 'MAIN'
        
        return f"Switched to {self.active_canvas_name} canvas"
        
    def _execute_promote(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        mode = cmd_dict['mode']
        
        if shape_name not in self.wip_shapes:
            raise ValueError(f"Shape '{shape_name}' not found on WIP canvas")
        
        if shape_name in self.main_shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on MAIN canvas")
        
        shape = self.wip_shapes[shape_name]
        
        promoted_shape = copy.deepcopy(shape)
        promoted_shape.add_history('PROMOTE', command_text)
        
        self.main_canvas.add_shape(promoted_shape)
        self.main_shapes[shape_name] = promoted_shape
        
        if mode == 'move':
            del self.wip_shapes[shape_name]
            self.wip_canvas.sync_shapes(self.wip_shapes)
            return f"Promoted '{shape_name}' from WIP to MAIN (moved)"
        else:
            return f"Promoted '{shape_name}' from WIP to MAIN (copied)"
        
    def _execute_unpromote(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        mode = cmd_dict['mode']
        
        if shape_name not in self.main_shapes:
            raise ValueError(f"Shape '{shape_name}' not found on MAIN canvas")
        
        if shape_name in self.wip_shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on WIP canvas")
        
        shape = self.main_shapes[shape_name]
        
        unpromoted_shape = copy.deepcopy(shape)
        unpromoted_shape.add_history('UNPROMOTE', command_text)
        
        self.wip_canvas.add_shape(unpromoted_shape)
        self.wip_shapes[shape_name] = unpromoted_shape
        
        if mode == 'move':
            del self.main_shapes[shape_name]
            self.main_canvas.sync_shapes(self.main_shapes)
            return f"Unpromoted '{shape_name}' from MAIN to WIP (moved)"
        else:
            return f"Unpromoted '{shape_name}' from MAIN to WIP (copied)"
            
    def _execute_stash(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        
        shapes = self.get_active_shapes()
        
        if shape_name not in shapes:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
        
        if shape_name in self.stash:
            raise ValueError(f"Shape '{shape_name}' already in stash")
        
        shape = shapes[shape_name]
        
        if shape.attrs['relationships']['group']:
            raise ValueError(f"Shape '{shape_name}' is in group '{shape.attrs['relationships']['group']}'. "
                           "EXTRACT it first or UNGROUP the group.")
        
        stashed_shape = copy.deepcopy(shape)
        stashed_shape.add_history('STASH', command_text)
        self.stash[shape_name] = stashed_shape
        
        del shapes[shape_name]
        self._sync_active_canvas()
        
        return f"Stashed '{shape_name}' from {self.active_canvas_name}"
        
    def _execute_unstash(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        mode = cmd_dict['mode']
        
        if shape_name not in self.stash:
            raise ValueError(f"Shape '{shape_name}' not found in stash")
        
        shapes = self.get_active_shapes()
        
        if shape_name in shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on {self.active_canvas_name} canvas")
        
        unstashed_shape = copy.deepcopy(self.stash[shape_name])
        unstashed_shape.add_history('UNSTASH', command_text)
        
        self.active_canvas.add_shape(unstashed_shape)
        shapes[shape_name] = unstashed_shape
        
        if mode == 'move':
            del self.stash[shape_name]
            return f"Unstashed '{shape_name}' to {self.active_canvas_name} (removed from stash)"
        else:
            return f"Unstashed '{shape_name}' to {self.active_canvas_name} (kept in stash)"
        
    def _execute_clear(self, cmd_dict, command_text):
        target = cmd_dict['target']
        all_flag = cmd_dict['all']
        
        if target is None:
            target = self.active_canvas_name
        
        if target == 'STASH':
            self.stash.clear()
            return "Stash cleared"
        
        if not all_flag:
            raise ValueError(f"Clearing {target} canvas requires ALL keyword for safety. "
                           f"Use: CLEAR {target} ALL")
        
        if target == 'WIP':
            self.wip_canvas.clear()
            self.wip_shapes.clear()
            return "WIP canvas cleared"
        else:
            self.main_canvas.clear()
            self.main_shapes.clear()
            return "MAIN canvas cleared"
        
    def _execute_info(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        
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
        
        info = [f"Shape: {shape_name}"]
        info.append(f"Location: {location}")
        info.append(f"Type: {shape.attrs['type']}")
        
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
        
        style = shape.attrs['style']
        info.append(f"Color: {style['color']}")
        info.append(f"Width: {style['width']}")
        info.append(f"Fill: {style['fill']}")
        info.append(f"Alpha: {style['transparency']}")
        info.append(f"Z-order: {style['z_coord']}")
        
        rel = shape.attrs['relationships']
        if rel['group']:
            info.append(f"In group: {rel['group']}")
        
        history = shape.attrs['history']
        if history:
            info.append(f"History (last 5):")
            for action_type, command, timestamp in history[-5:]:
                info.append(f"  [{action_type}] {command}")
        
        return "\n".join(info)
        
    def _execute_save(self, cmd_dict, command_text):
        filename = cmd_dict['filename']
        filepath = os.path.join('output', filename)
        
        self.main_canvas.save(filepath)
        
        return f"Saved MAIN canvas to {filepath}"
    
    def _execute_store(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        scope = cmd_dict['scope']
        
        shape = None
        if shape_name in self.wip_shapes:
            shape = self.wip_shapes[shape_name]
        elif shape_name in self.main_shapes:
            shape = self.main_shapes[shape_name]
        elif shape_name in self.stash:
            shape = self.stash[shape_name]
        else:
            raise ValueError(f"Shape '{shape_name}' not found")
        
        shape_data = self._serialize_shape(shape)
        
        if scope == 'global':
            save_dir = self.global_store_dir
        else:
            save_dir = self.project_store_dir
        
        filepath = save_dir / f"{shape_name}.json"
        with open(filepath, 'w') as f:
            json.dump(shape_data, f, indent=2)
        
        scope_name = "global library" if scope == 'global' else "project store"
        return f"Stored '{shape_name}' to {scope_name}: {filepath}"
    
    def _execute_load(self, cmd_dict, command_text):
        shape_name = cmd_dict['name']
        
        shapes = self.get_active_shapes()
        if shape_name in shapes:
            raise ValueError(f"Shape '{shape_name}' already exists on {self.active_canvas_name} canvas")
        
        filepath = self.project_store_dir / f"{shape_name}.json"
        source = "project store"
        
        if not filepath.exists():
            filepath = self.global_store_dir / f"{shape_name}.json"
            source = "global library"
        
        if not filepath.exists():
            raise ValueError(f"Shape '{shape_name}' not found in project store or global library")
        
        with open(filepath, 'r') as f:
            shape_data = json.load(f)
        
        shape = self._deserialize_shape(shape_data)
        shape.add_history('LOAD', command_text)
        
        self.active_canvas.add_shape(shape)
        shapes[shape_name] = shape
        
        return f"Loaded '{shape_name}' from {source} to {self.active_canvas_name}"
    
    def _execute_save_project(self, cmd_dict, command_text):
        filename = cmd_dict['filename']
        filepath = self.projects_dir / filename
        
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
        
        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return f"Saved project to {filepath}"
    
    def _execute_load_project(self, cmd_dict, command_text):
        filename = cmd_dict['filename']
        filepath = self.projects_dir / filename
        
        if not filepath.exists():
            raise ValueError(f"Project file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            project_data = json.load(f)
        
        self.wip_shapes.clear()
        self.main_shapes.clear()
        self.stash.clear()
        self.wip_canvas.clear()
        self.main_canvas.clear()
        
        for name, shape_data in project_data['wip_shapes'].items():
            shape = self._deserialize_shape(shape_data)
            self.wip_shapes[name] = shape
            self.wip_canvas.add_shape(shape)
        
        for name, shape_data in project_data['main_shapes'].items():
            shape = self._deserialize_shape(shape_data)
            self.main_shapes[name] = shape
            self.main_canvas.add_shape(shape)
        
        for name, shape_data in project_data['stash'].items():
            shape = self._deserialize_shape(shape_data)
            self.stash[name] = shape
        
        settings = project_data.get('canvas_settings', {})
        self.wip_canvas.show_grid = settings.get('show_grid', True)
        self.wip_canvas.show_rulers = settings.get('show_rulers', True)
        self.main_canvas.show_grid = settings.get('show_grid', True)
        self.main_canvas.show_rulers = settings.get('show_rulers', True)
        
        active = project_data.get('active_canvas', 'WIP')
        if active == 'MAIN':
            self.active_canvas = self.main_canvas
            self.active_canvas_name = 'MAIN'
        else:
            self.active_canvas = self.wip_canvas
            self.active_canvas_name = 'WIP'
        
        self.wip_canvas.redraw()
        self.main_canvas.redraw()
        
        wip_count = len(self.wip_shapes)
        main_count = len(self.main_shapes)
        stash_count = len(self.stash)
        
        return f"Loaded project from {filepath} (WIP: {wip_count}, MAIN: {main_count}, Stash: {stash_count})"
    
    def _serialize_shape(self, shape):
        data = {
            'name': shape.name,
            'type': shape.attrs['type'],
            'attrs': {}
        }
        
        attrs = copy.deepcopy(shape.attrs)
        
        if isinstance(shape, ShapeGroup):
            members = attrs['geometry']['members']
            attrs['geometry']['members'] = [m.name for m in members]
        
        data['attrs'] = attrs
        return data
    
    def _deserialize_shape(self, data):
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
            shape = ShapeGroup(name, [])
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
        
        shape.attrs = attrs
        
        return shape
    
    def _execute_list(self, cmd_dict, command_text):
        target = cmd_dict['target']
        
        if target is None:
            target = self.active_canvas_name
        
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
        json_files = list(store_dir.glob('*.json'))
        
        if not json_files:
            return f"No shapes in {store_name}"
        
        shapes_info = []
        for filepath in sorted(json_files):
            shape_name = filepath.stem
            with open(filepath, 'r') as f:
                data = json.load(f)
            shape_type = data['type']
            shapes_info.append(f"{shape_name} ({shape_type})")
        
        return f"{store_name.title()} ({len(json_files)} shapes):\n  " + "\n  ".join(shapes_info)
    
    # ============= Phase 5: Style Commands =============
    
    def _apply_style_to_shape(self, shape, style_attr, value, command_text):
        """Apply a style attribute to a shape or group (recursively)"""
        if isinstance(shape, ShapeGroup):
            # For groups, recursively apply to all members
            members = shape.attrs['geometry']['members']
            for member in members:
                self._apply_style_to_shape(member, style_attr, value, command_text)
        else:
            # For regular shapes, apply directly
            shape.attrs['style'][style_attr] = value
            shape.add_history('STYLE', command_text)
    
    def _execute_color(self, cmd_dict, command_text):
        """Execute COLOR command"""
        shape_names = cmd_dict['shapes']
        color = cmd_dict['color']
        
        shapes = self.get_active_shapes()
        
        applied_count = 0
        for shape_name in shape_names:
            if shape_name not in shapes:
                raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
            
            shape = shapes[shape_name]
            self._apply_style_to_shape(shape, 'color', color, command_text)
            applied_count += 1
        
        self.active_canvas.redraw()
        
        if applied_count == 1:
            return f"Set color of '{shape_names[0]}' to {color}"
        else:
            return f"Set color of {applied_count} shapes to {color}"
    
    def _execute_width(self, cmd_dict, command_text):
        """Execute WIDTH command"""
        shape_names = cmd_dict['shapes']
        width = cmd_dict['width']
        
        shapes = self.get_active_shapes()
        
        applied_count = 0
        for shape_name in shape_names:
            if shape_name not in shapes:
                raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
            
            shape = shapes[shape_name]
            self._apply_style_to_shape(shape, 'width', width, command_text)
            applied_count += 1
        
        self.active_canvas.redraw()
        
        if applied_count == 1:
            return f"Set width of '{shape_names[0]}' to {width}px"
        else:
            return f"Set width of {applied_count} shapes to {width}px"
    
    def _execute_fill(self, cmd_dict, command_text):
        """Execute FILL command"""
        shape_names = cmd_dict['shapes']
        fill = cmd_dict['fill']
        
        shapes = self.get_active_shapes()
        
        applied_count = 0
        for shape_name in shape_names:
            if shape_name not in shapes:
                raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
            
            shape = shapes[shape_name]
            self._apply_style_to_shape(shape, 'fill', fill, command_text)
            applied_count += 1
        
        self.active_canvas.redraw()
        
        fill_desc = "NONE" if fill is None else str(fill)
        if applied_count == 1:
            return f"Set fill of '{shape_names[0]}' to {fill_desc}"
        else:
            return f"Set fill of {applied_count} shapes to {fill_desc}"
    
    def _execute_alpha(self, cmd_dict, command_text):
        """Execute ALPHA command"""
        shape_names = cmd_dict['shapes']
        alpha = cmd_dict['alpha']
        
        shapes = self.get_active_shapes()
        
        applied_count = 0
        for shape_name in shape_names:
            if shape_name not in shapes:
                raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
            
            shape = shapes[shape_name]
            self._apply_style_to_shape(shape, 'transparency', alpha, command_text)
            applied_count += 1
        
        self.active_canvas.redraw()
        
        if applied_count == 1:
            return f"Set alpha of '{shape_name[0]}' to {alpha}"
        else:
            return f"Set alpha of {applied_count} shapes to {alpha}"
    
    def _execute_bring_forward(self, cmd_dict, command_text):
        """Execute BRING_FORWARD command"""
        shape_name = cmd_dict['name']
        steps = cmd_dict['steps']
        
        shapes = self.get_active_shapes()
        
        if shape_name not in shapes:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[shape_name]
        shape.attrs['style']['z_coord'] += steps
        shape.add_history('Z_ORDER', command_text)
        
        self.active_canvas.redraw()
        
        new_z = shape.attrs['style']['z_coord']
        return f"Brought '{shape_name}' forward by {steps} (z={new_z})"
    
    def _execute_send_backward(self, cmd_dict, command_text):
        """Execute SEND_BACKWARD command"""
        shape_name = cmd_dict['name']
        steps = cmd_dict['steps']
        
        shapes = self.get_active_shapes()
        
        if shape_name not in shapes:
            raise ValueError(f"Shape '{shape_name}' not found on {self.active_canvas_name} canvas")
        
        shape = shapes[shape_name]
        shape.attrs['style']['z_coord'] -= steps
        shape.add_history('Z_ORDER', command_text)
        
        self.active_canvas.redraw()
        
        new_z = shape.attrs['style']['z_coord']
        return f"Sent '{shape_name}' backward by {steps} (z={new_z})"