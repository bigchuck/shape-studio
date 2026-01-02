"""
Shape Studio UI Interface - Phase 3 Enhanced
Dual canvas system with command history recall
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk


class ShapeStudioUI:
    """Main UI for Shape Studio with WIP/Main canvas system"""
    
    def __init__(self, executor):
        self.executor = executor
        self.root = tk.Tk()
        self.root.title("Shape Studio - Command Line Drawing Tool")
        
        # Start in fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Allow Escape key to exit fullscreen
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        self.command_counter = 0  # Track command numbers
        
        # Command history for up/down arrow recall
        self.command_history = []
        self.history_index = -1
        
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
        self.command_input.bind('<Up>', self._history_up)
        self.command_input.bind('<Down>', self._history_down)
        
        execute_btn = tk.Button(input_frame, text="Execute", command=self._execute_command)
        execute_btn.pack(side=tk.LEFT)
        
        # Right panel - Canvas display with controls
        right_frame = tk.Frame(main_pane)
        
        # Canvas control bar
        control_frame = tk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Active canvas indicator
        self.canvas_indicator = tk.Label(
            control_frame, 
            text="Active: WIP", 
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='blue',
            padx=10,
            pady=5
        )
        self.canvas_indicator.pack(side=tk.LEFT, padx=10)
        
        # Switch canvas button
        self.switch_btn = tk.Button(
            control_frame,
            text="Switch to MAIN →",
            command=self._switch_canvas,
            font=('Arial', 10),
            bg='lightblue',
            width=15
        )
        self.switch_btn.pack(side=tk.LEFT, padx=5)
        
        # Spacer
        tk.Label(control_frame, text="  ").pack(side=tk.LEFT)
        
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
        
        # Canvas display with scrollbars
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
            text="Ready | Active: WIP | Use ↑↓ arrows for command history | ESC/F11 = fullscreen",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Focus on command input
        self.command_input.focus()
        
    def _history_up(self, event):
        """Navigate up in command history"""
        if not self.command_history:
            return
        
        # If at the bottom, go to most recent
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        # Otherwise, go one back (if not at the top)
        elif self.history_index > 0:
            self.history_index -= 1
        
        # Set the command input to the history entry
        if 0 <= self.history_index < len(self.command_history):
            self.command_input.delete(0, tk.END)
            self.command_input.insert(0, self.command_history[self.history_index])
        
        return "break"  # Prevent default behavior
        
    def _history_down(self, event):
        """Navigate down in command history"""
        if not self.command_history:
            return
        
        # If not at bottom, move forward
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_input.delete(0, tk.END)
            self.command_input.insert(0, self.command_history[self.history_index])
        # If at bottom or beyond, clear input and reset index
        else:
            self.history_index = -1
            self.command_input.delete(0, tk.END)
        
        return "break"  # Prevent default behavior
        
    def _switch_canvas(self):
        """Switch between WIP and MAIN canvas"""
        try:
            # Execute SWITCH command
            if self.executor.active_canvas_name == 'WIP':
                result = self.executor.execute('SWITCH MAIN')
            else:
                result = self.executor.execute('SWITCH WIP')
            
            # Update UI indicators
            self._update_canvas_indicators()
            self._update_canvas_display()
            
            # Log the switch
            self.command_counter += 1
            self._log_command(f"[{self.command_counter}] {result}")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            
    def _update_canvas_indicators(self):
        """Update the canvas indicator labels and button"""
        active = self.executor.active_canvas_name
        
        if active == 'WIP':
            self.canvas_indicator.config(
                text="Active: WIP",
                bg='blue'
            )
            self.switch_btn.config(
                text="Switch to MAIN →"
            )
            self.status_label.config(
                text=f"Active: WIP | Use ↑↓ arrows for command history | ESC/F11 = fullscreen"
            )
        else:  # MAIN
            self.canvas_indicator.config(
                text="Active: MAIN",
                bg='green'
            )
            self.switch_btn.config(
                text="← Switch to WIP"
            )
            self.status_label.config(
                text=f"Active: MAIN | Use ↑↓ arrows for command history | ESC/F11 = fullscreen"
            )
        
    def _toggle_rulers(self):
        """Toggle ruler visibility on active canvas"""
        state = self.executor.active_canvas.toggle_rulers()
        if state:
            self.ruler_btn.config(text="Rulers: ON", bg='lightgreen')
        else:
            self.ruler_btn.config(text="Rulers: OFF", bg='lightgray')
        self._update_canvas_display()
        
    def _toggle_grid(self):
        """Toggle grid visibility on active canvas"""
        state = self.executor.active_canvas.toggle_grid()
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
        
        # Add to command history (avoid duplicates of last command)
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        
        # Reset history index
        self.history_index = -1
            
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
            
            # Update canvas indicators if canvas was switched
            self._update_canvas_indicators()
            
            # Update display
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
        """Update the canvas display with current active canvas"""
        # Get display image from active canvas
        display_img = self.executor.active_canvas.get_display_image()
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(display_img)
        
        # Update canvas
        self.canvas_widget.delete("all")
        self.canvas_widget.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas_widget.config(scrollregion=(0, 0, display_img.width, display_img.height))
        
    def run(self):
        """Start the UI main loop"""
        self.root.mainloop()


def create_ui(executor):
    """Factory function to create and return the UI"""
    return ShapeStudioUI(executor)