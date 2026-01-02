"""
Shape Studio - Main Entry Point
Command-line driven shape drawing tool for LoRA training image generation
"""
from src.core.canvas import Canvas
from src.commands.executor import CommandExecutor
from src.ui.interface import ShapeStudioUI


def main():
    """Initialize and run Shape Studio"""
    # Create canvas (1024x1024)
    canvas = Canvas()
    
    # Create command executor
    executor = CommandExecutor(canvas)
    
    # Create and run UI
    ui = ShapeStudioUI(canvas, executor)
    ui.run()


if __name__ == "__main__":
    main()