"""
Help data for Shape Studio commands.
Each entry has:
  synopsis  - one-line description (used in HELP index)
  usage     - full usage block (used in HELP <command>)
"""

HELP = {
    'LINE': {
        'synopsis': 'Create a line segment between two points',
        'usage': (
            "LINE <name> <x1>,<y1> <x2>,<y2>\n"
            "\n"
            "  name       Shape name\n"
            "  x1,y1     Start point (pixels)\n"
            "  x2,y2     End point (pixels)\n"
            "\n"
            "Example:\n"
            "  LINE myline 100,100 400,400"
        ),
    },
    'POLY': {
        'synopsis': 'Create a polygon from three or more points',
        'usage': (
            "POLY <name> <x1>,<y1> <x2>,<y2> <x3>,<y3> ...\n"
            "\n"
            "  name       Shape name\n"
            "  x,y        Vertex points (pixels) — minimum 3 required\n"
            "\n"
            "Example:\n"
            "  POLY tri 100,100 400,100 250,400"
        ),
    },
    'MOVE': {
        'synopsis': 'Translate a shape by a delta offset',
        'usage': (
            "MOVE [<name>] <dx>,<dy>\n"
            "\n"
            "  name       Shape name (optional if WORKWITH is set)\n"
            "  dx,dy     Pixel offset (negative values move left/up)\n"
            "\n"
            "Examples:\n"
            "  MOVE tri 50,0\n"
            "  MOVE 50,0          (uses WORKWITH context)"
        ),
    },
    'ROTATE': {
        'synopsis': 'Rotate a shape about its centroid',
        'usage': (
            "ROTATE [<name>] <angle>\n"
            "\n"
            "  name       Shape name (optional if WORKWITH is set)\n"
            "  angle      Degrees (positive = clockwise)\n"
            "\n"
            "Examples:\n"
            "  ROTATE tri 45\n"
            "  ROTATE 45          (uses WORKWITH context)"
        ),
    },
    'SCALE': {
        'synopsis': 'Scale a shape uniformly about its centroid',
        'usage': (
            "SCALE [<name>] <factor>\n"
            "\n"
            "  name       Shape name (optional if WORKWITH is set)\n"
            "  factor     Multiplier (e.g. 2.0 doubles, 0.5 halves)\n"
            "\n"
            "Examples:\n"
            "  SCALE tri 1.5\n"
            "  SCALE 1.5          (uses WORKWITH context)"
        ),
    },
    'RESIZE': {
        'synopsis': 'Scale a shape independently on each axis',
        'usage': (
            "RESIZE [<name>] <x_factor> [y_factor]\n"
            "\n"
            "  name        Shape name (optional if WORKWITH is set)\n"
            "  x_factor    Horizontal scale multiplier\n"
            "  y_factor    Vertical scale multiplier (defaults to x_factor)\n"
            "\n"
            "Examples:\n"
            "  RESIZE tri 2.0 0.5\n"
            "  RESIZE 2.0         (uses WORKWITH context, uniform scale)"
        ),
    },
    'COLOR': {
        'synopsis': 'Set the outline color of a shape',
        'usage': (
            "COLOR [<name>] <color>\n"
            "\n"
            "  name    Shape name (optional if WORKWITH is set)\n"
            "  color   Named color, #rrggbb hex, RGB(r,g,b), or HSV(h,s,v)\n"
            "\n"
            "Examples:\n"
            "  COLOR tri red\n"
            "  COLOR tri #ff4400\n"
            "  COLOR red          (uses WORKWITH context)"
        ),
    },
    'FILL': {
        'synopsis': 'Set the fill color of a shape (or NONE to clear)',
        'usage': (
            "FILL [<name>] <color|NONE>\n"
            "\n"
            "  name    Shape name (optional if WORKWITH is set)\n"
            "  color   Any color format, or NONE to remove fill\n"
            "\n"
            "Examples:\n"
            "  FILL tri blue\n"
            "  FILL tri NONE\n"
            "  FILL blue          (uses WORKWITH context)"
        ),
    },
    'WIDTH': {
        'synopsis': 'Set the outline stroke width of a shape',
        'usage': (
            "WIDTH [<name>] <pixels>\n"
            "\n"
            "  name      Shape name (optional if WORKWITH is set)\n"
            "  pixels    Integer >= 1\n"
            "\n"
            "Examples:\n"
            "  WIDTH tri 3\n"
            "  WIDTH 3            (uses WORKWITH context)"
        ),
    },
    'ALPHA': {
        'synopsis': 'Set the opacity of a shape (0.0 transparent – 1.0 opaque)',
        'usage': (
            "ALPHA [<name>] <value>\n"
            "\n"
            "  name    Shape name (optional if WORKWITH is set)\n"
            "  value   Float 0.0 to 1.0\n"
            "\n"
            "Examples:\n"
            "  ALPHA tri 0.5\n"
            "  ALPHA 0.5          (uses WORKWITH context)"
        ),
    },
    'ZORDER': {
        'synopsis': 'Set the z-order (draw depth) of a shape',
        'usage': (
            "ZORDER [<name>] <value>\n"
            "\n"
            "  name    Shape name (optional if WORKWITH is set)\n"
            "  value   Integer — lower values drawn first (further back)\n"
            "\n"
            "Examples:\n"
            "  ZORDER tri 5\n"
            "  ZORDER 5           (uses WORKWITH context)"
        ),
    },
    'RESET_ZORDER': {
        'synopsis': 'Reset the canvas z-order counter',
        'usage': (
            "RESET_ZORDER [value]\n"
            "\n"
            "  value   Starting counter value (defaults to config setting)\n"
            "\n"
            "Use when z-order counter has drifted and new shapes need\n"
            "to be placed in front of existing ones.\n"
            "\n"
            "Example:\n"
            "  RESET_ZORDER\n"
            "  RESET_ZORDER 100"
        ),
    },
    'GROUP': {
        'synopsis': 'Combine shapes into a named group',
        'usage': (
            "GROUP <group_name> <shape1> <shape2> ...\n"
            "\n"
            "  group_name   Name for the new group\n"
            "  shape1...    Two or more existing shape names\n"
            "\n"
            "Example:\n"
            "  GROUP mygroup tri rect bg"
        ),
    },
    'UNGROUP': {
        'synopsis': 'Dissolve a group back into individual shapes',
        'usage': (
            "UNGROUP <group_name>\n"
            "\n"
            "  group_name   Name of the group to dissolve\n"
            "\n"
            "Example:\n"
            "  UNGROUP mygroup"
        ),
    },
    'EXTRACT': {
        'synopsis': 'Remove a single member from a group',
        'usage': (
            "EXTRACT <member> FROM <group>\n"
            "\n"
            "  member   Shape to extract\n"
            "  group    Group it currently belongs to\n"
            "\n"
            "Example:\n"
            "  EXTRACT tri FROM mygroup"
        ),
    },
    'DELETE': {
        'synopsis': 'Delete a shape from the active canvas',
        'usage': (
            "DELETE <shape> [CONFIRM]\n"
            "\n"
            "  shape     Shape name\n"
            "  CONFIRM   Required flag to actually delete\n"
            "\n"
            "Example:\n"
            "  DELETE tri CONFIRM"
        ),
    },
    'SWITCH': {
        'synopsis': 'Switch the active canvas between WIP and MAIN',
        'usage': (
            "SWITCH WIP|MAIN\n"
            "\n"
            "Example:\n"
            "  SWITCH MAIN\n"
            "  SWITCH WIP"
        ),
    },
    'PROMOTE': {
        'synopsis': 'Move or copy a shape from WIP to MAIN',
        'usage': (
            "PROMOTE [COPY] <shape>\n"
            "\n"
            "  COPY    Copy instead of move (shape stays in WIP)\n"
            "  shape   Shape name on WIP canvas\n"
            "\n"
            "Name collisions are resolved automatically with a suffix.\n"
            "\n"
            "Examples:\n"
            "  PROMOTE tri\n"
            "  PROMOTE COPY tri"
        ),
    },
    'UNPROMOTE': {
        'synopsis': 'Move or copy a shape from MAIN back to WIP',
        'usage': (
            "UNPROMOTE [COPY] <shape>\n"
            "\n"
            "  COPY    Copy instead of move (shape stays in MAIN)\n"
            "  shape   Shape name on MAIN canvas\n"
            "\n"
            "Name collisions are resolved automatically with a suffix.\n"
            "\n"
            "Examples:\n"
            "  UNPROMOTE tri\n"
            "  UNPROMOTE COPY tri"
        ),
    },
    'STASH': {
        'synopsis': 'Temporarily store a shape out of the active canvas',
        'usage': (
            "STASH <shape>\n"
            "\n"
            "  shape   Shape to move into the stash\n"
            "\n"
            "Example:\n"
            "  STASH tri"
        ),
    },
    'UNSTASH': {
        'synopsis': 'Restore a shape from the stash to the active canvas',
        'usage': (
            "UNSTASH [MOVE] <shape>\n"
            "\n"
            "  MOVE    Remove from stash after restoring (default: copy)\n"
            "  shape   Shape name in stash\n"
            "\n"
            "Examples:\n"
            "  UNSTASH tri\n"
            "  UNSTASH MOVE tri"
        ),
    },
    'STORE': {
        'synopsis': 'Save a shape to the project store or global library',
        'usage': (
            "STORE [GLOBAL] <shape>\n"
            "\n"
            "  GLOBAL   Save to global library instead of project store\n"
            "  shape    Shape name to persist\n"
            "\n"
            "Examples:\n"
            "  STORE tri\n"
            "  STORE GLOBAL tri"
        ),
    },
    'LOAD': {
        'synopsis': 'Load a shape from the project store or global library',
        'usage': (
            "LOAD <shape>\n"
            "\n"
            "  shape   Shape name to load (project store searched first)\n"
            "\n"
            "Name collisions are resolved automatically with a suffix.\n"
            "\n"
            "Example:\n"
            "  LOAD tri"
        ),
    },
    'CLEAR': {
        'synopsis': 'Clear shapes from a canvas or stash',
        'usage': (
            "CLEAR [WIP|MAIN|STASH] [ALL]\n"
            "\n"
            "  WIP|MAIN|STASH   Target (defaults to active canvas)\n"
            "  ALL              Required confirmation flag\n"
            "\n"
            "Examples:\n"
            "  CLEAR ALL\n"
            "  CLEAR WIP ALL\n"
            "  CLEAR STASH ALL"
        ),
    },
    'LIST': {
        'synopsis': 'List shapes, stores, or procedural methods',
        'usage': (
            "LIST [WIP|MAIN|STASH|STORE|GLOBAL|PROC]\n"
            "LIST PRESET <method>\n"
            "\n"
            "  WIP|MAIN   Shapes on that canvas\n"
            "  STASH      Shapes in stash\n"
            "  STORE      Project store contents\n"
            "  GLOBAL     Global library contents\n"
            "  PROC       Available procedural methods\n"
            "  PRESET     Presets for a procedural method\n"
            "\n"
            "Examples:\n"
            "  LIST\n"
            "  LIST MAIN\n"
            "  LIST PROC\n"
            "  LIST PRESET dynamic_polygon"
        ),
    },
    'INFO': {
        'synopsis': 'Show detailed information about a shape or proc method',
        'usage': (
            "INFO <shape>\n"
            "INFO PROC <method>\n"
            "\n"
            "Examples:\n"
            "  INFO tri\n"
            "  INFO PROC dynamic_polygon"
        ),
    },
    'SAVE': {
        'synopsis': 'Save the active canvas to a PNG file',
        'usage': (
            "SAVE <filename>\n"
            "\n"
            "  filename   Output path (.png added if missing)\n"
            "\n"
            "Example:\n"
            "  SAVE output/myshape.png"
        ),
    },
    'SAVE_PROJECT': {
        'synopsis': 'Save the entire session to a project file',
        'usage': (
            "SAVE_PROJECT <filename>\n"
            "\n"
            "  filename   Project filename (.shapestudio added if missing)\n"
            "\n"
            "Example:\n"
            "  SAVE_PROJECT mysession"
        ),
    },
    'LOAD_PROJECT': {
        'synopsis': 'Load a previously saved session',
        'usage': (
            "LOAD_PROJECT <filename>\n"
            "\n"
            "  filename   Project filename (.shapestudio added if missing)\n"
            "\n"
            "Example:\n"
            "  LOAD_PROJECT mysession"
        ),
    },
    'PROC': {
        'synopsis': 'Generate a shape using a procedural method',
        'usage': (
            "PROC <method> <name> [PARAM=value ...]\n"
            "\n"
            "  method   Procedural method name (see LIST PROC)\n"
            "  name     Name for the generated shape\n"
            "  PARAM    Method-specific parameters\n"
            "\n"
            "Use INFO PROC <method> for full parameter reference.\n"
            "\n"
            "Example:\n"
            "  PROC dynamic_polygon shape1 vertices=6 bounds=100,100,668,668"
        ),
    },
    'RUN': {
        'synopsis': 'Execute a script file or named section',
        'usage': (
            "RUN <scriptfile> [label|executable_name|--ALL]\n"
            "\n"
            "  scriptfile   .json or .txt script in scripts directory\n"
            "  label        Named section (@label) in .txt file\n"
            "  executable   Named executable in .json file\n"
            "  --ALL        Run all sections/executables\n"
            "\n"
            "Examples:\n"
            "  RUN myscript.json gen1\n"
            "  RUN myscript.txt setup"
        ),
    },
    'BATCH': {
        'synopsis': 'Generate multiple outputs from a script',
        'usage': (
            "BATCH <count> <scriptfile> [executable] <output_prefix> [WIP|MAIN] [STORE]\n"
            "\n"
            "  count          Number of iterations\n"
            "  scriptfile     .json script in scripts directory\n"
            "  executable     Named executable (required for JSON)\n"
            "  output_prefix  Path prefix for output PNGs\n"
            "  WIP|MAIN       Canvas to save (default WIP)\n"
            "  STORE          Also save shape JSON alongside each PNG\n"
            "\n"
            "Example:\n"
            "  BATCH 50 myscript.json gen1 output/run1"
        ),
    },
    'ANIMATE': {
        'synopsis': 'Preview dynamic_polygon iteration frames as animation',
        'usage': (
            "ANIMATE <base_name> [FPS=n] [LOOP=true|false]\n"
            "\n"
            "  base_name   Shape name prefix for iteration snapshots\n"
            "  FPS         Frames per second, 1-10 (default 2)\n"
            "  LOOP        Loop the animation (default false)\n"
            "\n"
            "Example:\n"
            "  ANIMATE shape1 FPS=3 LOOP=true"
        ),
    },
    'ENHANCE': {
        'synopsis': 'Apply an enhancement method to a shape',
        'usage': (
            "ENHANCE <method> <shape> [key=value ...]\n"
            "\n"
            "  method   Enhancement method name\n"
            "  shape    Target shape name\n"
            "  key=val  Intent parameters for the method\n"
            "\n"
            "Example:\n"
            "  ENHANCE color_balance tri target_hue=120"
        ),
    },
    'VALIDATE': {
        'synopsis': 'Validate a script file without executing it',
        'usage': (
            "VALIDATE <scriptfile>\n"
            "\n"
            "  scriptfile   Script to validate (in scripts directory)\n"
            "\n"
            "Example:\n"
            "  VALIDATE myscript.json"
        ),
    },
    'RENAME': {
        'synopsis': 'Rename a shape on the active canvas',
        'usage': (
            "RENAME <old_name> <new_name>\n"
            "\n"
            "  old_name   Current name (canonical aliases accepted)\n"
            "  new_name   New unique name (must not already exist)\n"
            "\n"
            "The shape's canonical_name (origin name) is preserved.\n"
            "\n"
            "Example:\n"
            "  RENAME shape1 background"
        ),
    },
    'WORKWITH': {
        'synopsis': 'Set implicit shape context for style/transform commands [interactive]',
        'usage': (
            "WORKWITH [<shape>|OFF]\n"
            "\n"
            "  shape   Set this shape as the implicit target\n"
            "  OFF     Clear the context\n"
            "  (bare)  Also clears context\n"
            "\n"
            "When set, COLOR, FILL, WIDTH, ALPHA, ZORDER, MOVE,\n"
            "ROTATE, SCALE, RESIZE all use this shape if no name\n"
            "is given. An explicit name always overrides.\n"
            "\n"
            "Ignored during RUN and BATCH execution.\n"
            "Active context shown in the status bar.\n"
            "\n"
            "Examples:\n"
            "  WORKWITH shape1\n"
            "  COLOR red          (targets shape1)\n"
            "  COLOR blue shape2  (targets shape2 explicitly)\n"
            "  WORKWITH OFF"
        ),
    },
    'VIEWPORT': {
        'synopsis': 'Draw a centered border guide for physical canvas framing [interactive]',
        'usage': (
            "VIEWPORT <width>,<height> | VIEWPORT OFF\n"
            "\n"
            "  width,height   Pixel dimensions (integers) or\n"
            "                 ratio multipliers (floats, e.g. 0.7,1.0)\n"
            "  OFF            Remove the viewport border\n"
            "\n"
            "Float values (any number containing a decimal point)\n"
            "are multiplied by 768 to get pixel dimensions.\n"
            "The border appears on both WIP and MAIN canvases.\n"
            "Does not affect saved PNG output.\n"
            "\n"
            "Examples:\n"
            "  VIEWPORT 538,768\n"
            "  VIEWPORT 0.7,1.0    (same as above)\n"
            "  VIEWPORT 1.0,1.0    (full canvas)\n"
            "  VIEWPORT OFF"
        ),
    },
    'DEFORM': {
        'synopsis': 'Stretch or compress a polygon along its principal axis',
        'usage': (
            "DEFORM <name> AXIS=major|minor ALONG=<factor> ACROSS=<factor>\n"
            "\n"
            "  name    Polygon shape to deform\n"
            "  AXIS    Reference axis: major (longest) or minor (shortest)\n"
            "  ALONG   Scale factor along the named axis (1.0 = no change)\n"
            "  ACROSS  Scale factor perpendicular to named axis (1.0 = no change)\n"
            "\n"
            "Factors > 1.0 stretch, < 1.0 compress.\n"
            "\n"
            "Examples:\n"
            "  DEFORM shape1 AXIS=major ALONG=1.25 ACROSS=0.85\n"
            "  DEFORM shape1 AXIS=minor ALONG=0.9 ACROSS=1.1"
        ),
    },
    'CONFIG': {
        'synopsis': 'Read or set a runtime configuration value',
        'usage': (
            "CONFIG <path> [value]\n"
            "\n"
            "  path    Dot-separated config path\n"
            "  value   New value (omit to read current value)\n"
            "\n"
            "Type is preserved from the existing config value.\n"
            "\n"
            "Examples:\n"
            "  CONFIG procedural.validation.min_aspect_ratio\n"
            "  CONFIG procedural.validation.min_aspect_ratio 0.05\n"
            "  CONFIG procedural.validation.min_segment_clearance 8.0\n"
            "  CONFIG procedural.validation.min_angle 5.0"
        ),
    },
    'COMPOSE': {
        'synopsis': 'Load and combine shapes into a composition',
        'usage': (
            "COMPOSE is used inside executable JSON only:\n"
            "\n"
            "  {\n"
            "    \"command\": \"COMPOSE\",\n"
            "    \"compose_parameters\": {\n"
            "      \"shapes\": {\n"
            "        \"specified\": [\"sa224/gen1_0033\", \"sa224/gen4_0050\"]\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "\n"
            "Shapes are loaded under working names compose_shape_1, compose_shape_2, ...\n"
            "and remain on canvas for subsequent commands.\n"
            "Saves a construction JSON alongside each output PNG.\n"
            "\n"
            "LOAD <composition_name> reloads a saved composition."
        ),
    },
    'HELP': {
        'synopsis': 'Show command help in the log',
        'usage': (
            "HELP [<command>]\n"
            "\n"
            "  (bare)    Print compact index of all commands\n"
            "  command   Print full usage for that command\n"
            "\n"
            "Examples:\n"
            "  HELP\n"
            "  HELP COLOR\n"
            "  HELP WORKWITH"
        ),
    },
}