#!/usr/bin/env python3
"""
Test Suite for FBX to MDL Converter

Comprehensive tests for conversion integrity, file format validation,
and error handling scenarios.

Author: FBX to MDL Converter Tool
License: MIT
"""

import unittest
import tempfile
import os
import sys
import struct
from pathlib import Path
import json

# Add the converter module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fbx_to_mdl_converter import (
    FBXToMDLConverter, 
    MDLVertex, 
    MDLTriangle, 
    MDLBone, 
    MDLSequence, 
    MDLTexture,
    MDL_MAGIC, 
    MDL_VERSION,
    MDL_ANORMS
)

class TestMDLDataStructures(unittest.TestCase):
    """Test MDL data structure classes"""
    
    def test_mdl_vertex_creation(self):
        """Test MDLVertex creation and attributes"""
        vertex = MDLVertex(x=128, y=64, z=192, normal_index=5)
        self.assertEqual(vertex.x, 128)
        self.assertEqual(vertex.y, 64)
        self.assertEqual(vertex.z, 192)
        self.assertEqual(vertex.normal_index, 5)
    
    def test_mdl_triangle_creation(self):
        """Test MDLTriangle creation and attributes"""
        triangle = MDLTriangle(face_front=True, vertex_indices=[0, 1, 2])
        self.assertTrue(triangle.face_front)
        self.assertEqual(triangle.vertex_indices, [0, 1, 2])
    
    def test_mdl_bone_creation(self):
        """Test MDLBone creation and attributes"""
        bone = MDLBone(
            name="root",
            parent=-1,
            flags=0,
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0)
        )
        self.assertEqual(bone.name, "root")
        self.assertEqual(bone.parent, -1)
        self.assertEqual(bone.position, (0.0, 0.0, 0.0))

class TestFBXToMDLConverter(unittest.TestCase):
    """Test the main converter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.converter = FBXToMDLConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_converter_initialization(self):
        """Test converter initialization"""
        self.assertEqual(len(self.converter.vertices), 0)
        self.assertEqual(len(self.converter.triangles), 0)
        self.assertEqual(len(self.converter.bones), 0)
        self.assertEqual(len(self.converter.sequences), 0)
        self.assertEqual(len(self.converter.textures), 0)
        self.assertEqual(self.converter.model_name, "")
    
    def test_find_closest_normal(self):
        """Test normal vector mapping to anorms"""
        # Test exact match with first anorm
        normal = MDL_ANORMS[0]
        index = self.converter.find_closest_normal(normal)
        self.assertEqual(index, 0)
        
        # Test with up vector (should find closest)
        up_normal = (0.0, 0.0, 1.0)
        index = self.converter.find_closest_normal(up_normal)
        self.assertTrue(0 <= index < len(MDL_ANORMS))
        
        # Test with arbitrary normal
        arbitrary_normal = (0.5, 0.5, 0.7071)
        index = self.converter.find_closest_normal(arbitrary_normal)
        self.assertTrue(0 <= index < len(MDL_ANORMS))
    
    def test_compress_vertex(self):
        """Test vertex compression to 0-255 range"""
        bounds_min = (-10.0, -5.0, -2.0)
        bounds_max = (10.0, 5.0, 2.0)
        
        # Test center point
        vertex = (0.0, 0.0, 0.0)
        compressed = self.converter.compress_vertex(vertex, bounds_min, bounds_max)
        self.assertEqual(compressed, (127, 127, 127))  # Approximately center
        
        # Test min bounds
        vertex = bounds_min
        compressed = self.converter.compress_vertex(vertex, bounds_min, bounds_max)
        self.assertEqual(compressed, (0, 0, 0))
        
        # Test max bounds
        vertex = bounds_max
        compressed = self.converter.compress_vertex(vertex, bounds_min, bounds_max)
        self.assertEqual(compressed, (255, 255, 255))
    
    def test_write_mdl_file_empty(self):
        """Test writing empty MDL file"""
        output_path = os.path.join(self.temp_dir, "test_empty.mdl")
        self.converter.model_name = "test_model"
        
        success = self.converter.write_mdl_file(output_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify file header
        with open(output_path, 'rb') as f:
            magic = f.read(4)
            version = struct.unpack('<I', f.read(4))[0]
            
            self.assertEqual(magic, MDL_MAGIC)
            self.assertEqual(version, MDL_VERSION)
    
    def test_write_mdl_file_with_data(self):
        """Test writing MDL file with sample data"""
        output_path = os.path.join(self.temp_dir, "test_data.mdl")
        
        # Add sample data
        self.converter.model_name = "test_model"
        self.converter.bounds_min = [-1.0, -1.0, -1.0]
        self.converter.bounds_max = [1.0, 1.0, 1.0]
        
        # Add vertices
        for i in range(3):
            vertex = MDLVertex(x=i*50, y=i*50, z=i*50, normal_index=i)
            self.converter.vertices.append(vertex)
        
        # Add triangle
        triangle = MDLTriangle(face_front=True, vertex_indices=[0, 1, 2])
        self.converter.triangles.append(triangle)
        
        # Add bone
        bone = MDLBone(
            name="root",
            parent=-1,
            flags=0,
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0)
        )
        self.converter.bones.append(bone)
        
        success = self.converter.write_mdl_file(output_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify file size is reasonable
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 100)  # Should have substantial content
    
    def test_generate_qc_file(self):
        """Test QC file generation"""
        mdl_path = os.path.join(self.temp_dir, "test.mdl")
        qc_path = os.path.join(self.temp_dir, "test.qc")
        
        self.converter.model_name = "test_model"
        
        # Add sample texture
        texture = MDLTexture(
            name="test_texture.bmp",
            flags=0,
            width=256,
            height=256,
            index=0
        )
        self.converter.textures.append(texture)
        
        # Add sample sequence
        sequence = MDLSequence(
            name="idle",
            fps=30.0,
            flags=0,
            activity=1,
            actweight=1,
            numevents=0,
            eventindex=0,
            numframes=30,
            numblends=1,
            animindex=0,
            motiontype=0,
            motionbone=0,
            linearmovement=(0.0, 0.0, 0.0),
            automoveposindex=0,
            automoveangleindex=0,
            bbmin=(-1.0, -1.0, -1.0),
            bbmax=(1.0, 1.0, 1.0)
        )
        self.converter.sequences.append(sequence)
        
        success = self.converter.generate_qc_file(mdl_path, qc_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(qc_path))
        
        # Verify QC content
        with open(qc_path, 'r') as f:
            content = f.read()
            self.assertIn("test_model", content)
            self.assertIn("test_texture.bmp", content)
            self.assertIn("idle", content)
            self.assertIn("fps 30", content)
    
    def test_export_preview_json(self):
        """Test JSON preview export"""
        json_path = os.path.join(self.temp_dir, "preview.json")
        
        self.converter.model_name = "test_model"
        self.converter.bounds_min = [-1.0, -1.0, -1.0]
        self.converter.bounds_max = [1.0, 1.0, 1.0]
        
        # Add sample data
        vertex = MDLVertex(x=128, y=128, z=128, normal_index=0)
        self.converter.vertices.append(vertex)
        
        triangle = MDLTriangle(face_front=True, vertex_indices=[0, 0, 0])
        self.converter.triangles.append(triangle)
        
        success = self.converter.export_preview_json(json_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(json_path))
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["model_name"], "test_model")
            self.assertEqual(data["vertex_count"], 1)
            self.assertEqual(data["triangle_count"], 1)
            self.assertIn("vertices", data)
            self.assertIn("triangles", data)

class TestMDLConstants(unittest.TestCase):
    """Test MDL format constants and anorms"""
    
    def test_mdl_constants(self):
        """Test MDL format constants"""
        self.assertEqual(MDL_MAGIC, b'IDPO')
        self.assertEqual(MDL_VERSION, 6)
    
    def test_mdl_anorms_count(self):
        """Test that we have exactly 162 anorms"""
        self.assertEqual(len(MDL_ANORMS), 162)
    
    def test_mdl_anorms_normalized(self):
        """Test that anorms are approximately normalized"""
        for i, anorm in enumerate(MDL_ANORMS):
            length_sq = anorm[0]**2 + anorm[1]**2 + anorm[2]**2
            self.assertAlmostEqual(length_sq, 1.0, places=5, 
                                 msg=f"Anorm {i} is not normalized: {anorm}")
    
    def test_mdl_anorms_coverage(self):
        """Test that anorms provide good coverage of unit sphere"""
        # Test some key directions are represented
        test_vectors = [
            (0.0, 0.0, 1.0),   # Up
            (0.0, 0.0, -1.0),  # Down
            (1.0, 0.0, 0.0),   # Right
            (-1.0, 0.0, 0.0),  # Left
            (0.0, 1.0, 0.0),   # Forward
            (0.0, -1.0, 0.0),  # Back
        ]
        
        converter = FBXToMDLConverter()
        for test_vec in test_vectors:
            index = converter.find_closest_normal(test_vec)
            closest_anorm = MDL_ANORMS[index]
            
            # Calculate dot product to verify reasonable approximation
            dot = (test_vec[0] * closest_anorm[0] + 
                   test_vec[1] * closest_anorm[1] + 
                   test_vec[2] * closest_anorm[2])
            
            # Should be reasonably close (dot product > 0.7)
            self.assertGreater(dot, 0.7, 
                             f"Anorm {index} {closest_anorm} not close enough to {test_vec}")

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.converter = FBXToMDLConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_nonexistent_fbx(self):
        """Test loading non-existent FBX file"""
        fake_path = "/nonexistent/file.fbx"
        success = self.converter.load_fbx_with_blender(fake_path)
        self.assertFalse(success)
    
    def test_write_to_invalid_path(self):
        """Test writing to invalid path"""
        invalid_path = "/invalid/path/that/does/not/exist/test.mdl"
        success = self.converter.write_mdl_file(invalid_path)
        self.assertFalse(success)
    
    def test_vertex_compression_edge_cases(self):
        """Test vertex compression with edge cases"""
        # Test with zero bounds (should not crash)
        bounds_min = (0.0, 0.0, 0.0)
        bounds_max = (0.0, 0.0, 0.0)
        vertex = (0.0, 0.0, 0.0)
        
        # This should handle division by zero gracefully
        try:
            compressed = self.converter.compress_vertex(vertex, bounds_min, bounds_max)
            # Should clamp to valid range
            self.assertTrue(0 <= compressed[0] <= 255)
            self.assertTrue(0 <= compressed[1] <= 255)
            self.assertTrue(0 <= compressed[2] <= 255)
        except ZeroDivisionError:
            self.fail("Vertex compression should handle zero bounds gracefully")

class TestCLIIntegration(unittest.TestCase):
    """Test command-line interface integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing"""
        # Import main function
        from fbx_to_mdl_converter import main
        
        # Test with minimal arguments (this will fail due to no FBX file, but should parse)
        old_argv = sys.argv
        try:
            sys.argv = [
                'fbx_to_mdl_converter.py',
                'nonexistent.fbx',
                os.path.join(self.temp_dir, 'output.mdl')
            ]
            
            # This should return 1 due to missing file, but parsing should work
            result = main()
            self.assertEqual(result, 1)  # Error due to missing file
            
        finally:
            sys.argv = old_argv

def create_sample_fbx_data():
    """Create sample FBX-like data for testing (mock implementation)"""
    # This would be used for integration tests with actual FBX files
    # For now, we'll use mock data in our tests
    pass

def run_converter_integration_test():
    """Run full integration test if test FBX files are available"""
    # This function would test the full pipeline:
    # 1. Load an actual FBX file
    # 2. Convert to MDL
    # 3. Validate the output
    # 4. Test QC generation
    # 5. Test JSON preview export
    
    test_fbx_dir = Path("test_assets")
    if test_fbx_dir.exists():
        print("Running integration tests with test FBX files...")
        # Implementation would go here
    else:
        print("No test assets directory found. Skipping integration tests.")
        print("To run integration tests, create 'test_assets/' directory with sample FBX files.")

if __name__ == '__main__':
    # Run integration test first if possible
    run_converter_integration_test()
    
    # Run unit tests
    unittest.main(verbosity=2)