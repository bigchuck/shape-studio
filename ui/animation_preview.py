"""
Animation Preview Window for Shape Studio
Displays procedural generation evolution with playback controls
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw
import copy
from src.config import config


class AnimationPreview(tk.Toplevel):
    """Preview window for animating procedural generation iterations"""
    
    def __init__(self, parent, snapshots, base_name, fps, loop, executor, ui_instance=None):
        """
        Initialize animation preview window
        
        Args:
            parent: Parent Tk window
            snapshots: List of Polygon snapshot objects (iter_0, iter_1, ...)
            base_name: Base shape name (e.g., "demo1")
            fps: Frames per second (1-10)
            loop: Whether to loop continuously
            executor: CommandExecutor instance (for promotion)
            ui_instance: ShapeStudioUI instance (for display refresh)
        """
        super().__init__(parent)
        
        self.snapshots = snapshots
        self.base_name = base_name
        self.executor = executor
        self.ui_instance = ui_instance 
        self.current_frame = 0
        self.playing = False
        self.fps = fps if fps is not None else config.animation.default_fps
        self.loop = loop
        self.timer_id = None
        
        # Calculate bounds from all snapshots
        self.bounds = self._calculate_bounds()
        self.scale, self.offset = self._calculate_scale_and_offset()
        
        # Setup window
        self.title(f"Dynamic Polygon Evolution: {base_name}")
        self.resizable(False, False)
        
        # Setup UI
        self._setup_ui()
        
        # Draw initial frame
        self._draw_current_frame()
        
        # Bind window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _calculate_bounds(self):
        """Calculate bounding box that encompasses all iterations"""
        all_points = []
        
        for snapshot in self.snapshots:
            points = snapshot.attrs['geometry']['points']
            all_points.extend(points)
        
        if not all_points:
            return (0, 0, 768, 768)
        
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        # Add 10% padding
        width = x_max - x_min
        height = y_max - y_min
        padding_x = width * 0.1
        padding_y = height * 0.1
        
        return (
            x_min - padding_x,
            y_min - padding_y,
            x_max + padding_x,
            y_max + padding_y
        )
    
    def _calculate_scale_and_offset(self):
        """Calculate scale factor and offset to fit bounds in 512x512 canvas"""
        x1, y1, x2, y2 = self.bounds
        width = x2 - x1
        height = y2 - y1
        
        max_dim = max(width, height)
        
        preview_size = config.animation.preview_size

        # Scale to fit in 512x512
        if max_dim > preview_size:
            scale = preview_size / max_dim
        else:
            scale = 1.0  # Don't upscale if smaller
        
        # Calculate offset to center in canvas
        scaled_width = width * scale
        scaled_height = height * scale
        offset_x = (preview_size - scaled_width) / 2 - x1 * scale
        offset_y = (preview_size - scaled_height) / 2 - y1 * scale
        
        return scale, (offset_x, offset_y)
    
    def _setup_ui(self):
        """Setup the UI components"""
        # Main container
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas frame
        canvas_frame = tk.Frame(main_frame, bg='lightgray', relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(pady=(0, 10))
        
        # Create PIL canvas for drawing
        self.canvas_size = preview_size
        self.canvas_image = Image.new('RGB', (self.canvas_size, self.canvas_size), 'white')
        self.canvas_draw = ImageDraw.Draw(self.canvas_image)
        
        # Tkinter canvas for display
        self.canvas = tk.Canvas(
            canvas_frame, 
            width=self.canvas_size, 
            height=self.canvas_size,
            bg='white',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Info frame
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.iteration_label = tk.Label(
            info_frame,
            text=f"Iteration: 0 / {len(self.snapshots) - 1}",
            font=('Arial', 10)
        )
        self.iteration_label.pack()
        
        # Controls frame
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Playback controls
        playback_frame = tk.Frame(controls_frame)
        playback_frame.pack(side=tk.LEFT)
        
        self.play_button = tk.Button(
            playback_frame,
            text="▶️ Play",
            command=self._toggle_play,
            width=8
        )
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = tk.Button(
            playback_frame,
            text="⏹️ Stop",
            command=self._on_stop,
            width=8,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Step controls
        step_frame = tk.Frame(controls_frame)
        step_frame.pack(side=tk.LEFT, padx=10)
        
        self.prev_button = tk.Button(
            step_frame,
            text="←",
            command=self._step_backward,
            width=3
        )
        self.prev_button.pack(side=tk.LEFT, padx=2)
        
        self.next_button = tk.Button(
            step_frame,
            text="→",
            command=self._step_forward,
            width=3
        )
        self.next_button.pack(side=tk.LEFT, padx=2)
        
        # Action buttons
        action_frame = tk.Frame(controls_frame)
        action_frame.pack(side=tk.RIGHT)
        
        self.promote_button = tk.Button(
            action_frame,
            text="PROMOTE",
            command=self._on_promote,
            bg='lightgreen',
            width=10
        )
        self.promote_button.pack(side=tk.LEFT, padx=2)
        
        self.close_button = tk.Button(
            action_frame,
            text="CLOSE",
            command=self._on_close,
            width=10
        )
        self.close_button.pack(side=tk.LEFT, padx=2)
        
        # FPS slider frame
        fps_frame = tk.Frame(main_frame)
        fps_frame.pack(fill=tk.X)
        
        tk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.fps_var = tk.IntVar(value=self.fps)
        self.fps_slider = tk.Scale(
            fps_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.fps_var,
            command=self._on_fps_change,
            showvalue=True
        )
        self.fps_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _draw_current_frame(self):
        """Draw the current iteration frame"""
        # Clear canvas
        self.canvas_image = Image.new('RGB', (self.canvas_size, self.canvas_size), 'white')
        self.canvas_draw = ImageDraw.Draw(self.canvas_image)
        
        # Get current snapshot
        snapshot = self.snapshots[self.current_frame]
        
        # Transform points
        points = snapshot.attrs['geometry']['points']
        transformed_points = self._transform_points(points)
        
        # Get style
        style = snapshot.attrs['style']
        color = style.get('color', 'black')
        width = style.get('width', 2)
        fill_color = style.get('fill')
        
        # Draw polygon
        self.canvas_draw.polygon(
            transformed_points,
            outline=color,
            fill=fill_color,
            width=width
        )
        
        # Update canvas display
        from PIL import ImageTk
        self.photo = ImageTk.PhotoImage(self.canvas_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Update iteration label
        self.iteration_label.config(
            text=f"Iteration: {self.current_frame} / {len(self.snapshots) - 1}"
        )
    
    def _transform_points(self, points):
        """Transform points to canvas coordinates with scaling and offset"""
        offset_x, offset_y = self.offset
        transformed = []
        
        for x, y in points:
            new_x = x * self.scale + offset_x
            new_y = y * self.scale + offset_y
            transformed.append((new_x, new_y))
        
        return transformed
    
    def _toggle_play(self):
        """Toggle play/pause"""
        if self.playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """Start playback"""
        self.playing = True
        self.play_button.config(text="⏸️ Pause")
        self.stop_button.config(state=tk.NORMAL)
        self.promote_button.config(state=tk.DISABLED)
        self._advance_frame()
    
    def _pause(self):
        """Pause playback"""
        self.playing = False
        self.play_button.config(text="▶️ Play")
        self.promote_button.config(state=tk.NORMAL)
        
        # Cancel timer
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
    
    def _on_stop(self):
        """Stop playback and reset to frame 0"""
        self._pause()
        self.current_frame = 0
        self._draw_current_frame()
        self.stop_button.config(state=tk.DISABLED)
    
    def _advance_frame(self):
        """Advance to next frame and schedule next update"""
        if not self.playing:
            return
        
        self.current_frame += 1
        
        # Check if reached end
        if self.current_frame >= len(self.snapshots):
            if self.loop:
                self.current_frame = 0
            else:
                self.current_frame = len(self.snapshots) - 1
                self._pause()
                return
        
        self._draw_current_frame()
        
        # Schedule next frame
        delay_ms = int(1000 / self.fps_var.get())
        self.timer_id = self.after(delay_ms, self._advance_frame)
    
    def _step_forward(self):
        """Step forward one frame"""
        if self.playing:
            return
        
        if self.current_frame < len(self.snapshots) - 1:
            self.current_frame += 1
            self._draw_current_frame()
    
    def _step_backward(self):
        """Step backward one frame"""
        if self.playing:
            return
        
        if self.current_frame > 0:
            self.current_frame -= 1
            self._draw_current_frame()
    
    def _on_fps_change(self, value):
        """Handle FPS slider change"""
        self.fps = int(value)
        # If playing, the new FPS will take effect on next frame
    
    def _on_promote(self):
        """Promote current iteration to WIP, replacing all snapshots"""
        if self.playing:
            messagebox.showwarning(
                "Cannot Promote",
                "Please pause playback before promoting."
            )
            return
        
        # Confirmation dialog
        current_snapshot = self.snapshots[self.current_frame]
        response = messagebox.askyesno(
            "Confirm Promotion",
            f"Promote {current_snapshot.name} to WIP as '{self.base_name}'?\n\n"
            f"This will:\n"
            f"• Delete all iteration snapshots from WIP\n"
            f"• Replace with geometry from iteration {self.current_frame}\n"
            f"• Close this preview window"
        )
        
        if not response:
            return
        
        # Import shape classes
        from src.core.shape import Polygon
        
        # 1. Create new shape with base name from current snapshot's geometry
        current_geom = current_snapshot.attrs['geometry']
        current_style = current_snapshot.attrs['style']
        
        new_shape = Polygon(
            self.base_name,
            copy.deepcopy(current_geom['points'])
        )
        
        # Preserve styles
        new_shape.attrs['style']['color'] = current_style.get('color', 'black')
        new_shape.attrs['style']['width'] = current_style.get('width', 2)
        new_shape.attrs['style']['fill'] = current_style.get('fill')
        new_shape.attrs['style']['transparency'] = current_style.get('transparency', 1.0)
        new_shape.attrs['style']['z_coord'] = current_style.get('z_coord', 0)
        
        new_shape.add_history('PROMOTE', f'Promoted from {current_snapshot.name} via animation')
        
        # 2. Delete ALL snapshots from WIP
        shapes_to_delete = []
        for snapshot in self.snapshots:
            if snapshot.name in self.executor.wip_shapes:
                shapes_to_delete.append(snapshot.name)
        
        # Also delete the original base shape if it exists
        if self.base_name in self.executor.wip_shapes:
            shapes_to_delete.append(self.base_name)
        
        for name in shapes_to_delete:
            del self.executor.wip_shapes[name]
        
        # 3. Add the promoted shape
        self.executor.wip_shapes[self.base_name] = new_shape
        
        # 4. Sync and redraw WIP canvas
        self.executor.wip_canvas.sync_shapes(self.executor.wip_shapes)
        
        # Refresh the UI display
        if self.ui_instance:
            self.ui_instance._update_canvas_display()

        # 5. Show confirmation message
        messagebox.showinfo(
            "Promotion Complete",
            f"Promoted iteration {self.current_frame} to WIP as '{self.base_name}'.\n"
            f"Deleted {len(shapes_to_delete)} snapshots from WIP."
        )
        
        # 6. Close preview window
        self.destroy()
    
    def _on_close(self):
        """Close the window without promoting"""
        # Stop playback
        if self.playing:
            self._pause()
        
        # Destroy window (leaves snapshots on WIP)
        self.destroy()