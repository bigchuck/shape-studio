"""
Canvas management for Shape Studio - Phase 5
Handles the 768x768 PIL image with optional ruler overlay, grid, and z-ordering
"""
from PIL import Image, ImageDraw, ImageFont
from src.config import config


class Canvas:
    """Manages the drawing canvas and shape collection"""
    
    def __init__(self, size=768):
        self.size = size
        self.width = config.canvas.width
        self.height = config.canvas.height
        self.image = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.image)
        self.shapes = []
        
        # Display options
        self.show_rulers = True
        self.show_grid = True
        
        # Draw initial grid
        if self.show_grid:
            self._draw_grid_on_canvas(self.draw)
        
    def add_shape(self, shape):
        """Add a shape to the canvas"""
        self.shapes.append(shape)
        shape.draw(self.draw)
        
    def remove_shape(self, shape):
        """Remove a shape from the canvas"""
        if shape in self.shapes:
            self.shapes.remove(shape)
            
    def sync_shapes(self, shapes_dict):
        """Sync canvas's shape list with a dictionary of shapes
        
        This rebuilds the canvas to match the executor's registry.
        Use this after deleting/stashing shapes.
        """
        # Replace our shapes list with values from the dict
        self.shapes = list(shapes_dict.values())
        # Redraw everything
        self.redraw()
        
    def clear(self):
        """Clear all shapes and reset canvas"""
        self.shapes = []
        self.image = Image.new('RGB', (self.width, self.height), 'white')
        self.draw = ImageDraw.Draw(self.image)
        
        # Redraw grid if enabled
        if self.show_grid:
            self._draw_grid_on_canvas(self.draw)
        
    def get_shapes(self):
        """Return list of all shapes"""
        return self.shapes
        
    def redraw(self):
        """Redraw all shapes on a fresh canvas, respecting z-order"""
        self.image = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.image)
        
        # Draw grid first (if enabled) so shapes appear on top
        if self.show_grid:
            self._draw_grid_on_canvas(self.draw)
        
        # Sort shapes by z_coord (lower z_coord drawn first = further back)
        sorted_shapes = sorted(self.shapes, key=lambda s: s.attrs['style']['z_coord'])
        
        for shape in sorted_shapes:
            shape.draw(self.draw)
            
    def _draw_grid_on_canvas(self, draw):
        """Draw grid lines on the main canvas (every 128px)"""
        grid_color = (220, 220, 220)  # Light gray
        grid_interval = 128
        
        # Vertical lines
        for x in range(grid_interval, self.size, grid_interval):
            draw.line([(x, 0), (x, self.size)], fill=grid_color, width=1)
        
        # Horizontal lines
        for y in range(grid_interval, self.size, grid_interval):
            draw.line([(0, y), (self.size, y)], fill=grid_color, width=1)
            
    def save(self, filename):
        """Save the canvas without rulers to PNG file"""
        # Convert RGBA to RGB for saving
        if self.image.mode == 'RGBA':
            rgb_image = Image.new('RGB', self.image.size, (255, 255, 255))
            rgb_image.paste(self.image, mask=self.image.split()[3])  # Use alpha as mask
            rgb_image.save(filename, 'PNG')
        else:
            self.image.save(filename, 'PNG')
        
    def toggle_rulers(self):
        """Toggle ruler visibility"""
        self.show_rulers = not self.show_rulers
        return self.show_rulers
        
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid
        self.redraw()  # Redraw to update grid visibility
        return self.show_grid
        
    def get_display_image(self):
        """Get a copy of the image with optional rulers for display"""
        if self.show_rulers:
            # Create larger image with margin for rulers
            margin = 30
            display_size = self.size + 2 * margin
            display_img = Image.new('RGB', (display_size, display_size), 'white')
            
            # Paste the canvas in the center
            display_img.paste(self.image, (margin, margin))
            
            # Draw rulers on the margin
            self._draw_rulers(display_img, margin)
            
            return display_img
        else:
            # Return canvas without rulers
            return self.image.copy()
        
    def _draw_rulers(self, img, margin):
        """Draw ruler marks with labels OUTSIDE the canvas area"""
        draw = ImageDraw.Draw(img)
        
        # Try to use a small font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 9)
        except:
            font = ImageFont.load_default()
        
        ruler_color = (100, 100, 100)
        tick_length_major = 8
        tick_length_minor = 4
        
        # Major tick every 128 pixels, minor every 64
        major_interval = 128
        minor_interval = 64
        
        # Canvas starts at (margin, margin) in the display image
        canvas_start = margin
        canvas_end = margin + self.size
        
        # Draw top ruler
        for x in range(0, self.size + 1, minor_interval):
            canvas_x = canvas_start + x
            if x % major_interval == 0:
                # Major tick - extends into margin
                draw.line([(canvas_x, canvas_start - tick_length_major), 
                          (canvas_x, canvas_start)], fill=ruler_color, width=1)
                if x < self.size:  # Don't draw number at right edge
                    # Draw number above the tick
                    text = str(x)
                    # Center the text on the tick mark
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    draw.text((canvas_x - text_width // 2, canvas_start - tick_length_major - 12), 
                             text, fill=ruler_color, font=font)
            else:
                # Minor tick
                draw.line([(canvas_x, canvas_start - tick_length_minor), 
                          (canvas_x, canvas_start)], fill=ruler_color, width=1)
        
        # Draw left ruler
        for y in range(0, self.size + 1, minor_interval):
            canvas_y = canvas_start + y
            if y % major_interval == 0:
                # Major tick - extends into margin
                draw.line([(canvas_start - tick_length_major, canvas_y), 
                          (canvas_start, canvas_y)], fill=ruler_color, width=1)
                if y < self.size:  # Don't draw number at bottom edge
                    # Draw number to the left of the tick
                    text = str(y)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    draw.text((canvas_start - tick_length_major - text_width - 4, 
                              canvas_y - text_height // 2), 
                             text, fill=ruler_color, font=font)
            else:
                # Minor tick
                draw.line([(canvas_start - tick_length_minor, canvas_y), 
                          (canvas_start, canvas_y)], fill=ruler_color, width=1)
        
        # Draw right ruler (just ticks, no numbers)
        for y in range(0, self.size + 1, minor_interval):
            canvas_y = canvas_start + y
            if y % major_interval == 0:
                draw.line([(canvas_end, canvas_y), 
                          (canvas_end + tick_length_major, canvas_y)], fill=ruler_color, width=1)
            else:
                draw.line([(canvas_end, canvas_y), 
                          (canvas_end + tick_length_minor, canvas_y)], fill=ruler_color, width=1)
        
        # Draw bottom ruler (just ticks, no numbers)
        for x in range(0, self.size + 1, minor_interval):
            canvas_x = canvas_start + x
            if x % major_interval == 0:
                draw.line([(canvas_x, canvas_end), 
                          (canvas_x, canvas_end + tick_length_major)], fill=ruler_color, width=1)
            else:
                draw.line([(canvas_x, canvas_end), 
                          (canvas_x, canvas_end + tick_length_minor)], fill=ruler_color, width=1)
        
        # Draw corner frame to box in the canvas
        draw.rectangle([canvas_start, canvas_start, canvas_end, canvas_end], 
                      outline=ruler_color, width=1)