"""
Parameter type converters for procedural generation system
Converts string parameters from scripts to proper Python types
"""


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
}