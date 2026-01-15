"""
Enhancement Helper Functions
PIL-based utilities for pixel analysis and canvas inspection
"""
from PIL import Image
from collections import Counter
import colorsys


def get_dominant_colors(image, num_colors=5, sample_size=1000):
    """
    Extract dominant colors from PIL Image
    
    Args:
        image: PIL Image object
        num_colors: Number of dominant colors to return
        sample_size: Number of pixels to sample (0 = all pixels)
        
    Returns:
        List of (color_hex, frequency) tuples
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get pixel data
    pixels = list(image.getdata())
    
    # Sample if needed for performance
    if sample_size > 0 and len(pixels) > sample_size:
        import random
        pixels = random.sample(pixels, sample_size)
    
    # Count colors
    color_counts = Counter(pixels)
    most_common = color_counts.most_common(num_colors)
    
    # Convert to hex with frequencies
    results = []
    total = sum(count for _, count in most_common)
    for rgb, count in most_common:
        hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
        frequency = count / total
        results.append((hex_color, frequency))
    
    return results


def get_color_histogram(image):
    """
    Get RGB histogram from PIL Image
    
    Args:
        image: PIL Image object
        
    Returns:
        Dict with 'r', 'g', 'b' keys containing histogram lists
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    histogram = image.histogram()
    
    # Split into R, G, B channels (256 bins each)
    return {
        'r': histogram[0:256],
        'g': histogram[256:512],
        'b': histogram[512:768]
    }


def get_average_color(image, region=None):
    """
    Get average color from image or region
    
    Args:
        image: PIL Image object
        region: Optional (x1, y1, x2, y2) tuple for crop region
        
    Returns:
        Hex color string
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Crop to region if specified
    if region:
        image = image.crop(region)
    
    # Get all pixels
    pixels = list(image.getdata())
    
    if not pixels:
        return '#000000'
    
    # Calculate average
    r_avg = sum(p[0] for p in pixels) / len(pixels)
    g_avg = sum(p[1] for p in pixels) / len(pixels)
    b_avg = sum(p[2] for p in pixels) / len(pixels)
    
    return '#{:02x}{:02x}{:02x}'.format(int(r_avg), int(g_avg), int(b_avg))


def get_color_temperature(hex_color):
    """
    Classify color as warm, cool, or neutral
    
    Args:
        hex_color: Hex color string
        
    Returns:
        'warm', 'cool', or 'neutral'
    """
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # Hue ranges (normalized 0-1):
    # Warm: 0-0.15 (red-orange-yellow)
    # Cool: 0.45-0.75 (cyan-blue-purple)
    # Neutral: everything else or low saturation
    
    if s < 0.2:  # Low saturation = neutral
        return 'neutral'
    
    if h < 0.15 or h > 0.85:  # Red-orange range
        return 'warm'
    elif 0.45 <= h <= 0.75:  # Cyan-blue-purple range
        return 'cool'
    else:
        return 'neutral'


def get_complementary_color(hex_color):
    """
    Get complementary color (opposite on color wheel)
    
    Args:
        hex_color: Hex color string
        
    Returns:
        Complementary hex color string
    """
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # Rotate hue by 180 degrees (0.5 in 0-1 scale)
    h_comp = (h + 0.5) % 1.0
    
    # Convert back to RGB
    r_comp, g_comp, b_comp = colorsys.hsv_to_rgb(h_comp, s, v)
    
    return '#{:02x}{:02x}{:02x}'.format(
        int(r_comp * 255),
        int(g_comp * 255),
        int(b_comp * 255)
    )


def get_shape_bounds_on_canvas(shape):
    """
    Get bounding box of shape in canvas coordinates
    
    Args:
        shape: Shape object with geometry
        
    Returns:
        (x1, y1, x2, y2) tuple or None if shape has no geometry
    """
    if not hasattr(shape, 'attrs') or 'geometry' not in shape.attrs:
        return None
    
    geometry = shape.attrs['geometry']
    
    if 'points' in geometry:
        points = geometry['points']
        if not points:
            return None
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return (min(xs), min(ys), max(xs), max(ys))
    
    elif 'start' in geometry and 'end' in geometry:
        # Line
        x1, y1 = geometry['start']
        x2, y2 = geometry['end']
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    return None


def get_shape_centroid(shape):
    """
    Get centroid of shape
    
    Args:
        shape: Shape object with geometry
        
    Returns:
        (x, y) tuple or None
    """
    if not hasattr(shape, 'attrs') or 'geometry' not in shape.attrs:
        return None
    
    geometry = shape.attrs['geometry']
    
    if 'points' in geometry:
        points = geometry['points']
        if not points:
            return None
        x_avg = sum(p[0] for p in points) / len(points)
        y_avg = sum(p[1] for p in points) / len(points)
        return (x_avg, y_avg)
    
    elif 'start' in geometry and 'end' in geometry:
        # Line midpoint
        x1, y1 = geometry['start']
        x2, y2 = geometry['end']
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    return None


def get_canvas_region_around_shape(shape, margin=50):
    """
    Get region around shape with margin
    
    Args:
        shape: Shape object
        margin: Pixels to extend beyond shape bounds
        
    Returns:
        (x1, y1, x2, y2) tuple or None
    """
    bounds = get_shape_bounds_on_canvas(shape)
    if not bounds:
        return None
    
    x1, y1, x2, y2 = bounds
    return (
        max(0, x1 - margin),
        max(0, y1 - margin),
        min(768, x2 + margin),  # Canvas max width
        min(768, y2 + margin)   # Canvas max height
    )