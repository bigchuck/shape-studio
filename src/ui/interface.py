"""
Shape Studio UI Interface - Phase 4
Three-panel layout with help browser (fixed sash positioning)
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk


class ShapeStudioUI:
    """Main UI for Shape Studio with help browser"""
    
    def __init__(self, executor):
        self.executor = executor
        self.root = tk.Tk()
        self.root.title("Shape Studio - Command Line Drawing Tool")
        
        # Start in fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Keybindings
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        self.command_counter = 0
        self.command_history = []
        self.history_index = -1
        self.zoom_level = 1.0  # Default zoom level (100%)
        
        # Load help content BEFORE setting up UI
        self._load_help_content()
        self._setup_ui()
        self._update_canvas_display()

        # Give executor reference to root window for animation
        self.executor.ui_root = self.root
        self.executor.ui_instance = self
        
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)
        
    def _load_help_content(self):
        """Load help content from file"""
        try:
            with open('HELP.md', 'r') as f:
                self.help_content = f.read()
        except FileNotFoundError:
            self.help_content = """# SHAPE STUDIO - QUICK HELP

Help file (HELP.md) not found in project directory.

## BASIC COMMANDS
LINE <n> <x1>,<y1> <x2>,<y2>
POLY <n> <x1>,<y1> <x2>,<y2> <x3>,<y3> ...
MOVE <n> <dx>,<dy>
ROTATE <n> <angle>
SCALE <n> <factor>
RESIZE <n> <x_factor> [y_factor]

## GROUPS
GROUP <n> <shape1> <shape2> ...
UNGROUP <n>
EXTRACT <member> FROM <group>

## CANVAS
SWITCH WIP|MAIN
PROMOTE [COPY] <shape>
UNPROMOTE [COPY] <shape>
CLEAR <canvas> ALL
LIST [WIP|MAIN|STASH|STORE|GLOBAL]

## PERSISTENCE
SAVE_PROJECT <file>
LOAD_PROJECT <file>
STORE [GLOBAL] <shape>
LOAD <shape>

## UTILITIES
DELETE <shape> [CONFIRM]
INFO <shape>
STASH <shape>
UNSTASH [MOVE] <shape>
SAVE <file>.png

For full documentation, place HELP.md in the project root directory.
"""
        
    def _setup_ui(self):
        """Set up three-panel UI layout"""
        # Main container with three panels
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # === LEFT PANEL: Command Log ===
        left_frame = tk.Frame(self.main_pane, bg='lightgray')
        
        log_label = tk.Label(left_frame, text="Command Log", font=('Arial', 10, 'bold'))
        log_label.pack(pady=5)
        
        self.command_log = scrolledtext.ScrolledText(
            left_frame, width=50, height=30, font=('Consolas', 9), wrap=tk.WORD
        )
        self.command_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.command_log.config(state=tk.DISABLED)
        
        # Command input
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
        
        # === MIDDLE PANEL: Canvas ===
        middle_frame = tk.Frame(self.main_pane, bg='white')
        
        # Control bar
        control_frame = tk.Frame(middle_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.canvas_indicator = tk.Label(
            control_frame, text="Active: WIP", font=('Arial', 12, 'bold'),
            fg='white', bg='blue', padx=10, pady=5
        )
        self.canvas_indicator.pack(side=tk.LEFT, padx=10)
        
        self.switch_btn = tk.Button(
            control_frame, text="Switch to MAIN →", command=self._switch_canvas,
            font=('Arial', 10), bg='lightblue', width=15
        )
        self.switch_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="  ").pack(side=tk.LEFT)
        
        self.ruler_btn = tk.Button(
            control_frame, text="Rulers: ON", command=self._toggle_rulers,
            bg='lightgreen', width=12
        )
        self.ruler_btn.pack(side=tk.LEFT, padx=5)
        
        self.grid_btn = tk.Button(
            control_frame, text="Grid: ON", command=self._toggle_grid,
            bg='lightgreen', width=12
        )
        self.grid_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="  ").pack(side=tk.LEFT)

        self.zoom_label = tk.Label(
            control_frame, text="Zoom: 100%", font=('Arial', 9)
        )
        self.zoom_label.pack(side=tk.LEFT, padx=5)

        self.zoom_out_btn = tk.Button(
            control_frame, text="−", command=self._zoom_out,
            font=('Arial', 12, 'bold'), width=2
        )
        self.zoom_out_btn.pack(side=tk.LEFT, padx=2)

        self.zoom_in_btn = tk.Button(
            control_frame, text="+", command=self._zoom_in,
            font=('Arial', 12, 'bold'), width=2
        )
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)

        self.zoom_reset_btn = tk.Button(
            control_frame, text="100%", command=self._zoom_reset,
            font=('Arial', 9), width=5
        )
        self.zoom_reset_btn.pack(side=tk.LEFT, padx=2)

        # Canvas display
        canvas_frame = tk.Frame(middle_frame, bg='gray')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas_widget = tk.Canvas(
            canvas_frame, bg='white',
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )
        self.canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas_widget.yview)
        h_scrollbar.config(command=self.canvas_widget.xview)
        
        # === RIGHT PANEL: Help Browser ===
        right_frame = tk.Frame(self.main_pane, bg='lightblue')
        
        help_label = tk.Label(right_frame, text="Help", 
                             font=('Arial', 10, 'bold'))
        help_label.pack(pady=5)
        
        # Search box
        search_frame = tk.Frame(right_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="Search:", font=('Arial', 8)).pack(side=tk.LEFT)
        
        self.search_entry = tk.Entry(search_frame, font=('Arial', 8))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self._search_help)
        
        clear_search_btn = tk.Button(search_frame, text="Clear", 
                                     command=self._clear_search, width=5, font=('Arial', 8))
        clear_search_btn.pack(side=tk.LEFT)
        
        # Help text display
        self.help_text = scrolledtext.ScrolledText(
            right_frame, width=38, height=40, font=('Courier', 8),
            wrap=tk.WORD, bg='#f5f5f5'
        )
        self.help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add panels to main pane
        self.main_pane.add(left_frame, minsize=450, width=450)
        self.main_pane.add(middle_frame, minsize=400)
        self.main_pane.add(right_frame, minsize=300, width=300)
        
        # Status bar
        status_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame, 
            text="Ready | Active: WIP | ↑↓ for history | ESC/F11 = fullscreen",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Focus on command input
        self.command_input.focus()
        
        # Display help content
        self._display_help()
        
        # FIX: Set sash positions after window is rendered
        self.root.after(100, self._set_sash_positions)
        
    def _set_sash_positions(self):
        """Set the sash positions to enforce panel widths"""
        try:
            # Get screen width
            screen_width = self.root.winfo_width()
            
            # Set sash positions:
            # First sash at 450px (end of left panel)
            # Second sash at (screen_width - 300) (start of right panel)
            self.main_pane.sash_place(0, 450, 0)
            self.main_pane.sash_place(1, screen_width - 300, 0)
        except:
            # If it fails, try again in 100ms
            self.root.after(100, self._set_sash_positions)
        
    def _display_help(self):
        """Display help content in help panel"""
        self.help_text.config(state=tk.NORMAL)
        self.help_text.delete(1.0, tk.END)
        self.help_text.insert(tk.END, self.help_content)
        self.help_text.config(state=tk.DISABLED)
        
    def _search_help(self, event=None):
        """Search and highlight in help content"""
        search_term = self.search_entry.get().upper()
        
        self.help_text.config(state=tk.NORMAL)
        
        # Remove previous highlights
        self.help_text.tag_remove('highlight', 1.0, tk.END)
        
        if search_term:
            # Search and highlight
            start_pos = '1.0'
            while True:
                start_pos = self.help_text.search(search_term, start_pos, 
                                                  nocase=True, stopindex=tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_term)}c"
                self.help_text.tag_add('highlight', start_pos, end_pos)
                start_pos = end_pos
            
            # Configure highlight tag
            self.help_text.tag_config('highlight', background='yellow', 
                                     foreground='black')
            
            # Scroll to first match
            first_match = self.help_text.search(search_term, 1.0, nocase=True)
            if first_match:
                self.help_text.see(first_match)
        
        self.help_text.config(state=tk.DISABLED)
        
    def _clear_search(self):
        """Clear search box and highlights"""
        self.search_entry.delete(0, tk.END)
        self.help_text.config(state=tk.NORMAL)
        self.help_text.tag_remove('highlight', 1.0, tk.END)
        self.help_text.config(state=tk.DISABLED)
        
    def _history_up(self, event):
        """Navigate up in command history"""
        if not self.command_history:
            return
        
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        
        if 0 <= self.history_index < len(self.command_history):
            self.command_input.delete(0, tk.END)
            self.command_input.insert(0, self.command_history[self.history_index])
        
        return "break"
        
    def _history_down(self, event):
        """Navigate down in command history"""
        if not self.command_history:
            return
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_input.delete(0, tk.END)
            self.command_input.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = -1
            self.command_input.delete(0, tk.END)
        
        return "break"
        
    def _switch_canvas(self):
        """Switch between WIP and MAIN canvas"""
        try:
            if self.executor.active_canvas_name == 'WIP':
                result = self.executor.execute('SWITCH MAIN')
            else:
                result = self.executor.execute('SWITCH WIP')
            
            self._update_canvas_indicators()
            self._update_canvas_display()
            
            self.command_counter += 1
            self._log_command(f"[{self.command_counter}] {result}")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            
    def _update_canvas_indicators(self):
        """Update canvas indicator labels and button"""
        active = self.executor.active_canvas_name
        
        if active == 'WIP':
            self.canvas_indicator.config(text="Active: WIP", bg='blue')
            self.switch_btn.config(text="Switch to MAIN →")
            self.status_label.config(
                text=f"Active: WIP | ↑↓ for history | ESC/F11 = fullscreen"
            )
        else:
            self.canvas_indicator.config(text="Active: MAIN", bg='green')
            self.switch_btn.config(text="← Switch to WIP")
            self.status_label.config(
                text=f"Active: MAIN | ↑↓ for history | ESC/F11 = fullscreen"
            )
        
    def _toggle_rulers(self):
        """Toggle ruler visibility"""
        state = self.executor.active_canvas.toggle_rulers()
        if state:
            self.ruler_btn.config(text="Rulers: ON", bg='lightgreen')
        else:
            self.ruler_btn.config(text="Rulers: OFF", bg='lightgray')
        self._update_canvas_display()
        
    def _toggle_grid(self):
        """Toggle grid visibility"""
        state = self.executor.active_canvas.toggle_grid()
        if state:
            self.grid_btn.config(text="Grid: ON", bg='lightgreen')
        else:
            self.grid_btn.config(text="Grid: OFF", bg='lightgray')
        self._update_canvas_display()
        
    def _execute_command(self, event=None):
        """Execute the command from input field"""
        command = self.command_input.get().strip()
        if not command:
            return
        
        # Add to history
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        
        self.history_index = -1
        self.command_counter += 1
        
        # Log command
        self._log_command(f"[{self.command_counter}] {command}")
        
        # Clear input
        self.command_input.delete(0, tk.END)
        
        # Execute
        try:
            result = self.executor.execute(command)
            if result:
                self._log_output(f"    → {result}")
            
            self._update_canvas_indicators()
            self._update_canvas_display()
            
            self.status_label.config(text=f"Command executed: {command}")
        except Exception as e:
            error_msg = f"    ✗ Error: {str(e)}"
            self._log_output(error_msg)
            self.status_label.config(text=f"Error: {str(e)}")
            
    def _log_command(self, text):
        """Add command to log"""
        self.command_log.config(state=tk.NORMAL)
        self.command_log.insert(tk.END, text + "\n")
        self.command_log.config(state=tk.DISABLED)
        self.command_log.see(tk.END)
        
    def _log_output(self, text):
        """Add output to log"""
        self.command_log.config(state=tk.NORMAL)
        self.command_log.insert(tk.END, text + "\n")
        self.command_log.config(state=tk.DISABLED)
        self.command_log.see(tk.END)
        
    def _update_canvas_display(self):
        """Update canvas display"""
        display_img = self.executor.active_canvas.get_display_image()
        # Apply zoom if not 100%
        if self.zoom_level != 1.0:
            new_width = int(display_img.width * self.zoom_level)
            new_height = int(display_img.height * self.zoom_level)
            display_img = display_img.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )
        self.photo = ImageTk.PhotoImage(display_img)
        self.canvas_widget.delete("all")
        self.canvas_widget.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas_widget.config(scrollregion=(0, 0, display_img.width, display_img.height))
        
    def _zoom_in(self):
        """Increase zoom level"""
        if self.zoom_level < 3.0:  # Max 300%
            self.zoom_level = min(3.0, self.zoom_level + 0.25)
            self._update_zoom_display()

    def _zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_level > 0.25:  # Min 25%
            self.zoom_level = max(0.25, self.zoom_level - 0.25)
            self._update_zoom_display()

    def _zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self._update_zoom_display()

    def _update_zoom_display(self):
        """Update zoom label and redraw canvas"""
        zoom_pct = int(self.zoom_level * 100)
        self.zoom_label.config(text=f"Zoom: {zoom_pct}%")
        self._update_canvas_display()

    def run(self):
        """Start the UI main loop"""
        self.root.mainloop()


def create_ui(executor):
    """Factory function to create and return the UI"""
    return ShapeStudioUI(executor)