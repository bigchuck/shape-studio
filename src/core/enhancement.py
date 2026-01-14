"""
Enhancement Method Registry and Base Classes
Manages registered aesthetic enhancers and their specifications
"""
from abc import ABC, abstractmethod


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


class EnhancementRegistry:
    """Registry for enhancement methods"""
    
    def __init__(self):
        self.methods = {}
    
    def register(self, method_class):
        """
        Register an enhancement method
        
        Args:
            method_class: Class implementing EnhancementMethod
        """
        method = method_class()
        self.methods[method.name] = method
    
    def get(self, name):
        """
        Get enhancement method by name
        
        Args:
            name: Method name
            
        Returns:
            EnhancementMethod or None
        """
        return self.methods.get(name)
    
    def list_methods(self):
        """
        Get list of all registered methods
        
        Returns:
            list: List of method names
        """
        return list(self.methods.keys())
    
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