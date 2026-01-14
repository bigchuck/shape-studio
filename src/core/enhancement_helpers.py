"""
PIL Helper Functions for Enhancement Modules
Provides common image analysis utilities
"""
from PIL import Image, ImageDraw
from collections import defaultdict
import colorsys


def render_canvas_to_pil(canvas, width=768, height=768):
    """
    Render canvas to PIL Image for pixel analysis
    
    Args:
        canvas: Canvas object with shapes
        width: Image width (default 768)
        height: Image height (default 768)
        
    Returns:
        PIL.Image: Rendered canvas
    """
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Sort shapes by z-order
    sorted_shapes = sorted(canvas.shapes.values(), key=lambda s: s.attrs.get('z_order', 0))
    
    for shape in sorted_shapes:
        shape.draw(draw)
    
    return img


def get_color_histogram(image, bins=16):
    """
    Compute color histogram across RGB channels
    
    Args:
        image: PIL Image
        bins: Number of bins per channel
        
    Returns:
        dict: Histogram data with RGB channel breakdowns
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = list(image.getdata())
    
    # Initialize histograms
    r_hist = defaultdict(int)
    g_hist = defaultdict(int)
    b_hist = defaultdict(int)
    
    bin_size = 256 // bins
    
    for r, g, b in pixels:
        r_bin = (r // bin_size) * bin_size
        g_bin = (g // bin_size) * bin_size
        b_bin = (b // bin_size) * bin_size
        
        r_hist[r_bin] += 1
        g_hist[g_bin] += 1
        b_hist[b_bin] += 1
    
    return {
        'red': dict(r_hist),
        'green': dict(g_hist),
        'blue': dict(b_hist),
        'total_pixels': len(pixels)
    }


def get_dominant_colors(image, num_colors=5):
    """
    Extract dominant colors from image
    
    Args:
        image: PIL Image
        num_colors: Number of dominant colors to extract
        
    Returns:
        list: List of (color_hex, percentage) tuples
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Quantize to reduce color space
    quantized = image.quantize(colors=num_colors)
    palette = quantized.getpalette()
    
    # Count color frequencies
    color_counts = defaultdict(int)
    for pixel in quantized.getdata():
        color_counts[pixel] += 1
    
    # Convert to hex and percentages
    total_pixels = image.width * image.height
    results = []
    
    for color_idx, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
        r = palette[color_idx * 3]
        g = palette[color_idx * 3 + 1]
        b = palette[color_idx * 3 + 2]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        percentage = (count / total_pixels) * 100
        results.append((hex_color, percentage))
    
    return results[:num_colors]


def get_average_brightness(image):
    """
    Calculate average brightness of image
    
    Args:
        image: PIL Image
        
    Returns:
        float: Average brightness (0.0-1.0)
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = list(image.getdata())
    total_brightness = 0
    
    for r, g, b in pixels:
        # Convert to HSV and get value (brightness)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        total_brightness += v
    
    return total_brightness / len(pixels)


def get_average_saturation(image):
    """
    Calculate average saturation of image
    
    Args:
        image: PIL Image
        
    Returns:
        float: Average saturation (0.0-1.0)
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = list(image.getdata())
    total_saturation = 0
    
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        total_saturation += s
    
    return total_saturation / len(pixels)


def get_color_temperature(image):
    """
    Estimate color temperature (warm vs cool)
    
    Args:
        image: PIL Image
        
    Returns:
        str: 'warm', 'neutral', or 'cool'
        float: Temperature score (-1.0 to 1.0, negative=cool, positive=warm)
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = list(image.getdata())
    warm_score = 0
    
    for r, g, b in pixels:
        # Warm colors have more red/yellow, cool colors have more blue
        warm_score += (r - b) / 255
    
    avg_score = warm_score / len(pixels)
    
    if avg_score > 0.1:
        return 'warm', avg_score
    elif avg_score < -0.1:
        return 'cool', avg_score
    else:
        return 'neutral', avg_score


def get_shape_bounds_on_canvas(shape):
    """
    Get bounding box of shape in canvas coordinates
    
    Args:
        shape: Shape object
        
    Returns:
        tuple: (min_x, min_y, max_x, max_y) or None if no geometry
    """
    if 'geometry' not in shape.attrs:
        return None
    
    points = shape.attrs['geometry'].get('points', [])
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    return (min(xs), min(ys), max(xs), max(ys))


def get_shape_centroid(shape):
    """
    Get centroid of shape
    
    Args:
        shape: Shape object
        
    Returns:
        tuple: (center_x, center_y) or None if no geometry
    """
    if 'geometry' not in shape.attrs:
        return None
    
    points = shape.attrs['geometry'].get('points', [])
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def get_canvas_thirds_points(width=768, height=768):
    """
    Get rule of thirds intersection points
    
    Args:
        width: Canvas width
        height: Canvas height
        
    Returns:
        list: List of (x, y) tuples for the 4 intersection points
    """
    x1 = width / 3
    x2 = 2 * width / 3
    y1 = height / 3
    y2 = 2 * height / 3
    
    return [
        (x1, y1),  # Top-left third
        (x2, y1),  # Top-right third
        (x1, y2),  # Bottom-left third
        (x2, y2),  # Bottom-right third
    ]


def distance_to_nearest_thirds_point(x, y, width=768, height=768):
    """
    Calculate distance from point to nearest rule of thirds intersection
    
    Args:
        x, y: Point coordinates
        width, height: Canvas dimensions
        
    Returns:
        float: Distance to nearest intersection point
    """
    thirds_points = get_canvas_thirds_points(width, height)
    
    min_dist = float('inf')
    for tx, ty in thirds_points:
        dist = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
        min_dist = min(min_dist, dist)
    
    return min_dist