"""
Builds the carrot models for Adapting Farming.
(Inventory icons are made separately with ChatGPT; see docs/guides/art-guide.md.)

Run headless from the repo root:
    blender --background --factory-startup --python art/farming/carrot/build_carrot.py

Outputs:
    art/farming/carrot/carrot.blend            source scene
    art/farming/carrot/previews/*.png          preview renders
    unity/BinaryNestModAssets/Assets/Farming/Carrot/
        Models/Carrot<Stage>.fbx               one model per growth stage
        Textures/CarrotFrond.png               frond texture with alpha (2 green variants)

Scale: 1 Blender unit = 1 metre = 1 game block. Each model's origin is where
the plant meets the soil.

Leaves are drawn like the vanilla potato and blueberry leaves: one flat card
per frond, textured with a feathery leaf whose transparent areas cut out the
fine outline. That keeps them thin and detailed instead of chunky geometry.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
UNITY_CARROT = os.path.join(REPO, "unity", "BinaryNestModAssets", "Assets", "Farming", "Carrot")
EXPORT_DIR = os.path.join(UNITY_CARROT, "Models")
TEXTURE_DIR = os.path.join(UNITY_CARROT, "Textures")
PREVIEW_DIR = os.path.join(HERE, "previews")
for d in (EXPORT_DIR, TEXTURE_DIR, PREVIEW_DIR):
    os.makedirs(d, exist_ok=True)

STAGES = [
    dict(name="CarrotSeedling", fronds=3,  length=(0.09, 0.13), shoulder=0.0,   seed=11),
    dict(name="CarrotGrowth",   fronds=5,  length=(0.20, 0.28), shoulder=0.016, seed=22),
    dict(name="CarrotHarvest",  fronds=7, length=(0.34, 0.46), shoulder=0.032, seed=33),
]

# Two muted greens, one per texture tile; each frond picks one (sRGB).
FROND_VARIANTS = [
    (0.13, 0.26, 0.07),
    (0.17, 0.29, 0.09),
]
STALK_RGB = (0.17, 0.29, 0.10)
ROOT_RGB = (0.80, 0.32, 0.05)
FROND_TILE = (256, 512)    # one frond per tile: u across the frond, v from base to tip
FROND_WIDTH = 0.42         # card width as a fraction of the frond's length
CARD_START = 0.22          # the leafy card starts this far along the stalk

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


# --------------------------------------------------------------------------
# Frond texture (RGBA): a pinnate carrot leaf with finely divided leaflets.
# Drawn at 2x and averaged down for soft edges.
# --------------------------------------------------------------------------
def make_frond_texture():
    tw, th = FROND_TILE
    ss = 2
    W, H = tw * ss * len(FROND_VARIANTS), th * ss
    rgba = [None] * (W * H)

    def put(x, y, col):
        if 0 <= x < W and 0 <= y < H:
            rgba[y * W + x] = col

    def ellipse(cx, cy, rx, ry, ang, col):
        """Filled, rotated ellipse in pixel space."""
        ca, sa = math.cos(ang), math.sin(ang)
        ext = int(max(rx, ry)) + 1
        for y in range(int(cy) - ext, int(cy) + ext + 1):
            for x in range(int(cx) - ext, int(cx) + ext + 1):
                dx, dy = x - cx, y - cy
                lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
                if (lx / rx) ** 2 + (ly / ry) ** 2 <= 1.0:
                    put(x, y, col)

    def line(x0, y0, x1, y1, r, col):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) / max(r * 0.7, 0.7)) + 1
        for i in range(steps + 1):
            t = i / steps
            ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r, 0.0, col)

    def shade(rgb, k):
        return (min(rgb[0] * k, 1.0), min(rgb[1] * k, 1.0), min(rgb[2] * k, 1.0), 1.0)

    def half_width(v):
        """Frond outline: widest about a third of the way up, narrow tip."""
        if v < 0.32:
            return 0.46 * (v / 0.32) ** 0.55
        return 0.46 * max(1.0 - (v - 0.32) / 0.68, 0.0) ** 0.85

    for variant, base_rgb in enumerate(FROND_VARIANTS):
        rng = random.Random(100 + variant)
        ox = variant * tw * ss

        def px_u(u):
            return ox + u * tw * ss

        def px_v(v):
            return v * th * ss

        stem = shade(base_rgb, 1.35)
        levels = 11                                   # pairs of side branches (pinnae)
        for k in range(levels):
            v0 = 0.05 + 0.9 * k / levels + rng.uniform(-0.012, 0.012)
            for side in (-1, 1):
                v0s = v0 + (0.025 if side > 0 else 0.0) + rng.uniform(-0.01, 0.01)
                hw = half_width(min(v0s + 0.06, 1.0))
                if hw < 0.03:
                    continue
                u1 = 0.5 + side * hw * rng.uniform(0.75, 0.98)
                v1 = min(v0s + hw * rng.uniform(0.4, 0.7) + 0.02, 0.995)
                x0, y0, x1, y1 = px_u(0.5), px_v(v0s), px_u(u1), px_v(v1)
                dirx, diry = x1 - x0, y1 - y0
                blen = math.hypot(dirx, diry)
                bang = math.atan2(diry, dirx)
                n = max(3, int(hw * 16))              # leaflets along the branch
                for j in range(n):
                    f = (j + 0.6) / n
                    cx, cy = x0 + dirx * f, y0 + diry * f
                    plen = blen * (0.22 - 0.10 * f) * rng.uniform(0.85, 1.15)
                    for up in (1, -1):
                        if rng.random() < 0.18:               # a few leaflets missing
                            continue
                        a = bang + up * math.radians(rng.uniform(28, 62))
                        col = shade(base_rgb, rng.uniform(0.85, 1.12) * (0.9 + 0.2 * v0s))
                        # 2-3 narrow lobes per leaflet: the feathery carrot look
                        for lobe in range(rng.choice((2, 3))):
                            la = a + math.radians((lobe - 1) * 14)
                            ex = cx + math.cos(la) * plen * 0.5
                            ey = cy + math.sin(la) * plen * 0.5
                            ellipse(ex, ey, plen * 0.5, max(plen * 0.08, 1.4), la, col)
                line(x0, y0, x1, y1, 1.4, stem)
        line(px_u(0.5), px_v(0.0), px_u(0.5), px_v(0.97), 2.4, stem)   # main stem

    # Average 2x2 down. Transparent pixels keep the leaf colour so filtered
    # edges don't get dark fringes.
    fill = (*FROND_VARIANTS[0], 0.0)
    w, h = W // ss, H // ss
    px = [0.0] * (w * h * 4)
    for y in range(h):
        for x in range(w):
            r = g = b = 0.0
            n_col = 0
            for sy in range(ss):
                for sx in range(ss):
                    c = rgba[(y * ss + sy) * W + x * ss + sx]
                    if c is not None:
                        r += c[0]
                        g += c[1]
                        b += c[2]
                        n_col += 1
            i = (y * w + x) * 4
            if n_col:
                px[i:i + 4] = (r / n_col, g / n_col, b / n_col, n_col / (ss * ss))
            else:
                px[i:i + 4] = fill
    img = bpy.data.images.new("CarrotFrond", w, h, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels = px
    img.filepath_raw = os.path.join(TEXTURE_DIR, "CarrotFrond.png")
    img.file_format = "PNG"
    img.save()
    return img


FROND_IMAGE = make_frond_texture()


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_material(name, rgb, roughness=0.6, image=None, cutout=False):
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
        if cutout:
            mat.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    mat.use_backface_culling = False
    mat.diffuse_color = (*rgb, 1.0)
    return mat


MAT_STALK = make_material("CarrotStalk", STALK_RGB, 0.8)
MAT_LEAF = make_material("CarrotLeaf", (1, 1, 1), 0.55, FROND_IMAGE, cutout=True)
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


# Levels of detail. LOD0 is the full model; the game switches to the others
# as the plant gets smaller on screen. All LODs use the same random seed, so
# fronds sit in the same places.
LODS = [
    dict(card_segs=6, stalk_sides=5, stalk_points=5, root_sides=12, root_rings=9),
    dict(card_segs=4, stalk_sides=4, stalk_points=4, root_sides=8,  root_rings=6),
    dict(card_segs=2, stalk_sides=3, stalk_points=3, root_sides=6,  root_rings=4),
]


def add_frond_card(bm, uv_layer, p0, p1, p2, width, segs, variant, roll=0.0, mirror=False):
    """One flat, slightly cupped card following the frond's curve, drawn from
    both sides by the shader (Cull Off). The texture's alpha cuts out the leaf."""
    left, mid, right = [], [], []
    for i in range(segs + 1):
        t = CARD_START + (1.0 - CARD_START) * i / segs
        c = bezier(p0, p1, p2, t)
        tan = bezier_tangent(p0, p1, p2, t)
        side = tan.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
        normal = side.cross(tan).normalized()
        # roll the card around the stalk so fronds don't all face up
        side, normal = (side * math.cos(roll) + normal * math.sin(roll),
                        normal * math.cos(roll) - side * math.sin(roll))
        cup = normal * width * 0.10          # edges sit a little below the midrib
        left.append(bm.verts.new(c - side * width * 0.5 - cup))
        mid.append(bm.verts.new(c))
        right.append(bm.verts.new(c + side * width * 0.5 - cup))
    tiles = len(FROND_VARIANTS)
    for i in range(segs):
        for quad, us in (((left[i], mid[i], mid[i + 1], left[i + 1]), (0.0, 0.5, 0.5, 0.0)),
                         ((mid[i], right[i], right[i + 1], mid[i + 1]), (0.5, 1.0, 1.0, 0.5))):
            f = bm.faces.new(quad)
            f.material_index = MAT_INDEX["leaf"]
            f.smooth = True
            for loop, u, row in zip(f.loops, us, (i, i, i + 1, i + 1)):
                uu = 1.0 - u if mirror else u               # mirrored fronds break repetition
                loop[uv_layer].uv = Vector(((variant + uu) / tiles, row / segs))


def add_frond(bm, uv_layer, rng, azimuth, length, lod):
    out = Vector((math.cos(azimuth), math.sin(azimuth), 0))
    elev = math.radians(rng.uniform(50, 80))
    droop = rng.uniform(0.15, 0.35)
    variant = rng.randrange(len(FROND_VARIANTS))
    width = length * FROND_WIDTH * rng.uniform(0.8, 1.1)
    roll = math.radians(rng.uniform(-40, 40))
    mirror = rng.random() < 0.5
    p0 = out * 0.004
    p1 = p0 + (out * math.cos(elev) + Vector((0, 0, math.sin(elev)))) * length * 0.6
    p2 = p0 + out * length * (0.55 + droop) + Vector((0, 0, length * (0.85 - droop)))

    # thin stalk (petiole) up to just past where the leafy card begins
    n = lod["stalk_points"]
    add_tube(bm, [bezier(p0, p1, p2, CARD_START * 1.3 * i / (n - 1)) for i in range(n)],
             length * 0.011, length * 0.007, lod["stalk_sides"], MAT_INDEX["stalk"])
    add_frond_card(bm, uv_layer, p0, p1, p2, width, lod["card_segs"], variant, roll, mirror)


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


def build_stage(cfg, lod_index=0):
    lod = LODS[lod_index]
    rng = random.Random(cfg["seed"])
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    n = cfg["fronds"]
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.55, 0.55)   # irregular spacing
        add_frond(bm, uv_layer, rng, az, rng.uniform(*cfg["length"]), lod)
    if cfg["shoulder"] > 0:
        add_root(bm, cfg["shoulder"], 0.13, cfg["shoulder"] * 1.4,
                 sides=lod["root_sides"], rings_n=lod["root_rings"], rng=rng)
    return finish_object(bm, f"{cfg['name']}_LOD{lod_index}")


# --------------------------------------------------------------------------
# Build and export the growth stages
# --------------------------------------------------------------------------
stage_lods = {cfg["name"]: [build_stage(cfg, i) for i in range(len(LODS))] for cfg in STAGES}
models = [lods[0] for lods in stage_lods.values()]   # LOD0s, used for previews

# One FBX per stage holding <Stage>_LOD0.._LOD2. Unity groups them by suffix.
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
    print(f"[carrot] {name}: tris " + " / ".join(f"LOD{i} {c}" for i, c in enumerate(counts))
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
    render(os.path.join(PREVIEW_DIR, f"{obj.name.rsplit('_LOD', 1)[0]}.png"), 900, 900)

# --- LOD comparison for the grown carrot ------------------------------------
lod_objs = stage_lods["CarrotHarvest"]
for i, o in enumerate(lod_objs):
    o.location = ((i - 1) * 1.05, 30.0, 0.0)
show_only(lod_objs)
cam_data.type = "PERSP"
cam_data.lens = 50
aim((0.0, 30.0 - 4.2, 1.5), (0.0, 30.0, 0.12))
render(os.path.join(PREVIEW_DIR, "carrot_harvest_lods.png"), 1500, 600)

# Leave the file in an editable state
for o in scene.objects:
    o.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "carrot.blend"))
print("[carrot] saved carrot.blend")
