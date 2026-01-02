"""
Tkinter user interface for Shape Studio.
Split pane layout with command log (left) and canvas display (right).
"""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
from src.core.canvas import Canvas
from src.commands.parser import CommandParser
from src.commands.executor import CommandExecutor


class ShapeStudioUI:
    """Main UI for Shape Studio."""
    
    def __init__(self, root):
        """
        Initialize the UI.
        
        Args:
            root: tkinter root window
        """
        self.root = root
        self.root.title("Shape Studio")
        self.root.geometry("1400x800")
        
        # Initialize canvas and command system
        self.canvas_obj = Canvas(size=1024)
        self.parser = CommandParser()
        self.executor = CommandExecutor(self.canvas_obj)
        
        # Setup UI
        self._setup_ui()
        
        # Display initial canvas
        self._update_canvas_display()
    
    def _setup_ui(self):
        """Setup the UI layout."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Command log
        left_panel = ttk.Frame(main_container, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Command log label
        ttk.Label(left_panel, text="Command Log", font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        
        # Command log text widget with scrollbar
        log_frame = ttk.Frame(left_panel)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=30, width=40,
                                yscrollcommand=log_scrollbar.set,
                                font=('Courier', 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # Make log read-only
        self.log_text.config(state=tk.DISABLED)
        
        # Command entry
        entry_frame = ttk.Frame(left_panel)
        entry_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(entry_frame, text="Command:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.command_entry = ttk.Entry(entry_frame, font=('Courier', 10))
        self.command_entry.pack(fill=tk.X, pady=(5, 5))
        self.command_entry.bind('<Return>', self._on_command_enter)
        self.command_entry.focus()
        
        # Execute button
        self.execute_btn = ttk.Button(entry_frame, text="Execute", command=self._execute_command)
        self.execute_btn.pack(fill=tk.X)
        
        # Right panel - Canvas display
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas label
        ttk.Label(right_panel, text="Canvas (1024x1024)", font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        
        # Canvas display
        self.canvas_label = tk.Label(right_panel, bg='white')
        self.canvas_label.pack()
        
        # Welcome message
        self._log_message("Welcome to Shape Studio!", 'info')
        self._log_message("Type commands below or press Enter to execute.", 'info')
        self._log_message("Try: LINE l1 100,100 900,900", 'info')
        self._log_message("-" * 50, 'separator')
    
    def _log_message(self, message, msg_type='normal'):
        """
        Add a message to the command log.
        
        Args:
            message: Message text
            msg_type: 'normal', 'error', 'success', 'info', 'separator'
        """
        self.log_text.config(state=tk.NORMAL)
        
        # Apply different formatting based on message type
        if msg_type == 'error':
            self.log_text.insert(tk.END, f'❌ {message}\n', 'error')
            self.log_text.tag_config('error', foreground='red')
        elif msg_type == 'success':
            self.log_text.insert(tk.END, f'✓ {message}\n', 'success')
            self.log_text.tag_config('success', foreground='green')
        elif msg_type == 'info':
            self.log_text.insert(tk.END, f'ℹ {message}\n', 'info')
            self.log_text.tag_config('info', foreground='blue')
        elif msg_type == 'separator':
            self.log_text.insert(tk.END, f'{message}\n', 'separator')
            self.log_text.tag_config('separator', foreground='gray')
        else:
            self.log_text.insert(tk.END, f'{message}\n')
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _on_command_enter(self, event):
        """Handle Enter key press in command entry."""
        self._execute_command()
    
    def _execute_command(self):
        """Execute the command in the entry field."""
        command_text = self.command_entry.get().strip()
        
        if not command_text:
            return
        
        # Log the command
        self._log_message(f'> {command_text}')
        
        # Parse and execute
        parsed = self.parser.parse(command_text)
        result = self.executor.execute(parsed)
        
        # Log the result
        if result.startswith('Error') or 'error' in result.lower():
            self._log_message(result, 'error')
        else:
            self._log_message(result, 'success')
        
        # Update canvas display
        self._update_canvas_display()
        
        # Clear entry and add separator
        self.command_entry.delete(0, tk.END)
        self._log_message("-" * 50, 'separator')
    
    def _update_canvas_display(self):
        """Update the canvas display with current image."""
        # Convert PIL image to PhotoImage
        photo = ImageTk.PhotoImage(self.canvas_obj.get_image())
        
        # Update label
        self.canvas_label.config(image=photo)
        self.canvas_label.image = photo  # Keep a reference
    
    def run(self):
        """Start the UI event loop."""
        self.root.mainloop()


def main():
    """Main entry point for the UI."""
    root = tk.Tk()
    app = ShapeStudioUI(root)
    app.run()


if __name__ == '__main__':
    main()
