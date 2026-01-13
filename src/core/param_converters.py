"""
Parameter type converters for procedural generation system
Converts string parameters from scripts to proper Python types
"""
from src.config import config

def int_converter(value):
    """Convert to integer"""
    return int(value)


def float_converter(value):
    """Convert to float"""
    return float(value)


def int_or_range(value):
    """Convert to int or tuple of ints (for ranges)
    
    Examples:
        "5" -> 5
        "5,8" -> (5, 8)
    """
    if ',' in value:
        parts = [int(x.strip()) for x in value.split(',')]
        if len(parts) != 2:
            raise ValueError(f"Range must be exactly 2 values, got {len(parts)}")
        return tuple(parts)
    return int(value)


def float_or_range(value):
    """Convert to float or tuple of floats (for ranges)
    
    Examples:
        "0.5" -> 0.5
        "0.2,0.8" -> (0.2, 0.8)
    """
    if ',' in value:
        parts = [float(x.strip()) for x in value.split(',')]
        if len(parts) != 2:
            raise ValueError(f"Range must be exactly 2 values, got {len(parts)}")
        return tuple(parts)
    return float(value)


def bounds_converter(value):
    """Convert to bounds tuple (x1, y1, x2, y2)
    
    Example:
        "100,100,600,600" -> (100, 100, 600, 600)
    """
    parts = [int(x.strip()) for x in value.split(',')]
    if len(parts) != 4:
        raise ValueError(f"Bounds must be 4 values (x1,y1,x2,y2), got {len(parts)}")
    return tuple(parts)


def point_converter(value):
    """Convert to point tuple (x, y)
    
    Example:
        "100,200" -> (100.0, 200.0)
    """
    parts = [float(x.strip()) for x in value.split(',')]
    if len(parts) != 2:
        raise ValueError(f"Point must be 2 values (x,y), got {len(parts)}")
    return tuple(parts)


def string_converter(value):
    """Pass through as string"""
    return value


def bool_converter(value):
    """Convert to boolean
    
    Examples:
        "TRUE", "true", "1", "YES", "yes", "ON" -> True
        "FALSE", "false", "0", "NO", "no", "OFF" -> False
    """
    return value.upper() in ['TRUE', '1', 'YES', 'ON']


def list_converter(value):
    """Convert comma-separated string to list
    
    Example:
        "split_offset,sawtooth,squarewave" -> ['split_offset', 'sawtooth', 'squarewave']
    """
    return [x.strip() for x in value.split(',')]


def choice_converter(value, choices):
    """Validate value is in allowed choices
    
    Args:
        value: The value to validate
        choices: List of allowed values
    
    Returns:
        value if valid
        
    Raises:
        ValueError if not in choices
    """
    if value not in choices:
        raise ValueError(f"Must be one of {choices}, got '{value}'")
    return value

def convert_weighted_list(value, choices=None):
    """Convert to weighted list format, supporting multiple input formats
    
    Accepts:
    - Weighted string: "op1:50,op2:30,op3:20" -> [['op1', 50], ['op2', 30], ['op3', 20]]
    - Simple string: "op1,op2,op3" -> [['op1', 1], ['op2', 1], ['op3', 1]]
    - Simple list: ['op1', 'op2'] -> [['op1', 1], ['op2', 1]]
    - Weighted list: [['op1', 5], ['op2', 3]] -> [['op1', 5], ['op2', 3]]
    
    Args:
        value: Input value (string or list)
        choices: Valid operation names (optional)
        
    Returns:
        List of [operation, weight] pairs
        
    Raises:
        ValueError: If format is invalid
    """
    # Handle string input (from template substitution)
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("Operations string cannot be empty")
        
        # Split by comma
        parts = [p.strip() for p in value.split(',')]
        weighted = []
        
        for part in parts:
            if ':' in part:
                # Weighted format: "operation:weight"
                op, weight_str = part.split(':', 1)
                op = op.strip()
                weight_str = weight_str.strip()
                
                try:
                    weight = float(weight_str)
                except ValueError:
                    raise ValueError(f"Invalid weight '{weight_str}' for operation '{op}'")
                
                if weight < 0:
                    raise ValueError(f"Weight for '{op}' must be non-negative, got {weight}")
                
                weighted.append([op, weight])
            else:
                # Simple format: "operation" (default weight 1)
                weighted.append([part, 1])
        
        value = weighted
    
    # Handle list input
    if not isinstance(value, list):
        raise ValueError(f"Weighted list must be a list or string, got {type(value).__name__}")
    
    if len(value) == 0:
        raise ValueError("Operations list cannot be empty")
    
    # Detect list format
    if all(isinstance(item, str) for item in value):
        # Simple list format: ['op1', 'op2']
        # Convert to weighted with equal weights
        weighted = [[op, 1] for op in value]
    elif all(isinstance(item, list) and len(item) == 2 for item in value):
        # Weighted list format: [['op1', weight1], ['op2', weight2]]
        weighted = value
        
        # Validate weights
        for i, (op, weight) in enumerate(weighted):
            if not isinstance(weight, (int, float)):
                raise ValueError(f"Weight for '{op}' must be a number, got {type(weight).__name__}")
            if weight < 0:
                raise ValueError(f"Weight for '{op}' must be non-negative, got {weight}")
    else:
        raise ValueError(
            "Operations must be simple list ['op1', 'op2'] "
            "or weighted list [['op1', weight1], ['op2', weight2]]"
        )
    
    # Validate operation names if choices provided
    if choices:
        for op, weight in weighted:
            if op not in choices:
                raise ValueError(f"Unknown operation '{op}', must be one of {choices}")
    
    return weighted
 
# Registry of converters by type name
CONVERTERS = {
    'int': int_converter,
    'float': float_converter,
    'int_or_range': int_or_range,
    'float_or_range': float_or_range,
    'bounds': bounds_converter,
    'point': point_converter,
    'str': string_converter,
    'bool': bool_converter,
    'list': list_converter,
    'weighted_list': convert_weighted_list,
}