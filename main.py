#!/usr/bin/env python3
"""
Shape Studio - Command-line driven shape drawing tool
Main entry point
"""

import sys
import tkinter as tk
from src.ui.interface import ShapeStudioUI


def main():
    """Main entry point."""
    try:
        root = tk.Tk()
        app = ShapeStudioUI(root)
        app.run()
    except KeyboardInterrupt:
        print("\nExiting Shape Studio...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
