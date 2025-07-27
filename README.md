Convert your Scratch 3.0 (`.sb3`) projects into native **Nintendo 3DS** homebrew games written in C++, low memory usage, and hardware compatibility.

> Note: This tool does **not** generate a ready-to-run `.3dsx` file. It creates a DevkitPro-compatible C++ project that you must compile manually using [devkitARM](https://devkitpro.org/).

## Features

- **Scratch-like Engine Structure**  
  Block execution order, sprite update priority, and logic flow mimic original Scratch behavior.


- **Smart Image Caching**  
  Automatically deduplicates images (by filename) and uses a RAM-efficient on-demand cache.


- **Supported Blocks**  
  -  Movement: `move`, `go to`, `glide`, `set x/y`, `change x/y`, `turn`
  -  Events: `when flag clicked`
  -  Control: `wait (sec)`, `repeat`
  -  _Variables and nested expressions are not supported yet_


- **Custom Screen Layouts**
  - Top screen (400x240)
  - Bottom screen (320x240)
  - Dual-screen mode (400x480 mapped layout)


- **One-File C++ Output**  
  Generates a single `main.cpp` for simplicity and easier debugging.


- **Graphics Pipeline**
  - Images converted to `.t3x` format using `.t3s` descriptor files
  - Output stored under `/gfx/` for use with 3DS GPU
  - `icon.png` (optional) used for homebrew launcher display


-  **Simplified Hitbox Model**  
  Only rectangular (non-rotated) axis-aligned bounding boxes are used for collision.  
  This improves performance on the 3DS but may differ from pixel-perfect Scratch behavior.


---

## Requirements


- Python 3.8+

- [DevkitPro / devkitARM](https://devkitpro.org/) (for compiling `.3dsx`)

- `make` and 3DS homebrew build tools (`makerom`, etc.)

- `.sb3` Scratch 3.0 project file

---

##  Getting Started

> It is **highly recommended** to test or create your Scratch project with a mod like [Turbowarp](https://turbowarp.org/),  
> as it allows resolution changes, framerate tweaking, and behaviour more similar to hardware-constrained devices like the 3DS.

1. Place your `.sb3` file and (optionally) `icon.png` into the root folder.
2. Run the Python generator and follow the prompts
3. The tool will output in 'temp' a new game project
## Developer Notes

This tool is designed for minimal footprint and efficiency. It avoids over engineering:
- No full AST parser, instead it translates Scratch opcodes directly to structured C++ code
- Internally, the translator avoids heavy abstractions. Each Scratch script is mapped to procedural C++ logic with a simple loop counter and execution stack.  
- Currently, control logic and rendering/state logic are not yet decoupled, this is a planned architectural refactor.

Planned improvements include:
- Full control/event support
- Stack-safe recursion handling
- Better error messaging & debug logs
- .3dsx auto-build integration via Python sub process and evtl. a website where you can upload a sb3 file and download the project folder and .3dsx file
