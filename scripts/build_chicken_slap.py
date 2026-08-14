"""Build a blocky chicken-slap weapon and export Roblox-ready FBX/OBJ."""

from __future__ import annotations

import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

# Palette tiles in the atlas (u0, v0, u1, v1)
YELLOW = (0.02, 0.02, 0.48, 0.48)
RED = (0.52, 0.02, 0.98, 0.48)
ORANGE = (0.02, 0.52, 0.48, 0.98)
BLACK = (0.52, 0.52, 0.98, 0.98)

COLORS = {
    "yellow": (0.96, 0.75, 0.16, 1.0),
    "red": (0.86, 0.18, 0.16, 1.0),
    "orange": (0.91, 0.52, 0.16, 1.0),
    "black": (0.07, 0.07, 0.08, 1.0),
}


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def map_uvs_to_tile(obj: bpy.types.Object, tile: tuple[float, float, float, float]) -> None:
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    u0, v0, u1, v1 = tile
    for item in mesh.uv_layers.active.data:
        item.uv.x = u0 + item.uv.x * (u1 - u0)
        item.uv.y = v0 + item.uv.y * (v1 - v0)


def add_box(
    name: str,
    location: tuple[float, float, float],
    size: tuple[float, float, float],
    tile: tuple[float, float, float, float],
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    map_uvs_to_tile(obj, tile)
    return obj


def add_sphere(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    tile: tuple[float, float, float, float],
    scale: tuple[float, float, float] | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    if scale:
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    map_uvs_to_tile(obj, tile)
    return obj


def make_atlas(path: Path) -> bpy.types.Image:
    size = 64
    img = bpy.data.images.new("chicken_slap_atlas", width=size, height=size, alpha=True)
    pixels = [0.0] * (size * size * 4)
    regions = [
        (0, 0, size // 2, size // 2, COLORS["yellow"]),
        (size // 2, 0, size, size // 2, COLORS["red"]),
        (0, size // 2, size // 2, size, COLORS["orange"]),
        (size // 2, size // 2, size, size, COLORS["black"]),
    ]
    for x0, y0, x1, y1, color in regions:
        r, g, b, a = color
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * size + x) * 4
                pixels[i : i + 4] = [r, g, b, a]
    img.pixels = pixels
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    return img


def assign_atlas_material(obj: bpy.types.Object, image: bpy.types.Image) -> None:
    mat = bpy.data.materials.new("ChickenSlap")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    obj.data.materials.append(mat)


def join_objects(objects: list[bpy.types.Object], name: str) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    return joined


def build_weapon() -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []

    def box(name, loc, size, tile, rot=(0.0, 0.0, 0.0)):
        parts.append(add_box(name, loc, size, tile, rot))

    def sphere(name, loc, radius, tile, scale=None):
        parts.append(add_sphere(name, loc, radius, tile, scale))

    # Body shaft (extends +X toward the head). Origin will be the grip.
    box("Body", (1.25, 0.0, 0.22), (2.9, 0.72, 0.68), YELLOW)

    # Head cube
    box("Head", (3.42, 0.0, 0.48), (1.92, 1.92, 1.92), YELLOW)

    # Beak / muzzle
    box("Beak", (4.62, 0.0, 0.38), (1.12, 0.52, 0.46), ORANGE)
    box("MuzzleHole", (5.14, 0.0, 0.38), (0.20, 0.26, 0.22), BLACK)

    # Eyes on the front face of the head
    sphere("EyeL", (4.36, 0.48, 0.95), 0.16, BLACK)
    sphere("EyeR", (4.36, -0.48, 0.95), 0.16, BLACK)

    # Comb: four stepped red blocks on top of the head (back -> front)
    box("Comb1", (2.72, 0.0, 1.62), (0.36, 0.70, 0.48), RED)
    box("Comb2", (3.10, 0.0, 1.78), (0.36, 0.78, 0.82), RED)
    box("Comb3", (3.48, 0.0, 1.88), (0.36, 0.86, 1.02), RED)
    box("Comb4", (3.86, 0.0, 1.70), (0.36, 0.74, 0.66), RED)

    # Wattles hanging under the beak
    sphere("WattleL", (4.28, 0.22, -0.28), 0.18, RED, scale=(0.90, 0.80, 1.70))
    sphere("WattleR", (4.28, -0.22, -0.28), 0.18, RED, scale=(0.90, 0.80, 1.70))

    # Wings (both sides), pixel-stepped
    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        y = 0.48 * side
        box(f"WingBase{suffix}", (1.45, y, 0.28), (1.15, 0.14, 0.58), YELLOW)
        box(f"WingMid{suffix}", (1.05, y * 1.08, 0.16), (0.55, 0.14, 0.38), YELLOW)
        box(f"WingTip{suffix}", (0.72, y * 1.14, 0.04), (0.32, 0.14, 0.22), YELLOW)

    # Tail feathers at the rear of the shaft
    box("Tail1", (0.02, 0.0, 0.72), (0.28, 0.50, 0.42), RED)
    box("Tail2", (-0.22, 0.0, 0.82), (0.26, 0.42, 0.62), RED)
    box("Tail3", (-0.46, 0.0, 0.68), (0.24, 0.34, 0.34), RED)

    # Black grip with horizontal ridges
    box("Grip", (0.02, 0.0, -0.72), (0.38, 0.42, 1.18), BLACK)
    for i, z in enumerate((-0.30, -0.52, -0.74, -0.96, -1.18)):
        box(f"GripRidge{i}", (0.02, 0.0, z), (0.42, 0.48, 0.08), BLACK)

    # Yellow trigger-guard frame around the grip
    box("GuardRear", (-0.28, 0.0, -0.78), (0.14, 0.46, 1.28), YELLOW)
    box("GuardBottom", (0.06, 0.0, -1.40), (0.82, 0.46, 0.14), YELLOW)
    box("GuardFront", (0.40, 0.0, -0.95), (0.14, 0.46, 0.78), YELLOW)

    return parts


def set_origin_to_grip(obj: bpy.types.Object) -> None:
    # Grip center is near world origin already; snap origin to (0,0,-0.72)
    bpy.context.scene.cursor.location = Vector((0.02, 0.0, -0.72))
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    obj.location = (0.0, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)


def bevel(obj: bpy.types.Object) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = 0.028
    mod.segments = 1
    mod.limit_method = "ANGLE"
    mod.angle_limit = 0.7
    bpy.ops.object.modifier_apply(modifier="Bevel")


def export_files(obj: bpy.types.Object) -> tuple[Path, Path]:
    obj_path = OUT / "chicken_slap.obj"
    fbx_path = OUT / "chicken_slap_roblox.fbx"

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.wm.obj_export(
        filepath=str(obj_path),
        export_selected_objects=True,
        export_materials=True,
        export_uv=True,
        export_pbr_extensions=False,
    )
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        add_leaf_bones=False,
        axis_forward="-Z",
        axis_up="Y",
        object_types={"MESH"},
    )
    return obj_path, fbx_path


def render_preview(obj: bpy.types.Object) -> Path:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.filepath = str(OUT / "chicken_slap_preview.png")
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.82, 0.88, 0.95, 1.0)
    bg.inputs[1].default_value = 1.0

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    target = Vector((2.4, 0.0, 0.35))
    cam.location = (7.4, -6.2, 2.6)
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

    light_data = bpy.data.lights.new("Key", type="AREA")
    light_data.energy = 400
    light_data.size = 4
    light = bpy.data.objects.new("Key", light_data)
    scene.collection.objects.link(light)
    light.location = (3.0, -4.0, 6.0)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 120
    fill_data.size = 5
    fill = bpy.data.objects.new("Fill", fill_data)
    scene.collection.objects.link(fill)
    fill.location = (-3.0, 4.0, 4.0)

    bpy.ops.render.render(write_still=True)
    return Path(scene.render.filepath)


def triangle_count(obj: bpy.types.Object) -> int:
    mesh = obj.data
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)


def main() -> None:
    reset_scene()
    atlas = make_atlas(OUT / "chicken_slap_atlas.png")
    parts = build_weapon()
    weapon = join_objects(parts, "ChickenSlap")
    assign_atlas_material(weapon, atlas)
    bpy.context.view_layer.objects.active = weapon
    weapon.select_set(True)
    bevel(weapon)
    set_origin_to_grip(weapon)

    tris = triangle_count(weapon)
    print(f"Triangle count: {tris}")
    if tris > 3800:
        raise SystemExit(f"Too many triangles for Roblox: {tris}")

    obj_path, fbx_path = export_files(weapon)
    preview = render_preview(weapon)
    print(f"OBJ: {obj_path}")
    print(f"FBX: {fbx_path}")
    print(f"Preview: {preview}")
    print(f"Atlas: {OUT / 'chicken_slap_atlas.png'}")


if __name__ == "__main__":
    # bpy as a module ignores extra CLI flags; keep this import-safe.
    os.chdir(ROOT)
    main()
