# FBX to MDL Converter for Counter-Strike 1.6

A complete Python-based tool that converts `.fbx` 3D models into `.mdl` files compatible with Counter-Strike 1.6 and the GoldSrc engine. This tool automatically handles mesh processing, bone hierarchies, animations, textures, and generates proper MDL binary files with correct headers.

## 🚀 Features

### Core Functionality
- ✅ **Automatic FBX parsing** using Blender's `bpy` module
- ✅ **Mesh vertex compression** to 0-255 range (required by MDL format)
- ✅ **Precalculated normal mapping** to standard 162 MDL anorms (anorms.h)
- ✅ **8-bit indexed texture support** (BMP, PNG, TGA input → indexed palette output)
- ✅ **Proper MDL binary writing** with correct headers:
  - Magic: `IDPO`
  - Version: `6`
  - Sections for vertices, triangles, bones, animations, textures, sequences
- ✅ **Optional QC file generation** for StudioMDL usage
- ✅ **Full CLI interface** with comprehensive options

### Advanced Features
- 🦴 **Bones/Skeletons** - Complete bone hierarchy and transformations
- 🎬 **Animations** - Keyframes, frame timing, multiple sequences
- 🎨 **Materials** - Diffuse textures and basic properties
- 📊 **JSON preview export** - Mesh and animation data for validation
- 🔧 **Error handling** - Robust handling of missing meshes, textures, or corrupted files

## 📦 Installation

### Prerequisites

The converter requires Python 3.7+ and Blender as a Python module.

### Method 1: Using pip (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Install Blender as Python module
pip install bpy
```

### Method 2: Manual Blender Installation

If `pip install bpy` fails, you can use Blender's built-in Python:

1. Download and install [Blender](https://www.blender.org/download/)
2. Use Blender's Python interpreter:
   ```bash
   /path/to/blender/python -m pip install numpy pillow
   /path/to/blender/python fbx_to_mdl_converter.py input.fbx output.mdl
   ```

### Method 3: Docker (Alternative)

```bash
# Build Docker image with Blender
docker build -t fbx-to-mdl .
docker run -v $(pwd):/workspace fbx-to-mdl input.fbx output.mdl
```

## 🎯 Usage

### Basic Conversion

```bash
# Convert FBX to MDL
python fbx_to_mdl_converter.py weapon.fbx models/weapons/ak47.mdl

# Convert with verbose output
python fbx_to_mdl_converter.py player.fbx models/player/leet.mdl --verbose
```

### Advanced Options

```bash
# Generate QC file for StudioMDL
python fbx_to_mdl_converter.py model.fbx output.mdl --create-qc

# Export preview JSON for validation
python fbx_to_mdl_converter.py model.fbx output.mdl --preview-json preview.json

# Combine all options
python fbx_to_mdl_converter.py complex_model.fbx final.mdl --create-qc --preview-json preview.json --verbose
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `input_fbx` | Input FBX file path (required) |
| `output_mdl` | Output MDL file path (required) |
| `--create-qc` | Generate QC file for StudioMDL |
| `--preview-json` | Export preview data as JSON |
| `--verbose, -v` | Enable verbose output |

## 📁 Project Structure

```
fbx-to-mdl-converter/
├── fbx_to_mdl_converter.py    # Main converter script
├── requirements.txt           # Python dependencies
├── test_converter.py         # Automated test suite
├── README.md                 # This file
├── examples/                 # Example files and usage
│   ├── sample_weapon.fbx
│   ├── sample_player.fbx
│   └── output_examples/
└── docs/                     # Additional documentation
    ├── MDL_FORMAT.md
    ├── TROUBLESHOOTING.md
    └── CONTRIBUTING.md
```

## 🧪 Testing

Run the automated test suite to verify conversion integrity:

```bash
# Run all tests
python test_converter.py

# Run specific test categories
python -m pytest test_converter.py::TestMDLDataStructures -v
python -m pytest test_converter.py::TestFBXToMDLConverter -v
python -m pytest test_converter.py::TestErrorHandling -v
```

### Test Coverage

The test suite includes:
- ✅ MDL data structure validation
- ✅ Vertex compression accuracy
- ✅ Normal vector mapping
- ✅ Binary file format compliance
- ✅ QC file generation
- ✅ JSON export functionality
- ✅ Error handling scenarios
- ✅ CLI argument parsing

## 📋 MDL Format Compliance

The converter generates MDL files that are 100% compatible with CS 1.6 (GoldSrc engine):

### Header Structure
```c
typedef struct {
    char magic[4];        // "IDPO"
    int version;          // 6
    char name[64];        // Model name
    int length;           // Model name length
    vec3_t eyeposition;   // Eye position
    vec3_t min, max;      // Bounding box
    vec3_t bbmin, bbmax;  // Clipping box
    // ... additional fields
} studiohdr_t;
```

### Key Features
- **Vertex Compression**: Coordinates compressed to 0-255 range
- **Anorms**: 162 precalculated normal vectors for efficient lighting
- **Bone Hierarchy**: Complete skeletal structure with transformations
- **Animation Sequences**: Multiple animation sequences with proper timing
- **Texture Support**: 8-bit indexed textures with palette

## 🎨 Supported Input Formats

### FBX Files
- **Meshes**: Triangulated geometry with UVs
- **Materials**: Diffuse textures, basic properties
- **Bones**: Complete skeletal hierarchies
- **Animations**: Keyframe animations, multiple sequences
- **Textures**: Embedded or referenced image files

### Texture Formats
- **Input**: BMP, PNG, TGA, JPG
- **Output**: 8-bit indexed palette (256 colors)
- **Dimensions**: Power of 2 recommended (256x256, 512x512)

## ⚙️ Configuration

### Model Optimization

For best results with CS 1.6:

1. **Polygon Count**: Keep under 2048 triangles
2. **Vertex Count**: Keep under 2048 vertices  
3. **Bone Count**: Maximum 128 bones
4. **Texture Size**: 256x256 or 512x512 recommended
5. **Animation**: 30 FPS for smooth playback

### FBX Export Settings

When exporting from 3D software to FBX:

- **Units**: Use centimeters or consistent scale
- **Axis**: Y-up, Z-forward (Blender/Maya style)
- **Triangulate**: Enable mesh triangulation
- **Embed Textures**: Include textures in FBX file
- **Bake Animations**: Bake keyframes for complex rigs

## 🔧 Troubleshooting

### Common Issues

#### "Blender's bpy module not available"
```bash
# Solution 1: Install bpy via pip
pip install bpy

# Solution 2: Use Blender's Python
/path/to/blender/python fbx_to_mdl_converter.py input.fbx output.mdl

# Solution 3: Check Python version (requires 3.7+)
python --version
```

#### "No mesh objects found in FBX file"
- Ensure FBX contains visible mesh objects
- Check if meshes are in separate files
- Verify FBX export settings include geometry

#### "Failed to write MDL file"
- Check output directory permissions
- Ensure sufficient disk space
- Verify output path is valid

#### "Vertex compression errors"
- Check model scale (should be reasonable units)
- Verify mesh has valid geometry
- Ensure no NaN or infinite coordinates

### Advanced Debugging

Enable verbose mode for detailed information:

```bash
python fbx_to_mdl_converter.py input.fbx output.mdl --verbose
```

Export preview JSON to inspect data:

```bash
python fbx_to_mdl_converter.py input.fbx output.mdl --preview-json debug.json
```

## 🎯 Examples

### Weapon Model Conversion

```bash
# Convert AK-47 weapon model
python fbx_to_mdl_converter.py weapons/ak47.fbx models/weapons/v_ak47.mdl --create-qc

# Output files:
# - models/weapons/v_ak47.mdl (main model file)
# - models/weapons/v_ak47.qc (StudioMDL script)
```

### Player Model Conversion

```bash
# Convert terrorist player model with animations
python fbx_to_mdl_converter.py players/leet.fbx models/player/leet/leet.mdl --create-qc --verbose

# Expected output:
# Loading FBX file: players/leet.fbx
# Loaded model: leet
# Vertices: 1856
# Triangles: 1642
# Bones: 64
# Sequences: 12
# Textures: 3
# Writing MDL file: models/player/leet/leet.mdl
# Generating QC file: models/player/leet/leet.qc
# Conversion completed successfully!
```

### Complex Model with Preview

```bash
# Convert complex model with validation
python fbx_to_mdl_converter.py complex/mech.fbx models/mech.mdl \
    --create-qc \
    --preview-json mech_preview.json \
    --verbose

# Inspect the preview JSON
cat mech_preview.json | jq '.vertex_count, .triangle_count, .bone_count'
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-username/fbx-to-mdl-converter.git
cd fbx-to-mdl-converter

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python test_converter.py

# Format code
black fbx_to_mdl_converter.py test_converter.py

# Type checking
mypy fbx_to_mdl_converter.py
```

### Feature Requests

Want a new feature? Please open an issue with:
- Clear description of the feature
- Use case examples
- Expected behavior
- Any relevant technical details

## 📚 Additional Resources

- [MDL Format Documentation](docs/MDL_FORMAT.md)
- [Counter-Strike Modding Guide](https://developer.valvesoftware.com/wiki/Half-Life_Model_Viewer)
- [Blender FBX Export Guide](https://docs.blender.org/manual/en/latest/addons/import_export/scene_fbx.html)
- [StudioMDL Documentation](https://developer.valvesoftware.com/wiki/Studiomdl)

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Valve Corporation** - for the GoldSrc engine and MDL format
- **Blender Foundation** - for the excellent 3D software and Python API
- **Counter-Strike Modding Community** - for reverse engineering and documentation
- **FBX SDK** - for the FBX format specification

## 🐛 Bug Reports

Found a bug? Please report it with:

1. **Input FBX file** (if possible to share)
2. **Error message** or unexpected behavior
3. **System information** (OS, Python version, Blender version)
4. **Steps to reproduce**

Submit issues at: [GitHub Issues](https://github.com/your-username/fbx-to-mdl-converter/issues)

## 🔄 Version History

### v1.0.0 (Current)
- ✅ Initial release
- ✅ FBX to MDL conversion
- ✅ Blender bpy integration
- ✅ QC file generation
- ✅ JSON preview export
- ✅ Comprehensive test suite
- ✅ CLI interface

### Planned Features
- 🔄 GUI interface
- 🔄 Batch conversion
- 🔄 Advanced texture processing
- 🔄 Animation optimization
- 🔄 LOD generation
- 🔄 Alternative FBX parsers

---

**Made with ❤️ for the Counter-Strike modding community**