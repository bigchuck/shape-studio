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

## Usage

*To be documented as development progresses*

## Development Status

🚧 **Initial Setup** - Project structure established, ready for development

## License

*To be determined*
