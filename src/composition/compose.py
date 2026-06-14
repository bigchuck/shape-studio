"""
Composition builder for Shape Studio.
Handles loading component shapes under predictable working names
and producing the construction JSON that records what was used.

Shape selection methods (shapes block):

  Backward-compatible shorthand:
    "specified": ["sa224/gen1_0033", "sa224/gen4_0050"]

  New multi-method selection array:
    "selection": [
      {"method": "specified", "shapes": ["sa224/gen1_0033"]},
      {"method": "pool", "shapes": ["sa224/gen4_0050", "sa224/gen4_0051"], "count": 1, "replacement": false},
      {"method": "wildcard", "pattern": "sa224/gen2_*", "count": 2, "replacement": false}
    ]

Working names are assigned sequentially across all selection entries:
  compose_shape_1, compose_shape_2, ...
"""
import json
import random
import fnmatch
from datetime import datetime
from pathlib import Path


class CompositionBuilder:
    """Orchestrates loading shapes for a COMPOSE operation."""

    WORKING_NAME_PREFIX = "compose_shape_"

    # -----------------------------------------------------------------------
    # Public entry point — resolves shapes block and loads all shapes
    # -----------------------------------------------------------------------

    def load_shapes(self, shapes_spec, executor):
        """Resolve a shapes spec and load all shapes onto the active canvas.

        Supports both the legacy 'specified' shorthand and the new
        'selection' array with multiple methods.

        Args:
            shapes_spec: Dict from compose_parameters['shapes']
            executor:    CommandExecutor instance

        Returns:
            List of dicts: [{'working_name': ..., 'source': ...}, ...]

        Raises:
            ValueError: if any shape cannot be found or loaded
        """
        shape_list = self._resolve_shapes_spec(shapes_spec, executor)
        return self._load_shape_list(shape_list, executor)

    # -----------------------------------------------------------------------
    # Shape resolution — builds the ordered list of shape names to load
    # -----------------------------------------------------------------------

    def _resolve_shapes_spec(self, shapes_spec, executor):
        """Resolve shapes spec to an ordered list of shape name strings.

        Args:
            shapes_spec: The 'shapes' dict from compose_parameters
            executor:    CommandExecutor — used to access project_store_dir

        Returns:
            List of shape name strings in load order
        """
        # Legacy shorthand: {"specified": [...]}
        if 'specified' in shapes_spec and 'selection' not in shapes_spec:
            return list(shapes_spec['specified'])

        # New multi-method selection array
        if 'selection' in shapes_spec:
            result = []
            for entry in shapes_spec['selection']:
                result.extend(
                    self._resolve_selection_entry(entry, executor)
                )
            return result

        raise ValueError(
            "COMPOSE shapes block must contain 'specified' or 'selection' key"
        )

    def _resolve_selection_entry(self, entry, executor):
        """Resolve a single selection entry to a list of shape name strings.

        Args:
            entry:    One dict from the 'selection' array
            executor: CommandExecutor — used to access project_store_dir

        Returns:
            List of shape name strings
        """
        method = entry.get('method', '').lower()

        if method == 'specified':
            return list(entry.get('shapes', []))

        elif method == 'pool':
            pool    = list(entry.get('shapes', []))
            count   = self._resolve_count(entry.get('count', len(pool)))
            replace = bool(entry.get('replacement', False))
            count   = min(count, len(pool)) if not replace else count
            if replace:
                return random.choices(pool, k=count)
            else:
                return random.sample(pool, k=count)

        elif method == 'wildcard':
            pattern     = entry.get('pattern', '')
            all_matches = self._glob_shapes(pattern, executor)
            if not all_matches:
                raise ValueError(
                    f"COMPOSE wildcard '{pattern}' matched no shapes in project store"
                )
            count   = self._resolve_count(entry.get('count', len(all_matches)))
            replace = bool(entry.get('replacement', False))
            count   = min(count, len(all_matches)) if not replace else count
            if replace:
                return random.choices(all_matches, k=count)
            else:
                return random.sample(all_matches, k=count)

        else:
            raise ValueError(
                f"COMPOSE selection entry has unknown method '{method}'. "
                f"Use 'specified', 'pool', or 'wildcard'."
            )

    def _glob_shapes(self, pattern, executor):
        """Find all shape names in the project store matching a full-path pattern.

        Pattern is matched against the shape name as stored (subdir/name),
        using Unix shell-style wildcards (* and ?).

        Args:
            pattern:  Full-path glob pattern e.g. 'sa224/gen1_*'
            executor: CommandExecutor — provides project_store_dir

        Returns:
            Sorted list of matching shape name strings (without .json suffix)
        """
        store_dir = executor.project_store_dir
        matches = []

        for json_file in store_dir.rglob('*.json'):
            # Build the shape name as stored: subdir/stem
            try:
                rel = json_file.relative_to(store_dir)
            except ValueError:
                continue

            # Convert to forward-slash name without .json
            parts = list(rel.parts)
            parts[-1] = parts[-1][:-5]  # strip .json
            shape_name = '/'.join(parts)

            # Skip composition JSON files (they have composition_id key)
            # Check cheaply by looking for the key in first 200 bytes
            try:
                with open(json_file, 'r') as f:
                    head = f.read(200)
                if 'composition_id' in head:
                    continue
            except (OSError, UnicodeDecodeError):
                continue

            if fnmatch.fnmatch(shape_name, pattern):
                matches.append(shape_name)

        return sorted(matches)

    @staticmethod
    def _resolve_count(count_spec):
        """Resolve a count value — fixed int or random spec.

        Args:
            count_spec: int or {'random': 'uniform_int', 'min': N, 'max': M}

        Returns:
            Resolved int count
        """
        if isinstance(count_spec, int):
            return count_spec
        if isinstance(count_spec, dict):
            dist = count_spec.get('random', '').lower()
            if dist == 'uniform_int':
                lo = int(count_spec.get('min', 1))
                hi = int(count_spec.get('max', 1))
                return random.randint(lo, hi)
            raise ValueError(
                f"COMPOSE count random spec must use 'uniform_int', got '{dist}'"
            )
        return int(count_spec)

    # -----------------------------------------------------------------------
    # Shape loading — takes resolved name list, loads onto canvas
    # -----------------------------------------------------------------------

    def _load_shape_list(self, shape_list, executor):
        """Load an ordered list of shape names onto the active canvas under
        predictable working names (compose_shape_1, compose_shape_2, ...).

        Args:
            shape_list: Ordered list of shape name strings
            executor:   CommandExecutor instance

        Returns:
            List of dicts: [{'working_name': ..., 'source': ...}, ...]

        Raises:
            ValueError: if any shape is not found in the store
        """
        records = []
        for idx, source_name in enumerate(shape_list, start=1):
            working_name = f"{self.WORKING_NAME_PREFIX}{idx}"

            # Load onto active canvas under source name first
            executor.execute(f"LOAD {source_name}")

            # Find the loaded shape by canonical name (handles collision suffix)
            shapes = executor.get_active_shapes()
            storage_name = None
            for sname, shape in shapes.items():
                canonical = getattr(shape, 'canonical_name', shape.name)
                if canonical == source_name:
                    storage_name = sname
                    break

            if storage_name is None:
                raise ValueError(
                    f"COMPOSE: failed to locate loaded shape '{source_name}' on canvas"
                )

            # Rename to working name
            executor.execute(f"RENAME {storage_name} {working_name}")

            # Clean up detritus from original shape's history —
            # history and procedure params are irrelevant in composition context.
            # Preserve derived_from breadcrumb if present.
            shapes = executor.get_active_shapes()
            if working_name in shapes:
                shape = shapes[working_name]
                shape.attrs['history'] = []
                shape.attrs.pop('procedure', None)

            records.append({
                'working_name': working_name,
                'source': source_name,
            })

        return records

    # Backward-compatible alias used by any existing callers
    def load_specified_shapes(self, shape_list, executor):
        """Backward-compatible alias for _load_shape_list."""
        return self._load_shape_list(shape_list, executor)

    # -----------------------------------------------------------------------
    # Construction JSON
    # -----------------------------------------------------------------------

    def build_construction_json(self, composition_id, exec_name,
                                shapes_loaded, commands_applied=None):
        """Assemble the construction record for a composition.

        Args:
            composition_id:   Unique identifier string (e.g. 'compose_test1_0001')
            exec_name:        Executable name that produced this composition
            shapes_loaded:    List of {'working_name', 'source'} dicts
            commands_applied: Ordered list of command strings applied after loading

        Returns:
            Dict suitable for json.dump
        """
        return {
            'composition_id': composition_id,
            'executable':     exec_name,
            'timestamp':      datetime.now().isoformat(),
            'shapes_loaded':  shapes_loaded,
            'commands_applied': commands_applied or [],
        }

    def save_construction_json(self, data, filepath):
        """Write construction JSON to filepath, creating parent dirs as needed.

        Args:
            data:     Dict from build_construction_json
            filepath: pathlib.Path destination
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)