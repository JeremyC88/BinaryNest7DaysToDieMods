"""
Builds the three carrot growth-stage models for Adapting Farming, exports them
for Unity and renders preview images.

Run headless from the repo root:
    blender --background --factory-startup --python art/farming/carrot/build_carrot.py

Outputs:
    carrot.blend                 source scene (next to this script)
    previews/*.png               preview renders (next to this script)
    unity/BinaryNestModAssets/Assets/Farming/Carrot/Models/Carrot<Stage>.fbx
                                 one model per stage, origin at ground centre,
                                 written straight into the Unity project

Scale: 1 Blender unit = 1 metre = 1 game block. Origin of each model is the
centre of the block's top surface (where the plant meets the soil).
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EXPORT_DIR = os.path.join(REPO, "unity", "BinaryNestModAssets", "Assets", "Farming", "Carrot", "Models")
PREVIEW_DIR = os.path.join(HERE, "previews")
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# Stage definitions
# --------------------------------------------------------------------------
STAGES = [
    # name, fronds, frond length range (m), leaflet pairs, carrot shoulder radius (0 = none), seed
    dict(name="CarrotSeedling", fronds=3, length=(0.09, 0.13), pairs=2, shoulder=0.0,   seed=11),
    dict(name="CarrotGrowth",   fronds=6, length=(0.20, 0.28), pairs=3, shoulder=0.016, seed=22),
    dict(name="CarrotHarvest",  fronds=10, length=(0.34, 0.46), pairs=4, shoulder=0.032, seed=33),
]

# --------------------------------------------------------------------------
# Scene setup
# --------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0


def make_material(name, rgb, roughness=0.6):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1.0)
    return mat


MAT_LEAF = make_material("CarrotLeaf", (0.13, 0.38, 0.08), 0.55)
MAT_STALK = make_material("CarrotStalk", (0.30, 0.52, 0.16), 0.6)
MAT_ROOT = make_material("CarrotRoot", (0.88, 0.36, 0.05), 0.45)
MAT_SOIL = make_material("PreviewSoil", (0.16, 0.10, 0.06), 0.95)

MAT_INDEX = {"stalk": 0, "leaf": 1, "root": 2}


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def bezier(p0, p1, p2, t):
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def bezier_tangent(p0, p1, p2, t):
    return (2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1)).normalized()


def add_tube(bm, points, r0, r1, sides, mat):
    """Tapered tube through points (open ends are hidden in soil / leaflets)."""
    rings = []
    n = len(points)
    for i, p in enumerate(points):
        t = i / (n - 1)
        if i < n - 1:
            d = (points[i + 1] - p).normalized()
        else:
            d = (p - points[i - 1]).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
        a = d.cross(up).normalized()
        b = d.cross(a).normalized()
        r = r0 + (r1 - r0) * t
        ring = []
        for s in range(sides):
            ang = 2 * math.pi * s / sides
            ring.append(bm.verts.new(p + (a * math.cos(ang) + b * math.sin(ang)) * r))
        rings.append(ring)
    for i in range(n - 1):
        for s in range(sides):
            f = bm.faces.new((rings[i][s], rings[i][(s + 1) % sides],
                              rings[i + 1][(s + 1) % sides], rings[i + 1][s]))
            f.material_index = mat


# Feathery leaflet outline in local (x = width, y = length) space, 0..1 long.
LEAFLET_OUTLINE = [
    (-0.42, 0.28), (-0.16, 0.40), (-0.36, 0.62), (-0.10, 0.70),
    (0.0, 1.0),
    (0.10, 0.70), (0.36, 0.62), (0.16, 0.40), (0.42, 0.28),
]


def add_leaflet(bm, base, direction, normal, size, mat):
    """Flat, lobed leaflet with a slight fold along its midrib. Both sides are
    modelled so it shows with back-face culling on."""
    direction = direction.normalized()
    side = normal.cross(direction).normalized()
    normal = direction.cross(side).normalized()
    mid = base + direction * size * 0.45 + normal * size * 0.06  # raised midrib = fold
    outline = []
    for x, y in LEAFLET_OUTLINE:
        lift = -abs(x) * size * 0.25  # edges droop
        outline.append(base + side * x * size + direction * y * size + normal * lift)

    for flip in (False, True):
        b = bm.verts.new(base)
        m = bm.verts.new(mid)
        vs = [bm.verts.new(p) for p in outline]
        ring = [b] + vs
        for i in range(len(ring)):
            tri = (m, ring[i], ring[(i + 1) % len(ring)])
            if flip:
                tri = tri[::-1]
            f = bm.faces.new(tri)
            f.material_index = mat


def add_frond(bm, rng, azimuth, length, pairs):
    """One carrot leaf: a curved stalk with paired lobed leaflets and a tip."""
    out = Vector((math.cos(azimuth), math.sin(azimuth), 0))
    elev = math.radians(rng.uniform(55, 75))
    droop = rng.uniform(0.15, 0.35)
    p0 = out * 0.004
    p1 = p0 + (out * math.cos(elev) + Vector((0, 0, math.sin(elev)))) * length * 0.6
    p2 = p0 + out * length * (0.55 + droop) + Vector((0, 0, length * (0.85 - droop)))

    pts = [bezier(p0, p1, p2, i / 7) for i in range(8)]
    add_tube(bm, pts, length * 0.022, length * 0.008, 4, MAT_INDEX["stalk"])

    leaflet_size = length * 0.30
    for k in range(pairs):
        t = 0.35 + 0.55 * k / max(pairs, 1)
        base = bezier(p0, p1, p2, t)
        tan = bezier_tangent(p0, p1, p2, t)
        side = tan.cross(Vector((0, 0, 1))).normalized()
        normal = side.cross(tan).normalized()
        size = leaflet_size * (1.0 - 0.35 * k / max(pairs, 1))
        for sgn in (-1, 1):
            d = (tan * 0.55 + side * sgn).normalized()
            add_leaflet(bm, base, d, normal, size, MAT_INDEX["leaf"])
    # tip leaflet
    tan = bezier_tangent(p0, p1, p2, 1.0)
    side = tan.cross(Vector((0, 0, 1))).normalized()
    add_leaflet(bm, p2, tan, side.cross(tan), leaflet_size * 0.7, MAT_INDEX["leaf"])


def add_shoulder(bm, radius):
    """Top of the carrot root showing above the soil, tapering below it."""
    rings = []
    profile = [  # (height, radius factor)
        (-0.12, 0.30), (-0.06, 0.75), (-0.01, 1.0), (radius * 1.1, 0.95), (radius * 1.6, 0.55),
    ]
    sides = 10
    for z, rf in profile:
        ring = []
        for s in range(sides):
            ang = 2 * math.pi * s / sides
            ring.append(bm.verts.new((math.cos(ang) * radius * rf, math.sin(ang) * radius * rf, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(sides):
            f = bm.faces.new((rings[i][s], rings[i][(s + 1) % sides],
                              rings[i + 1][(s + 1) % sides], rings[i + 1][s]))
            f.material_index = MAT_INDEX["root"]
    top = bm.faces.new(rings[-1])
    top.material_index = MAT_INDEX["root"]


def build_stage(cfg):
    rng = random.Random(cfg["seed"])
    bm = bmesh.new()
    n = cfg["fronds"]
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        length = rng.uniform(*cfg["length"])
        add_frond(bm, rng, az, length, cfg["pairs"])
    if cfg["shoulder"] > 0:
        add_shoulder(bm, cfg["shoulder"])
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index == MAT_INDEX["root"]])

    mesh = bpy.data.meshes.new(cfg["name"])
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = poly.material_index != MAT_INDEX["leaf"]
    obj = bpy.data.objects.new(cfg["name"], mesh)
    for m in (MAT_STALK, MAT_LEAF, MAT_ROOT):
        obj.data.materials.append(m)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# --------------------------------------------------------------------------
# Build, export
# --------------------------------------------------------------------------
models = [build_stage(cfg) for cfg in STAGES]

for obj in models:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(EXPORT_DIR, obj.name + ".fbx"),
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
    )
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    dims = obj.dimensions
    print(f"[carrot] {obj.name}: {tris} tris, size {dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} m")

# --------------------------------------------------------------------------
# Preview scene (soil tiles, lights, camera) in its own collection
# --------------------------------------------------------------------------
preview = bpy.data.collections.new("Preview")
scene.collection.children.link(preview)

spacing = 1.1
for i, obj in enumerate(models):
    obj.location.x = (i - 1) * spacing
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(obj.location.x, 0, -0.5))
    soil = bpy.context.active_object
    soil.name = f"PreviewSoil_{obj.name}"
    soil.data.materials.append(MAT_SOIL)
    for c in soil.users_collection:
        c.objects.unlink(soil)
    preview.objects.link(soil)

world = bpy.data.worlds.new("PreviewWorld")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.55, 0.65, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.8
scene.world = world

sun_data = bpy.data.lights.new("PreviewSun", "SUN")
sun_data.energy = 3.5
sun = bpy.data.objects.new("PreviewSun", sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
preview.objects.link(sun)

cam_data = bpy.data.cameras.new("PreviewCamera")
cam = bpy.data.objects.new("PreviewCamera", cam_data)
preview.objects.link(cam)
scene.camera = cam

# Render engine: prefer EEVEE, fall back to whatever is available.
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
print(f"[carrot] render engine: {scene.render.engine}")
if scene.render.engine == "CYCLES":
    scene.cycles.samples = 64
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"


def aim(cam_obj, target, location):
    cam_obj.location = location
    direction = Vector(target) - Vector(location)
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render(path, res_x, res_y):
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[carrot] rendered {path}")


# Lineup of all three stages
cam_data.lens = 50
aim(cam, (0, 0, 0.18), (0.0, -3.6, 1.35))
render(os.path.join(PREVIEW_DIR, "carrot_stages_lineup.png"), 1600, 700)

# Close-up of each stage
for obj in models:
    h = max(obj.dimensions.z, 0.12)
    cam_data.lens = 60
    target = (obj.location.x, 0, h * 0.45)
    dist = 0.55 + h * 2.4
    aim(cam, target, (obj.location.x + dist * 0.6, -dist * 0.8, h * 0.45 + dist * 0.45))
    render(os.path.join(PREVIEW_DIR, f"{obj.name}.png"), 900, 900)

# The .blend keeps the stages laid out side by side for editing. The FBX files
# were exported earlier, with each model at the origin.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "carrot.blend"))
print("[carrot] saved carrot.blend")
