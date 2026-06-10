"""
Composition builder for Shape Studio.
Handles loading component shapes under predictable working names
and producing the construction JSON that records what was used.
"""
import json
from datetime import datetime
from pathlib import Path


class CompositionBuilder:
    """Orchestrates loading shapes for a COMPOSE operation."""

    WORKING_NAME_PREFIX = "compose_shape_"

    def load_specified_shapes(self, shape_list, executor):
        """Load a list of named shapes onto the active canvas under
        predictable working names (compose_shape_1, compose_shape_2, ...).

        Args:
            shape_list: List of shape name strings as stored under shapes/
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

            # Rename from source name to working name
            shapes = executor.get_active_shapes()

            # The loaded shape may have a collision suffix; find it by canonical
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

            records.append({
                'working_name': working_name,
                'source': source_name,
            })

        return records

    def build_construction_json(self, composition_id, exec_name,
                                shapes_loaded, commands_applied=None):
        """Assemble the construction record for a composition.

        Args:
            composition_id:   Unique identifier string (e.g. 'compose_test1_0001')
            exec_name:        Executable name that produced this composition
            shapes_loaded:    List of {'working_name', 'source'} dicts
            commands_applied: List of command strings applied after loading
                              (empty list for test 1; future use for transforms)

        Returns:
            Dict suitable for json.dump
        """
        return {
            'composition_id': composition_id,
            'executable': exec_name,
            'timestamp': datetime.now().isoformat(),
            'shapes_loaded': shapes_loaded,
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