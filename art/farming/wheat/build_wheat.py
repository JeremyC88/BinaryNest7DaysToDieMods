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
        Textures/WheatPlant.png               RGBA atlas: ears, stems and leaves (green + gold)

Scale: 1 Blender unit = 1 metre = 1 game block. Each model's origin is where
the plant meets the soil.

Like the vanilla plants, everything is drawn on flat cut-out cards: thin
crossed cards for each stem (a real wheat stem is only ~3-4 mm across), crossed
cards for each ear with the spikelets and bristles in the texture, and single
cards for the leaves. The texture's transparency cuts out the shapes.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

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
    dict(name="WheatSeedling", seed=51, colour="green", stalks=0, blades=7, blade_len=(0.08, 0.15)),
    dict(name="WheatGrowth", seed=52, colour="green", stalks=14, height=(0.36, 0.50), blades=4,
         blade_len=(0.12, 0.20), leaves=(2, 3), leaf_len=(0.14, 0.22), ear_scale=0.62, lean=0.10),
    dict(name="WheatHarvest", seed=53, colour="gold", stalks=22, height=(0.72, 0.92), blades=0,
         blade_len=(0.1, 0.1), leaves=(2, 2), leaf_len=(0.16, 0.24), ear_scale=1.0, lean=0.16),
]

# Colours (sRGB)
COLOURS = {
    "green": dict(stem=(0.30, 0.42, 0.15), leaf=(0.22, 0.36, 0.12), grain=(0.46, 0.55, 0.24), awn=(0.55, 0.62, 0.32)),
    "gold": dict(stem=(0.78, 0.63, 0.35), leaf=(0.70, 0.57, 0.31), grain=(0.80, 0.62, 0.30), awn=(0.88, 0.75, 0.48)),
}

# Atlas layout (final pixels, 512 x 512): x0, y0, width, height. v=0 is the base.
ATLAS = 512
RECTS = {
    ("ear", "green"): (0, 0, 128, 256),
    ("ear", "gold"): (128, 0, 128, 256),
    ("leaf", "green"): (256, 0, 64, 512),
    ("leaf", "gold"): (320, 0, 64, 512),
    ("stem", "green"): (384, 0, 32, 512),
    ("stem", "gold"): (416, 0, 32, 512),
}
EAR_W, EAR_H = 0.05, 0.16      # ear card size (m), incl. bristles, at ear_scale 1
STEM_W = 0.007                 # stem card width (m); the stem itself is ~half of it
LEAF_W = 0.017                 # leaf card width (m); the blade shape comes from the texture

# Levels of detail (see art guide: ~55% at LOD1, ~15-20% at LOD2).
LODS = [
    dict(stem_cards=2, stem_segs=5, ear_cards=2, leaf_segs=5, leaves_per_stalk=99),
    dict(stem_cards=2, stem_segs=3, ear_cards=2, leaf_segs=3, leaves_per_stalk=99),
    dict(stem_cards=1, stem_segs=2, ear_cards=1, leaf_segs=2, leaves_per_stalk=1),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


# --------------------------------------------------------------------------
# Texture atlas (RGBA), drawn at 2x and averaged down for soft edges
# --------------------------------------------------------------------------
def make_atlas():
    ss = 2
    W = ATLAS * ss
    rgba = [None] * (W * W)

    def paint(rect, inside, col, uv_box=(0.0, 0.0, 1.0, 1.0)):
        """Paint pixels of `rect` whose (u, v) in 0..1 satisfy inside(u, v)."""
        x0, y0, w, h = (c * ss for c in rect)
        u0, v0, u1, v1 = uv_box
        for py in range(max(int(y0 + v0 * h) - 1, y0), min(int(y0 + v1 * h) + 2, y0 + h)):
            v = (py - y0 + 0.5) / h
            for px in range(max(int(x0 + u0 * w) - 1, x0), min(int(x0 + u1 * w) + 2, x0 + w)):
                u = (px - x0 + 0.5) / w
                if inside(u, v):
                    rgba[py * W + px] = col

    def shade(rgb, k):
        return (min(rgb[0] * k, 1.0), min(rgb[1] * k, 1.0), min(rgb[2] * k, 1.0), 1.0)

    # --- ears: drawn in metres so shapes aren't stretched by the card's aspect
    def ear_ellipse(rect, cx, cy, a, b, ang, col):
        """Ellipse in metres: centre (cx, cy), semi-axes a (along ang) and b."""
        ca, sa = math.cos(ang), math.sin(ang)
        r = max(a, b)

        def inside(u, v):
            x, y = (u - 0.5) * EAR_W - cx, v * EAR_H - cy
            lx, ly = x * ca + y * sa, -x * sa + y * ca
            return (lx / a) ** 2 + (ly / b) ** 2 <= 1.0

        box = ((cx - r) / EAR_W + 0.5, (cy - r) / EAR_H, (cx + r) / EAR_W + 0.5, (cy + r) / EAR_H)
        paint(rect, inside, col, box)

    def ear_line(rect, x0, y0, x1, y1, rad, col):
        n = int(math.hypot(x1 - x0, y1 - y0) / (rad * 0.8)) + 1
        for i in range(n + 1):
            t = i / n
            ear_ellipse(rect, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, rad, rad, 0.0, col)

    for colour, c in COLOURS.items():
        rng = random.Random(7 if colour == "gold" else 3)

        # Ear
        rect = RECTS[("ear", colour)]
        ear_line(rect, 0.0, 0.0, 0.0, 0.03, 0.0011, shade(c["stem"], 1.0))
        levels = 15
        awns = []
        for i in range(levels):
            f = i / (levels - 1)
            y = 0.022 + f * 0.092
            side = 1 if i % 2 == 0 else -1
            size = 1.0 - 0.32 * f ** 1.5
            for outer, ang_deg, off in ((0, 16, 0.0030), (1, 36, 0.0050)):
                ang = math.radians(90 - side * ang_deg)          # from vertical, leaning out
                a, b = 0.0068 * size, 0.0031 * size
                cx = side * off * size
                cy = y + outer * 0.0018
                k = rng.uniform(0.9, 1.1)
                ear_ellipse(rect, cx, cy, a * 1.12, b * 1.28, ang, shade(c["grain"], 0.62 * k))   # outline
                ear_ellipse(rect, cx, cy, a, b, ang, shade(c["grain"], k))
                tip = (cx + math.cos(ang) * a, cy + math.sin(ang) * a)
                awn_ang = math.radians(90 - side * ang_deg * 0.45)
                length = rng.uniform(0.032, 0.044) * (0.85 + 0.3 * f)
                awns.append((tip, awn_ang, length))
        ear_ellipse(rect, 0.0, 0.121, 0.0055, 0.0026, math.radians(90), shade(c["grain"], 1.0))
        for (x0, y0), ang, length in awns:
            ear_line(rect, x0, y0, x0 + math.cos(ang) * length, min(y0 + math.sin(ang) * length, EAR_H * 0.995),
                     0.00038, shade(c["awn"], rng.uniform(0.9, 1.08)))

        # Leaf blade: full width at the base tapering to a point, lighter midrib
        rect = RECTS[("leaf", colour)]

        def leaf_inside(u, v):
            hw = 0.44 * (1.0 - v) ** 0.75
            return abs(u - 0.5) <= hw

        paint(rect, leaf_inside, shade(c["leaf"], 1.0))
        paint(rect, lambda u, v: leaf_inside(u, v) and abs(u - 0.5) > 0.30 * (1.0 - v) ** 0.75,
              shade(c["leaf"], 0.82))                                     # darker edges
        paint(rect, lambda u, v: abs(u - 0.5) < 0.035 and v < 0.97, shade(c["leaf"], 1.25))  # midrib

        # Stem: round-looking (darker edges, lighter centre) with a few nodes
        rect = RECTS[("stem", colour)]
        paint(rect, lambda u, v: 0.25 <= u <= 0.75, shade(c["stem"], 0.8))
        paint(rect, lambda u, v: 0.36 <= u <= 0.64, shade(c["stem"], 1.05))
        for node_v in (0.22, 0.45, 0.66, 0.84):
            paint(rect, lambda u, v, n=node_v: 0.22 <= u <= 0.78 and abs(v - n) < 0.006,
                  shade(c["stem"], 0.7))

    # Average down. Transparent pixels take a neutral straw-green so filtered
    # edges don't get dark fringes.
    fill = (0.5, 0.5, 0.25, 0.0)
    px = [0.0] * (ATLAS * ATLAS * 4)
    for y in range(ATLAS):
        for x in range(ATLAS):
            r = g = b = 0.0
            n = 0
            for sy in range(ss):
                for sx in range(ss):
                    col = rgba[(y * ss + sy) * W + x * ss + sx]
                    if col is not None:
                        r += col[0]
                        g += col[1]
                        b += col[2]
                        n += 1
            i = (y * ATLAS + x) * 4
            px[i:i + 4] = (r / n, g / n, b / n, n / (ss * ss)) if n else fill
    img = bpy.data.images.new("WheatPlant", ATLAS, ATLAS, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels = px
    img.filepath_raw = os.path.join(TEXTURE_DIR, "WheatPlant.png")
    img.file_format = "PNG"
    img.save()
    return img


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_material(name, rgb, roughness=0.6, image=None, cutout=False):
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
        if cutout:
            mat.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    mat.use_backface_culling = False
    mat.diffuse_color = (*rgb, 1.0)
    return mat


ATLAS_IMAGE = make_atlas()
MAT_PLANT = make_material("WheatPlant", (1, 1, 1), 0.75, ATLAS_IMAGE, cutout=True)
MAT_SOIL = make_material("PreviewSoil", (0.16, 0.10, 0.06), 0.95)


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


def add_strip(bm, uv_layer, centres, sides, width, rect):
    """A flat card along `centres`, `width` wide across `sides`, textured with
    the atlas `rect` (u across, v along from the first centre to the last)."""
    x0, y0, w, h = rect
    n = len(centres)
    left = [bm.verts.new(c - s * width * 0.5) for c, s in zip(centres, sides)]
    right = [bm.verts.new(c + s * width * 0.5) for c, s in zip(centres, sides)]
    for i in range(n - 1):
        f = bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
        f.smooth = True
        for loop, (u, v) in zip(f.loops, ((0, i), (1, i), (1, i + 1), (0, i + 1))):
            loop[uv_layer].uv = Vector(((x0 + u * w) / ATLAS, (y0 + v / (n - 1) * h) / ATLAS))


def add_crossed(bm, uv_layer, points, width, rect, cards):
    """1 or 2 cards along `points`; 2 cards are crossed at 90 degrees (an X
    from above) so the stem or ear looks solid from every side."""
    tangents = []
    for i, p in enumerate(points):
        d = (points[i + 1] - p) if i < len(points) - 1 else (p - points[i - 1])
        tangents.append(d.normalized())
    bases = [perpendicular_basis(t) for t in tangents]
    add_strip(bm, uv_layer, points, [a for a, _ in bases], width, rect)
    if cards > 1:
        add_strip(bm, uv_layer, points, [b for _, b in bases], width, rect)


def add_blade(bm, uv_layer, base, direction_xy, length, droop, segs, rect, lift=0.0):
    """Arching leaf blade card from base (blade shape from the texture)."""
    out = Vector((direction_xy.x, direction_xy.y, 0)).normalized()
    p0 = base
    p1 = base + out * length * 0.25 + Vector((0, 0, length * (0.75 + lift)))
    p2 = base + out * length * (0.55 + droop) + Vector((0, 0, length * (0.55 - droop)))
    centres, sides = [], []
    for i in range(segs + 1):
        t = i / segs
        tan = bezier_tangent(p0, p1, p2, t)
        side = tan.cross(Vector((0, 0, 1)))
        centres.append(bezier(p0, p1, p2, t))
        sides.append(side.normalized() if side.length > 1e-6 else Vector((1, 0, 0)))
    add_strip(bm, uv_layer, centres, sides, LEAF_W, rect)


def finish_object(bm, name):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(MAT_PLANT)
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
                           ear_turn=rng.uniform(0, math.pi)))
    blades = []
    for i in range(cfg["blades"]):
        ang = 2 * math.pi * i / max(cfg["blades"], 1) + rng.uniform(-0.3, 0.3)
        blades.append((ang, rng.uniform(*cfg["blade_len"]), rng.uniform(0.1, 0.35)))
    return stalks, blades


def build_stage(cfg, plan, lod_index):
    lod = LODS[lod_index]
    colour = cfg["colour"]
    stalks, blades = plan
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for ang, length, droop in blades:
        add_blade(bm, uv_layer, Vector((0, 0, 0)), Vector((math.cos(ang), math.sin(ang), 0)),
                  length, droop, lod["leaf_segs"], RECTS[("leaf", colour)])
    for s in stalks:
        h = s["height"]
        p0 = s["base"]
        p2 = p0 + s["lean_dir"] * h * s["lean"] + Vector((0, 0, h))
        p1 = p0 + s["lean_dir"] * h * s["lean"] * 0.2 + Vector((0, 0, h * 0.6))
        n = lod["stem_segs"] + 1
        add_crossed(bm, uv_layer, [bezier(p0, p1, p2, i / (n - 1)) for i in range(n)],
                    STEM_W, RECTS[("stem", colour)], lod["stem_cards"])
        for frac, ang, length, droop in s["leaves"][:lod["leaves_per_stalk"]]:
            add_blade(bm, uv_layer, bezier(p0, p1, p2, frac), Vector((math.cos(ang), math.sin(ang), 0)),
                      length, droop, lod["leaf_segs"], RECTS[("leaf", colour)], lift=-0.35)
        # Ear: crossed cards continuing along the stem's direction from its top.
        sc = cfg["ear_scale"]
        t = bezier_tangent(p0, p1, p2, 1.0)
        start = p2 - t * 0.02 * sc
        ear_pts = [start + t * EAR_H * sc * k / 2 for k in range(3)]
        add_crossed(bm, uv_layer, ear_pts, EAR_W * sc, RECTS[("ear", colour)], lod["ear_cards"])
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
