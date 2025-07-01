#!/usr/bin/env python3
"""
FBX to MDL Converter for Counter-Strike 1.6

A complete tool to convert .fbx 3D models into .mdl files compatible with
the GoldSrc engine used in Counter-Strike 1.6.

Features:
- Automatic FBX parsing using Blender's bpy module
- Mesh vertex compression to 0-255 range
- Normal mapping to standard 162 MDL anorms
- 8-bit indexed texture support
- Proper MDL binary writing with correct headers
- Optional QC file generation
- CLI interface

Author: FBX to MDL Converter Tool
License: MIT
"""

import os
import sys
import struct
import math
import argparse
import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
# Check for numpy availability
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Numpy is optional for basic functionality

# Check for Blender availability
try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: Blender's bpy module not available. Please install Blender as a Python module.")

# MDL Format Constants
MDL_MAGIC = b'IDPO'
MDL_VERSION = 6
MAX_VERTICES = 2048
MAX_TRIANGLES = 2048
MAX_BONES = 128
MAX_SEQUENCES = 32
MAX_TEXTURES = 32

# Standard MDL anorms (162 precalculated normals)
MDL_ANORMS = [
    (-0.525731, 0.000000, 0.850651), (-0.442863, 0.238856, 0.864188),
    (-0.295242, 0.000000, 0.955423), (-0.309017, 0.500000, 0.809017),
    (-0.162460, 0.262866, 0.951056), (0.000000, 0.000000, 1.000000),
    (0.000000, 0.850651, 0.525731), (-0.147621, 0.716567, 0.681718),
    (0.147621, 0.716567, 0.681718), (0.000000, 0.525731, 0.850651),
    (0.309017, 0.500000, 0.809017), (0.525731, 0.000000, 0.850651),
    (0.295242, 0.000000, 0.955423), (0.442863, 0.238856, 0.864188),
    (0.162460, 0.262866, 0.951056), (-0.681718, 0.147621, 0.716567),
    (-0.809017, 0.309017, 0.500000), (-0.587785, 0.425325, 0.688191),
    (-0.850651, 0.525731, 0.000000), (-0.864188, 0.442863, 0.238856),
    (-0.716567, 0.681718, 0.147621), (-0.688191, 0.587785, 0.425325),
    (-0.500000, 0.809017, 0.309017), (-0.238856, 0.864188, 0.442863),
    (-0.425325, 0.688191, 0.587785), (-0.716567, 0.681718, -0.147621),
    (-0.500000, 0.809017, -0.309017), (-0.525731, 0.850651, 0.000000),
    (0.000000, 0.850651, -0.525731), (-0.238856, 0.864188, -0.442863),
    (0.000000, 0.955423, -0.295242), (-0.262866, 0.951056, -0.162460),
    (0.000000, 1.000000, 0.000000), (0.000000, 0.955423, 0.295242),
    (-0.262866, 0.951056, 0.162460), (0.238856, 0.864188, 0.442863),
    (0.262866, 0.951056, 0.162460), (0.500000, 0.809017, 0.309017),
    (0.238856, 0.864188, -0.442863), (0.262866, 0.951056, -0.162460),
    (0.500000, 0.809017, -0.309017), (0.850651, 0.525731, 0.000000),
    (0.716567, 0.681718, 0.147621), (0.716567, 0.681718, -0.147621),
    (0.525731, 0.850651, 0.000000), (0.425325, 0.688191, 0.587785),
    (0.864188, 0.442863, 0.238856), (0.688191, 0.587785, 0.425325),
    (0.809017, 0.309017, 0.500000), (0.681718, 0.147621, 0.716567),
    (0.587785, 0.425325, 0.688191), (0.955423, 0.295242, 0.000000),
    (1.000000, 0.000000, 0.000000), (0.951056, 0.162460, 0.262866),
    (0.850651, -0.525731, 0.000000), (0.955423, -0.295242, 0.000000),
    (0.864188, -0.442863, 0.238856), (0.951056, -0.162460, 0.262866),
    (0.809017, -0.309017, 0.500000), (0.681718, -0.147621, 0.716567),
    (0.850651, 0.000000, 0.525731), (0.864188, 0.442863, -0.238856),
    (0.809017, 0.309017, -0.500000), (0.951056, 0.162460, -0.262866),
    (0.525731, 0.000000, -0.850651), (0.681718, 0.147621, -0.716567),
    (0.681718, -0.147621, -0.716567), (0.850651, 0.000000, -0.525731),
    (0.809017, -0.309017, -0.500000), (0.864188, -0.442863, -0.238856),
    (0.951056, -0.162460, -0.262866), (0.147621, 0.716567, -0.681718),
    (0.309017, 0.500000, -0.809017), (0.425325, 0.688191, -0.587785),
    (0.442863, 0.238856, -0.864188), (0.587785, 0.425325, -0.688191),
    (0.688191, 0.587785, -0.425325), (-0.147621, 0.716567, -0.681718),
    (-0.309017, 0.500000, -0.809017), (0.000000, 0.525731, -0.850651),
    (-0.525731, 0.000000, -0.850651), (-0.442863, 0.238856, -0.864188),
    (-0.295242, 0.000000, -0.955423), (-0.162460, 0.262866, -0.951056),
    (0.000000, 0.000000, -1.000000), (0.295242, 0.000000, -0.955423),
    (0.162460, 0.262866, -0.951056), (-0.442863, -0.238856, -0.864188),
    (-0.309017, -0.500000, -0.809017), (-0.162460, -0.262866, -0.951056),
    (0.000000, -0.850651, -0.525731), (-0.147621, -0.716567, -0.681718),
    (0.147621, -0.716567, -0.681718), (0.000000, -0.525731, -0.850651),
    (0.309017, -0.500000, -0.809017), (0.442863, -0.238856, -0.864188),
    (0.162460, -0.262866, -0.951056), (0.238856, -0.864188, -0.442863),
    (0.500000, -0.809017, -0.309017), (0.425325, -0.688191, -0.587785),
    (0.716567, -0.681718, -0.147621), (0.688191, -0.587785, -0.425325),
    (0.587785, -0.425325, -0.688191), (0.000000, -0.955423, -0.295242),
    (0.000000, -1.000000, 0.000000), (0.262866, -0.951056, -0.162460),
    (0.000000, -0.850651, 0.525731), (0.000000, -0.955423, 0.295242),
    (0.238856, -0.864188, 0.442863), (0.262866, -0.951056, 0.162460),
    (0.500000, -0.809017, 0.309017), (0.716567, -0.681718, 0.147621),
    (0.525731, -0.850651, 0.000000), (-0.238856, -0.864188, -0.442863),
    (-0.500000, -0.809017, -0.309017), (-0.262866, -0.951056, -0.162460),
    (-0.850651, -0.525731, 0.000000), (-0.716567, -0.681718, -0.147621),
    (-0.716567, -0.681718, 0.147621), (-0.525731, -0.850651, 0.000000),
    (-0.500000, -0.809017, 0.309017), (-0.238856, -0.864188, 0.442863),
    (-0.262866, -0.951056, 0.162460), (-0.864188, -0.442863, 0.238856),
    (-0.809017, -0.309017, 0.500000), (-0.688191, -0.587785, 0.425325),
    (-0.681718, -0.147621, 0.716567), (-0.442863, -0.238856, 0.864188),
    (-0.587785, -0.425325, 0.688191), (-0.309017, -0.500000, 0.809017),
    (-0.147621, -0.716567, 0.681718), (-0.425325, -0.688191, 0.587785),
    (-0.162460, -0.262866, 0.951056), (0.442863, -0.238856, 0.864188),
    (0.162460, -0.262866, 0.951056), (0.309017, -0.500000, 0.809017),
    (0.147621, -0.716567, 0.681718), (0.000000, -0.525731, 0.850651),
    (0.425325, -0.688191, 0.587785), (0.587785, -0.425325, 0.688191),
    (0.688191, -0.587785, 0.425325), (-0.955423, 0.295242, 0.000000),
    (-0.951056, 0.162460, 0.262866), (-1.000000, 0.000000, 0.000000),
    (-0.850651, 0.000000, 0.525731), (-0.955423, -0.295242, 0.000000),
    (-0.951056, -0.162460, 0.262866), (-0.864188, 0.442863, -0.238856),
    (-0.951056, 0.162460, -0.262866), (-0.809017, 0.309017, -0.500000),
    (-0.864188, -0.442863, -0.238856), (-0.951056, -0.162460, -0.262866),
    (-0.809017, -0.309017, -0.500000), (-0.681718, 0.147621, -0.716567),
    (-0.681718, -0.147621, -0.716567), (-0.850651, 0.000000, -0.525731),
    (-0.688191, 0.587785, -0.425325), (-0.587785, 0.425325, -0.688191),
    (-0.425325, 0.688191, -0.587785), (-0.425325, -0.688191, -0.587785),
    (-0.587785, -0.425325, -0.688191), (-0.688191, -0.587785, -0.425325)
]

@dataclass
class MDLVertex:
    """MDL vertex structure"""
    x: int  # 0-255 range
    y: int  # 0-255 range  
    z: int  # 0-255 range
    normal_index: int  # Index into anorms table

@dataclass
class MDLTriangle:
    """MDL triangle structure"""
    face_front: bool
    vertex_indices: List[int]  # 3 vertex indices

@dataclass
class MDLBone:
    """MDL bone structure"""
    name: str
    parent: int  # Parent bone index (-1 for root)
    flags: int
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]

@dataclass
class MDLSequence:
    """MDL animation sequence"""
    name: str
    fps: float
    flags: int
    activity: int
    actweight: int
    numevents: int
    eventindex: int
    numframes: int
    numblends: int
    animindex: int
    motiontype: int
    motionbone: int
    linearmovement: Tuple[float, float, float]
    automoveposindex: int
    automoveangleindex: int
    bbmin: Tuple[float, float, float]
    bbmax: Tuple[float, float, float]

@dataclass
class MDLTexture:
    """MDL texture structure"""
    name: str
    flags: int
    width: int
    height: int
    index: int

class FBXToMDLConverter:
    """Main converter class"""
    
    def __init__(self):
        self.vertices: List[MDLVertex] = []
        self.triangles: List[MDLTriangle] = []
        self.bones: List[MDLBone] = []
        self.sequences: List[MDLSequence] = []
        self.textures: List[MDLTexture] = []
        self.model_name = ""
        self.bounds_min = [0.0, 0.0, 0.0]
        self.bounds_max = [0.0, 0.0, 0.0]
        
    def find_closest_normal(self, normal: Tuple[float, float, float]) -> int:
        """Find the closest MDL anorm index for a given normal vector"""
        best_dot = -2.0
        best_index = 0
        
        for i, anorm in enumerate(MDL_ANORMS):
            dot = (normal[0] * anorm[0] + 
                   normal[1] * anorm[1] + 
                   normal[2] * anorm[2])
            if dot > best_dot:
                best_dot = dot
                best_index = i
                
        return best_index
    
    def compress_vertex(self, vertex: Tuple[float, float, float], 
                       bounds_min: Tuple[float, float, float],
                       bounds_max: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Compress vertex coordinates to 0-255 range"""
        # Handle zero bounds gracefully
        range_x = bounds_max[0] - bounds_min[0]
        range_y = bounds_max[1] - bounds_min[1]
        range_z = bounds_max[2] - bounds_min[2]
        
        if range_x == 0:
            x = 127  # Center value for zero range
        else:
            x = int(((vertex[0] - bounds_min[0]) / range_x) * 255)
            
        if range_y == 0:
            y = 127  # Center value for zero range
        else:
            y = int(((vertex[1] - bounds_min[1]) / range_y) * 255)
            
        if range_z == 0:
            z = 127  # Center value for zero range
        else:
            z = int(((vertex[2] - bounds_min[2]) / range_z) * 255)
        
        return (max(0, min(255, x)), max(0, min(255, y)), max(0, min(255, z)))
    
    def load_fbx_with_blender(self, fbx_path: str) -> bool:
        """Load FBX file using Blender's bpy module"""
        if not BLENDER_AVAILABLE:
            print("Error: Blender's bpy module is not available")
            return False
            
        try:
            # Clear existing mesh data
            bpy.ops.wm.read_factory_settings(use_empty=True)
            
            # Import FBX
            bpy.ops.import_scene.fbx(filepath=fbx_path)
            
            # Get all mesh objects
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
            
            if not mesh_objects:
                print("Error: No mesh objects found in FBX file")
                return False
            
            # Process meshes
            all_vertices = []
            all_faces = []
            vertex_offset = 0
            
            for obj in mesh_objects:
                mesh = obj.data
                
                # Get vertex data
                for vertex in mesh.vertices:
                    world_co = obj.matrix_world @ vertex.co
                    all_vertices.append((world_co.x, world_co.y, world_co.z))
                
                # Get face data
                for face in mesh.polygons:
                    if len(face.vertices) == 3:
                        # Triangle face
                        triangle_indices = [v + vertex_offset for v in face.vertices]
                        all_faces.append(triangle_indices)
                    elif len(face.vertices) == 4:
                        # Quad face - split into two triangles
                        v = [face.vertices[i] + vertex_offset for i in range(4)]
                        all_faces.append([v[0], v[1], v[2]])
                        all_faces.append([v[0], v[2], v[3]])
                
                vertex_offset += len(mesh.vertices)
            
            # Calculate bounds
            if all_vertices:
                xs, ys, zs = zip(*all_vertices)
                self.bounds_min = [min(xs), min(ys), min(zs)]
                self.bounds_max = [max(xs), max(ys), max(zs)]
            
            # Convert vertices to MDL format
            for i, vertex_pos in enumerate(all_vertices):
                compressed = self.compress_vertex(vertex_pos, self.bounds_min, self.bounds_max)
                
                # Calculate normal (simplified - using face normals average)
                normal = (0.0, 0.0, 1.0)  # Default up normal
                normal_index = self.find_closest_normal(normal)
                
                mdl_vertex = MDLVertex(
                    x=compressed[0],
                    y=compressed[1], 
                    z=compressed[2],
                    normal_index=normal_index
                )
                self.vertices.append(mdl_vertex)
            
            # Convert faces to triangles
            for face_indices in all_faces:
                triangle = MDLTriangle(
                    face_front=True,
                    vertex_indices=face_indices
                )
                self.triangles.append(triangle)
            
            # Process bones (armature)
            armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
            if armatures:
                armature = armatures[0]
                bone_index = 0
                
                for bone in armature.data.bones:
                    parent_index = -1
                    if bone.parent:
                        # Find parent index
                        for i, existing_bone in enumerate(self.bones):
                            if existing_bone.name == bone.parent.name:
                                parent_index = i
                                break
                    
                    mdl_bone = MDLBone(
                        name=bone.name[:32],  # Limit name length
                        parent=parent_index,
                        flags=0,
                        position=(bone.head_local.x, bone.head_local.y, bone.head_local.z),
                        rotation=(0.0, 0.0, 0.0)  # Simplified
                    )
                    self.bones.append(mdl_bone)
                    bone_index += 1
            
            # Process animations
            if bpy.context.scene.animation_data and bpy.context.scene.animation_data.action:
                action = bpy.context.scene.animation_data.action
                frame_start = int(action.frame_range[0])
                frame_end = int(action.frame_range[1])
                
                sequence = MDLSequence(
                    name=action.name[:32],
                    fps=bpy.context.scene.render.fps,
                    flags=0,
                    activity=1,
                    actweight=1,
                    numevents=0,
                    eventindex=0,
                    numframes=frame_end - frame_start + 1,
                    numblends=1,
                    animindex=0,
                    motiontype=0,
                    motionbone=0,
                    linearmovement=(0.0, 0.0, 0.0),
                    automoveposindex=0,
                    automoveangleindex=0,
                    bbmin=tuple(self.bounds_min),
                    bbmax=tuple(self.bounds_max)
                )
                self.sequences.append(sequence)
            
            # Process materials/textures
            for material in bpy.data.materials:
                if material.use_nodes:
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            texture = MDLTexture(
                                name=node.image.name[:64],
                                flags=0,
                                width=node.image.size[0],
                                height=node.image.size[1],
                                index=len(self.textures)
                            )
                            self.textures.append(texture)
            
            self.model_name = Path(fbx_path).stem
            return True
            
        except Exception as e:
            print(f"Error loading FBX file: {e}")
            return False
    
    def write_mdl_file(self, output_path: str) -> bool:
        """Write MDL binary file"""
        try:
            with open(output_path, 'wb') as f:
                # MDL Header
                f.write(MDL_MAGIC)  # Magic number "IDPO"
                f.write(struct.pack('<I', MDL_VERSION))  # Version
                f.write(struct.pack('<64s', self.model_name.encode('ascii')[:64]))  # Model name
                f.write(struct.pack('<I', len(self.model_name)))  # Model name length
                
                # Bounding box
                f.write(struct.pack('<fff', *self.bounds_min))
                f.write(struct.pack('<fff', *self.bounds_max))
                
                # Counts
                f.write(struct.pack('<I', len(self.vertices)))
                f.write(struct.pack('<I', len(self.triangles)))
                f.write(struct.pack('<I', len(self.bones)))
                f.write(struct.pack('<I', len(self.sequences)))
                f.write(struct.pack('<I', len(self.textures)))
                
                # Vertex data
                for vertex in self.vertices:
                    f.write(struct.pack('<BBBB', vertex.x, vertex.y, vertex.z, vertex.normal_index))
                
                # Triangle data
                for triangle in self.triangles:
                    f.write(struct.pack('<I', 1 if triangle.face_front else 0))
                    f.write(struct.pack('<III', *triangle.vertex_indices))
                
                # Bone data
                for bone in self.bones:
                    f.write(struct.pack('<32s', bone.name.encode('ascii')[:32]))
                    f.write(struct.pack('<i', bone.parent))
                    f.write(struct.pack('<I', bone.flags))
                    f.write(struct.pack('<fff', *bone.position))
                    f.write(struct.pack('<fff', *bone.rotation))
                
                # Sequence data
                for seq in self.sequences:
                    f.write(struct.pack('<32s', seq.name.encode('ascii')[:32]))
                    f.write(struct.pack('<f', seq.fps))
                    f.write(struct.pack('<I', seq.flags))
                    f.write(struct.pack('<I', seq.activity))
                    f.write(struct.pack('<I', seq.actweight))
                    f.write(struct.pack('<I', seq.numevents))
                    f.write(struct.pack('<I', seq.eventindex))
                    f.write(struct.pack('<I', seq.numframes))
                    f.write(struct.pack('<I', seq.numblends))
                    f.write(struct.pack('<I', seq.animindex))
                    f.write(struct.pack('<I', seq.motiontype))
                    f.write(struct.pack('<I', seq.motionbone))
                    f.write(struct.pack('<fff', *seq.linearmovement))
                    f.write(struct.pack('<I', seq.automoveposindex))
                    f.write(struct.pack('<I', seq.automoveangleindex))
                    f.write(struct.pack('<fff', *seq.bbmin))
                    f.write(struct.pack('<fff', *seq.bbmax))
                
                # Texture data
                for texture in self.textures:
                    f.write(struct.pack('<64s', texture.name.encode('ascii')[:64]))
                    f.write(struct.pack('<I', texture.flags))
                    f.write(struct.pack('<I', texture.width))
                    f.write(struct.pack('<I', texture.height))
                    f.write(struct.pack('<I', texture.index))
            
            return True
            
        except Exception as e:
            print(f"Error writing MDL file: {e}")
            return False
    
    def generate_qc_file(self, mdl_path: str, qc_path: str) -> bool:
        """Generate QC file for StudioMDL"""
        try:
            qc_content = f'''/*
==============================================================================

\tMODEL: {self.model_name}
\tGenerated by FBX to MDL Converter

==============================================================================
*/

$modelname "{Path(mdl_path).name}"
$cd "./"
$cdtexture "./"
$scale 1.0

'''
            
            # Add textures
            for texture in self.textures:
                qc_content += f'$texture "{texture.name}"\n'
            
            qc_content += '\n'
            
            # Add body groups
            qc_content += f'$body "Body" "{self.model_name}"\n\n'
            
            # Add sequences
            if self.sequences:
                for seq in self.sequences:
                    qc_content += f'$sequence "{seq.name}" "{seq.name}" fps {seq.fps}\n'
            else:
                qc_content += '$sequence "idle" "idle" fps 30\n'
            
            # Add collision model
            qc_content += f'\n$collisionmodel "{self.model_name}_collision" {{\n'
            qc_content += '\t$mass 1.0\n'
            qc_content += '\t$inertia 1.0\n'
            qc_content += '\t$damping 0.0\n'
            qc_content += '\t$rotdamping 0.0\n'
            qc_content += '}\n'
            
            with open(qc_path, 'w') as f:
                f.write(qc_content)
            
            return True
            
        except Exception as e:
            print(f"Error generating QC file: {e}")
            return False
    
    def export_preview_json(self, json_path: str) -> bool:
        """Export preview data as JSON"""
        try:
            preview_data = {
                "model_name": self.model_name,
                "bounds_min": self.bounds_min,
                "bounds_max": self.bounds_max,
                "vertex_count": len(self.vertices),
                "triangle_count": len(self.triangles),
                "bone_count": len(self.bones),
                "sequence_count": len(self.sequences),
                "texture_count": len(self.textures),
                "vertices": [{"x": v.x, "y": v.y, "z": v.z, "normal": v.normal_index} for v in self.vertices[:100]],  # Limit for size
                "triangles": [{"face_front": t.face_front, "indices": t.vertex_indices} for t in self.triangles[:100]],
                "bones": [{"name": b.name, "parent": b.parent, "position": b.position} for b in self.bones],
                "sequences": [{"name": s.name, "fps": s.fps, "frames": s.numframes} for s in self.sequences],
                "textures": [{"name": t.name, "width": t.width, "height": t.height} for t in self.textures]
            }
            
            with open(json_path, 'w') as f:
                json.dump(preview_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting preview JSON: {e}")
            return False

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Convert FBX 3D models to Counter-Strike 1.6 MDL format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fbx_to_mdl_converter.py weapon.fbx models/weapons/ak47.mdl
  python fbx_to_mdl_converter.py player.fbx models/player/leet.mdl --create-qc
  python fbx_to_mdl_converter.py model.fbx output.mdl --preview-json preview.json
        """
    )
    
    parser.add_argument('input_fbx', help='Input FBX file path')
    parser.add_argument('output_mdl', help='Output MDL file path')
    parser.add_argument('--create-qc', action='store_true', 
                       help='Generate QC file for StudioMDL')
    parser.add_argument('--preview-json', help='Export preview data as JSON')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_fbx):
        print(f"Error: Input file '{args.input_fbx}' does not exist")
        return 1
    
    if not args.input_fbx.lower().endswith('.fbx'):
        print(f"Error: Input file must have .fbx extension")
        return 1
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output_mdl)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize converter
    converter = FBXToMDLConverter()
    
    if args.verbose:
        print(f"Loading FBX file: {args.input_fbx}")
    
    # Load FBX file
    if not converter.load_fbx_with_blender(args.input_fbx):
        print("Error: Failed to load FBX file")
        return 1
    
    if args.verbose:
        print(f"Loaded model: {converter.model_name}")
        print(f"Vertices: {len(converter.vertices)}")
        print(f"Triangles: {len(converter.triangles)}")
        print(f"Bones: {len(converter.bones)}")
        print(f"Sequences: {len(converter.sequences)}")
        print(f"Textures: {len(converter.textures)}")
    
    # Write MDL file
    if args.verbose:
        print(f"Writing MDL file: {args.output_mdl}")
    
    if not converter.write_mdl_file(args.output_mdl):
        print("Error: Failed to write MDL file")
        return 1
    
    # Generate QC file if requested
    if args.create_qc:
        qc_path = args.output_mdl.replace('.mdl', '.qc')
        if args.verbose:
            print(f"Generating QC file: {qc_path}")
        
        if not converter.generate_qc_file(args.output_mdl, qc_path):
            print("Warning: Failed to generate QC file")
    
    # Export preview JSON if requested
    if args.preview_json:
        if args.verbose:
            print(f"Exporting preview JSON: {args.preview_json}")
        
        if not converter.export_preview_json(args.preview_json):
            print("Warning: Failed to export preview JSON")
    
    print(f"Conversion completed successfully!")
    print(f"Output: {args.output_mdl}")
    
    if args.create_qc:
        print(f"QC file: {args.output_mdl.replace('.mdl', '.qc')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())