"""
Shape Studio UI Interface - Phase 4
Three-panel layout with help browser (fixed sash positioning)
"""
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
from src.config import config
from src.commands.parser import MissingParamsError

class ShapeStudioUI:
    """Main UI for Shape Studio with help browser"""
    
    def __init__(self, executor):
        self.executor = executor
        self.root = tk.Tk()
        self.root.title(config.ui.window_title)
        
        # Start in fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Keybindings
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        self.command_counter = 0
        self.command_history = []
        self.history_index = -1
        self.zoom_level = 1.0  # Default zoom level (100%)
        self.replay_dialog = None
        self._load_command_history()
        
        self._setup_ui()
        self._update_canvas_display()

        # Give executor reference to root window for animation
        self.executor.ui_root = self.root
        self.executor.ui_instance = self
        
    def _load_command_history(self):
        """Load command history from disk on startup"""
        history_file = getattr(config.ui, 'history_file', 'history.json')
        try:
            with open(history_file, 'r') as f:
                self.command_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.command_history = []

    def _save_command_history(self):
        """Persist command history to disk"""
        history_file = getattr(config.ui, 'history_file', 'history.json')
        with open(history_file, 'w') as f:
            json.dump(self.command_history, f, indent=2)

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)
        
    def _setup_ui(self):
        """Set up three-panel UI layout"""
        # Main container with three panels
        # Bottom input bar spanning full width
        input_bar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        input_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.input_label = tk.Label(input_bar, text="Command:")
        self.input_label.pack(side=tk.LEFT, padx=(5, 2))

        self.command_input = tk.Entry(input_bar, font=('Consolas', 10))
        self.command_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.command_input.bind('<Return>', self._execute_command)
        self.command_input.bind('<Up>', self._history_up)
        self.command_input.bind('<Down>', self._history_down)

        execute_btn = tk.Button(input_bar, text="Execute", command=self._execute_command)
        execute_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # === LEFT PANEL: Command Log ===
        left_frame = tk.Frame(self.main_pane, bg='lightgray')
        
        log_label = tk.Label(left_frame, text="Command Log", font=('Arial', 10, 'bold'))
        log_label.pack(pady=5)
        
        self.command_log = scrolledtext.ScrolledText(
            left_frame, width=50, height=30, font=('Consolas', 11), wrap=tk.WORD
        )
        self.command_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.command_log.config(state=tk.DISABLED)
        

        
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
            control_frame, text="Switch to MAIN >", command=self._switch_canvas,
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
            control_frame, text="-", command=self._zoom_out,
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
        
        # Add panels to main pane
        self.main_pane.add(left_frame, minsize=700, width=700)
        self.main_pane.add(middle_frame, minsize=800)
        
        # Status bar
        status_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame, 
            text="Ready | Active: WIP | up/dn for history | ESC/F11 = fullscreen",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Focus on command input
        self.command_input.focus()
                
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
            self.main_pane.sash_place(0, 500, 0)
        except:
            # If it fails, try again in 100ms
            self.root.after(100, self._set_sash_positions)
        
    def _history_up(self, event):
        """Navigate up in command history"""
        if not self.command_history:
            return "break"
        
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        # At index 0: clamp, do not roll
        
        self.command_input.delete(0, tk.END)
        self.command_input.insert(0, self.command_history[self.history_index])
        return "break"
        
    def _history_down(self, event):
        """Navigate down in command history"""
        if not self.command_history or self.history_index == -1:
            return "break"
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_input.delete(0, tk.END)
            self.command_input.insert(0, self.command_history[self.history_index])
        # At bottom: clamp, do not clear or roll
        
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
        
        ww = self.executor.workwith
        ww_text = f" | WW: {ww}" if ww else ""

        if active == 'WIP':
            self.canvas_indicator.config(text="Active: WIP", bg='blue')
            self.switch_btn.config(text="Switch to MAIN >")
            self.status_label.config(
                text=f"Active: WIP{ww_text} | up/dn for history | ESC/F11 = fullscreen"
            )
        else:
            self.canvas_indicator.config(text="Active: MAIN", bg='green')
            self.switch_btn.config(text="< Switch to WIP")
            self.status_label.config(
                text=f"Active: MAIN{ww_text} | up/dn for history | ESC/F11 = fullscreen"
            )

    def _update_replay_prompt(self):
        """Update the command label to reflect replay mode state."""
        state = self.executor.replay_state
        if state is not None:
            idx   = state['index'] + 1   # next to execute, 1-based
            total = state['total']
            self.input_label.config(
                text=f"[REPLAY {idx}/{total}]",
                fg='white', bg='darkred'
            )
        else:
            self.input_label.config(
                text="Command:", fg='black', bg=self.root.cget('bg')
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
            history_max = getattr(config.ui, 'history_max', 50)
            if len(self.command_history) > history_max:
                self.command_history = self.command_history[-history_max:]
            self._save_command_history()

        # If we executed from mid-history, position to next entry forward.
        # Otherwise reset to bottom.
        if self.history_index != -1 and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
        else:
            self.history_index = -1
        self.command_counter += 1
        
        # Log command
        self._log_command(f"[{self.command_counter}] {command}")
        
        # Clear input
        self.command_input.delete(0, tk.END)

        # REPLAY mode intercept
        if self.executor.replay_state is not None or command.upper() in ('NEXT', 'SKIP', 'QUIT'):
            verb = command.strip().upper()
            if verb == 'NEXT':
                msg, done = self.executor.replay_next()
                self._log_output(f"    >> {msg}")
                self._update_canvas_display()
                self._update_replay_prompt()
                return
            elif verb == 'SKIP':
                msg, done = self.executor.replay_skip()
                self._log_output(f"    >> {msg}")
                self._update_replay_prompt()
                return
            elif verb == 'QUIT':
                msg = self.executor.replay_quit()
                self._log_output(f"    >> {msg}")
                self._update_replay_prompt()
                return
            # Non-NEXT/SKIP/QUIT in replay mode: fall through to normal execute

        # Execute
        try:
            result = self.executor.execute(command)
            if result:
                self._log_output(f"    >> {result}")

            self._update_canvas_indicators()
            self._update_canvas_display()
            self._update_replay_prompt()

            # Open replay dialog when REPLAY arms, refresh if already open
            if self.executor.replay_state is not None:
                if self.replay_dialog is None or not self.replay_dialog.alive:
                    self.command_input.config(state='disabled')
                    self.replay_dialog = ReplayDialog(self.root, self.executor, self)
                else:
                    self.replay_dialog.refresh()

            self.status_label.config(text=f"Command executed: {command}")
        except MissingParamsError as e:
            # Auto-invoke help for bare required-param commands
            cmd_name = command.split()[0].upper()
            try:
                self.executor.execute(f"HELP {cmd_name}")
            except Exception:
                pass
            self._log_output(f"    !! {str(e)}")
            self.status_label.config(text=f"Missing params: {cmd_name}")
            
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

# ---------------------------------------------------------------------------
# Replay Dialog
# ---------------------------------------------------------------------------

class ReplayDialog:
    """Non-modal Toplevel dialog for stepping through REPLAY sessions.
    Provides command list with current-position highlight, NEXT/SKIP/QUIT
    buttons, and a restricted command entry for visual adjustments.
    """

    _ALLOWED_COMMANDS = {'FILL', 'COLOR', 'WIDTH', 'ALPHA', 'ZORDER', 'HIGH'}

    def __init__(self, parent, executor, ui):
        self.executor = executor
        self.ui       = ui
        self.alive    = True

        self.win = tk.Toplevel(parent)
        self.win.title("REPLAY")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        # Center over the command log panel (left panel, sash at ~500px)
        self.win.update_idletasks()
        dlg_w  = 480
        dlg_h  = 700
        rx     = parent.winfo_x()
        ry     = parent.winfo_y()
        # Left panel spans from root x to approximately sash x (500px)
        try:
            sash_x = parent.winfo_rootx() + self.ui.main_pane.sash_coord(0)[0]
        except Exception:
            sash_x = rx + 500
        panel_center_x = rx + (sash_x - rx) // 2
        px = panel_center_x - dlg_w // 2
        py = ry + 40
        self.win.geometry(f"{dlg_w}x{dlg_h}+{px}+{py}")
        self.win.resizable(True, True)

        self._build()
        self.refresh()

        # Enter key on dialog drives NEXT when entry is empty
        self.win.bind('<Return>', self._on_enter)

    def _build(self):
        """Build dialog layout."""
        # --- Status bar ---
        self.status_var = tk.StringVar(value="")
        status = tk.Label(
            self.win, textvariable=self.status_var,
            font=('Consolas', 10, 'bold'), anchor='w',
            bg='darkred', fg='white', padx=6
        )
        status.pack(fill=tk.X, side=tk.TOP)

        # --- Command list ---
        list_frame = tk.Frame(self.win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame, font=('Consolas', 10),
            yscrollcommand=scrollbar.set,
            selectmode=tk.BROWSE, activestyle='none',
            bg='#1e1e1e', fg='#cccccc',
            selectbackground='#3a3a3a',
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # --- Button row ---
        btn_frame = tk.Frame(self.win, pady=4)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.next_btn = tk.Button(
            btn_frame, text="NEXT", width=10, bg='#2e7d32', fg='white',
            font=('Arial', 10, 'bold'), command=self._do_next
        )
        self.next_btn.pack(side=tk.LEFT, padx=6)

        self.skip_btn = tk.Button(
            btn_frame, text="SKIP", width=10, bg='#e65100', fg='white',
            font=('Arial', 10, 'bold'), command=self._do_skip
        )
        self.skip_btn.pack(side=tk.LEFT, padx=2)

        self.quit_btn = tk.Button(
            btn_frame, text="QUIT", width=10, bg='#b71c1c', fg='white',
            font=('Arial', 10, 'bold'), command=self._do_quit
        )
        self.quit_btn.pack(side=tk.LEFT, padx=2)

        # --- Command entry ---
        entry_frame = tk.Frame(self.win, pady=2)
        entry_frame.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(entry_frame, text="Cmd:", font=('Consolas', 9)).pack(side=tk.LEFT, padx=4)
        self.cmd_entry = tk.Entry(entry_frame, font=('Consolas', 10))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.cmd_entry.bind('<Return>', self._on_entry_return)

        tk.Button(
            entry_frame, text="Run", command=self._do_entry_cmd
        ).pack(side=tk.LEFT, padx=4)

    def refresh(self):
        """Rebuild listbox content to reflect current replay_state."""
        state = self.executor.replay_state
        if state is None:
            return

        commands = state['commands']
        idx      = state['index']
        total    = state['total']
        high     = state.get('highlight_active', False)
        h_shape  = state.get('highlight_shape')

        # Update status
        shape_info = f"  shape: {h_shape}" if high and h_shape else ""
        pending    = "  [NEXT to transition]" if state.get('pending_transition') else ""
        self.status_var.set(f"Step {idx}/{total}{shape_info}{pending}")

        # Rebuild list
        self.listbox.delete(0, tk.END)

        # Pre-scan transition boundaries for spacers
        boundaries = set()
        if high:
            prev_target = None
            for i, cmd in enumerate(commands):
                t = self._parse_target(cmd)
                if t and t != prev_target and prev_target is not None:
                    boundaries.add(i)
                if t:
                    prev_target = t

        # Offset tracks inserted spacer rows
        offset = 0
        for i, cmd in enumerate(commands):
            if i in boundaries:
                self.listbox.insert(tk.END, "")
                self.listbox.itemconfig(tk.END, bg='#333333', fg='#333333')
                offset += 1

            self.listbox.insert(tk.END, f"  {cmd}")

            list_i = i + offset
            if i < idx:
                # Already executed
                self.listbox.itemconfig(list_i, bg='#2a2a2a', fg='#555555')
            elif i == idx:
                # Current / pending
                self.listbox.itemconfig(list_i, bg='#3a3000', fg='#ffee88')
            else:
                # Not yet reached
                self.listbox.itemconfig(list_i, bg='#1e1e1e', fg='#cccccc')

        # Scroll current command into view
        visible_idx = idx + offset
        if visible_idx < self.listbox.size():
            self.listbox.see(visible_idx)

    def _parse_target(self, cmd_str):
        tokens = cmd_str.strip().split()
        return tokens[1] if len(tokens) >= 2 else None

    def _do_next(self):
        msg, done = self.executor.replay_next()
        self.ui._log_output(f"    >> {msg}")
        self.ui._update_canvas_display()
        self.ui._update_replay_prompt()
        if done:
            self._finish()
        else:
            self.refresh()

    def _do_skip(self):
        msg, done = self.executor.replay_skip()
        self.ui._log_output(f"    >> {msg}")
        self.ui._update_replay_prompt()
        if done:
            self._finish()
        else:
            self.refresh()

    def _do_quit(self):
        msg = self.executor.replay_quit()
        self.ui._log_output(f"    >> {msg}")
        self.ui._update_replay_prompt()
        self._close()

    def _do_entry_cmd(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        verb = cmd.split()[0].upper()
        if verb not in self._ALLOWED_COMMANDS:
            self.cmd_entry.config(bg='#ffcccc')
            self.win.after(600, lambda: self.cmd_entry.config(bg='white'))
            return
        self.cmd_entry.delete(0, tk.END)
        try:
            result = self.executor.execute(cmd)
            if result:
                self.ui._log_output(f"    >> {result}")
            self.ui._update_canvas_display()
            self.refresh()
        except Exception as e:
            self.ui._log_output(f"    !! {e}")

    def _on_entry_return(self, event):
        """Enter in entry field: submit if text present, else NEXT."""
        if self.cmd_entry.get().strip():
            self._do_entry_cmd()
        else:
            self._do_next()

    def _on_enter(self, event):
        """Enter key on dialog window (not in entry): drive NEXT."""
        # Only fire if focus is not on the entry field
        if self.win.focus_get() is not self.cmd_entry:
            self._do_next()

    def _finish(self):
        """Replay completed — show status then auto-close."""
        self.status_var.set("REPLAY complete.")
        self.next_btn.config(state='disabled')
        self.skip_btn.config(state='disabled')
        self.win.after(1500, self._close)

    def _on_close(self):
        """X button pressed — treat as QUIT."""
        if self.executor.replay_state is not None:
            self.executor.replay_quit()
            self.ui._update_replay_prompt()
        self._close()

    def _close(self):
        """Tear down dialog and re-enable main command bar."""
        self.alive = False
        self.ui.replay_dialog = None
        self.ui.command_input.config(state='normal')
        self.ui.command_input.focus()
        self.win.destroy()


def create_ui(executor):
    """Factory function to create and return the UI"""
    return ShapeStudioUI(executor)