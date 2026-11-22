"""
Builds the carrot models and icons for Adapting Farming.

Run headless from the repo root:
    blender --background --factory-startup --python art/farming/carrot/build_carrot.py

Outputs:
    art/farming/carrot/carrot.blend            source scene
    art/farming/carrot/previews/*.png          preview renders (incl. icon copies)
    unity/BinaryNestModAssets/Assets/Farming/Carrot/
        Models/Carrot<Stage>.fbx               one model per growth stage
        Textures/CarrotLeaf.png                leaf texture (4 green variants)
    Mods/BinaryNest_Farming/UIAtlases/ItemIconAtlas/
        foodCropCarrot.png, plantedCarrot1.png 160x160 inventory icons

Scale: 1 Blender unit = 1 metre = 1 game block. Each model's origin is where
the plant meets the soil.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
UNITY_CARROT = os.path.join(REPO, "unity", "BinaryNestModAssets", "Assets", "Farming", "Carrot")
EXPORT_DIR = os.path.join(UNITY_CARROT, "Models")
TEXTURE_DIR = os.path.join(UNITY_CARROT, "Textures")
ICON_DIR = os.path.join(REPO, "Mods", "BinaryNest_Farming", "UIAtlases", "ItemIconAtlas")
PREVIEW_DIR = os.path.join(HERE, "previews")
for d in (EXPORT_DIR, TEXTURE_DIR, ICON_DIR, PREVIEW_DIR):
    os.makedirs(d, exist_ok=True)

STAGES = [
    dict(name="CarrotSeedling", fronds=3,  length=(0.09, 0.13), pairs=2, shoulder=0.0,   seed=11),
    dict(name="CarrotGrowth",   fronds=6,  length=(0.20, 0.28), pairs=3, shoulder=0.016, seed=22),
    dict(name="CarrotHarvest",  fronds=10, length=(0.34, 0.46), pairs=4, shoulder=0.032, seed=33),
]

# Four slightly different, muted greens. One is picked per frond.
LEAF_VARIANTS = [
    (0.135, 0.285, 0.075),
    (0.165, 0.315, 0.090),
    (0.115, 0.255, 0.070),
    (0.185, 0.305, 0.100),
]
STALK_RGB = (0.17, 0.29, 0.10)
ROOT_RGB = (0.80, 0.32, 0.05)
LEAF_TEX_SIZE = (256, 64)  # 4 tiles of 64x64, one per variant

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


# --------------------------------------------------------------------------
# Leaf texture: midrib, side veins, darker edges and base, lighter tips
# --------------------------------------------------------------------------
def make_leaf_texture():
    w, h = LEAF_TEX_SIZE
    tile = w // len(LEAF_VARIANTS)
    rng = random.Random(7)
    px = [0.0] * (w * h * 4)
    for y in range(h):
        v = (y + 0.5) / h
        for x in range(w):
            variant = x // tile
            u = ((x % tile) + 0.5) / tile
            r, g, b = LEAF_VARIANTS[variant]
            side = abs(u - 0.5) * 2.0                     # 0 at midrib, 1 at edge
            shade = (0.78 + 0.30 * v) * (1.0 - 0.28 * side * side)
            vein = (v - side * 0.55) * 7.0
            if side < 0.07:                                # midrib
                shade *= 1.22
                r, g, b = r + 0.015, g + 0.015, b + 0.005
            elif (vein - math.floor(vein)) < 0.10 and side < 0.85:  # side veins
                shade *= 1.07
            shade *= 1.0 + rng.uniform(-0.05, 0.05)
            i = (y * w + x) * 4
            px[i:i + 4] = (min(r * shade, 1), min(g * shade, 1), min(b * shade, 1), 1.0)
    img = bpy.data.images.new("CarrotLeaf", w, h, alpha=False)
    img.pixels = px
    img.filepath_raw = os.path.join(TEXTURE_DIR, "CarrotLeaf.png")
    img.file_format = "PNG"
    img.save()
    return img


LEAF_IMAGE = make_leaf_texture()


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_material(name, rgb, roughness=0.6, image=None):
    """rgb is an sRGB colour, the same values Unity's material colour uses."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*[srgb_to_linear(c) for c in rgb], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if image is not None:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Linear"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    mat.diffuse_color = (*rgb, 1.0)
    return mat


MAT_STALK = make_material("CarrotStalk", STALK_RGB, 0.8)
MAT_LEAF = make_material("CarrotLeaf", LEAF_VARIANTS[0], 0.55, LEAF_IMAGE)
MAT_ROOT = make_material("CarrotRoot", ROOT_RGB, 0.45)
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
    rings = []
    n = len(points)
    for i, p in enumerate(points):
        t = i / (n - 1)
        d = (points[i + 1] - p).normalized() if i < n - 1 else (p - points[i - 1]).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
        a = d.cross(up).normalized()
        b = d.cross(a).normalized()
        r = r0 + (r1 - r0) * t
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * s / sides) +
                                        b * math.sin(2 * math.pi * s / sides)) * r)
                      for s in range(sides)])
    for i in range(n - 1):
        for s in range(sides):
            f = bm.faces.new((rings[i][s], rings[i][(s + 1) % sides],
                              rings[i + 1][(s + 1) % sides], rings[i + 1][s]))
            f.material_index = mat
            f.smooth = True


# Lobed leaflet outline in local (x = width, y = length) space, 0..1 long.
LEAFLET_OUTLINE = [
    (-0.30, 0.16), (-0.14, 0.24), (-0.44, 0.34), (-0.18, 0.44), (-0.38, 0.58),
    (-0.13, 0.64), (-0.24, 0.80), (-0.06, 0.82),
    (0.0, 1.0),
    (0.06, 0.82), (0.24, 0.80), (0.13, 0.64), (0.38, 0.58), (0.18, 0.44),
    (0.44, 0.34), (0.14, 0.24), (0.30, 0.16),
]


def add_leaflet(bm, uv_layer, base, direction, normal, size, variant):
    """Lobed leaflet with a raised midrib, modelled on both sides, with UVs
    into the leaf texture tile for its colour variant."""
    direction = direction.normalized()
    side = normal.cross(direction).normalized()
    normal = direction.cross(side).normalized()

    def uv(x, y):
        u = min(max(0.5 + x, 0.03), 0.97)
        return Vector(((variant + u) / len(LEAF_VARIANTS), y))

    pts = [(0.0, 0.0, 0.0)]                              # base
    pts += [(0.0, 0.40, 0.07), (0.0, 0.72, 0.05)]        # raised midrib points
    pts += [(x, y, -abs(x) * 0.30) for x, y in LEAFLET_OUTLINE]

    def world(x, y, lift):
        return base + side * x * size + direction * y * size + normal * lift * size

    # Triangles as indices into pts: fan the outline around the two midrib
    # points (lower half -> pts[1], upper half -> pts[2]), plus a bridging
    # triangle on each side where the fan switches centre.
    ring = [0] + list(range(3, len(pts)))
    tris = []
    for i in range(len(ring)):
        a, c = ring[i], ring[(i + 1) % len(ring)]
        lower = pts[a][1] <= 0.5 and pts[c][1] <= 0.5
        tris.append((1 if lower else 2, a, c))
    for i in range(len(ring)):
        a, c = ring[i], ring[(i + 1) % len(ring)]
        if (pts[a][1] <= 0.5) != (pts[c][1] <= 0.5):
            pivot = a if pts[a][1] <= 0.5 else c
            tris.append((1, pivot, 2))

    for back in (False, True):
        vs = [bm.verts.new(world(*p)) for p in pts]
        for tri in tris:
            p0, p1, p2 = (vs[i].co for i in tri)
            facing = (p1 - p0).cross(p2 - p0).dot(normal)
            if (facing < 0) != back:
                tri = tri[::-1]
            f = bm.faces.new([vs[i] for i in tri])
            f.material_index = MAT_INDEX["leaf"]
            f.smooth = True
            for loop in f.loops:
                p = pts[vs.index(loop.vert)]
                loop[uv_layer].uv = uv(p[0], p[1])


def add_frond(bm, uv_layer, rng, azimuth, length, pairs, base_offset=Vector()):
    out = Vector((math.cos(azimuth), math.sin(azimuth), 0))
    elev = math.radians(rng.uniform(55, 75))
    droop = rng.uniform(0.15, 0.35)
    variant = rng.randrange(len(LEAF_VARIANTS))
    p0 = base_offset + out * 0.004
    p1 = p0 + (out * math.cos(elev) + Vector((0, 0, math.sin(elev)))) * length * 0.6
    p2 = p0 + out * length * (0.55 + droop) + Vector((0, 0, length * (0.85 - droop)))

    add_tube(bm, [bezier(p0, p1, p2, i / 9) for i in range(10)],
             length * 0.022, length * 0.008, 5, MAT_INDEX["stalk"])

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
            add_leaflet(bm, uv_layer, base, d, normal, size, variant)
    tan = bezier_tangent(p0, p1, p2, 1.0)
    side = tan.cross(Vector((0, 0, 1))).normalized()
    add_leaflet(bm, uv_layer, p2, tan, side.cross(tan), leaflet_size * 0.7, variant)


def add_root(bm, radius, length, above, sides=12, rings_n=9, rng=None):
    """Carrot root: rounded shoulder 'above' metres over the soil, tapering to
    a point 'length' below the top. Slight ring wobble for definition."""
    rings = []
    top = above
    for i in range(rings_n):
        t = i / (rings_n - 1)                    # 0 = top, 1 = tip
        z = top - t * length
        rf = (1.0 - t) ** 0.85 if t > 0.08 else 0.82 + t * 2.2
        wobble = 1.0 + (rng.uniform(-0.04, 0.04) if rng else 0.0)
        rings.append([bm.verts.new((math.cos(2 * math.pi * s / sides) * radius * rf * wobble,
                                    math.sin(2 * math.pi * s / sides) * radius * rf * wobble, z))
                      for s in range(sides)])
    for i in range(rings_n - 1):
        for s in range(sides):
            f = bm.faces.new((rings[i][s], rings[i][(s + 1) % sides],
                              rings[i + 1][(s + 1) % sides], rings[i + 1][s]))
            f.material_index = MAT_INDEX["root"]
            f.smooth = True
    cap = bm.faces.new(rings[0])
    cap.material_index = MAT_INDEX["root"]
    tip = bm.verts.new((0, 0, top - length * 1.02))
    for s in range(sides):
        f = bm.faces.new((rings[-1][(s + 1) % sides], rings[-1][s], tip))
        f.material_index = MAT_INDEX["root"]
        f.smooth = True


def finish_object(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index != MAT_INDEX["leaf"]])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for m in (MAT_STALK, MAT_LEAF, MAT_ROOT):
        obj.data.materials.append(m)
    scene.collection.objects.link(obj)
    return obj


def build_stage(cfg):
    rng = random.Random(cfg["seed"])
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    n = cfg["fronds"]
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        add_frond(bm, uv_layer, rng, az, rng.uniform(*cfg["length"]), cfg["pairs"])
    if cfg["shoulder"] > 0:
        add_root(bm, cfg["shoulder"], 0.13, cfg["shoulder"] * 1.4, rng=rng)
    return finish_object(bm, cfg["name"])


def build_whole_carrot(name, seed, length=0.20, radius=0.028):
    """A pulled carrot (root + leafy top) for the item icon, lying along +Z."""
    rng = random.Random(seed)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    add_root(bm, radius, length, 0.0, rng=rng)
    for i in range(5):
        az = 2 * math.pi * i / 5 + rng.uniform(-0.3, 0.3)
        add_frond(bm, uv_layer, rng, az, rng.uniform(0.10, 0.14), 2)
    return finish_object(bm, name)


# --------------------------------------------------------------------------
# Build and export the growth stages
# --------------------------------------------------------------------------
models = [build_stage(cfg) for cfg in STAGES]

for obj in models:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(EXPORT_DIR, obj.name + ".fbx"),
        use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", bake_space_transform=True,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,
        path_mode="STRIP",
    )
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    d = obj.dimensions
    print(f"[carrot] {obj.name}: {tris} tris, size {d.x:.2f} x {d.y:.2f} x {d.z:.2f} m")

# --------------------------------------------------------------------------
# Rendering setup
# --------------------------------------------------------------------------
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
print(f"[carrot] render engine: {scene.render.engine}")
scene.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("PreviewWorld")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.55, 0.65, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.8
scene.world = world

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(sun)

cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def aim(location, target):
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


def render(path, res_x, res_y):
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[carrot] rendered {path}")


def show_only(objs):
    keep = set(objs) | {cam, sun}
    for o in scene.objects:
        o.hide_render = o not in keep


# --- Growth stage previews on soil blocks --------------------------------
soils = []
spacing = 1.1
for i, obj in enumerate(models):
    obj.location.x = (i - 1) * spacing
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(obj.location.x, 0, -0.5))
    soil = bpy.context.active_object
    soil.name = f"PreviewSoil_{obj.name}"
    soil.data.materials.append(MAT_SOIL)
    soils.append(soil)

show_only(models + soils)
cam_data.type = "PERSP"
cam_data.lens = 50
aim((0.0, -3.6, 1.35), (0, 0, 0.18))
render(os.path.join(PREVIEW_DIR, "carrot_stages_lineup.png"), 1600, 700)
for obj in models:
    h = max(obj.dimensions.z, 0.12)
    cam_data.lens = 60
    dist = 0.55 + h * 2.4
    aim((obj.location.x + dist * 0.6, -dist * 0.8, h * 0.45 + dist * 0.45), (obj.location.x, 0, h * 0.45))
    render(os.path.join(PREVIEW_DIR, f"{obj.name}.png"), 900, 900)

# --- Icons: transparent background, orthographic, fitted -----------------
icon_objs = []

# foodCropCarrot: two pulled carrots crossed
c1 = build_whole_carrot("IconCarrotA", 101)
c2 = build_whole_carrot("IconCarrotB", 202, length=0.18, radius=0.025)
c1.matrix_world = Matrix.Translation((10.0, 0.0, 0.0)) @ Matrix.Rotation(math.radians(-50), 4, "Y")
c2.matrix_world = Matrix.Translation((10.05, 0.04, -0.03)) @ Matrix.Rotation(math.radians(-30), 4, "Y") @ Matrix.Rotation(math.radians(25), 4, "Z")

# plantedCarrot1 (Carrot Seeds): a young carrot plant in a small mound of soil
seed_plant = models[1].copy()
seed_plant.data = models[1].data.copy()
seed_plant.name = "IconSeedPlant"
scene.collection.objects.link(seed_plant)
seed_plant.location = (20.0, 0.0, 0.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(20.0, 0.0, -0.05), segments=24, ring_count=12)
mound = bpy.context.active_object
mound.scale = (1.0, 1.0, 0.38)
mound.data.materials.append(MAT_SOIL)
bpy.ops.object.shade_smooth()

scene.render.film_transparent = True
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
cam_data.type = "ORTHO"

ICONS = [
    ("foodCropCarrot", [c1, c2], (0.35, -1.0, 0.55)),
    ("plantedCarrot1", [seed_plant, mound], (0.45, -1.0, 0.75)),
]
depsgraph = bpy.context.evaluated_depsgraph_get()
for icon_name, objs, view_dir in ICONS:
    show_only(objs)
    coords = []
    for o in objs:
        coords += [o.matrix_world @ Vector(c) for c in o.bound_box]
    centre = sum(coords, Vector()) / len(coords)
    aim(centre + Vector(view_dir).normalized() * 5.0, centre)
    bpy.context.view_layer.update()
    flat = [c for v in coords for c in v]
    loc, scale = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), flat)
    cam.location = loc
    cam_data.ortho_scale = scale * 0.92
    render(os.path.join(ICON_DIR, f"{icon_name}.png"), 160, 160)
    render(os.path.join(PREVIEW_DIR, f"icon_{icon_name}.png"), 160, 160)

# Leave the file in an editable state
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
for o in scene.objects:
    o.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "carrot.blend"))
print("[carrot] saved carrot.blend")
