"""
Builds the wheat models for Adapting Farming.
(Inventory icons are made separately with ChatGPT; see docs/guides/art-guide.md.)
Follows docs/guides/art-guide.md (same pipeline as the carrot).

Run headless from the repo root:
    blender --background --factory-startup --python art/farming/wheat/build_wheat.py

Outputs:
    art/farming/wheat/wheat.blend             source scene
    art/farming/wheat/previews/*.png          preview renders
    unity/BinaryNestModAssets/Assets/Farming/Wheat/
        Models/Wheat<Stage>.fbx               one FBX per stage, LOD0..LOD2 inside
        Textures/WheatPlant.png               stalk/leaf texture (2 green + 2 gold)

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
UNITY_WHEAT = os.path.join(REPO, "unity", "BinaryNestModAssets", "Assets", "Farming", "Wheat")
EXPORT_DIR = os.path.join(UNITY_WHEAT, "Models")
TEXTURE_DIR = os.path.join(UNITY_WHEAT, "Textures")
PREVIEW_DIR = os.path.join(HERE, "previews")
for d in (EXPORT_DIR, TEXTURE_DIR, PREVIEW_DIR):
    os.makedirs(d, exist_ok=True)

# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------
STAGES = [
    dict(name="WheatSeedling", seed=51, stalks=0, blades=7, blade_len=(0.08, 0.15),
         tiles=(0, 1), grain=None),
    dict(name="WheatGrowth", seed=52, stalks=10, height=(0.36, 0.50), blades=4, blade_len=(0.12, 0.20),
         leaves=(2, 3), leaf_len=(0.14, 0.22), head_len=0.045, kernel_scale=0.75, awn_len=0.012,
         tiles=(0, 1), grain="green", lean=0.10),
    dict(name="WheatHarvest", seed=53, stalks=16, height=(0.72, 0.92), blades=0, blade_len=(0.1, 0.1),
         leaves=(2, 2), leaf_len=(0.16, 0.24), head_len=0.088, kernel_scale=1.3, awn_len=0.036,
         tiles=(2, 3), grain="gold", lean=0.16),
]

# Texture tiles (sRGB): 0-1 green, 2-3 golden straw.
PLANT_TILES = [
    (0.20, 0.33, 0.11),
    (0.25, 0.37, 0.13),
    (0.74, 0.60, 0.33),
    (0.67, 0.52, 0.27),
]
GRAIN_GREEN = (0.45, 0.53, 0.23)
GRAIN_GOLD = (0.80, 0.62, 0.30)
TEX_SIZE = (256, 64)

# Levels of detail (see art guide: ~55% at LOD1, ~15-20% at LOD2).
LODS = [
    dict(stalk_sides=5, stalk_points=8, leaf_segs=6, head_levels=12, awn_every=1, spindle=False),
    dict(stalk_sides=4, stalk_points=5, leaf_segs=4, head_levels=7,  awn_every=2, spindle=False),
    dict(stalk_sides=3, stalk_points=3, leaf_segs=2, head_levels=0,  awn_every=0, spindle=True),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


# --------------------------------------------------------------------------
# Texture and materials
# --------------------------------------------------------------------------
def make_plant_texture():
    """Lengthwise fibres, darker edges and base, lighter tips. u across, v along."""
    w, h = TEX_SIZE
    tile = w // len(PLANT_TILES)
    rng = random.Random(9)
    px = [0.0] * (w * h * 4)
    for y in range(h):
        v = (y + 0.5) / h
        for x in range(w):
            t = x // tile
            u = ((x % tile) + 0.5) / tile
            r, g, b = PLANT_TILES[t]
            side = abs(u - 0.5) * 2.0
            shade = (0.82 + 0.26 * v) * (1.0 - 0.22 * side * side)
            fibre = math.sin(u * math.pi * 9.0)
            shade *= 1.0 + 0.05 * fibre
            if side < 0.08:
                shade *= 1.10
            shade *= 1.0 + rng.uniform(-0.04, 0.04)
            i = (y * w + x) * 4
            px[i:i + 4] = (min(r * shade, 1), min(g * shade, 1), min(b * shade, 1), 1.0)
    img = bpy.data.images.new("WheatPlant", w, h, alpha=False)
    img.pixels = px
    img.filepath_raw = os.path.join(TEXTURE_DIR, "WheatPlant.png")
    img.file_format = "PNG"
    img.save()
    return img


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_material(name, rgb, roughness=0.6, image=None):
    """rgb is sRGB, the same values Unity's material colour uses."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*[srgb_to_linear(c) for c in rgb], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if image is not None:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    mat.diffuse_color = (*rgb, 1.0)
    return mat


PLANT_IMAGE = make_plant_texture()
MAT_PLANT = make_material("WheatPlant", (1, 1, 1), 0.75, PLANT_IMAGE)
MAT_GRAIN_GREEN = make_material("WheatGrainGreen", GRAIN_GREEN, 0.6)
MAT_GRAIN_GOLD = make_material("WheatGrainGold", GRAIN_GOLD, 0.55)
MAT_SOIL = make_material("PreviewSoil", (0.16, 0.10, 0.06), 0.95)
MAT_INDEX = {"plant": 0, "grain_green": 1, "grain_gold": 2}
GRAIN_MAT = {"green": MAT_INDEX["grain_green"], "gold": MAT_INDEX["grain_gold"]}


def tile_uv(tile, u, v):
    u = min(max(u, 0.03), 0.97)
    return Vector(((tile + u) / len(PLANT_TILES), min(max(v, 0.0), 1.0)))


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def bezier(p0, p1, p2, t):
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def bezier_tangent(p0, p1, p2, t):
    return (2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1)).normalized()


def perpendicular_basis(d):
    up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
    a = d.cross(up).normalized()
    return a, d.cross(a).normalized()


def add_tube(bm, uv_layer, points, r0, r1, sides, tile):
    rings = []
    n = len(points)
    for i, p in enumerate(points):
        d = (points[i + 1] - p).normalized() if i < n - 1 else (p - points[i - 1]).normalized()
        a, b = perpendicular_basis(d)
        r = r0 + (r1 - r0) * i / (n - 1)
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * s / sides) +
                                        b * math.sin(2 * math.pi * s / sides)) * r)
                      for s in range(sides)])
    for i in range(n - 1):
        for s in range(sides):
            quad = [rings[i][s], rings[i][(s + 1) % sides], rings[i + 1][(s + 1) % sides], rings[i + 1][s]]
            uvs = [(s / sides, i / (n - 1)), ((s + 1) / sides, i / (n - 1)),
                   ((s + 1) / sides, (i + 1) / (n - 1)), (s / sides, (i + 1) / (n - 1))]
            # Wind the quad so its normal points away from the stalk's centre line.
            p0, p1, p2 = (v.co for v in quad[:3])
            centroid = sum((v.co for v in quad), Vector()) / 4
            if (p1 - p0).cross(p2 - p0).dot(centroid - (points[i] + points[i + 1]) / 2) < 0:
                quad, uvs = quad[::-1], uvs[::-1]
            f = bm.faces.new(quad)
            f.material_index = MAT_INDEX["plant"]
            f.smooth = True
            for loop, (uu, vv) in zip(f.loops, uvs):
                loop[uv_layer].uv = tile_uv(tile, 0.3 + uu * 0.4, vv)


def add_ribbon(bm, uv_layer, centres, widths, sides, normals, tile):
    """Two-sided strip (grass blade / leaf) through centre points."""
    for back in (False, True):
        left = [bm.verts.new(c - s * w * 0.5) for c, s, w in zip(centres, sides, widths)]
        right = [bm.verts.new(c + s * w * 0.5) for c, s, w in zip(centres, sides, widths)]
        n = len(centres)
        for i in range(n - 1):
            quad = [left[i], right[i], right[i + 1], left[i + 1]]
            uvs = [(0, i / (n - 1)), (1, i / (n - 1)), (1, (i + 1) / (n - 1)), (0, (i + 1) / (n - 1))]
            if right[i + 1] is left[i + 1] or (right[i + 1].co - left[i + 1].co).length < 1e-6:
                quad, uvs = quad[:3], uvs[:3]
            p0, p1, p2 = (v.co for v in quad[:3])
            facing = (p1 - p0).cross(p2 - p0).dot(normals[i])
            if (facing < 0) != back:
                quad, uvs = quad[::-1], uvs[::-1]
            f = bm.faces.new(quad)
            f.material_index = MAT_INDEX["plant"]
            f.smooth = True
            for loop, uv in zip(f.loops, uvs):
                loop[uv_layer].uv = tile_uv(tile, *uv)


def add_blade(bm, uv_layer, base, direction_xy, length, width, droop, segs, tile, lift=0.0):
    """Arching grass blade / wheat leaf from base."""
    out = Vector((direction_xy.x, direction_xy.y, 0)).normalized()
    p0 = base
    p1 = base + out * length * 0.25 + Vector((0, 0, length * (0.75 + lift)))
    p2 = base + out * length * (0.55 + droop) + Vector((0, 0, length * (0.55 - droop)))
    centres, widths, sides, normals = [], [], [], []
    for i in range(segs + 1):
        t = i / segs
        c = bezier(p0, p1, p2, t)
        tan = bezier_tangent(p0, p1, p2, t)
        side = tan.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
        centres.append(c)
        widths.append(width * (1.0 - t) ** 0.7 if i < segs else 0.0)
        sides.append(side)
        normals.append(side.cross(tan).normalized())
    add_ribbon(bm, uv_layer, centres, widths, sides, normals, tile)


def add_kernel(bm, centre, axis, width, length, mat, ring=4):
    """Low-poly grain: two cones joined at a ring (diamond), smooth shaded."""
    a, b = perpendicular_basis(axis)
    tip = bm.verts.new(centre + axis * length * 0.5)
    base = bm.verts.new(centre - axis * length * 0.5)
    ring_c = centre + axis * length * 0.05
    rv = [bm.verts.new(ring_c + (a * math.cos(2 * math.pi * i / ring) + b * math.sin(2 * math.pi * i / ring)) * width)
          for i in range(ring)]
    for i in range(ring):
        for tri in ((tip, rv[i], rv[(i + 1) % ring]), (base, rv[(i + 1) % ring], rv[i])):
            p0, p1, p2 = (v.co for v in tri)
            cen = (p0 + p1 + p2) / 3
            if (p1 - p0).cross(p2 - p0).dot(cen - centre) < 0:
                tri = tri[::-1]
            f = bm.faces.new(tri)
            f.material_index = mat
            f.smooth = True
    return tip.co.copy()


def add_awn(bm, start, direction, length, width, mat):
    """A thin bristle: a two-sided sliver."""
    a, _ = perpendicular_basis(direction)
    v0 = start - a * width
    v1 = start + a * width
    v2 = start + direction * length
    for back in (False, True):
        vs = [bm.verts.new(v0), bm.verts.new(v1), bm.verts.new(v2)]
        f = bm.faces.new(vs if not back else vs[::-1])
        f.material_index = mat
        f.smooth = True


def add_head(bm, top, tangent, cfg, lod, grain_mat):
    """Wheat ear: alternating pairs of kernels up the head, with awns."""
    t = tangent.normalized()
    a, b = perpendicular_basis(t)
    hl = cfg["head_len"]
    ks = cfg["kernel_scale"]
    if lod["spindle"]:
        add_kernel(bm, top + t * hl * 0.5, t, 0.011 * ks, hl * 1.05, grain_mat, ring=6)
        return
    levels = lod["head_levels"]
    scale_up = 12.0 / levels
    for i in range(levels):
        f = i / (levels - 1)
        p = top + t * hl * f
        theta = (i % 2) * math.pi / 2
        size = (1.0 - 0.35 * f) * ks * (scale_up ** 0.45)
        for k in (0, 1):
            ang = theta + k * math.pi
            d = a * math.cos(ang) + b * math.sin(ang)
            centre = p + d * 0.0045 * ks
            axis = (t * 0.85 + d * 0.45).normalized()
            tip = add_kernel(bm, centre, axis, 0.0042 * size, 0.0105 * size, grain_mat)
            if lod["awn_every"] and cfg["awn_len"] > 0 and (i + k) % lod["awn_every"] == 0:
                add_awn(bm, tip, (t * 0.8 + d * 0.25).normalized(), cfg["awn_len"] * (0.8 + 0.4 * f),
                        0.0007, grain_mat)


def finish_object(bm, name, materials=(MAT_PLANT, MAT_GRAIN_GREEN, MAT_GRAIN_GOLD)):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for m in materials:
        obj.data.materials.append(m)
    scene.collection.objects.link(obj)
    return obj


def plan_stage(cfg):
    """All random choices for a stage, made once so every LOD matches."""
    rng = random.Random(cfg["seed"])
    stalks = []
    for i in range(cfg["stalks"]):
        ang = rng.uniform(0, 2 * math.pi)
        r = 0.075 * math.sqrt(rng.random())
        base = Vector((math.cos(ang) * r, math.sin(ang) * r, 0.0))
        lean_dir = Vector((math.cos(ang), math.sin(ang), 0)) if r > 0.01 else Vector((1, 0, 0))
        height = rng.uniform(*cfg["height"])
        lean = rng.uniform(0.3, 1.0) * cfg["lean"]
        nleaves = rng.randint(*cfg["leaves"])
        leaves = [(rng.uniform(0.12, 0.45), rng.uniform(0, 2 * math.pi), rng.uniform(*cfg["leaf_len"]),
                   rng.uniform(0.25, 0.45)) for _ in range(nleaves)]
        stalks.append(dict(base=base, lean_dir=lean_dir, height=height, lean=lean, leaves=leaves,
                           tile=cfg["tiles"][rng.randrange(2)]))
    blades = []
    for i in range(cfg["blades"]):
        ang = 2 * math.pi * i / max(cfg["blades"], 1) + rng.uniform(-0.3, 0.3)
        blades.append((ang, rng.uniform(*cfg["blade_len"]), rng.uniform(0.1, 0.35),
                       cfg["tiles"][rng.randrange(2)]))
    return stalks, blades


def build_stage(cfg, plan, lod_index):
    lod = LODS[lod_index]
    stalks, blades = plan
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for ang, length, droop, tile in blades:
        add_blade(bm, uv_layer, Vector((0, 0, 0)), Vector((math.cos(ang), math.sin(ang), 0)),
                  length, 0.010, droop, lod["leaf_segs"], tile)
    for s in stalks:
        h = s["height"]
        p0 = s["base"]
        p2 = p0 + s["lean_dir"] * h * s["lean"] + Vector((0, 0, h))
        p1 = p0 + s["lean_dir"] * h * s["lean"] * 0.2 + Vector((0, 0, h * 0.6))
        n = lod["stalk_points"]
        add_tube(bm, uv_layer, [bezier(p0, p1, p2, i / (n - 1)) for i in range(n)],
                 0.0050, 0.0032, lod["stalk_sides"], s["tile"])
        for frac, ang, length, droop in s["leaves"]:
            base = bezier(p0, p1, p2, frac)
            add_blade(bm, uv_layer, base, Vector((math.cos(ang), math.sin(ang), 0)),
                      length, 0.011, droop, lod["leaf_segs"], s["tile"], lift=-0.35)
        if cfg["grain"]:
            add_head(bm, p2, bezier_tangent(p0, p1, p2, 1.0), cfg, lod, GRAIN_MAT[cfg["grain"]])
    return finish_object(bm, f"{cfg['name']}_LOD{lod_index}")


# --------------------------------------------------------------------------
# Build and export
# --------------------------------------------------------------------------
stage_lods = {}
for cfg in STAGES:
    plan = plan_stage(cfg)
    stage_lods[cfg["name"]] = [build_stage(cfg, plan, i) for i in range(len(LODS))]
models = [lods[0] for lods in stage_lods.values()]

for name, lods in stage_lods.items():
    bpy.ops.object.select_all(action="DESELECT")
    for o in lods:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lods[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(EXPORT_DIR, name + ".fbx"),
        use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", bake_space_transform=True,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,
        path_mode="STRIP",
    )
    counts = [sum(len(p.vertices) - 2 for p in o.data.polygons) for o in lods]
    d = lods[0].dimensions
    print(f"[wheat] {name}: tris " + " / ".join(f"LOD{i} {c}" for i, c in enumerate(counts))
          + f", size {d.x:.2f} x {d.y:.2f} x {d.z:.2f} m")

# --------------------------------------------------------------------------
# Rendering setup
# --------------------------------------------------------------------------
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
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
lights = [sun]


def aim(location, target):
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


def render(path, res_x, res_y):
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[wheat] rendered {os.path.relpath(path, REPO)}")


def show_only(objs):
    keep = set(objs) | {cam} | set(lights)
    for o in scene.objects:
        o.hide_render = o not in keep


# --- Growth stage previews on soil blocks ---------------------------------
soils = []
for i, obj in enumerate(models):
    obj.location.x = (i - 1) * 1.1
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(obj.location.x, 0, -0.5))
    soil = bpy.context.active_object
    soil.data.materials.append(MAT_SOIL)
    soils.append(soil)

show_only(models + soils)
cam_data.type = "PERSP"
cam_data.lens = 50
aim((0.0, -3.9, 1.6), (0, 0, 0.35))
render(os.path.join(PREVIEW_DIR, "wheat_stages_lineup.png"), 1600, 800)
for obj in models:
    h = max(obj.dimensions.z, 0.12)
    cam_data.lens = 60
    dist = 0.6 + h * 2.2
    aim((obj.location.x + dist * 0.6, -dist * 0.8, h * 0.5 + dist * 0.35), (obj.location.x, 0, h * 0.5))
    render(os.path.join(PREVIEW_DIR, f"{obj.name.rsplit('_LOD', 1)[0]}.png"), 900, 900)

# --- LOD comparison for the grown wheat -----------------------------------
lod_objs = stage_lods["WheatHarvest"]
for i, o in enumerate(lod_objs):
    o.location = ((i - 1) * 0.8, 30.0, 0.0)
show_only(lod_objs)
cam_data.lens = 50
aim((0.0, 30.0 - 3.6, 0.9), (0.0, 30.0, 0.45))
render(os.path.join(PREVIEW_DIR, "wheat_harvest_lods.png"), 1500, 700)

for o in scene.objects:
    o.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "wheat.blend"))
print("[wheat] saved wheat.blend")
