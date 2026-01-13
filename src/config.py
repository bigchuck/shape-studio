"""
Configuration Management for Shape Studio
Provides centralized configuration with hierarchical access
"""
import json
import os
from pathlib import Path


class ConfigNode:
    """
    Hierarchical configuration node supporting dot notation access.
    Immutable after initialization to prevent runtime modification.
    """
    
    def __init__(self, data):
        """Initialize node from dictionary"""
        self._data = {}
        self._frozen = False
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursive: nested dicts become ConfigNodes
                self._data[key] = ConfigNode(value)
            else:
                self._data[key] = value
    
    def __getattr__(self, name):
        """Support dot notation: config.canvas.width"""
        if name.startswith('_'):
            # Internal attributes
            return object.__getattribute__(self, name)
        
        if name not in self._data:
            raise AttributeError(f"Configuration key '{name}' not found")
        
        return self._data[name]
    
    def __setattr__(self, name, value):
        """Prevent modification after freezing"""
        if name.startswith('_'):
            # Allow internal attributes
            object.__setattr__(self, name, value)
            return
        
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError("Configuration is read-only after initialization")
        
        self._data[name] = value
    
    def get(self, path, default=None):
        """
        Get value by path with optional default.
        
        Args:
            path: Dot-separated path (e.g., 'canvas.width')
            default: Value to return if path not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        current = self
        
        try:
            for key in keys:
                current = getattr(current, key)
            return current
        except AttributeError:
            return default
    
    def to_dict(self):
        """Convert back to plain dictionary (for debugging/export)"""
        result = {}
        for key, value in self._data.items():
            if isinstance(value, ConfigNode):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
    
    def _freeze(self):
        """Recursively freeze this node and all children"""
        self._frozen = True
        for value in self._data.values():
            if isinstance(value, ConfigNode):
                value._freeze()


class Config:
    """
    Shape Studio configuration manager.
    Loads from JSON file if present, otherwise uses defaults.
    Read-only after initialization.
    """
    
    def __init__(self):
        """Initialize with default configuration"""
        self._root = ConfigNode(self._get_defaults())
        self._loaded = False
    
    def load(self, config_path=None):
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to config.json (optional)
                        If None, looks in standard location
        """
        if self._loaded:
            raise RuntimeError("Configuration already loaded")
        
        # Determine config file location
        if config_path is None:
            # Look for config.json in project root
            possible_paths = [
                Path(__file__).parent.parent / 'config.json',  # project root
                Path('config.json'),  # current directory
            ]
            
            config_path = None
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
        
        # Load from file if present
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            
            # Merge user config with defaults
            merged = self._merge_configs(self._get_defaults(), user_config)
            self._root = ConfigNode(merged)
        
        # Freeze configuration (make read-only)
        self._root._freeze()
        self._loaded = True
    
    def _get_defaults(self):
        """Return default configuration dictionary"""
        return {
            # Canvas and display settings
            'canvas': {
                'width': 768,
                'height': 768,
                'origin': 'top-left',  # coordinate system
                'grid_spacing': 64,
                'default_bounds_margin': 100,  # margin from edges for default bounds
            },
            
            # File system paths
            'paths': {
                'output': 'output',
                'scripts': 'scripts',
                'shapes': 'shapes',  # project object store
                'projects': 'projects',
                'templates': 'templates',
                'global_library': '~/.shapestudio/shapes',
            },
            
            # Procedural generation system
            'procedural': {
                # Core algorithm defaults
                'defaults': {
                    'iterations': 10,
                    'max_retries': 15,
                    'connect': 'angle_sort',
                    'direction_bias': 'random',
                },
                
                # Shape modification parameters
                'operations': {
                    'break_margin': 0.15,        # minimum distance from endpoints (0.0-0.5)
                    'break_width_max': 0.5,      # maximum break width as fraction (0.0-1.0)
                    'projection_max': 2.0,       # maximum projection distance multiplier
                    'min_segment_length': 10,    # minimum segment length for selection (pixels)
                },
                
                # Squarewave-specific settings
                'squarewave': {
                    'independent_directions': False,
                    'opposite_direction_prob': 0.2,
                },
                
                # Geometric validation thresholds
                'validation': {
                    'enabled': True,
                    'check_intersections': True,
                    
                    # Minimum clearance between non-adjacent segments
                    'min_segment_clearance': 15.0,         # pixels (absolute)
                    'min_segment_clearance_relative': 0.02, # fraction of diagonal (if use_relative)
                    'use_relative_clearance': False,        # use relative vs absolute
                    
                    # Minimum interior angle at vertices
                    'min_angle': 20.0,  # degrees
                    
                    # Minimum aspect ratio (width/height) for protrusions
                    'min_aspect_ratio': 0.4,  # prevents needle-like extensions
                    
                    # Whether to validate on each retry or only final result
                    'validate_each_retry': True,
                },
                
                # Debug and visualization
                'debug': {
                    'verbose_default': 0,          # 0=silent, 1=summary, 2=detailed, 3=full
                    'save_iterations_default': False,
                    'snapshot_interval_default': 1,
                },
            },
            
            # Randomization system
            'randomization': {
                # Normal distribution settings
                'normal_distribution': {
                    'max_sampling_attempts': 1000,  # rejection sampling retry limit
                    'fallback_to_uniform': False,   # fallback if all attempts fail
                    'warn_on_failures': True,       # log warning on fallback
                },
                
                # General randomization
                'default_distribution': 'uniform',
                'seed': None,  # None = random, int = reproducible
            },
            
            # Animation preview system
            'animation': {
                'default_fps': 2,
                'fps_range': [1, 10],
                'preview_size': 512,  # preview window dimensions
                'default_loop': False,
            },
            
            # UI settings (for future use)
            'ui': {
                'command_log_width': 400,
                'canvas_padding': 10,
                'window_title': 'Shape Studio',
            },
        }
    
    def _merge_configs(self, defaults, overrides):
        """
        Recursively merge override config into defaults.
        
        Args:
            defaults: Default configuration dict
            overrides: User-provided overrides
            
        Returns:
            Merged configuration dict
        """
        result = defaults.copy()
        
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dicts
                result[key] = self._merge_configs(result[key], value)
            else:
                # Direct override
                result[key] = value
        
        return result
    
    def __getattr__(self, name):
        """Support dot notation: config.canvas"""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return getattr(self._root, name)
    
    def get(self, path, default=None):
        """
        Get configuration value by path.
        
        Args:
            path: Dot-separated path (e.g., 'canvas.width')
            default: Value to return if path not found
            
        Returns:
            Configuration value or default
            
        Example:
            width = config.get('canvas.width', 800)
        """
        return self._root.get(path, default)
    
    def to_dict(self):
        """Export configuration as dictionary (for debugging)"""
        return self._root.to_dict()
    
    def export_json(self, output_path):
        """
        Export current configuration to JSON file.
        
        Args:
            output_path: Path to write JSON config
        """
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Module-level singleton
# Initialized on first import, loaded in main.py
_config_instance = None


def get_config():
    """
    Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Convenience alias for imports: from src.config import config
config = get_config()