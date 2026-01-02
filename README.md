# Shape Studio

A command-line driven shape drawing and manipulation tool for creating 1024x1024 PNG images suitable for LoRA training datasets.

## Overview

Shape Studio provides a Tkinter-based interface with:
- Command log panel (left side)
- 1024x1024 canvas with grid (right side)
- Command-driven shape creation and manipulation
- PNG export for training data generation

## Features (Planned)

### Shape Creation
- Lines, polygons, and basic shapes
- Random parameter generation
- Parametric shape definitions

### Shape Manipulation
- Move, resize, rotate, reorient
- Major/minor axes visualization
- Elongation transformations
- Segment operations (split, push convex/concave)

### Advanced Features
- Macro system for complex operations
- Batch generation capabilities
- Command file loading
- Export to PNG (1024x1024)

## Project Structure

```
shape-studio/
├── src/
│   ├── core/          # Shape classes and transformations
│   ├── commands/      # Command parser and executor
│   └── ui/            # Tkinter interface
├── examples/          # Example command files
├── output/            # Generated PNG images (git-ignored)
└── macros/            # User-defined macros
```

## Requirements

- Python 3.8+
- Pillow (PIL)
- tkinter (usually included with Python)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run Shape Studio:
```bash
python main.py
```

3. The interface will open with:
   - **Left panel**: Command log showing your commands and results
   - **Right panel**: 1024x1024 canvas with grid overlay

## Command Reference

### Shape Creation

```
LINE <name> <x1>,<y1> <x2>,<y2>
  Create a line from point 1 to point 2
  Example: LINE l1 100,100 900,900

POLY <name> <x1>,<y1> <x2>,<y2> <x3>,<y3> ...
  Create a polygon with given vertices (auto-closes)
  Example: POLY tri 512,200 300,700 724,700
```

### Shape Manipulation

```
MOVE <name> <dx>,<dy>
  Translate shape by dx, dy
  Example: MOVE tri 50,100

ROTATE <name> <angle>
  Rotate shape around its center (degrees)
  Example: ROTATE square1 45

SCALE <name> <factor>
  Scale shape uniformly
  Example: SCALE tri 1.5

RESIZE <name> <sx>,<sy>
  Scale shape non-uniformly (x and y separately)
  Example: RESIZE tri 1.2,0.8
```

### Canvas Operations

```
CLEAR
  Clear all shapes from canvas

LIST
  Show all shapes currently on canvas

SAVE <filename>
  Save canvas as PNG to output/ directory
  Example: SAVE my_drawing.png
```

### Random Values

Use `RAND(min,max)` anywhere you'd use a number:
```
LINE l1 RAND(100,900),RAND(100,900) RAND(100,900),RAND(100,900)
ROTATE square1 RAND(0,360)
```

## Example Session

```
LINE l1 100,100 900,900
LINE l2 100,900 900,100
POLY tri 512,200 300,700 724,700
ROTATE tri 30
MOVE tri 0,50
SCALE tri 0.9
SAVE cross_and_triangle.png
```

## Development Status

✅ **v0.1 - Foundation Complete**
- Basic Tkinter interface with split pane layout
- Canvas rendering with grid (1024x1024)
- Command parsing and execution
- Line and Polygon shapes
- Basic transformations (move, rotate, scale)
- Random parameter support
- PNG export

🚧 **Coming Next**
- Advanced shape operations (elongation, axes)
- Segment operations (split, push)
- Macro system
- Command file loading
- Batch generation

## License

*To be determined*
