"""
Template system for Shape Studio
Provides reusable procedural blueprints with parameter substitution
"""
import json
import random
import re
from pathlib import Path
from src.config import config


class TemplateLibrary:
    """Manages loading and indexing of template definitions"""
    
    def __init__(self, project_root='.'):
        self.project_root = Path(project_root)
        self.templates = {}  # name -> template_def
        self.search_paths = [
            self.project_root / 'templates',  # Project templates
            Path.home() / '.shapestudio' / 'templates'  # Global templates
        ]
        
    def load_library(self, filepath):
        """Load templates from a JSON library file
        
        Args:
            filepath: Path to template library JSON
            
        Returns:
            Number of templates loaded
            
        Raises:
            FileNotFoundError: If library file doesn't exist
            ValueError: If JSON is invalid
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Template library not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate structure
        if 'templates' not in data:
            raise ValueError(f"Template library must have 'templates' key: {filepath}")
        
        templates = data['templates']
        if not isinstance(templates, dict):
            raise ValueError(f"Templates must be a dictionary: {filepath}")
        
        # Load each template
        count = 0
        for name, template_def in templates.items():
            self._validate_template(name, template_def, filepath)
            self.templates[name] = template_def
            count += 1
        
        return count
    
    def _validate_template(self, name, template_def, source_file):
        """Validate template definition structure"""
        # Must have commands
        if 'commands' not in template_def:
            raise ValueError(f"Template '{name}' missing 'commands' key in {source_file}")
        
        commands = template_def['commands']
        if not isinstance(commands, list):
            raise ValueError(f"Template '{name}' commands must be a list in {source_file}")
        
        if not commands:
            raise ValueError(f"Template '{name}' has no commands in {source_file}")
        
        # All commands must be strings
        for i, cmd in enumerate(commands):
            if not isinstance(cmd, str):
                raise ValueError(
                    f"Template '{name}' command {i} must be a string in {source_file}"
                )
        
        # Validate param definitions if present
        if 'required_params' in template_def:
            if not isinstance(template_def['required_params'], list):
                raise ValueError(
                    f"Template '{name}' required_params must be a list in {source_file}"
                )
        
        if 'optional_params' in template_def:
            if not isinstance(template_def['optional_params'], dict):
                raise ValueError(
                    f"Template '{name}' optional_params must be a dict in {source_file}"
                )
    
    def get_template(self, name):
        """Get template definition by name
        
        Returns:
            Template definition dict or None if not found
        """
        return self.templates.get(name)
    
    def list_templates(self):
        """Return list of loaded template names"""
        return sorted(self.templates.keys())
    
    def search_for_library(self, filename):
        """Search for library file in search paths
        
        Args:
            filename: Library filename (e.g., 'library.json')
            
        Returns:
            Full path if found, None otherwise
        """
        # Try as absolute/relative path first
        filepath = Path(filename)
        if filepath.exists():
            return filepath
        
        # Search in paths
        for search_path in self.search_paths:
            candidate = search_path / filename
            if candidate.exists():
                return candidate
        
        return None


class TemplateExecutor:
    """Executes templated command sequences with parameter substitution"""
    
    def __init__(self, library, command_executor):
        """
        Args:
            library: TemplateLibrary instance
            command_executor: CommandExecutor instance for running commands
        """
        self.library = library
        self.executor = command_executor
        
    def execute_script(self, script_filepath, executable_name=None, 
                      batch_mode=False, randomization_values=None):
        """Execute a templated script
        
        Args:
            script_filepath: Path to script JSON file
            executable_name: Name of executable to run, or None for --ALL
            batch_mode: If True, run for BATCH (affects error handling)
            randomization_values: Dict of pre-selected random values (for BATCH)
            
        Returns:
            List of result messages
            
        Raises:
            FileNotFoundError: If script doesn't exist
            ValueError: If script is invalid or executable not found
        """
        # Load script
        script_data = self._load_script(script_filepath)
        
        # Load template libraries
        self._load_libraries(script_data, script_filepath)
        
        # Get executables to run
        executables = script_data.get('executables', {})
        if not executables:
            raise ValueError(f"No executables found in {script_filepath}")
        
        # Determine which executables to run
        if executable_name is None or executable_name == '--ALL':
            exec_names = list(executables.keys())
        elif ',' in executable_name:
            # Multiple executables specified
            exec_names = [n.strip() for n in executable_name.split(',')]
        else:
            exec_names = [executable_name]
        
        # Validate all executables exist
        for name in exec_names:
            if name not in executables:
                available = ', '.join(executables.keys())
                raise ValueError(
                    f"Executable '{name}' not found in {script_filepath}\n"
                    f"Available executables: {available}"
                )
        
        # Execute each
        results = []
        global_params = script_data.get('global_params', {})
        
        for exec_name in exec_names:
            executable = executables[exec_name]
            result = self._execute_one(
                exec_name, executable, global_params,
                batch_mode, randomization_values
            )
            results.append(f"[{exec_name}] {result}")
        
        return results
    
    def _load_script(self, filepath):
        """Load and validate script JSON"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Script file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Check if it's new format (with executables) or old format (array)
        if isinstance(data, list):
            raise ValueError(
                f"Script {filepath} is old format (array of commands).\n"
                f"For template support, use new format with 'executables' key.\n"
                f"Use plain RUN command for old format scripts."
            )
        
        if not isinstance(data, dict):
            raise ValueError(f"Script must be JSON object: {filepath}")
        
        return data
    
    def _load_libraries(self, script_data, script_filepath):
        """Load template libraries referenced in script"""
        libraries = script_data.get('template_libraries', [])
        
        if not isinstance(libraries, list):
            raise ValueError("'template_libraries' must be a list")
        
        script_dir = Path(script_filepath).parent
        
        for lib_ref in libraries:
            # Try relative to script first
            lib_path = script_dir / lib_ref
            if not lib_path.exists():
                # Try search paths
                lib_path = self.library.search_for_library(lib_ref)
                if lib_path is None:
                    raise FileNotFoundError(
                        f"Template library not found: {lib_ref}\n"
                        f"Searched in:\n"
                        f"  - {script_dir / lib_ref}\n"
                        f"  - {self.library.search_paths}"
                    )
            
            self.library.load_library(lib_path)
    
    def _execute_one(self, exec_name, executable, global_params, 
                    batch_mode, randomization_values):
        """Execute a single named executable"""
        commands = executable.get('commands', [])
        
        if not commands:
            raise ValueError(f"Executable '{exec_name}' has no commands")
        
        # Build parameter context for substitution
        param_context = {}
        
        # Start with global params
        param_context.update(global_params)
        
        # Apply randomization if provided (BATCH mode)
        if randomization_values:
            param_context.update(randomization_values)
        
        # Execute each command in sequence
        results = []
        for i, cmd_spec in enumerate(commands):
            if not isinstance(cmd_spec, dict):
                raise ValueError(
                    f"Command {i} in executable '{exec_name}' must be a dict"
                )
            
            template_name = cmd_spec.get('template')
            if not template_name:
                raise ValueError(
                    f"Command {i} in executable '{exec_name}' missing 'template' key"
                )
            
            # Get template
            template = self.library.get_template(template_name)
            if not template:
                available = ', '.join(self.library.list_templates())
                raise ValueError(
                    f"Template '{template_name}' not found\n"
                    f"Available templates: {available}"
                )
            
            # Execute this command
            result = self._execute_template_command(
                template_name, template, cmd_spec, param_context
            )
            results.append(result)
        
        return f"Executed {len(commands)} template command(s)"
    
    def _execute_template_command(self, template_name, template, 
                                  cmd_spec, param_context):
        """Execute a single template command with parameter substitution"""
        # Get explicit params from command
        explicit_params = cmd_spec.get('params', {})
        
        # Build full parameter set
        params = {}
        
        # Start with template's optional params (defaults)
        optional_params = template.get('optional_params', {})
        params.update(optional_params)
        
        # Override with context (global + randomization)
        params.update(param_context)
        
        # Override with explicit params - but first substitute any ${...} in their values
        for key, value in explicit_params.items():
            if isinstance(value, str) and '${' in value:
                # This param value contains a reference - substitute it
                value = self._substitute_params(value, params)
            params[key] = value
        
        # Check required params
        required_params = template.get('required_params', [])
        missing = []
        for req in required_params:
            if req not in params:
                missing.append(req)
        
        if missing:
            raise ValueError(
                f"Template '{template_name}' missing required parameters: {', '.join(missing)}\n"
                f"Required: {', '.join(required_params)}"
            )
        
        # Substitute and execute each command in template
        template_commands = template['commands']
        for cmd_template in template_commands:
            # Perform substitution
            resolved_cmd = self._substitute_params(cmd_template, params)
            
            # Execute the command
            self.executor.execute(resolved_cmd)
        
        return f"Template '{template_name}' applied"
    
    def _substitute_params(self, command_str, params):
        """Substitute ${var} placeholders in command string
        
        Args:
            command_str: Command string with ${var} placeholders
            params: Dict of parameter values
            
        Returns:
            Command string with substitutions applied
            
        Raises:
            ValueError: If any ${var} cannot be resolved
        """
        # Find all ${...} patterns
        pattern = r'\$\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            if var_name not in params:
                raise ValueError(
                    f"Undefined variable: ${{{var_name}}}\n"
                    f"Available parameters: {', '.join(sorted(params.keys()))}\n"
                    f"In command: {command_str}"
                )
            return str(params[var_name])
        
        result = re.sub(pattern, replacer, command_str)
        
        # Verify no unresolved variables remain
        remaining = re.findall(pattern, result)
        if remaining:
            raise ValueError(f"Unresolved variables after substitution: {remaining}")
        
        return result
    
    def validate_script(self, script_filepath):
        """Validate a script without executing it
        
        Returns:
            Tuple of (is_valid, messages_list)
        """
        messages = []
        
        try:
            # Load script
            script_data = self._load_script(script_filepath)
            messages.append(f"✓ Script structure valid")
            
            # Load libraries
            try:
                self._load_libraries(script_data, script_filepath)
                lib_count = len(self.library.templates)
                messages.append(f"✓ Loaded {lib_count} templates from libraries")
            except Exception as e:
                messages.append(f"✗ Library loading failed: {e}")
                return (False, messages)
            
            # Check executables
            executables = script_data.get('executables', {})
            if not executables:
                messages.append(f"✗ No executables defined")
                return (False, messages)
            
            messages.append(f"✓ Found {len(executables)} executable(s)")
            
            # Validate each executable
            global_params = script_data.get('global_params', {})
            
            for exec_name, executable in executables.items():
                try:
                    self._validate_executable(exec_name, executable, global_params)
                    messages.append(f"  ✓ {exec_name}")
                except Exception as e:
                    messages.append(f"  ✗ {exec_name}: {e}")
                    return (False, messages)
            
            messages.append("✓ All executables valid")
            return (True, messages)
            
        except Exception as e:
            messages.append(f"✗ Validation failed: {e}")
            return (False, messages)
    
    def _validate_executable(self, exec_name, executable, global_params):
        """Validate a single executable without executing"""
        commands = executable.get('commands', [])
        
        if not commands:
            raise ValueError("No commands defined")
        
        # Check each command references valid template
        for i, cmd_spec in enumerate(commands):
            if not isinstance(cmd_spec, dict):
                raise ValueError(f"Command {i} must be dict")
            
            template_name = cmd_spec.get('template')
            if not template_name:
                raise ValueError(f"Command {i} missing 'template' key")
            
            # Check template exists
            template = self.library.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Build param context
            params = {}
            params.update(global_params)
            params.update(template.get('optional_params', {}))
            params.update(cmd_spec.get('params', {}))
            
            # Check required params
            required = template.get('required_params', [])
            missing = [r for r in required if r not in params]
            if missing:
                raise ValueError(
                    f"Command {i} template '{template_name}' "
                    f"missing required params: {', '.join(missing)}"
                )
    
    def list_executables(self, script_filepath):
        """List executables in a script file
        
        Returns:
            Formatted string with executable information
        """
        script_data = self._load_script(script_filepath)
        executables = script_data.get('executables', {})
        
        if not executables:
            return f"No executables in {script_filepath}"
        
        lines = [f"Executables in '{script_filepath}':"]
        
        for name, executable in executables.items():
            desc = executable.get('description', 'No description')
            lines.append(f"  {name}: {desc}")
            
            # List templates used
            commands = executable.get('commands', [])
            templates_used = []
            for cmd_spec in commands:
                if isinstance(cmd_spec, dict):
                    template_name = cmd_spec.get('template')
                    if template_name and template_name not in templates_used:
                        templates_used.append(template_name)
            
            if templates_used:
                lines.append(f"    - Uses templates: {', '.join(templates_used)}")
            lines.append(f"    - Commands: {len(commands)}")
            
            # Check for randomization
            randomization = executable.get('randomization')
            if randomization:
                rand_keys = ', '.join(randomization.keys())
                lines.append(f"    - Randomization: {rand_keys}")
            
            lines.append("")  # Blank line between executables
        
        return '\n'.join(lines)
    
    def generate_randomization(self, executable):
        """Generate random values for an executable's randomization spec
        
        Supports four formats:
        - Dict: {"type": "normal", "min": x, "max": y, "mean": z, "std": w} - normal distribution
        - Range: [min, max] - uniform random number in range
        - Simple list: [val1, val2, ...] - uniform random choice
        - Weighted list: "val1:weight1,val2:weight2, ..." - weighted random choice
        
        Args:
            executable: Executable dict with optional 'randomization' key
            
        Returns:
            Dict of randomized parameter values
            
        Raises:
            ValueError: If format is invalid or weights are invalid
        """
        randomization = executable.get('randomization', {})

        if not randomization:
            return {}
        
        randomized = {}
        
        for key, spec in randomization.items():
            # Check if this is a dictionary format (for distributions)
            if isinstance(spec, dict):
                dist_type = spec.get('type')
                if dist_type == 'normal':
                    randomized[key] = self._generate_normal_value(key, spec)
                else:
                    raise ValueError(
                        f"Unknown distribution type '{dist_type}' for '{key}'\n"
                        f"Supported types: 'normal'"
                    )
                continue
            
            # Existing list-based format handling
            if not isinstance(spec, list):
                raise ValueError(
                    f"Randomization value for '{key}' must be list or dict (for distributions)"
                )
            
            if len(spec) == 0:
                raise ValueError(f"Randomization list for '{key}' is empty")
            
            # Check if this is a range format: [min, max]
            if len(spec) == 2 and isinstance(spec[0], (int, float)) and isinstance(spec[1], (int, float)):
                # Range format: [min, max]
                min_val, max_val = spec
                if min_val > max_val:
                    raise ValueError(
                        f"Invalid range for '{key}': min ({min_val}) > max ({max_val})"
                    )
                
                if isinstance(min_val, int) and isinstance(max_val, int):
                    randomized[key] = random.randint(min_val, max_val)
                else:
                    randomized[key] = random.uniform(min_val, max_val)
            
            # Check if this is weighted format: [[val, weight], [val, weight], ...]
            elif all(isinstance(item, list) for item in spec):
                # Validate weighted format
                self._validate_weighted_list(key, spec)
                
                # Extract values and weights
                values = [item[0] for item in spec]
                weights = [item[1] for item in spec]
                
                # Use weighted random selection
                randomized[key] = random.choices(values, weights=weights)[0]
            
            # Simple list format: [val1, val2, ...]
            else:
                # Verify it's not a mix of weighted and simple
                if any(isinstance(item, list) for item in spec):
                    raise ValueError(
                        f"Mixed format detected for '{key}': "
                        f"use all weighted [[val, weight], ...] or all simple [val, ...]"
                    )
                
                # Uniform random choice
                randomized[key] = random.choice(spec)
        
        return randomized
            
    def _validate_weighted_list(self, key, spec):
        """Validate weighted list format
        
        Args:
            key: Parameter name (for error messages)
            spec: List of [value, weight] pairs
            
        Raises:
            ValueError: If format is invalid
        """
        for i, item in enumerate(spec):
            # Check structure
            if not isinstance(item, list):
                raise ValueError(
                    f"Weighted list for '{key}' item {i}: expected [value, weight], got {type(item).__name__}"
                )
            
            if len(item) != 2:
                raise ValueError(
                    f"Weighted list for '{key}' item {i}: expected [value, weight] with 2 elements, got {len(item)}"
                )
            
            value, weight = item
            
            # Validate weight
            if not isinstance(weight, (int, float)):
                raise ValueError(
                    f"Weighted list for '{key}' item {i}: weight must be number, got {type(weight).__name__} ({weight})"
                )
            
            if weight <= 0:
                raise ValueError(
                    f"Weighted list for '{key}' item {i}: weight must be positive, got {weight}"
                )
            
            # Note: We allow any value type for the value itself
            # Could be string, int, float, etc.

    def _generate_normal_value(self, key, spec):
        """Generate a value from a normal distribution with rejection sampling
        
        Args:
            key: Parameter name (for error messages)
            spec: Dict with keys: type, min, max, mean, std
            
        Returns:
            Generated value (int or float based on min/max types)
            
        Raises:
            ValueError: If spec is invalid or rejection sampling fails
        """
        # Validate required fields
        required = ['min', 'max', 'mean', 'std']
        missing = [f for f in required if f not in spec]
        if missing:
            raise ValueError(
                f"Normal distribution for '{key}' missing required fields: {', '.join(missing)}\n"
                f"Required: type, min, max, mean, std"
            )
        
        min_val = spec['min']
        max_val = spec['max']
        mean = spec['mean']
        std = spec['std']
        
        # Validate types
        if not isinstance(min_val, (int, float)):
            raise ValueError(f"Normal distribution for '{key}': 'min' must be numeric")
        if not isinstance(max_val, (int, float)):
            raise ValueError(f"Normal distribution for '{key}': 'max' must be numeric")
        if not isinstance(mean, (int, float)):
            raise ValueError(f"Normal distribution for '{key}': 'mean' must be numeric")
        if not isinstance(std, (int, float)):
            raise ValueError(f"Normal distribution for '{key}': 'std' must be numeric")
        
        # Validate ranges
        if min_val >= max_val:
            raise ValueError(
                f"Normal distribution for '{key}': min ({min_val}) must be < max ({max_val})"
            )
        
        if std <= 0:
            raise ValueError(
                f"Normal distribution for '{key}': std ({std}) must be positive"
            )
        
        # Rejection sampling with retry limit
        max_retries = config.randomization.normal_distribution.max_sampling_attempts
        for attempt in range(max_retries):
            value = random.gauss(mean, std)
            
            # Check if value is in valid range
            if min_val <= value <= max_val:
                # Determine if result should be int or float
                if isinstance(min_val, int) and isinstance(max_val, int):
                    return round(value)
                else:
                    return value
        if config.randomization.normal_distribution.fallback_to_uniform:
            # Fall back to uniform distribution
            value = random.uniform(min_val, max_val)
        else:
            # Raise error
            raise ValueError(f"Normal distribution sampling failed after {max_retries} attempts")

        if config.randomization.normal_distribution.warn_on_failures:
            import warnings
            warnings.warn(f"Normal distribution sampling required {max_retries} attempts")

        # Failed to generate valid value after max retries
        raise ValueError(
            f"Normal distribution for '{key}' failed after {max_retries} attempts\n"
            f"Parameters: mean={mean}, std={std}, range=[{min_val}, {max_val}]\n"
            f"Consider: (1) reducing std, (2) adjusting mean closer to range center, "
            f"or (3) widening the range"
        )