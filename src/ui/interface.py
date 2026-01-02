"""
Shape Studio UI Interface with Fullscreen Support and Toggle Controls
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk


class ShapeStudioUI:
    """Main UI for Shape Studio with fullscreen capability"""
    
    def __init__(self, canvas, executor):
        self.canvas = canvas
        self.executor = executor
        self.root = tk.Tk()
        self.root.title("Shape Studio - Command Line Drawing Tool")
        
        # Start in fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Allow Escape key to exit fullscreen
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        self.command_counter = 0  # Track command numbers
        self._setup_ui()
        self._update_canvas_display()
        
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode on/off"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)
        
    def _setup_ui(self):
        """Set up the UI layout"""
        # Main container with two panels
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Command log and input (450px wide)
        left_frame = tk.Frame(main_pane, width=450)
        left_frame.pack_propagate(False)
        
        # Command log label
        log_label = tk.Label(left_frame, text="Command Log", font=('Arial', 10, 'bold'))
        log_label.pack(pady=5)
        
        # Command log (scrolled text)
        self.command_log = scrolledtext.ScrolledText(
            left_frame, 
            width=50, 
            height=30,
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.command_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.command_log.config(state=tk.DISABLED)
        
        # Command input area
        input_frame = tk.Frame(left_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        input_label = tk.Label(input_frame, text="Command:")
        input_label.pack(side=tk.LEFT)
        
        self.command_input = tk.Entry(input_frame, font=('Consolas', 10))
        self.command_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.command_input.bind('<Return>', self._execute_command)
        
        execute_btn = tk.Button(input_frame, text="Execute", command=self._execute_command)
        execute_btn.pack(side=tk.LEFT)
        
        # Right panel - Canvas display with controls
        right_frame = tk.Frame(main_pane)
        
        # Canvas control bar
        control_frame = tk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        canvas_label = tk.Label(control_frame, text="Canvas (768x768)", font=('Arial', 10, 'bold'))
        canvas_label.pack(side=tk.LEFT, padx=10)
        
        # Toggle buttons
        self.ruler_btn = tk.Button(
            control_frame, 
            text="Rulers: ON", 
            command=self._toggle_rulers,
            bg='lightgreen',
            width=12
        )
        self.ruler_btn.pack(side=tk.LEFT, padx=5)
        
        self.grid_btn = tk.Button(
            control_frame, 
            text="Grid: ON", 
            command=self._toggle_grid,
            bg='lightgreen',
            width=12
        )
        self.grid_btn.pack(side=tk.LEFT, padx=5)
        
        # Canvas display with scrollbars (in case fullscreen isn't enough)
        canvas_frame = tk.Frame(right_frame, bg='gray')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Canvas widget
        self.canvas_widget = tk.Canvas(
            canvas_frame,
            bg='white',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        self.canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas_widget.yview)
        h_scrollbar.config(command=self.canvas_widget.xview)
        
        # Add panels to main pane
        main_pane.add(left_frame)
        main_pane.add(right_frame)
        
        # Status bar at bottom
        status_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame, 
            text="Ready | Press ESC or F11 to toggle fullscreen",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Focus on command input
        self.command_input.focus()
        
    def _toggle_rulers(self):
        """Toggle ruler visibility"""
        state = self.canvas.toggle_rulers()
        if state:
            self.ruler_btn.config(text="Rulers: ON", bg='lightgreen')
        else:
            self.ruler_btn.config(text="Rulers: OFF", bg='lightgray')
        self._update_canvas_display()
        
    def _toggle_grid(self):
        """Toggle grid visibility"""
        state = self.canvas.toggle_grid()
        if state:
            self.grid_btn.config(text="Grid: ON", bg='lightgreen')
        else:
            self.grid_btn.config(text="Grid: OFF", bg='lightgray')
        self._update_canvas_display()
        
    def _execute_command(self, event=None):
        """Execute the command from the input field"""
        command = self.command_input.get().strip()
        if not command:
            return
            
        # Increment command counter
        self.command_counter += 1
        
        # Log the command with number
        self._log_command(f"[{self.command_counter}] {command}")
        
        # Clear input
        self.command_input.delete(0, tk.END)
        
        # Execute command
        try:
            result = self.executor.execute(command)
            if result:
                self._log_output(f"    → {result}")
            self._update_canvas_display()
            self.status_label.config(text=f"Command executed: {command}")
        except Exception as e:
            error_msg = f"    ✗ Error: {str(e)}"
            self._log_output(error_msg)
            self.status_label.config(text=f"Error: {str(e)}")
            
    def _log_command(self, text):
        """Add command to the log"""
        self.command_log.config(state=tk.NORMAL)
        self.command_log.insert(tk.END, text + "\n")
        self.command_log.config(state=tk.DISABLED)
        self.command_log.see(tk.END)
        
    def _log_output(self, text):
        """Add output/result to the log"""
        self.command_log.config(state=tk.NORMAL)
        self.command_log.insert(tk.END, text + "\n")
        self.command_log.config(state=tk.DISABLED)
        self.command_log.see(tk.END)
        
    def _update_canvas_display(self):
        """Update the canvas display with current image"""
        # Get display image with rulers
        display_img = self.canvas.get_display_image()
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(display_img)
        
        # Update canvas
        self.canvas_widget.delete("all")
        self.canvas_widget.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas_widget.config(scrollregion=(0, 0, display_img.width, display_img.height))
        
    def run(self):
        """Start the UI main loop"""
        self.root.mainloop()


def create_ui(canvas, executor):
    """Factory function to create and return the UI"""
    return ShapeStudioUI(canvas, executor)