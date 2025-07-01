#!/usr/bin/env python3
"""
Texture Processor for FBX to MDL Converter

Handles texture conversion, palette generation, and 8-bit indexing
for Counter-Strike 1.6 MDL format compatibility.

Author: FBX to MDL Converter Tool
License: MIT
"""

import os
import math
from typing import List, Tuple, Optional, Dict
from pathlib import Path

# Check for numpy availability
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Numpy is optional for texture processing

try:
    from PIL import Image, ImagePalette
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Create dummy classes for type hints when PIL is not available
    class Image:
        class Image:
            pass
    print("Warning: PIL/Pillow not available. Texture processing will be limited.")

class TextureProcessor:
    """Handles texture processing for MDL format"""
    
    def __init__(self):
        self.max_colors = 256
        self.target_size = (256, 256)  # Default CS 1.6 texture size
        
    def is_power_of_two(self, n: int) -> bool:
        """Check if number is power of 2"""
        return n > 0 and (n & (n - 1)) == 0
    
    def next_power_of_two(self, n: int) -> int:
        """Get next power of 2 >= n"""
        if n <= 0:
            return 1
        return 2 ** math.ceil(math.log2(n))
    
    def resize_to_power_of_two(self, image: Image.Image) -> Image.Image:
        """Resize image to power-of-2 dimensions"""
        width, height = image.size
        
        # Calculate target dimensions
        new_width = self.next_power_of_two(width)
        new_height = self.next_power_of_two(height)
        
        # Clamp to reasonable limits for CS 1.6
        new_width = min(new_width, 512)
        new_height = min(new_height, 512)
        
        if new_width != width or new_height != height:
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Resized texture from {width}x{height} to {new_width}x{new_height}")
        
        return image
    
    def quantize_image(self, image: Image.Image) -> Image.Image:
        """Convert image to 8-bit indexed color (256 colors max)"""
        if not PIL_AVAILABLE:
            print("Warning: Cannot quantize image - PIL not available")
            return image
        
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Quantize to 256 colors using optimized palette
        quantized = image.quantize(colors=self.max_colors, method=Image.Quantize.MEDIANCUT)
        
        return quantized
    
    def create_bmp_palette(self, image: Image.Image) -> bytes:
        """Create BMP-compatible palette data"""
        if image.mode != 'P':
            raise ValueError("Image must be in palette mode")
        
        palette = image.getpalette()
        if not palette:
            raise ValueError("Image has no palette")
        
        # BMP palette format: BGR + reserved byte for each color
        bmp_palette = bytearray()
        
        # Ensure we have exactly 256 colors
        rgb_palette = palette[:768]  # 256 * 3 bytes
        while len(rgb_palette) < 768:
            rgb_palette.extend([0, 0, 0])  # Pad with black
        
        for i in range(0, len(rgb_palette), 3):
            r = rgb_palette[i]
            g = rgb_palette[i + 1] if i + 1 < len(rgb_palette) else 0
            b = rgb_palette[i + 2] if i + 2 < len(rgb_palette) else 0
            
            # BMP format: BGR + reserved
            bmp_palette.extend([b, g, r, 0])
        
        return bytes(bmp_palette)
    
    def process_texture_file(self, input_path: str, output_dir: str) -> Optional[Dict]:
        """Process a texture file for MDL compatibility"""
        if not PIL_AVAILABLE:
            print(f"Warning: Cannot process texture {input_path} - PIL not available")
            return None
        
        try:
            # Load image
            image = Image.open(input_path)
            original_size = image.size
            
            print(f"Processing texture: {input_path} ({original_size[0]}x{original_size[1]})")
            
            # Resize to power of 2 if needed
            image = self.resize_to_power_of_two(image)
            
            # Convert to 8-bit indexed
            indexed_image = self.quantize_image(image)
            
            # Generate output filename
            input_name = Path(input_path).stem
            output_name = f"{input_name}_indexed.bmp"
            output_path = os.path.join(output_dir, output_name)
            
            # Create output directory if needed
            os.makedirs(output_dir, exist_ok=True)
            
            # Save as BMP with palette
            indexed_image.save(output_path, "BMP")
            
            # Extract palette data
            palette_data = self.create_bmp_palette(indexed_image)
            
            texture_info = {
                "input_path": input_path,
                "output_path": output_path,
                "original_size": original_size,
                "final_size": indexed_image.size,
                "colors_used": len(set(indexed_image.getdata())),
                "palette_size": len(palette_data),
                "format": "8-bit indexed BMP"
            }
            
            print(f"  -> Saved: {output_path}")
            print(f"  -> Size: {indexed_image.size[0]}x{indexed_image.size[1]}")
            print(f"  -> Colors: {texture_info['colors_used']}")
            
            return texture_info
            
        except Exception as e:
            print(f"Error processing texture {input_path}: {e}")
            return None
    
    def batch_process_textures(self, texture_paths: List[str], output_dir: str) -> List[Dict]:
        """Process multiple texture files"""
        results = []
        
        for texture_path in texture_paths:
            if os.path.exists(texture_path):
                result = self.process_texture_file(texture_path, output_dir)
                if result:
                    results.append(result)
            else:
                print(f"Warning: Texture file not found: {texture_path}")
        
        return results
    
    def create_texture_atlas(self, texture_paths: List[str], output_path: str, 
                           atlas_size: Tuple[int, int] = (512, 512)) -> Optional[Dict]:
        """Create texture atlas from multiple textures"""
        if not PIL_AVAILABLE:
            print("Warning: Cannot create texture atlas - PIL not available")
            return None
        
        try:
            # Calculate grid layout
            num_textures = len(texture_paths)
            if num_textures == 0:
                return None
            
            grid_size = math.ceil(math.sqrt(num_textures))
            cell_size = (atlas_size[0] // grid_size, atlas_size[1] // grid_size)
            
            # Create atlas image
            atlas = Image.new('RGB', atlas_size, (0, 0, 0))
            
            texture_info = []
            
            for i, texture_path in enumerate(texture_paths):
                if not os.path.exists(texture_path):
                    continue
                
                # Calculate position in grid
                row = i // grid_size
                col = i % grid_size
                x = col * cell_size[0]
                y = row * cell_size[1]
                
                # Load and resize texture
                texture = Image.open(texture_path)
                texture = texture.resize(cell_size, Image.Resampling.LANCZOS)
                
                # Paste into atlas
                atlas.paste(texture, (x, y))
                
                # Store UV coordinates
                u1 = x / atlas_size[0]
                v1 = y / atlas_size[1]
                u2 = (x + cell_size[0]) / atlas_size[0]
                v2 = (y + cell_size[1]) / atlas_size[1]
                
                texture_info.append({
                    "path": texture_path,
                    "uv_coords": (u1, v1, u2, v2),
                    "atlas_position": (x, y),
                    "cell_size": cell_size
                })
            
            # Convert to indexed and save
            indexed_atlas = self.quantize_image(atlas)
            indexed_atlas.save(output_path, "BMP")
            
            result = {
                "atlas_path": output_path,
                "atlas_size": atlas_size,
                "grid_size": grid_size,
                "cell_size": cell_size,
                "textures": texture_info,
                "total_textures": len(texture_info)
            }
            
            print(f"Created texture atlas: {output_path}")
            print(f"  -> Size: {atlas_size[0]}x{atlas_size[1]}")
            print(f"  -> Grid: {grid_size}x{grid_size}")
            print(f"  -> Textures: {len(texture_info)}")
            
            return result
            
        except Exception as e:
            print(f"Error creating texture atlas: {e}")
            return None
    
    def extract_embedded_textures(self, fbx_data: dict, output_dir: str) -> List[str]:
        """Extract embedded textures from FBX data (placeholder)"""
        # This would extract textures embedded in FBX files
        # For now, return empty list as placeholder
        extracted_paths = []
        
        # Implementation would depend on FBX structure
        # and would require parsing embedded texture data
        
        return extracted_paths
    
    def validate_texture_for_cs16(self, texture_path: str) -> Dict[str, bool]:
        """Validate texture compatibility with CS 1.6"""
        if not PIL_AVAILABLE:
            return {"valid": False, "reason": "PIL not available"}
        
        try:
            image = Image.open(texture_path)
            width, height = image.size
            
            validation = {
                "valid": True,
                "power_of_two": self.is_power_of_two(width) and self.is_power_of_two(height),
                "reasonable_size": 16 <= width <= 512 and 16 <= height <= 512,
                "square": width == height,
                "format_supported": image.format in ['BMP', 'PNG', 'TGA', 'JPEG'],
                "color_count_ok": True  # Will check if quantized
            }
            
            # Check color count for indexed images
            if image.mode == 'P':
                colors_used = len(set(image.getdata()))
                validation["color_count_ok"] = colors_used <= 256
            
            # Overall validation
            validation["valid"] = all([
                validation["power_of_two"],
                validation["reasonable_size"],
                validation["format_supported"],
                validation["color_count_ok"]
            ])
            
            if not validation["valid"]:
                reasons = []
                if not validation["power_of_two"]:
                    reasons.append("not power of 2 dimensions")
                if not validation["reasonable_size"]:
                    reasons.append("size not in 16-512 range")
                if not validation["format_supported"]:
                    reasons.append("unsupported format")
                if not validation["color_count_ok"]:
                    reasons.append("too many colors")
                
                validation["reason"] = "; ".join(reasons)
            
            return validation
            
        except Exception as e:
            return {"valid": False, "reason": f"Error reading texture: {e}"}

def main():
    """CLI for texture processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process textures for CS 1.6 MDL format")
    parser.add_argument('command', choices=['process', 'atlas', 'validate'],
                       help='Command to execute')
    parser.add_argument('input', help='Input texture file or directory')
    parser.add_argument('--output', '-o', help='Output path')
    parser.add_argument('--size', default='256x256', help='Target size (e.g. 256x256)')
    
    args = parser.parse_args()
    
    processor = TextureProcessor()
    
    if args.command == 'process':
        if os.path.isfile(args.input):
            output_dir = args.output or os.path.dirname(args.input)
            result = processor.process_texture_file(args.input, output_dir)
            if result:
                print(f"Processed successfully: {result['output_path']}")
        else:
            print(f"Error: Input file not found: {args.input}")
    
    elif args.command == 'validate':
        if os.path.isfile(args.input):
            validation = processor.validate_texture_for_cs16(args.input)
            print(f"Texture validation for {args.input}:")
            for key, value in validation.items():
                print(f"  {key}: {value}")
        else:
            print(f"Error: Input file not found: {args.input}")
    
    elif args.command == 'atlas':
        if os.path.isdir(args.input):
            # Find all image files in directory
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tga']
            texture_paths = []
            
            for ext in image_extensions:
                texture_paths.extend(Path(args.input).glob(f"*{ext}"))
                texture_paths.extend(Path(args.input).glob(f"*{ext.upper()}"))
            
            texture_paths = [str(p) for p in texture_paths]
            
            if texture_paths:
                output_path = args.output or os.path.join(args.input, "atlas.bmp")
                
                # Parse size
                if 'x' in args.size:
                    width, height = map(int, args.size.split('x'))
                    atlas_size = (width, height)
                else:
                    size = int(args.size)
                    atlas_size = (size, size)
                
                result = processor.create_texture_atlas(texture_paths, output_path, atlas_size)
                if result:
                    print(f"Created atlas: {result['atlas_path']}")
            else:
                print(f"No image files found in {args.input}")
        else:
            print(f"Error: Input directory not found: {args.input}")

if __name__ == "__main__":
    main()