#!/usr/bin/env python3
"""
MDL File Validator for Counter-Strike 1.6

Validates generated MDL files for format compliance and CS 1.6 compatibility.
Provides detailed analysis of model structure and potential issues.

Author: FBX to MDL Converter Tool
License: MIT
"""

import os
import struct
import sys
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# MDL Format constants
MDL_MAGIC = b'IDPO'
MDL_VERSION = 6
MAX_VERTICES_CS16 = 2048
MAX_TRIANGLES_CS16 = 2048
MAX_BONES_CS16 = 128
MAX_SEQUENCES_CS16 = 32
MAX_TEXTURES_CS16 = 32

@dataclass
class ValidationResult:
    """Result of MDL validation"""
    valid: bool
    warnings: List[str]
    errors: List[str]
    info: Dict[str, Any]

class MDLValidator:
    """Validates MDL files for CS 1.6 compatibility"""
    
    def __init__(self):
        self.reset_validation()
    
    def reset_validation(self):
        """Reset validation state"""
        self.warnings = []
        self.errors = []
        self.info = {}
    
    def add_error(self, message: str):
        """Add error message"""
        self.errors.append(message)
        print(f"ERROR: {message}")
    
    def add_warning(self, message: str):
        """Add warning message"""
        self.warnings.append(message)
        print(f"WARNING: {message}")
    
    def add_info(self, key: str, value: Any):
        """Add info item"""
        self.info[key] = value
    
    def validate_file(self, mdl_path: str) -> ValidationResult:
        """Validate an MDL file"""
        self.reset_validation()
        
        if not os.path.exists(mdl_path):
            self.add_error(f"MDL file not found: {mdl_path}")
            return ValidationResult(False, self.warnings, self.errors, self.info)
        
        file_size = os.path.getsize(mdl_path)
        self.add_info("file_size", file_size)
        
        if file_size < 100:
            self.add_error("MDL file too small (< 100 bytes)")
            return ValidationResult(False, self.warnings, self.errors, self.info)
        
        try:
            with open(mdl_path, 'rb') as f:
                # Validate header
                if not self._validate_header(f):
                    return ValidationResult(False, self.warnings, self.errors, self.info)
                
                # Read counts and validate
                if not self._validate_counts(f):
                    return ValidationResult(False, self.warnings, self.errors, self.info)
                
                # Validate data sections
                if not self._validate_data_sections(f):
                    return ValidationResult(False, self.warnings, self.errors, self.info)
        
        except Exception as e:
            self.add_error(f"Error reading MDL file: {e}")
            return ValidationResult(False, self.warnings, self.errors, self.info)
        
        # Overall validation
        is_valid = len(self.errors) == 0
        
        if is_valid:
            print(f"✅ MDL file validation passed: {mdl_path}")
        else:
            print(f"❌ MDL file validation failed: {mdl_path}")
        
        return ValidationResult(is_valid, self.warnings, self.errors, self.info)
    
    def _validate_header(self, f) -> bool:
        """Validate MDL header"""
        # Check magic number
        magic = f.read(4)
        if magic != MDL_MAGIC:
            self.add_error(f"Invalid magic number: {magic} (expected {MDL_MAGIC})")
            return False
        
        self.add_info("magic", magic.decode('ascii', errors='ignore'))
        
        # Check version
        version = struct.unpack('<I', f.read(4))[0]
        if version != MDL_VERSION:
            self.add_error(f"Invalid version: {version} (expected {MDL_VERSION})")
            return False
        
        self.add_info("version", version)
        
        # Read model name
        name_bytes = f.read(64)
        model_name = name_bytes.split(b'\x00')[0].decode('ascii', errors='ignore')
        self.add_info("model_name", model_name)
        
        if not model_name:
            self.add_warning("Model name is empty")
        
        # Read name length
        name_length = struct.unpack('<I', f.read(4))[0]
        self.add_info("name_length", name_length)
        
        if name_length != len(model_name):
            self.add_warning(f"Name length mismatch: {name_length} vs {len(model_name)}")
        
        # Read bounding box
        bounds_min = struct.unpack('<fff', f.read(12))
        bounds_max = struct.unpack('<fff', f.read(12))
        
        self.add_info("bounds_min", bounds_min)
        self.add_info("bounds_max", bounds_max)
        
        # Validate bounding box
        for i in range(3):
            if bounds_min[i] >= bounds_max[i]:
                self.add_warning(f"Invalid bounding box: min[{i}] >= max[{i}]")
        
        return True
    
    def _validate_counts(self, f) -> bool:
        """Validate object counts"""
        # Read counts
        vertex_count = struct.unpack('<I', f.read(4))[0]
        triangle_count = struct.unpack('<I', f.read(4))[0]
        bone_count = struct.unpack('<I', f.read(4))[0]
        sequence_count = struct.unpack('<I', f.read(4))[0]
        texture_count = struct.unpack('<I', f.read(4))[0]
        
        self.add_info("vertex_count", vertex_count)
        self.add_info("triangle_count", triangle_count)
        self.add_info("bone_count", bone_count)
        self.add_info("sequence_count", sequence_count)
        self.add_info("texture_count", texture_count)
        
        # Validate counts against CS 1.6 limits
        if vertex_count > MAX_VERTICES_CS16:
            self.add_error(f"Too many vertices: {vertex_count} (max {MAX_VERTICES_CS16})")
        elif vertex_count > MAX_VERTICES_CS16 * 0.8:
            self.add_warning(f"High vertex count: {vertex_count} (approaching limit)")
        
        if triangle_count > MAX_TRIANGLES_CS16:
            self.add_error(f"Too many triangles: {triangle_count} (max {MAX_TRIANGLES_CS16})")
        elif triangle_count > MAX_TRIANGLES_CS16 * 0.8:
            self.add_warning(f"High triangle count: {triangle_count} (approaching limit)")
        
        if bone_count > MAX_BONES_CS16:
            self.add_error(f"Too many bones: {bone_count} (max {MAX_BONES_CS16})")
        elif bone_count > MAX_BONES_CS16 * 0.8:
            self.add_warning(f"High bone count: {bone_count} (approaching limit)")
        
        if sequence_count > MAX_SEQUENCES_CS16:
            self.add_error(f"Too many sequences: {sequence_count} (max {MAX_SEQUENCES_CS16})")
        
        if texture_count > MAX_TEXTURES_CS16:
            self.add_error(f"Too many textures: {texture_count} (max {MAX_TEXTURES_CS16})")
        
        # Check for empty model
        if vertex_count == 0:
            self.add_warning("Model has no vertices")
        
        if triangle_count == 0:
            self.add_warning("Model has no triangles")
        
        return True
    
    def _validate_data_sections(self, f) -> bool:
        """Validate data sections"""
        vertex_count = self.info["vertex_count"]
        triangle_count = self.info["triangle_count"]
        bone_count = self.info["bone_count"]
        sequence_count = self.info["sequence_count"]
        texture_count = self.info["texture_count"]
        
        # Validate vertices
        if not self._validate_vertices(f, vertex_count):
            return False
        
        # Validate triangles
        if not self._validate_triangles(f, triangle_count, vertex_count):
            return False
        
        # Validate bones
        if not self._validate_bones(f, bone_count):
            return False
        
        # Validate sequences
        if not self._validate_sequences(f, sequence_count):
            return False
        
        # Validate textures
        if not self._validate_textures(f, texture_count):
            return False
        
        return True
    
    def _validate_vertices(self, f, count: int) -> bool:
        """Validate vertex data"""
        if count == 0:
            return True
        
        try:
            vertex_data = f.read(count * 4)  # 4 bytes per vertex (x,y,z,normal_index)
            
            if len(vertex_data) != count * 4:
                self.add_error(f"Insufficient vertex data: {len(vertex_data)} bytes (expected {count * 4})")
                return False
            
            # Check individual vertices
            invalid_vertices = 0
            for i in range(count):
                offset = i * 4
                x, y, z, normal_idx = struct.unpack('BBBB', vertex_data[offset:offset + 4])
                
                # Validate coordinates (should be 0-255)
                if x > 255 or y > 255 or z > 255:
                    invalid_vertices += 1
                
                # Validate normal index (should be 0-161)
                if normal_idx > 161:
                    invalid_vertices += 1
            
            if invalid_vertices > 0:
                self.add_warning(f"{invalid_vertices} vertices have invalid data")
            
            self.add_info("vertices_validated", True)
            return True
            
        except Exception as e:
            self.add_error(f"Error validating vertices: {e}")
            return False
    
    def _validate_triangles(self, f, count: int, vertex_count: int) -> bool:
        """Validate triangle data"""
        if count == 0:
            return True
        
        try:
            triangle_data = f.read(count * 16)  # 16 bytes per triangle
            
            if len(triangle_data) != count * 16:
                self.add_error(f"Insufficient triangle data: {len(triangle_data)} bytes (expected {count * 16})")
                return False
            
            # Check individual triangles
            invalid_triangles = 0
            for i in range(count):
                offset = i * 16
                face_front = struct.unpack('<I', triangle_data[offset:offset + 4])[0]
                v1, v2, v3 = struct.unpack('<III', triangle_data[offset + 4:offset + 16])
                
                # Validate vertex indices
                if v1 >= vertex_count or v2 >= vertex_count or v3 >= vertex_count:
                    invalid_triangles += 1
                
                # Check for degenerate triangles
                if v1 == v2 or v2 == v3 or v1 == v3:
                    invalid_triangles += 1
            
            if invalid_triangles > 0:
                self.add_warning(f"{invalid_triangles} triangles have invalid vertex indices")
            
            self.add_info("triangles_validated", True)
            return True
            
        except Exception as e:
            self.add_error(f"Error validating triangles: {e}")
            return False
    
    def _validate_bones(self, f, count: int) -> bool:
        """Validate bone data"""
        if count == 0:
            return True
        
        try:
            bone_data = f.read(count * 56)  # 56 bytes per bone
            
            if len(bone_data) != count * 56:
                self.add_error(f"Insufficient bone data: {len(bone_data)} bytes (expected {count * 56})")
                return False
            
            # Check bone hierarchy
            invalid_bones = 0
            bone_names = []
            
            for i in range(count):
                offset = i * 56
                name_bytes = bone_data[offset:offset + 32]
                bone_name = name_bytes.split(b'\x00')[0].decode('ascii', errors='ignore')
                bone_names.append(bone_name)
                
                parent_idx = struct.unpack('<i', bone_data[offset + 32:offset + 36])[0]
                
                # Validate parent index
                if parent_idx >= i and parent_idx != -1:
                    invalid_bones += 1  # Forward reference or self-reference
                
                if parent_idx < -1 or parent_idx >= count:
                    invalid_bones += 1  # Out of range
            
            if invalid_bones > 0:
                self.add_warning(f"{invalid_bones} bones have invalid parent references")
            
            # Check for duplicate bone names
            unique_names = set(bone_names)
            if len(unique_names) != len(bone_names):
                self.add_warning("Duplicate bone names detected")
            
            self.add_info("bones_validated", True)
            self.add_info("bone_names", bone_names)
            return True
            
        except Exception as e:
            self.add_error(f"Error validating bones: {e}")
            return False
    
    def _validate_sequences(self, f, count: int) -> bool:
        """Validate animation sequence data"""
        if count == 0:
            return True
        
        try:
            sequence_data = f.read(count * 176)  # 176 bytes per sequence
            
            if len(sequence_data) != count * 176:
                self.add_error(f"Insufficient sequence data: {len(sequence_data)} bytes (expected {count * 176})")
                return False
            
            sequence_names = []
            invalid_sequences = 0
            
            for i in range(count):
                offset = i * 176
                name_bytes = sequence_data[offset:offset + 32]
                seq_name = name_bytes.split(b'\x00')[0].decode('ascii', errors='ignore')
                sequence_names.append(seq_name)
                
                fps = struct.unpack('<f', sequence_data[offset + 32:offset + 36])[0]
                numframes = struct.unpack('<I', sequence_data[offset + 60:offset + 64])[0]
                
                # Validate FPS
                if fps <= 0 or fps > 120:
                    invalid_sequences += 1
                
                # Validate frame count
                if numframes == 0:
                    invalid_sequences += 1
            
            if invalid_sequences > 0:
                self.add_warning(f"{invalid_sequences} sequences have invalid parameters")
            
            self.add_info("sequences_validated", True)
            self.add_info("sequence_names", sequence_names)
            return True
            
        except Exception as e:
            self.add_error(f"Error validating sequences: {e}")
            return False
    
    def _validate_textures(self, f, count: int) -> bool:
        """Validate texture data"""
        if count == 0:
            return True
        
        try:
            texture_data = f.read(count * 80)  # 80 bytes per texture
            
            if len(texture_data) != count * 80:
                self.add_error(f"Insufficient texture data: {len(texture_data)} bytes (expected {count * 80})")
                return False
            
            texture_names = []
            invalid_textures = 0
            
            for i in range(count):
                offset = i * 80
                name_bytes = texture_data[offset:offset + 64]
                tex_name = name_bytes.split(b'\x00')[0].decode('ascii', errors='ignore')
                texture_names.append(tex_name)
                
                width = struct.unpack('<I', texture_data[offset + 68:offset + 72])[0]
                height = struct.unpack('<I', texture_data[offset + 72:offset + 76])[0]
                
                # Validate dimensions
                if width == 0 or height == 0:
                    invalid_textures += 1
                
                # Check if power of 2
                if not self._is_power_of_two(width) or not self._is_power_of_two(height):
                    invalid_textures += 1
                
                # Check reasonable size limits
                if width > 512 or height > 512 or width < 16 or height < 16:
                    invalid_textures += 1
            
            if invalid_textures > 0:
                self.add_warning(f"{invalid_textures} textures have invalid dimensions")
            
            self.add_info("textures_validated", True)
            self.add_info("texture_names", texture_names)
            return True
            
        except Exception as e:
            self.add_error(f"Error validating textures: {e}")
            return False
    
    def _is_power_of_two(self, n: int) -> bool:
        """Check if number is power of 2"""
        return n > 0 and (n & (n - 1)) == 0
    
    def generate_report(self, validation_result: ValidationResult, output_path: Optional[str] = None) -> str:
        """Generate detailed validation report"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append("MDL FILE VALIDATION REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Overall status
        status = "✅ VALID" if validation_result.valid else "❌ INVALID"
        report_lines.append(f"Overall Status: {status}")
        report_lines.append("")
        
        # Basic info
        if validation_result.info:
            report_lines.append("Model Information:")
            report_lines.append("-" * 30)
            
            for key, value in validation_result.info.items():
                if key in ["model_name", "version", "file_size", "vertex_count", 
                          "triangle_count", "bone_count", "sequence_count", "texture_count"]:
                    report_lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            
            report_lines.append("")
        
        # Errors
        if validation_result.errors:
            report_lines.append(f"Errors ({len(validation_result.errors)}):")
            report_lines.append("-" * 30)
            for error in validation_result.errors:
                report_lines.append(f"  ❌ {error}")
            report_lines.append("")
        
        # Warnings
        if validation_result.warnings:
            report_lines.append(f"Warnings ({len(validation_result.warnings)}):")
            report_lines.append("-" * 30)
            for warning in validation_result.warnings:
                report_lines.append(f"  ⚠️  {warning}")
            report_lines.append("")
        
        # Detailed info
        if validation_result.info:
            if "bone_names" in validation_result.info:
                report_lines.append("Bone Hierarchy:")
                report_lines.append("-" * 30)
                for i, name in enumerate(validation_result.info["bone_names"]):
                    report_lines.append(f"  {i}: {name}")
                report_lines.append("")
            
            if "sequence_names" in validation_result.info:
                report_lines.append("Animation Sequences:")
                report_lines.append("-" * 30)
                for i, name in enumerate(validation_result.info["sequence_names"]):
                    report_lines.append(f"  {i}: {name}")
                report_lines.append("")
            
            if "texture_names" in validation_result.info:
                report_lines.append("Textures:")
                report_lines.append("-" * 30)
                for i, name in enumerate(validation_result.info["texture_names"]):
                    report_lines.append(f"  {i}: {name}")
                report_lines.append("")
        
        # Recommendations
        if not validation_result.valid or validation_result.warnings:
            report_lines.append("Recommendations:")
            report_lines.append("-" * 30)
            
            if validation_result.errors:
                report_lines.append("  • Fix all errors before using in CS 1.6")
            
            if validation_result.warnings:
                report_lines.append("  • Review warnings for potential issues")
            
            # Specific recommendations based on data
            info = validation_result.info
            if info.get("vertex_count", 0) > MAX_VERTICES_CS16 * 0.8:
                report_lines.append("  • Consider reducing vertex count for better performance")
            
            if info.get("triangle_count", 0) > MAX_TRIANGLES_CS16 * 0.8:
                report_lines.append("  • Consider reducing triangle count for better performance")
            
            if info.get("bone_count", 0) > 64:
                report_lines.append("  • High bone count may impact performance")
            
            report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    f.write(report_text)
                print(f"Validation report saved to: {output_path}")
            except Exception as e:
                print(f"Error saving report: {e}")
        
        return report_text

def main():
    """CLI for MDL validator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate MDL files for CS 1.6 compatibility")
    parser.add_argument('mdl_file', help='Path to MDL file to validate')
    parser.add_argument('--report', '-r', help='Save detailed report to file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.mdl_file):
        print(f"Error: MDL file not found: {args.mdl_file}")
        return 1
    
    validator = MDLValidator()
    result = validator.validate_file(args.mdl_file)
    
    if args.verbose or args.report:
        report = validator.generate_report(result, args.report)
        if args.verbose:
            print("\n" + report)
    
    # Return appropriate exit code
    return 0 if result.valid else 1

if __name__ == "__main__":
    sys.exit(main())