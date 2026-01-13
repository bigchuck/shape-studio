"""
Shape Studio - Main Entry Point
"""
from src.core.canvas import Canvas
from src.commands.executor import CommandExecutor
from src.ui.interface import ShapeStudioUI
from src.config import config


def main():
    """Initialize and run Shape Studio with dual canvas system"""
    
    # Initialize configuration (load from file if present, otherwise use defaults)
    config.load()

    # Create WIP canvas (working/scratch space)
    wip_canvas = Canvas()
    
    # Create Main canvas (final composition)
    main_canvas = Canvas()
    
    # Create command executor with both canvases
    executor = CommandExecutor(wip_canvas, main_canvas)
    
    # Create and run UI
    ui = ShapeStudioUI(executor)
    ui.run()


if __name__ == "__main__":
    main()