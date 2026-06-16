"""
CommandLoopRunner for Shape Studio composition system.

Executes a command_loop spec against a set of loaded composition shapes.
Entirely self-contained — parse, validate, and execute are all here.
This module is intentionally isolated: changes to composition loop behavior
touch only this file.

JSON spec format (within compose_parameters):

  "command_loop": {
    "verbose": true,
    "iterations": 3,
    "commands": [
      {"command": "MOVE", "target": "all", "delta": [5, 5]}
    ],
    "select_blocks": [
      {
        "chance": 0.7,
        "target": "random",
        "commands": [
          {"command": "DEFORM", "axis": "major", "along": 0.8, "across": 1.0},
          {"command": "MOVE", "delta": [30, 30]}
        ]
      }
    ]
  }

Supported targets:
  "all"      — every working name in the composition
  "random"   — one shape chosen at random from working names (with replacement)
  <name>     — a specific working name e.g. "compose_shape_1"

Commands under a select_block inherit the resolved target automatically.
The "name" field in a command is optional inside a select_block;
if absent, the block's resolved target is used.

Logging:
  verbose key in command_loop spec controls UI log output.
  Defaults to True for now; flip default to False for production use.
"""

import math
import random
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Supported commands in a command_loop — maps to executor string commands
# ---------------------------------------------------------------------------
_SUPPORTED_COMMANDS = {'MOVE', 'ROTATE', 'SCALE', 'DEFORM', 'COLOR', 'WIDTH',
                       'FILL', 'ALPHA', 'ZORDER', 'REFLECT'}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_command_loop(spec):
    """Validate a command_loop spec dict.

    Args:
        spec: Dict from compose_parameters['command_loop']

    Returns:
        (is_valid: bool, messages: list of str)
    """
    if not isinstance(spec, dict):
        return False, ["command_loop must be a JSON object"]

    messages = []

    # iterations
    iterations = spec.get('iterations', 1)
    if isinstance(iterations, dict):
        dist = iterations.get('random', '')
        if dist not in ('uniform_int', 'normal'):
            messages.append(
                f"command_loop.iterations random spec must use 'uniform_int' or 'normal', "
                f"got '{dist}'"
            )
    elif not isinstance(iterations, int) or iterations < 1:
        messages.append(
            f"command_loop.iterations must be a positive integer or random spec, "
            f"got: {iterations!r}"
        )

    # always_transforms (was: commands)
    top_commands = spec.get('always_transforms', spec.get('commands', []))
    if not isinstance(top_commands, list):
        messages.append("command_loop.always_transforms must be a list")
    else:
        for i, cmd in enumerate(top_commands):
            msgs = _validate_command_entry(cmd, f"always_transforms[{i}]", require_target=True)
            messages.extend(msgs)

    # conditional_transforms (was: select_blocks)
    select_blocks = spec.get('conditional_transforms', spec.get('select_blocks', []))
    if not isinstance(select_blocks, list):
        messages.append("command_loop.conditional_transforms must be a list")
    else:
        for i, block in enumerate(select_blocks):
            msgs = _validate_select_block(block, i)
            messages.extend(msgs)

    return len(messages) == 0, messages


def _validate_select_block(block, idx):
    messages = []
    prefix = f"select_blocks[{idx}]"

    if not isinstance(block, dict):
        return [f"{prefix} must be a JSON object"]

    # chance
    chance = block.get('chance', 1.0)
    if not isinstance(chance, (int, float)) or not (0.0 <= float(chance) <= 1.0):
        messages.append(f"{prefix}.chance must be a float 0.0-1.0, got: {chance!r}")

    # target
    target = block.get('target')
    if target is None:
        messages.append(f"{prefix} missing required 'target' field")

    # commands
    cmds = block.get('commands', [])
    if not isinstance(cmds, list) or len(cmds) == 0:
        messages.append(f"{prefix}.commands must be a non-empty list")
    else:
        for i, cmd in enumerate(cmds):
            msgs = _validate_command_entry(cmd, f"{prefix}.commands[{i}]",
                                           require_target=False)
            messages.extend(msgs)

    return messages


def _validate_command_entry(cmd, path, require_target):
    messages = []
    if not isinstance(cmd, dict):
        return [f"{path} must be a JSON object"]

    cmd_name = cmd.get('command', '').upper()
    if not cmd_name:
        messages.append(f"{path} missing 'command' field")
    elif cmd_name not in _SUPPORTED_COMMANDS:
        messages.append(
            f"{path} unsupported command '{cmd_name}'. "
            f"Supported: {', '.join(sorted(_SUPPORTED_COMMANDS))}"
        )

    if require_target and 'target' not in cmd:
        messages.append(f"{path} missing 'target' field")

    return messages


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class CommandLoopRunner:
    """Executes a command_loop spec against loaded composition shapes.

    Args:
        executor: CommandExecutor instance — used to dispatch shape commands
        verbose:  If True, emit decision trace to the app UI log.
                  Overridden by 'verbose' key in spec if present.
                  Default True for now; flip to False for production.
    """

    def __init__(self, executor, verbose=True):
        self.executor = executor
        self._verbose_default = verbose

    # -----------------------------------------------------------------------
    # UI log output
    # -----------------------------------------------------------------------

    def _log(self, msg):
        """Emit a message to the app UI log if verbose is enabled."""
        if hasattr(self.executor, 'ui_instance') and self.executor.ui_instance:
            self.executor.ui_instance._log_output(f"    [loop] {msg}")
        else:
            print(f"[loop] {msg}")

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def run(self, spec, working_names):
        """Execute the command_loop.

        Args:
            spec:          command_loop dict from compose_parameters
            working_names: List of working name strings currently on canvas
                           e.g. ['compose_shape_1', 'compose_shape_2']

        Returns:
            Summary string of what was executed

        Raises:
            ValueError: if spec fails validation or a command fails
        """
        is_valid, messages = validate_command_loop(spec)
        if not is_valid:
            raise ValueError(
                "command_loop validation failed:\n  " + "\n  ".join(messages)
            )

        # verbose: spec key overrides constructor default
        verbose = bool(spec.get('verbose', self._verbose_default))

        iterations = int(self._resolve_numeric(spec.get('iterations', 1), default=1))
        top_commands    = spec.get('always_transforms', spec.get('commands', []))
        select_blocks   = spec.get('conditional_transforms', spec.get('select_blocks', []))

        applied_count = 0
        skipped_count = 0
        commands_applied = []

        placement_blocks = spec.get('placement_blocks', [])

        if verbose:
            self._log(
                f"Start: {iterations} iteration(s), "
                f"{len(top_commands)} always_transform(s), "
                f"{len(select_blocks)} conditional_transform(s), "
                f"{len(placement_blocks)} placement block(s). "
                f"Shapes: {', '.join(working_names)}"
            )

        for iteration in range(iterations):
            if verbose:
                self._log(f"--- Iteration {iteration + 1}/{iterations} ---")

            # always_transforms — apply unconditionally
            for idx, cmd_spec in enumerate(top_commands):
                target = cmd_spec.get('target', 'all')
                targets = self._resolve_targets(target, working_names)
                for name in targets:
                    exec_str, log_str = self._dispatch(cmd_spec, name)
                    if verbose:
                        self._log(f"  always[{idx}] {log_str}")
                    commands_applied.append(exec_str)
                    applied_count += 1

            # conditional_transforms — each fires independently by chance
            for bidx, block in enumerate(select_blocks):
                chance = float(block.get('chance', 1.0))
                roll = random.random()
                fired = roll <= chance

                if verbose:
                    self._log(
                        f"  cond[{bidx}] chance={chance:.2f} "
                        f"roll={roll:.3f} -> {'FIRED' if fired else 'SKIPPED'}"
                    )

                if not fired:
                    skipped_count += 1
                    continue

                target = block.get('target', 'random')
                resolved_targets = self._resolve_targets(target, working_names)
                resolved_targets = [t for t in resolved_targets if t is not None]

                if not resolved_targets:
                    if verbose:
                        self._log(f"  cond[{bidx}] target '{target}' unresolved, skipping")
                    continue

                if verbose:
                    self._log(f"  cond[{bidx}] target='{target}' resolved to {resolved_targets}")

                for resolved in resolved_targets:
                    for cidx, cmd_spec in enumerate(block.get('commands', [])):
                        exec_str, log_str = self._dispatch(cmd_spec, resolved)
                        if verbose:
                            self._log(f"    cmd[{cidx}] {log_str}")
                        commands_applied.append(exec_str)
                        applied_count += 1

            # placement_blocks — constraint-based solver for each
            for pidx, pb in enumerate(placement_blocks):
                target = pb.get('target', 'random')
                resolved_list = self._resolve_targets(target, working_names)
                resolved_list = [t for t in resolved_list if t is not None]

                if not resolved_list:
                    if verbose:
                        self._log(f"  placement[{pidx}] target '{target}' unresolved, skipping")
                    continue

                from src.composition.solver import PlacementSolver
                solver = PlacementSolver(self.executor, verbose=verbose)

                for resolved in resolved_list:
                    pb_resolved = dict(pb)
                    pb_resolved['target'] = resolved
                    pb_resolved['verbose'] = verbose

                    if verbose:
                        self._log(
                            f"  placement[{pidx}] target='{target}' resolved to '{resolved}' — running solver"
                        )

                    solver_summary, solver_cmds = solver.solve(pb_resolved)
                    commands_applied.extend(solver_cmds)
                    applied_count += 1
                    if verbose:
                        self._log(f"  placement[{pidx}] {solver_summary}")

        summary = (
            f"command_loop done: {iterations} iteration(s), "
            f"{applied_count} command(s) applied, "
            f"{skipped_count} conditional_transform(s) skipped"
        )
        if verbose:
            self._log(summary)

        return summary, commands_applied

    # -----------------------------------------------------------------------
    # Target resolution
    # -----------------------------------------------------------------------

    def _resolve_targets(self, target, working_names):
        """Resolve a target spec to a list of shape names.

        Accepts:
          'all'                        — all working names
          'random'                     — one random working name
          'compose_shape_N'            — specific name
          {'range': [lo, hi]}          — compose_shape_lo through compose_shape_hi
          {'list': [2, 3, 4]}          — compose_shape_2, compose_shape_3, etc.
          {'list': ['compose_shape_2']}— explicit name list

        Missing names are silently skipped.
        """
        if target == 'all':
            return list(working_names)

        if isinstance(target, dict):
            if 'range' in target:
                lo, hi = int(target['range'][0]), int(target['range'][1])
                names = [f"compose_shape_{n}" for n in range(lo, hi + 1)]
                return [n for n in names if n in working_names]

            if 'list' in target:
                items = target['list']
                names = []
                for item in items:
                    if isinstance(item, int):
                        names.append(f"compose_shape_{item}")
                    else:
                        names.append(str(item))
                return [n for n in names if n in working_names]

        result = self._resolve_single_target(target, working_names)
        return [result] if result is not None else []

    def _resolve_single_target(self, target, working_names):
        """Resolve a single target to one shape name.
        Returns None silently if not found — caller decides whether to log.
        """
        if not working_names:
            return None
        if isinstance(target, str):
            if target == 'random':
                return random.choice(working_names)
            if target in working_names:
                return target
        # Not found — return None silently (no warning log)
        return None

    # -----------------------------------------------------------------------
    # Numeric parameter resolution — supports fixed values and random ranges
    # -----------------------------------------------------------------------

    def _resolve_numeric(self, value, default=0.0):
        """Resolve a numeric parameter which may be a fixed value or a random spec.

        Fixed:   1.25  ->  1.25
        Uniform: {"random": "uniform", "min": 0.7, "max": 1.3}
        Normal:  {"random": "normal", "mean": 1.0, "std": 0.2, "min": 0.5, "max": 1.5}
                 min/max on normal acts as a clamp.

        Args:
            value:   Raw value from command spec (number or dict)
            default: Fallback if value is None

        Returns:
            Resolved float value

        Raises:
            ValueError: if distribution type is unknown or required keys missing
        """
        if value is None:
            return float(default)

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, dict):
            dist = value.get('random', '').lower()

            if dist == 'uniform':
                lo = float(value.get('min', 0.0))
                hi = float(value.get('max', 1.0))
                if lo > hi:
                    raise ValueError(
                        f"_resolve_numeric uniform: min ({lo}) > max ({hi})"
                    )
                return random.uniform(lo, hi)

            elif dist == 'uniform_int':
                lo = int(value.get('min', 0))
                hi = int(value.get('max', 1))
                if lo > hi:
                    raise ValueError(
                        f"_resolve_numeric uniform_int: min ({lo}) > max ({hi})"
                    )
                return float(random.randint(lo, hi))

            elif dist == 'normal':
                mean = float(value.get('mean', 0.0))
                std  = float(value.get('std',  1.0))
                result = random.gauss(mean, std)
                # Clamp if min/max provided
                if 'min' in value:
                    result = max(result, float(value['min']))
                if 'max' in value:
                    result = min(result, float(value['max']))
                return result

            else:
                raise ValueError(
                    f"_resolve_numeric: unknown distribution '{dist}'. "
                    f"Use 'uniform', 'uniform_int', or 'normal'."
                )

        raise ValueError(
            f"_resolve_numeric: expected number or dict, got {type(value).__name__}: {value!r}"
        )

    # -----------------------------------------------------------------------
    # Command dispatch
    # -----------------------------------------------------------------------

    def _dispatch(self, cmd_spec, shape_name):
        """Build and execute a command string for the given shape.
        Returns (exec_str, log_str) — exec_str is replayable, log_str is human-readable.
        """
        cmd_name = cmd_spec['command'].upper()

        if cmd_name == 'MOVE':
            return self._dispatch_move(cmd_spec, shape_name)
        elif cmd_name == 'ROTATE':
            return self._dispatch_rotate(cmd_spec, shape_name)
        elif cmd_name == 'SCALE':
            return self._dispatch_scale(cmd_spec, shape_name)
        elif cmd_name == 'DEFORM':
            return self._dispatch_deform(cmd_spec, shape_name)
        elif cmd_name in ('COLOR', 'WIDTH', 'FILL', 'ALPHA', 'ZORDER'):
            return self._dispatch_simple(cmd_name, cmd_spec, shape_name)
        elif cmd_name == 'REFLECT':
            return self._dispatch_reflect(cmd_spec, shape_name)
        else:
            raise ValueError(f"command_loop: unsupported command '{cmd_name}'")

    def _dispatch_move(self, cmd_spec, shape_name):
        """Execute MOVE. Accepts:
          delta: [dx, dy]
          direction + distance:
            direction may be:
              - 8-point compass:  N, NE, E, SE, S, SW, W, NW
              - 16-point compass: NNE, ENE, ESE, SSE, SSW, WSW, WNW, NNW
              - Numeric degrees:  0-360 float (0=North, clockwise)
              - "random":         random choice from all 16 compass points
              - {"random": "choice", "values": [...]}  random from named list
              - {"random": "degrees", "min": x, "max": y}  random degree range
            distance may be a fixed number or a random spec.
        """
        if 'delta' in cmd_spec:
            delta = cmd_spec['delta']
            dx, dy = float(delta[0]), float(delta[1])
            detail = f"delta={dx:.2f},{dy:.2f}"
        elif 'direction' in cmd_spec:
            distance = self._resolve_numeric(cmd_spec.get('distance'), default=20.0)
            direction, resolved_dir = self._resolve_direction(cmd_spec['direction'])
            dx, dy = self._direction_to_delta(direction, distance)
            detail = f"dir={resolved_dir} dist={distance:.2f} -> dx={dx:.2f},dy={dy:.2f}"
        else:
            raise ValueError("MOVE in command_loop requires 'delta' or 'direction'+'distance'")
        exec_str = f"MOVE {shape_name} {dx},{dy}"
        self.executor.execute(exec_str)
        return exec_str, f"MOVE -> '{shape_name}' ({detail})"

    def _resolve_direction(self, direction_spec):
        """Resolve a direction spec to a (direction_value, display_string) pair.

        direction_value is either a compass string or a float degrees value.
        display_string is suitable for logging.

        Args:
            direction_spec: string, number, or dict

        Returns:
            (direction_value, display_string)
        """
        _compass_16 = [
            'N', 'NNE', 'NE', 'ENE',
            'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW',
            'W', 'WNW', 'NW', 'NNW',
        ]

        # Plain string compass or "random"
        if isinstance(direction_spec, str):
            d = direction_spec.upper()
            if d == 'RANDOM':
                chosen = random.choice(_compass_16)
                return chosen, f"random->{chosen}"
            return d, d

        # Numeric degrees
        if isinstance(direction_spec, (int, float)):
            deg = float(direction_spec) % 360
            return deg, f"{deg:.1f}deg"

        # Dict random spec
        if isinstance(direction_spec, dict):
            dist = direction_spec.get('random', '').lower()

            if dist == 'choice':
                values = direction_spec.get('values', _compass_16)
                chosen = random.choice(values)
                chosen_u = chosen.upper() if isinstance(chosen, str) else float(chosen)
                return chosen_u, f"choice->{chosen_u}"

            elif dist == 'degrees':
                lo = float(direction_spec.get('min', 0.0))
                hi = float(direction_spec.get('max', 360.0))
                deg = random.uniform(lo, hi) % 360
                return deg, f"rnd-degrees({lo},{hi})->{deg:.1f}"

            else:
                raise ValueError(
                    f"_resolve_direction: unknown random type '{dist}'. "
                    f"Use 'choice' or 'degrees'."
                )

        raise ValueError(
            f"_resolve_direction: expected string, number, or dict, "
            f"got {type(direction_spec).__name__}: {direction_spec!r}"
        )

    @staticmethod
    def _direction_to_delta(direction, distance):
        """Convert a direction to (dx, dy). +x=East, +y=South.

        Accepts:
          - Compass string: 8-point (N, NE, ...) or 16-point (NNE, ENE, ...)
          - Float degrees:  0=North, 90=East, 180=South, 270=West (clockwise)
        """
        # Numeric degrees path
        if isinstance(direction, float):
            # Convert clockwise-from-North to standard math angle
            rad = math.radians(direction)
            dx =  distance * math.sin(rad)
            dy = -distance * math.cos(rad)
            return dx, dy

        # Compass string path — build full 16-point table
        d = direction.upper()
        s2 = math.sqrt(2)
        s5 = math.sqrt(5)  # used for NNE etc: component ratio is 1:2

        # For 16-point: NNE means 1 unit E, 2 units N (normalised)
        c1 = 1.0 / math.sqrt(5)   # short component (22.5deg offsets use 1/sqrt(5))
        c2 = 2.0 / math.sqrt(5)   # long component

        mapping = {
            # 8-point
            'N':   ( 0,            -distance),
            'NE':  ( distance/s2,  -distance/s2),
            'E':   ( distance,      0),
            'SE':  ( distance/s2,   distance/s2),
            'S':   ( 0,             distance),
            'SW':  (-distance/s2,   distance/s2),
            'W':   (-distance,      0),
            'NW':  (-distance/s2,  -distance/s2),
            # 16-point additions
            'NNE': ( distance*c1,  -distance*c2),
            'ENE': ( distance*c2,  -distance*c1),
            'ESE': ( distance*c2,   distance*c1),
            'SSE': ( distance*c1,   distance*c2),
            'SSW': (-distance*c1,   distance*c2),
            'WSW': (-distance*c2,   distance*c1),
            'WNW': (-distance*c2,  -distance*c1),
            'NNW': (-distance*c1,  -distance*c2),
        }
        if d not in mapping:
            raise ValueError(
                f"Unknown direction '{direction}'. "
                f"Use a 16-point compass name, a degree float, "
                f"'random', or a random dict spec."
            )
        return mapping[d]

    def _dispatch_rotate(self, cmd_spec, shape_name):
        angle = self._resolve_numeric(cmd_spec.get('angle'), default=0.0)
        exec_str = f"ROTATE {shape_name} {angle}"
        self.executor.execute(exec_str)
        return exec_str, f"ROTATE -> '{shape_name}' (angle={angle:.3f})"

    def _dispatch_scale(self, cmd_spec, shape_name):
        factor = self._resolve_numeric(cmd_spec.get('factor'), default=1.0)
        exec_str = f"SCALE {shape_name} {factor}"
        self.executor.execute(exec_str)
        return exec_str, f"SCALE -> '{shape_name}' (factor={factor:.3f})"

    def _dispatch_deform(self, cmd_spec, shape_name):
        axis   = cmd_spec.get('axis', 'major')
        along  = self._resolve_numeric(cmd_spec.get('along'),  default=1.0)
        across = self._resolve_numeric(cmd_spec.get('across'), default=1.0)
        exec_str = f"DEFORM {shape_name} AXIS={axis} ALONG={along} ACROSS={across}"
        self.executor.execute(exec_str)
        return exec_str, f"DEFORM -> '{shape_name}' (axis={axis} along={along:.3f} across={across:.3f})"

    def _dispatch_simple(self, cmd_name, cmd_spec, shape_name):
        """Dispatch single-value commands: COLOR, WIDTH, FILL, ALPHA, ZORDER."""
        if cmd_name == 'COLOR':
            value = cmd_spec.get('value', 'black')
        elif cmd_name == 'WIDTH':
            value = float(cmd_spec.get('value', 1))
        elif cmd_name == 'FILL':
            value = cmd_spec.get('value', 'none')
        elif cmd_name == 'ALPHA':
            value = float(cmd_spec.get('value', 1.0))
        elif cmd_name == 'ZORDER':
            value = cmd_spec.get('value', 0)
        exec_str = f"{cmd_name} {shape_name} {value}"
        self.executor.execute(exec_str)
        return exec_str, f"{cmd_name} -> '{shape_name}' (value={value})"

    # -----------------------------------------------------------------------
    # Utilities
    # -----------------------------------------------------------------------

    def _dispatch_reflect(self, cmd_spec, shape_name):
        axis = self._resolve_axis(cmd_spec.get('axis', 'horizontal'))
        exec_str = f"REFLECT {shape_name} AXIS={axis}"
        self.executor.execute(exec_str)
        return exec_str, f"REFLECT -> '{shape_name}' (axis={axis})"

    def _resolve_axis(self, axis_spec):
        """Resolve an axis spec — fixed string or random choice dict."""
        _ALL_AXES = ['horizontal', 'vertical', 'major', 'minor']
        if isinstance(axis_spec, str):
            if axis_spec.lower() == 'random':
                return random.choice(_ALL_AXES)
            return axis_spec.lower()
        if isinstance(axis_spec, dict):
            dist = axis_spec.get('random', '').lower()
            if dist == 'choice':
                values = axis_spec.get('values', _ALL_AXES)
                return random.choice(values).lower()
            raise ValueError(f"_resolve_axis: unsupported random type '{dist}'. Use 'choice'.")
        raise ValueError(
            f"_resolve_axis: expected string or dict, got {type(axis_spec).__name__}"
        )