import bpy
import sys
import os

# Get arguments passed from the MCP server
argv = sys.argv
argv = argv[argv.index("--") + 1:] # Extract args after "--"
input_path = argv[0]
output_path = argv[1]

# Clear existing default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import the raw AI-generated OBJ
bpy.ops.import_scene.obj(filepath=input_path)

# Select the imported object
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# ROBLOX OPTIMIZATION: Decimate to under 4,000 Triangles
modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
modifier.ratio = 1.0

# Calculate the ratio needed to hit ~3800 tris (leaving a buffer for Roblox's 4k limit)
current_tris = len(obj.data.polygons)
if current_tris > 3800:
    modifier.ratio = 3800 / current_tris
    
bpy.ops.object.modifier_apply(modifier="Decimate")

# Smooth shading (Roblox prefers this for low-poly models)
bpy.ops.object.shade_smooth()

# Export as Roblox-ready FBX
bpy.ops.export_scene.fbx(
    filepath=output_path,
    use_selection=True,
    mesh_smooth_type='FACE',
    path_mode='COPY',
    embed_textures=True
)

print(f"Successfully optimized and exported to {output_path}")