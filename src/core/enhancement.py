"""
Enhancement Method Registry and Base Classes
Manages registered aesthetic enhancers and their specifications
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import inspect
import importlib
import pkgutil

class EnhancementMethod(ABC):
    """Base class for enhancement methods"""
    
    @property
    @abstractmethod
    def name(self):
        """Method name (e.g., 'color_balance')"""
        pass
    
    @property
    @abstractmethod
    def description(self):
        """Human-readable description"""
        pass
    
    @property
    @abstractmethod
    def intent_spec(self):
        """
        Intent parameter specification
        
        Returns:
            dict: Parameter specifications with structure:
                {
                    'param_name': {
                        'type': 'string' | 'float' | 'int' | 'bool',
                        'required': bool,
                        'default': value,
                        'description': str,
                        'choices': [list] (optional, for string enums)
                    }
                }
        """
        pass
    
    @abstractmethod
    def validate_intent(self, intent_dict):
        """
        Validate the intent parameters
        Returns: (is_valid: bool, error_message: str)
        """
        pass
    
    @abstractmethod
    def enhance(self, canvas, shape_name, intent):
        """
        Perform enhancement
        
        Args:
            canvas: Active Canvas object
            shape_name: Name of shape to enhance, or "canvas" for global
            intent: Parsed intent dictionary
            
        Returns:
            dict: {
                'success': bool,
                'commands': {
                    'command_name': param_value,
                    ...
                },
                'reasoning': str,
                'modified_params': [list of param names]
            }
        """
        pass

    # === SHARED UTILITY METHODS ===
    
    def _parse_bool(self, value, default=False):
        """
        Convert string or boolean to boolean
        
        Args:
            value: String ('true', 'false', '1', '0', etc.) or bool
            default: Default value if parsing fails
            
        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return default
    
    def _parse_int(self, value, default=0):
        """
        Convert string or int to int
        
        Args:
            value: String or int
            default: Default value if parsing fails
            
        Returns:
            Integer value
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _parse_float(self, value, default=0.0):
        """
        Convert string or float to float
        
        Args:
            value: String or float
            default: Default value if parsing fails
            
        Returns:
            Float value
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _parse_choice(self, value, choices, default=None):
        """
        Validate value is in allowed choices
        
        Args:
            value: String value
            choices: List of allowed values
            default: Default if value not in choices
            
        Returns:
            Value if valid, otherwise default
        """
        if value in choices:
            return value
        return default if default is not None else choices[0]

class EnhancementRegistry:
    """Registry for enhancement methods"""
    
    def __init__(self):
        self.methods = {}
        self.methods: Dict[str, EnhancementMethod] = {}
        self._discover_methods()

    def _discover_methods(self):
        """Discover all EnhancementMethod subclasses"""
        # print("DEBUG: Starting discovery...")

        # Import all modules in the enhancers package
        try:
            import src.core.enhancers as enhancers_pkg
            # print(f"DEBUG: Imported enhancers package: {enhancers_pkg}")
            
            # Get the package path
            package_path = enhancers_pkg.__path__
            # print(f"DEBUG: Package path: {package_path}")
            
            # Import all modules in the package
            for importer, modname, ispkg in pkgutil.iter_modules(package_path):
                full_module_name = f'src.core.enhancers.{modname}'
                # print(f"DEBUG: Attempting to import {full_module_name}")
                try:
                    importlib.import_module(full_module_name)
                    # print(f"DEBUG: Successfully imported {full_module_name}")
                except Exception as e:
                    print(f"Warning: Could not import {full_module_name}: {e}")
                    import traceback
                    traceback.print_exc()
            
        except ImportError as e:
            print(f"Warning: Could not import enhancers package: {e}")
    
        # Now find all concrete subclasses
        # print(f"DEBUG: Looking for subclasses of {EnhancementMethod}")
        all_subclasses = self._get_all_subclasses(EnhancementMethod)
        # print(f"DEBUG: Found {len(all_subclasses)} subclass(es): {all_subclasses}")
    
        for cls in all_subclasses:
            # print(f"DEBUG: Checking {cls.__name__}, abstract={inspect.isabstract(cls)}")
            if not inspect.isabstract(cls):
                try:
                    # print(f"DEBUG: Attempting to instantiate {cls.__name__}")
                    instance = cls()
                    self.methods[instance.name] = instance
                    # print(f"Registered enhancement method: {instance.name}")
                except Exception as e:
                    print(f"Warning: Could not instantiate {cls.__name__}: {e}")
                    import traceback
                    traceback.print_exc()        
  
    def _get_all_subclasses(self, cls):
        """Recursively get all subclasses of a class"""
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(self._get_all_subclasses(subclass))
        return all_subclasses
    
    def get(self, name: str) -> Optional[EnhancementMethod]:
        """Get an enhancement method by name"""
        return self.methods.get(name)
    
    def list_methods(self) -> List[str]:
        """List all available enhancement method names"""
        return sorted(self.methods.keys())
    
    def get_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get information about an enhancement method"""
        method = self.get(name)
        if method:
            info = {
                'name': method.name,
                'description': method.description,
            }
            # Add metadata if available
            if hasattr(method, 'get_metadata'):
                info['metadata'] = method.get_metadata()
            return info
        return None

    def register(self, method_class):
        """
        Register an enhancement method
        
        Args:
            method_class: Class implementing EnhancementMethod
        """
        method = method_class()
        self.methods[method.name] = method
    
    def get_method_info(self, name):
        """
        Get information about a method
        
        Args:
            name: Method name
            
        Returns:
            dict: Method information or None
        """
        method = self.methods.get(name)
        if not method:
            return None
        
        return {
            'name': method.name,
            'description': method.description,
            'intent_spec': method.intent_spec
        }


# Global registry instance
_registry = EnhancementRegistry()


def get_registry():
    """Get the global enhancement registry"""
    return _registry