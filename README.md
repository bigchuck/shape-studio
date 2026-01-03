# Shape Studio

A command-line driven shape drawing and manipulation tool for creating 768x768 PNG images suitable for LoRA training datasets.

## Overview

Shape Studio provides a Tkinter-based interface with:
- Command log panel (left side)
- 768x768 canvas with grid (right side)
- Help browser (right side)
- Command-driven shape creation and manipulation
- Script execution and batch generation
- PNG export for training data generation

## New in Phase 5: AUTOMATION!

### Script Execution
- **RUN** command - Execute commands from text files
- Comment support (`#` prefix)
- Located in `scripts/` directory

### Batch Generation
- **BATCH** command - Generate multiple PNG variations
- Perfect for LoRA training datasets
- Automatic iteration with fresh random values
- Creative error recovery (random branching)
- Customizable target canvas

### Enhanced Randomization
- **RAND(min,max)** - Random numbers
- **RANDBOOL()** - Random 0 or 1

## Features

### Shape Creation
- Lines, polygons, and basic shapes
- Random parameter generation (RAND, RANDBOOL)
- Parametric shape definitions

### Shape Manipulation
- Move, resize, rotate transformations
- Groups with nested support
- Scale uniform or non-uniform

### Canvas System
- **WIP canvas** - Experimental workspace
- **MAIN canvas** - Final composition
- **Stash** - Temporary storage
- Easy promotion/unpromote between canvases

### Automation & Scripting
- **RUN** - Execute script files
- **BATCH** - Generate training datasets
- Script library in `scripts/` folder
- Comment support for documentation

### Persistence
- **Projects** - Save entire session (.shapestudio)
- **Object Store** - Reusable shape library
- **Global Library** - Share across projects
- Full session restoration

## Project Structure

```
shape-studio/
├── src/
│   ├── core/          # Shape classes and transformations
│   ├── commands/      # Command parser and executor
│   └── ui/            # Tkinter interface
├── scripts/           # Command script files (NEW!)
├── examples/          # Example command files
├── output/            # Generated PNG images (git-ignored)
├── shapes/            # Project object store
├── projects/          # Saved projects
└── HELP.md            # Full command reference
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
   - **Middle panel**: 768x768 canvas with grid overlay
   - **Right panel**: Help browser with command reference

## Command Reference (Quick)

### Shape Creation
```
LINE <name> <x1>,<y1> <x2>,<y2>
POLY <name> <x1>,<y1> <x2>,<y2> <x3>,<y3> ...
```

### Transformations
```
MOVE <name> <dx>,<dy>
ROTATE <name> <angle>
SCALE <name> <factor>
RESIZE <name> <sx> [sy]
```

### Groups
```
GROUP <group_name> <shape1> <shape2> ...
UNGROUP <group_name>
EXTRACT <member> FROM <group>
```

### Canvas Operations
```
SWITCH WIP|MAIN
PROMOTE [COPY] <shape>
UNPROMOTE [COPY] <shape>
CLEAR <canvas> ALL
LIST [WIP|MAIN|STASH|STORE|GLOBAL]
SAVE <filename>
```

### Automation (NEW!)
```
RUN <scriptfile>
BATCH <count> <scriptfile> <prefix> [WIP|MAIN]
```

### Randomization
```
RAND(min,max)     # Random number
RANDBOOL()        # Random 0 or 1
```

## Example: Generate LoRA Training Dataset

### Step 1: Create a script file `scripts/random_triangle.txt`
```
# Random triangle generator
CLEAR WIP ALL
POLY tri RAND(100,668),RAND(100,668) RAND(100,668),RAND(100,668) RAND(100,668),RAND(100,668)
ROTATE tri RAND(0,360)
SCALE tri RAND(0.7,1.3)
PROMOTE tri
CLEAR WIP ALL
```

### Step 2: Test it
```
RUN random_triangle.txt
```

### Step 3: Generate 100 variations
```
BATCH 100 random_triangle.txt training_data MAIN
```

This creates:
- `output/training_data_001.png`
- `output/training_data_002.png`
- ...
- `output/training_data_100.png`

Each with completely random triangle positions, rotations, and scales!

## Development Status

✅ **v0.5 - Automation Complete**
- Script execution (RUN command)
- Batch generation (BATCH command)
- RANDBOOL() function
- Creative error recovery in batch mode

✅ **v0.4 - Persistence Complete**
- Project save/load
- Object store (project and global)
- Shape library system

✅ **v0.3 - Canvas System Complete**
- Dual canvas (WIP/MAIN)
- Promote/unpromote operations
- Stash for temporary storage

✅ **v0.2 - Groups Complete**
- Shape grouping
- Group transformations
- Extract and ungroup operations

✅ **v0.1 - Foundation Complete**
- Basic Tkinter interface with three-panel layout
- Canvas rendering with grid (768x768)
- Command parsing and execution
- Line and Polygon shapes
- Basic transformations (move, rotate, scale)
- Random parameter support (RAND)
- PNG export

🚧 **Coming Next**
- Templates/procedures (parameterized shapes)
- Advanced shape operations (elongation, axes)
- Segment operations (split, push)

## License

*To be determined*
