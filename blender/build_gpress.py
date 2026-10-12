"""
Gutenbergs Druckerpresse — prozeduraler Blender-Aufbau + Animation + Export.

Einheiten: 1 Blender-Einheit = 1 dm (10 cm). Z = oben, -Y = vorne (Ausfahrseite des Karrens).
Im offenen Blender ausführen (z. B. über die MCP-Brücke):  exec(open(PFAD).read())
Schreibt: blender/gpress.blend, web/models/gpress.glb, web/models/timeline.json,
          web/models/bogen.jpg (Abzug, in Blender gerendert), web/models/bogen_rubr.jpg (mit Initiale)
"""
import bpy, bmesh, math, random, json, os, time
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler, noise
from bpy_extras import anim_utils

ROOT = "/Users/sim/Documents/lmgMINIprojekte/BLENDERgpress"
GLB_PATH = os.path.join(ROOT, "web/models/gpress.glb")
TIMELINE_PATH = os.path.join(ROOT, "web/models/timeline.json")
BLEND_PATH = os.path.join(ROOT, "blender/gpress.blend")
TEX_DIR = os.path.join(ROOT, "blender/tex")
FONT_PATH = "/System/Library/Fonts/Supplemental/STIXTwoMath.otf"
os.makedirs(TEX_DIR, exist_ok=True)

FPS = 30
DUR = 63.0
F_END = int(DUR * FPS)
KEY_STEP = 2
rng = random.Random(42)
t0_build = time.time()

# ---------------------------------------------------------------- timing (seconds)
PH = [
    (0.0, 6.0, "letter"), (6.0, 16.0, "setzen"), (16.0, 21.0, "form"), (21.0, 29.0, "einfaerben"),
    (29.0, 37.0, "papier"), (37.0, 40.5, "einfahren"), (40.5, 45.5, "drucken"), (45.5, 50.0, "ausfahren"),
    (50.0, 57.0, "bogen"), (57.0, 63.0, "rubrik"),
]
T_INK = (25.3, 28.0)
T_PRINT = 42.6
T_RUBRIC = (58.6, 61.0)

# ---------------------------------------------------------------- dimensions (dm)
Z_RAIL = 6.4                 # top of the iron rails
Z_CAR = Z_RAIL + 0.175       # carriage plank centre
Z_STONE_TOP = Z_RAIL + 0.35 + 0.40
TYPE_H = 0.236               # Schrifthöhe 23,6 mm
Z_T = Z_STONE_TOP + TYPE_H   # printing surface (top of the type)
FORME_Y = 0.5                # forme centre in carriage-local Y
HINGE_Y = FORME_Y - 2.1      # tympan hinge (carriage-local)
Y_IN, Y_OUT = -FORME_Y, -7.5 # carriage positions (world Y of carriage origin)
TYMP_OPEN = math.radians(125)
FRIS_OPEN = math.radians(150)
PLATEN_REST = Z_T + 0.27     # platen underside at rest
PLATEN_DROP = 0.17
BAR_PULL = math.radians(-80)
DRUM_R = 0.55

# type
EM = 0.52                    # Blender font size; gives an x-height of ≈ 7 mm (≈ 3× real B42 type, for readability)
LEAD = 0.215                 # line pitch (Kegelstärke)
COL_W = 2.9                  # column width
GAP = 0.005                  # sidebearing per sort
INIT_W = 0.46                # space left free for the hand-painted initial (lines 1–4)
TEXT = ("n principio creauit deus celum et terram. Terra autem erat inanis et uacua: et tenebre erant "
        "super faciem abissi: et spiritus domini ferebatur super aquas. Dixitq; deus. Fiat lux. "
        "Et facta est lux. Et uidit deus lucem q esset bona: et diuisit lucem a tenebris. Appellauitq; lucem diem "
        "et tenebras noctem. Factumq; est uespere et mane dies unus. Dixit quoq; deus. Fiat firmamentum in medio "
        "aquarum: et diuidat aquas ab aquis. Et fecit deus firmamentum.")
N_LINES = 10

# ---------------------------------------------------------------- helpers
def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def make_mat(name, hexcol, rough=0.5, metal=0.0, coat=0.0, emit=None, image=None, alpha=1.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    col = srgb(hexcol)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*srgb(emit[0]), 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    if image is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = image
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    m.diffuse_color = (*col, 1)
    return m


def write_anim(obj, frames, loc=None, quat=None, scale=None):
    ad = obj.animation_data_create()
    act = bpy.data.actions.new(obj.name + "_Action")
    ad.action = act
    slot = act.slots.new(id_type="OBJECT", name=obj.name)
    ad.action_slot = slot
    cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)

    def put(path, arr):
        arr = np.asarray(arr, dtype=np.float32)
        for idx in range(arr.shape[1]):
            fc = cb.fcurves.new(path, index=idx)
            fc.keyframe_points.add(len(frames))
            co = np.empty(len(frames) * 2, dtype=np.float32)
            co[0::2] = frames
            co[1::2] = arr[:, idx]
            fc.keyframe_points.foreach_set("co", co)
            fc.keyframe_points.foreach_set("interpolation", np.ones(len(frames), dtype=np.int32))
            fc.update()

    if loc is not None:
        put("location", loc)
    if quat is not None:
        obj.rotation_mode = "QUATERNION"
        q = np.asarray(quat, dtype=np.float32)
        for i in range(1, len(q)):
            if np.dot(q[i], q[i - 1]) < 0:
                q[i] = -q[i]
        put("rotation_quaternion", q)
    if scale is not None:
        put("scale", scale)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.actions, bpy.data.cameras,
                 bpy.data.lights, bpy.data.images, bpy.data.fonts):
        for d in list(coll):
            if d.users == 0 or coll is not bpy.data.fonts:
                try:
                    coll.remove(d)
                except Exception:
                    pass
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


reset()
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 0
scene.frame_end = F_END
scene.unit_settings.system = "NONE"
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.color = (0.003, 0.005, 0.009)
try:
    scene.world.use_nodes = True
except Exception:
    pass
_bg = scene.world.node_tree.nodes.get("Background")
if _bg:
    _bg.inputs["Color"].default_value = (0.003, 0.005, 0.009, 1)
    _bg.inputs["Strength"].default_value = 1.0
LINK = scene.collection


def new_obj(name, me, parent=None, loc=(0, 0, 0), rot=None):
    o = bpy.data.objects.new(name, me)
    LINK.objects.link(o)
    if parent:
        o.parent = parent
    o.location = loc
    if rot is not None:
        o.rotation_euler = rot
    return o


def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None)
    LINK.objects.link(o)
    o.empty_display_size = 0.3
    if parent:
        o.parent = parent
    o.location = loc
    return o


def wood_uv(bm, size, scale=4.0, seed=0.0):
    """Planar box mapping with the grain running along the longest axis of the part."""
    uvl = bm.loops.layers.uv.verify()
    long_ax = int(np.argmax(size))
    off = Vector((seed * 0.37 % 1, seed * 0.61 % 1))
    for f in bm.faces:
        n = f.normal
        a = int(np.argmax([abs(n.x), abs(n.y), abs(n.z)]))
        plane = [i for i in range(3) if i != a]
        ua = long_ax if long_ax in plane else plane[0]
        va = plane[1] if ua == plane[0] else plane[0]
        for l in f.loops:
            co = l.vert.co
            l[uvl].uv = (co[ua] / scale + off.x, co[va] / (scale * 1.1) + off.y)


def box_mesh(name, size, bevel=0.0, uv=None, mat=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect="EDGES", profile=0.5)
    if uv is not None:
        wood_uv(bm, size, *uv)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    return me


def box(name, size, loc, mat, parent=None, bevel=0.0, wood=False, rot=None):
    uv = (4.0, rng.random() * 10) if wood else None
    return new_obj(name, box_mesh(name, size, bevel, uv, mat), parent, loc, rot)


def cyl_mesh(name, r, h, mat=None, segs=24, axis="Z", r2=None, uv=False):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    if uv:
        wood_uv(bm, (r, r, h) if axis == "Z" else (h, r, r), 4.0, rng.random() * 10)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = len(p.vertices) == 4
    if mat:
        me.materials.append(mat)
    return me


def cyl(name, r, h, loc, mat, parent=None, axis="Z", segs=24, r2=None, wood=False):
    return new_obj(name, cyl_mesh(name, r, h, mat, segs, axis, r2, wood), parent, loc)


def join_into(name, objs, parent=None):
    """Join several objects (keeps materials) into one object named `name`."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    if parent:
        mw = o.matrix_world.copy()
        o.parent = parent
        o.matrix_world = mw
    return o


# ---------------------------------------------------------------- textures (generated, no downloads)
def save_np_image(name, arr, path):
    h, w, _ = arr.shape
    img = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "JPEG"
    img.save()
    img.reload()
    return img


def wood_texture(name, light, dark, W=1024, H=512, rings=12.0, seed=0.0):
    """Long-grain wood: gently wavering growth rings plus fine fibre streaks (grain runs along U)."""
    rs = np.random.RandomState(int(seed * 100) + 3)
    u = np.linspace(0, 1, W, dtype=np.float32)[None, :].repeat(H, 0)
    v = np.linspace(0, 1, H, dtype=np.float32)[:, None].repeat(W, 1)

    def noise1d(n, k):
        x = rs.rand(k + 1).astype(np.float32)
        x[-1] = x[0]
        return np.interp(np.linspace(0, k, n), np.arange(k + 1), x).astype(np.float32)

    warp = 0.018 * np.sin(2 * np.pi * (u * 1.0 + rs.rand())) + 0.01 * np.sin(2 * np.pi * (u * 2.0 + rs.rand()))
    phase = (v + warp) * rings + 1.5 * noise1d(H, 9)[:, None]
    g = 0.5 + 0.5 * np.sin(2 * np.pi * phase)
    g = g ** 3                                              # narrow dark late-wood lines
    fib = noise1d(H, 180)[:, None] * 0.6 + noise1d(H, 60)[:, None] * 0.4
    fib = fib * (0.85 + 0.15 * noise1d(W, 7)[None, :])
    k = np.clip(0.45 * g + 0.4 * fib + 0.15 * noise1d(H, 5)[:, None], 0, 1)[..., None]
    a, b = np.array(srgb(light), dtype=np.float32), np.array(srgb(dark), dtype=np.float32)
    col = a * (1 - k) + b * k
    col = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(col, 1 / 2.4) - 0.055)
    return save_np_image(name, col, os.path.join(TEX_DIR, name + ".jpg"))


IMG_OAK = wood_texture("eiche", "#a77a4c", "#6b4527", seed=1.0)
IMG_FLOOR = wood_texture("dielen", "#6d4c33", "#3b2717", rings=9.0, seed=2.0)

# ---------------------------------------------------------------- materials
M = {
    "eiche": make_mat("Eiche", "#9a6c42", 0.62, image=IMG_OAK),
    "eiche_dunkel": make_mat("Eiche_dunkel", "#6e4a2c", 0.55, image=IMG_OAK),
    "dielen": make_mat("Dielen", "#5a3d27", 0.75, image=IMG_FLOOR),
    "eisen": make_mat("Eisen", "#3d3f44", 0.42, metal=0.85),
    "messing": make_mat("Messing", "#b68a3e", 0.32, metal=1.0),
    "stein": make_mat("Marmor", "#9a968e", 0.35, coat=0.25),
    "leder": make_mat("Leder", "#6a4229", 0.72),
    "farbe": make_mat("Druckerschwaerze", "#0b0b0d", 0.22, coat=0.6),
    "papier": make_mat("Papier", "#efe7d3", 0.85),
    "pergament": make_mat("Pergament", "#dcc79d", 0.7),
    "kegel": make_mat("Letter_Kegel", "#8f9297", 0.38, metal=0.9),
    "bild": make_mat("Letter_Bild", "#a7aaaf", 0.28, metal=0.95),
    "signatur": make_mat("Letter_Signatur", "#4d5056", 0.5, metal=0.7),
    "kasten_lettern": make_mat("Kasten_Lettern", "#7b7f85", 0.45, metal=0.8),
    "rot": make_mat("Rubrik", "#b3261e", 0.6),
}

# ---------------------------------------------------------------- floor
floor = box("Boden_NOSHADOW", (60, 60, 0.2), (0, -3, -0.1), M["dielen"], wood=False)
bm = bmesh.new(); bm.from_mesh(floor.data); wood_uv(bm, (60, 60, 0.2), 6.0, 0.3); bm.to_mesh(floor.data); bm.free()
floor.name = "Boden"

# ---------------------------------------------------------------- press frame (Gestell)
W_X = 5.0                    # cheek centre x
for s, side in ((-1, "L"), (1, "R")):
    box(f"Wange_{side}", (2.0, 2.6, 17.2), (s * W_X, 0, 8.6), M["eiche"], bevel=0.05, wood=True)
    box(f"Schwelle_{side}", (2.4, 12.0, 1.4), (s * W_X, 0, 0.7), M["eiche_dunkel"], bevel=0.06, wood=True)
    # knee braces
    for sy in (-1, 1):
        b = box(f"Strebe_{side}{'v' if sy < 0 else 'h'}", (1.0, 4.6, 1.0), (s * W_X, sy * 2.6, 2.6), M["eiche_dunkel"], bevel=0.04, wood=True)
        b.rotation_euler = (math.radians(-45 * sy), 0, 0)
box("Krone", (12.6, 3.2, 1.0), (0, 0, 17.7), M["eiche_dunkel"], bevel=0.06, wood=True)
box("Kopf", (8.0, 3.0, 2.0), (0, 0, 13.8), M["eiche"], bevel=0.05, wood=True)
cyl("Kopf_Mutter", 0.85, 0.3, (0, 0, 12.66), M["messing"], segs=6)
box("Bruecke", (8.0, 2.4, 0.8), (0, 0, 10.0), M["eiche"], bevel=0.04, wood=True)
box("Winter", (8.0, 3.0, 1.2), (0, 0, 5.2), M["eiche"], bevel=0.05, wood=True)
# wedges ("Keile") that lock head and till into the cheeks
for s in (-1, 1):
    box(f"Keil_Kopf_{'L' if s < 0 else 'R'}", (0.5, 3.3, 0.6), (s * 4.25, 0, 15.1), M["eiche_dunkel"], bevel=0.02, wood=True)

# rails ("Laufbahn") with legs
RAIL_Y0, RAIL_Y1 = -11.6, 4.6
rail_len = RAIL_Y1 - RAIL_Y0
rail_cy = (RAIL_Y0 + RAIL_Y1) / 2
for s in (-1, 1):
    side = "L" if s < 0 else "R"
    box(f"Bahn_Balken_{side}", (0.7, rail_len, 0.55), (s * 2.1, rail_cy, Z_RAIL - 0.35), M["eiche_dunkel"], bevel=0.03, wood=True)
    box(f"Bahn_Schiene_{side}", (0.22, rail_len, 0.1), (s * 2.1, rail_cy, Z_RAIL - 0.05), M["eisen"])
    for y in (RAIL_Y0 + 0.6, RAIL_Y1 - 0.5):
        box(f"Bahn_Bein_{side}{'v' if y < 0 else 'h'}", (0.6, 0.6, Z_RAIL - 0.6), (s * 2.1, y, (Z_RAIL - 0.6) / 2), M["eiche_dunkel"], bevel=0.03, wood=True)
box("Bahn_Riegel_v", (4.8, 0.5, 0.5), (0, RAIL_Y0 + 0.6, 2.2), M["eiche_dunkel"], bevel=0.03, wood=True)
box("Bahn_Riegel_h", (4.8, 0.5, 0.5), (0, RAIL_Y1 - 0.5, 2.2), M["eiche_dunkel"], bevel=0.03, wood=True)

# rounce (Kurbel) – axle along X beside the rails, drum + crank
KURBEL_LOC = Vector((3.3, -2.6, Z_RAIL - 0.9))
kurbel = empty("Kurbel", KURBEL_LOC)
cyl("Kurbel_Trommel", DRUM_R, 1.0, (0.0, 0, 0), M["eiche"], kurbel, axis="X", wood=True)
cyl("Kurbel_Welle", 0.12, 2.4, (0.9, 0, 0), M["eisen"], kurbel, axis="X")
box("Kurbel_Arm", (0.18, 0.25, 1.9), (2.0, 0, 0.8), M["eisen"], kurbel)
cyl("Kurbel_Griff", 0.16, 0.9, (2.4, 0, 1.6), M["eiche_dunkel"], kurbel, axis="X", wood=True)
box("Kurbel_Lager", (0.5, 0.6, Z_RAIL - 0.9), (KURBEL_LOC.x + 1.4, KURBEL_LOC.y, (Z_RAIL - 0.9) / 2), M["eiche_dunkel"], bevel=0.03, wood=True)

# ---------------------------------------------------------------- type: glyph meshes (gebrochene Schrift)
FONT = bpy.data.fonts.load(FONT_PATH)
FR_CAP = {"C": 0x212D, "H": 0x210C, "I": 0x2111, "R": 0x211C, "Z": 0x2128}


def frak(ch):
    if "a" <= ch <= "z":
        return chr(0x1D51E + ord(ch) - ord("a"))
    if "A" <= ch <= "Z":
        return chr(FR_CAP[ch]) if ch in FR_CAP else chr(0x1D504 + ord(ch) - ord("A"))
    return ch


GLYPH = {}   # ch -> (verts np (N,3), faces list, xmin, xmax)


def glyph(ch):
    if ch in GLYPH:
        return GLYPH[ch]
    cu = bpy.data.curves.new("g", "FONT")
    cu.font = FONT
    cu.body = frak(ch)
    cu.size = EM
    cu.extrude = 0.0
    cu.resolution_u = 4
    ob = bpy.data.objects.new("g", cu)
    LINK.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    if len(bm.verts):
        # extrude the outline into a relief of 1,5 mm
        geom = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        bmesh.ops.translate(bm, vec=(0, 0, 0.015), verts=[e for e in geom["geom"] if isinstance(e, bmesh.types.BMVert)])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        v = np.array([x.co[:] for x in bm.verts], dtype=np.float32)
        bm.verts.index_update()
        f = [[x.index for x in fc.verts] for fc in bm.faces]
        xmin, xmax = float(v[:, 0].min()), float(v[:, 0].max())
    else:
        v, f, xmin, xmax = np.zeros((0, 3), np.float32), [], 0.0, EM * 0.33
    bm.free()
    GLYPH[ch] = (v, f, xmin, xmax)
    return GLYPH[ch]


# measure descent/ascent of the alphabet for the body (Kegel) placement
for c in set(TEXT):
    glyph(c)
allv = np.concatenate([g[0] for g in GLYPH.values() if len(g[0])])
Y_LO, Y_HI = float(allv[:, 1].min()), float(allv[:, 1].max())
BASE_OFF = -(Y_LO + Y_HI) / 2      # shift glyph so the body is centred on it
LEAD = max(LEAD, (Y_HI - Y_LO) + 0.012)
SPACE_W = 0.5 * float(np.median([g[3] - g[2] for c, g in GLYPH.items() if c.isalpha()]))




def adv(ch):
    if ch == " ":
        return SPACE_W
    v, f, a, b = glyph(ch)
    return (b - a) + 2 * GAP


# line breaking + justification (Gutenberg justified every line to the same width)
words = TEXT.split(" ")
lines, cur = [], []
for w in words:
    width_of = lambda ws: sum(adv(c) for c in " ".join(ws))
    avail = COL_W - (INIT_W if len(lines) < 4 else 0)
    if cur and width_of(cur + [w]) > avail:
        lines.append(cur)
        cur = [w]
    else:
        cur.append(w)
lines.append(cur)
lines = lines[:N_LINES]

FORME_X0 = -COL_W / 2
FORME_Y0 = (len(lines) - 1) * LEAD / 2          # first line at the top (+Y before mirroring)
layout = []                                     # per line: list of (ch, x_left, width)
for li, ws in enumerate(lines):
    indent = INIT_W if li < 4 else 0.0
    text = " ".join(ws)
    nat = sum(adv(c) for c in text)
    nsp = text.count(" ")
    extra = (COL_W - indent - nat) / nsp if (nsp and li < len(lines) - 1) else 0.0
    x = FORME_X0 + indent
    row = []
    for c in text:
        w = adv(c) + (extra if c == " " else 0.0)
        row.append((c, x, w))
        x += w
    layout.append(row)


# ---------------------------------------------------------------- spindle, bar, hose, platen
Z_SP_BOT = PLATEN_REST + 0.5
spindel = empty("Spindel", (0, 0, 0))
# screw: core + helical thread between till and head
cyl("Spindel_Kern", 0.42, 13.6 - Z_SP_BOT, (0, 0, (13.6 + Z_SP_BOT) / 2), M["eiche_dunkel"], spindel, segs=28, wood=True)
bm = bmesh.new()
pitch, turns, z_from = 0.55, 4.6, 10.6
prof = [Vector((0.40, 0, -0.17)), Vector((0.62, 0, -0.05)), Vector((0.62, 0, 0.05)), Vector((0.40, 0, 0.17))]
segs = int(turns * 36)
ring_idx = []
for i in range(segs + 1):
    a = 2 * math.pi * i / 36
    z = z_from + pitch * i / 36
    R = Matrix.Rotation(a, 3, "Z")
    ring_idx.append([bm.verts.new(R @ p + Vector((0, 0, z))) for p in prof])
for i in range(segs):
    for j in range(len(prof) - 1):
        bm.faces.new((ring_idx[i][j], ring_idx[i][j + 1], ring_idx[i + 1][j + 1], ring_idx[i + 1][j]))
me = bpy.data.meshes.new("Spindel_Gewinde"); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
me.materials.append(M["eiche_dunkel"])
new_obj("Spindel_Gewinde", me, spindel)
cyl("Spindel_Bund", 0.62, 0.5, (0, 0, 11.25), M["eisen"], spindel)
# bar ("Bengel") – iron bar through the spindle with a wooden grip
BAR_Z = 11.25
BAR_REST = math.radians(30)
bengel = empty("Bengel", (0, 0, BAR_Z), spindel)
bengel.rotation_euler = (0, 0, BAR_REST)
box("Bengel_Stange", (7.2, 0.24, 0.24), (3.6, 0, 0), M["eisen"], bengel)
g = cyl("Bengel_Griff", 0.24, 2.0, (7.6, 0, -0.3), M["eiche_dunkel"], bengel, axis="X", wood=True)
g.rotation_euler = (0, math.radians(18), 0)

# hose (Büchse) + platen (Tiegel) – translate down while the screw turns
tiegel = empty("Tiegel", (0, 0, 0))
box("Buechse", (1.5, 1.5, 3.4), (0, 0, PLATEN_REST + 0.5 + 1.7), M["eiche"], tiegel, bevel=0.03, wood=True)
box("Tiegel_Platte", (4.0, 3.4, 0.45), (0, 0, PLATEN_REST + 0.225), M["eiche"], tiegel, bevel=0.03, wood=True)
box("Tiegel_Eisen", (4.06, 3.46, 0.06), (0, 0, PLATEN_REST + 0.03), M["eisen"], tiegel)
for s in (-1, 1):
    box(f"Tiegel_Haken_{'L' if s < 0 else 'R'}", (0.12, 0.12, 1.2), (s * 0.85, 0, PLATEN_REST + 1.0), M["eisen"], tiegel).rotation_euler = (0, s * math.radians(35), 0)

# ---------------------------------------------------------------- carriage, stone, chase, tympan, frisket
karren = empty("Karren", (0, Y_OUT, Z_CAR))
box("Karren_Brett", (5.8, 6.6, 0.35), (0, 0, 0), M["eiche"], karren, bevel=0.03, wood=True)
for s in (-1, 1):
    box(f"Karren_Kufe_{'L' if s < 0 else 'R'}", (0.5, 6.4, 0.2), (s * 2.1, 0, -0.18), M["eisen"], karren)
STONE_Z = 0.175 + 0.2
box("Fundament", (4.6, 4.2, 0.4), (0, FORME_Y, STONE_Z), M["stein"], karren, bevel=0.02)
# coffin rim
for nm, sz, lc in (("Sarg_v", (5.4, 0.3, 0.55), (0, FORME_Y - 2.25, 0.45)), ("Sarg_h", (5.4, 0.3, 0.55), (0, FORME_Y + 2.25, 0.45)),
                   ("Sarg_l", (0.3, 4.8, 0.55), (-2.55, FORME_Y, 0.45)), ("Sarg_r", (0.3, 4.8, 0.55), (2.55, FORME_Y, 0.45))):
    box(nm, sz, lc, M["eiche_dunkel"], karren, bevel=0.02, wood=True)
Z_STONE_TOP_L = STONE_Z + 0.2          # carriage-local
# chase (Schließrahmen) with wooden furniture and quoins
CH_W, CH_H = 3.7, len(lines) * LEAD + 0.62
chase = empty("Schliessrahmen", (0, FORME_Y, Z_STONE_TOP_L), karren)
for nm, sz, lc in (("v", (CH_W, 0.14, 0.2), (0, -CH_H / 2, 0.1)), ("h", (CH_W, 0.14, 0.2), (0, CH_H / 2, 0.1)),
                   ("l", (0.14, CH_H, 0.2), (-CH_W / 2, 0, 0.1)), ("r", (0.14, CH_H, 0.2), (CH_W / 2, 0, 0.1))):
    box(f"Schliessrahmen_{nm}", sz, lc, M["eisen"], chase)
box("Steg_l", (0.22, CH_H - 0.14, 0.17), (-CH_W / 2 + 0.18, 0, 0.085), M["eiche"], chase, wood=True)
box("Steg_r", (0.22, CH_H - 0.14, 0.17), (CH_W / 2 - 0.18, 0, 0.085), M["eiche"], chase, wood=True)
for i, x in enumerate((-0.7, 0.7)):
    box(f"Keil_Form_{i}", (0.5, 0.18, 0.15), (x, CH_H / 2 - 0.17, 0.075), M["eiche_dunkel"], chase, wood=True)

# tympan (Deckel) hinged at the outer end of the stone; frisket (Rähmchen) hinged at its far end
TY_W, TY_L = 4.8, 4.2
deckel = empty("Deckel", (0, HINGE_Y, Z_T + 0.05 - Z_CAR), karren)
for nm, sz, lc in (("v", (TY_W, 0.22, 0.09), (0, 0.11, 0)), ("h", (TY_W, 0.22, 0.09), (0, TY_L - 0.11, 0)),
                   ("l", (0.22, TY_L, 0.09), (-TY_W / 2 + 0.11, TY_L / 2, 0)), ("r", (0.22, TY_L, 0.09), (TY_W / 2 - 0.11, TY_L / 2, 0))):
    box(f"Deckel_Rahmen_{nm}", sz, lc, M["eisen"], deckel)
box("Deckel_Pergament", (TY_W - 0.3, TY_L - 0.3, 0.02), (0, TY_L / 2, 0.0), M["pergament"], deckel)
for s in (-1, 1):
    cyl(f"Deckel_Scharnier_{'L' if s < 0 else 'R'}", 0.09, 0.5, (s * 1.6, 0, 0), M["messing"], deckel, axis="X")
# punctures (Punkturen) holding the sheet
for s in (-1, 1):
    cyl(f"Deckel_Punktur_{'L' if s < 0 else 'R'}", 0.03, 0.08, (s * 2.05, TY_L / 2, -0.05), M["eisen"], deckel, r2=0.0)

raehmchen = empty("Raehmchen", (0, TY_L, -0.045), deckel)
win_w, win_l = COL_W + 0.4, len(lines) * LEAD + 0.3
fw = (TY_W - win_w) / 2
fl = (TY_L - win_l) / 2
for nm, sz, lc in (("v", (TY_W, fl, 0.03), (0, -TY_L + fl / 2, 0)), ("h", (TY_W, fl, 0.03), (0, -fl / 2, 0)),
                   ("l", (fw, win_l, 0.03), (-TY_W / 2 + fw / 2, -TY_L / 2, 0)), ("r", (fw, win_l, 0.03), (TY_W / 2 - fw / 2, -TY_L / 2, 0))):
    box(f"Raehmchen_{nm}", sz, lc, M["pergament"], raehmchen)
for s in (-1, 1):
    box(f"Raehmchen_Eisen_{'L' if s < 0 else 'R'}", (0.06, TY_L, 0.05), (s * (TY_W / 2 - 0.03), -TY_L / 2, 0.01), M["eisen"], raehmchen)

# ---------------------------------------------------------------- composing station (Setzpult + Setzkasten + Winkelhaken)
PULT = Vector((-10.2, -4.2, 0))
TILT = math.radians(14)
CASE_W, CASE_D = 6.4, 3.8
case_frame = Matrix.Translation(PULT + Vector((0, 0, 9.6))) @ Matrix.Rotation(TILT, 4, "X")
for sx in (-1, 1):
    for sy in (-1, 1):
        h = 9.6 + sy * math.tan(TILT) * CASE_D / 2 - 0.2
        box(f"Pult_Bein_{sx}{sy}", (0.45, 0.45, h), PULT + Vector((sx * 2.9, sy * 1.6, h / 2)), M["eiche_dunkel"], bevel=0.03, wood=True)
box("Pult_Riegel", (6.0, 0.35, 0.35), PULT + Vector((0, 1.6, 2.0)), M["eiche_dunkel"], wood=True)
box("Pult_Riegel2", (6.0, 0.35, 0.35), PULT + Vector((0, -1.6, 2.0)), M["eiche_dunkel"], wood=True)
kasten = empty("Setzkasten", (0, 0, 0))
kasten.matrix_world = case_frame
box("Setzkasten_Boden", (CASE_W, CASE_D, 0.12), (0, 0, 0), M["eiche"], kasten, wood=True)
NCX, NCY = 14, 7
cw, cd = CASE_W / NCX, CASE_D / NCY
walls = []
for i in range(NCX + 1):
    walls.append(box(f"_w{i}", (0.05, CASE_D, 0.32), (-CASE_W / 2 + i * cw, 0, 0.16), M["eiche_dunkel"], kasten))
for j in range(NCY + 1):
    walls.append(box(f"_h{j}", (CASE_W, 0.05, 0.32), (0, -CASE_D / 2 + j * cd, 0.16), M["eiche_dunkel"], kasten))
join_into("Setzkasten_Faecher", walls, kasten)
# loose sorts lying in the compartments (one merged mesh)
bm = bmesh.new()
for i in range(NCX):
    for j in range(NCY):
        n = rng.randint(10, 26)
        cx = -CASE_W / 2 + (i + 0.5) * cw
        cy = -CASE_D / 2 + (j + 0.5) * cd
        for k in range(n):
            w = 0.05 + rng.random() * 0.06
            r = bmesh.ops.create_cube(bm, size=1.0)
            vs = r["verts"]
            bmesh.ops.scale(bm, vec=(w, 0.2, 0.06), verts=vs)
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(rng.uniform(-0.5, 0.5), 3, "Z") @ Matrix.Rotation(rng.uniform(-0.3, 0.3), 3, "X"))
            bmesh.ops.translate(bm, vec=(cx + rng.uniform(-0.12, 0.12), cy + rng.uniform(-0.12, 0.12), 0.09 + k * 0.006), verts=vs)
me = bpy.data.meshes.new("Setzkasten_Lettern"); bm.to_mesh(me); bm.free()
me.materials.append(M["kasten_lettern"])
new_obj("Setzkasten_Lettern", me, kasten)

def case_slot(ch):
    """World position of the compartment a character is taken from."""
    o = ord(ch.lower()) if ch.strip() else 32
    i = (o * 7) % NCX
    j = (o * 3) % NCY
    p = Vector((-CASE_W / 2 + (i + 0.5) * cw, -CASE_D / 2 + (j + 0.5) * cd, 0.2))
    return case_frame @ p

# composing stick on a ledge in front of the case
STICK = Vector((PULT.x + 0.2, PULT.y - CASE_D / 2 - 0.55, 9.6 - math.tan(TILT) * CASE_D / 2 - 0.05))
box("Pult_Leiste", (CASE_W, 0.7, 0.12), STICK + Vector((-0.2, 0.05, -0.12)), M["eiche"], wood=True)
wh = empty("Winkelhaken", STICK)
box("Winkelhaken_Boden", (3.6, 0.32, 0.03), (0, 0, -0.03), M["eisen"], wh)
box("Winkelhaken_Wand", (3.6, 0.03, 0.26), (0, 0.17, 0.1), M["eisen"], wh)
box("Winkelhaken_Kopf", (0.03, 0.34, 0.26), (-1.8, 0, 0.1), M["eisen"], wh)
box("Winkelhaken_Frosch", (0.08, 0.34, 0.26), (1.55, 0, 0.1), M["messing"], wh)

# ink table and paper bench
def table(name, loc, w, d, h):
    box(f"{name}_Platte", (w, d, 0.25), loc + Vector((0, 0, h - 0.125)), M["eiche"], bevel=0.03, wood=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"{name}_Bein_{sx}{sy}", (0.35, 0.35, h - 0.25), loc + Vector((sx * (w / 2 - 0.3), sy * (d / 2 - 0.3), (h - 0.25) / 2)), M["eiche_dunkel"], wood=True)

FARB = Vector((-6.4, -10.4, 0))
table("Farbtisch", FARB, 3.4, 3.0, 8.4)
box("Farbstein", (2.6, 2.2, 0.2), FARB + Vector((0, 0, 8.5)), M["stein"], bevel=0.02)
box("Farbe_Schicht", (1.8, 1.4, 0.012), FARB + Vector((0, 0.2, 8.606)), M["farbe"])
cyl("Farbe_Spatel", 0.06, 1.4, FARB + Vector((1.0, -0.8, 8.64)), M["eiche_dunkel"], axis="Y", wood=True)
PAP = Vector((9.6, -5.6, 0))
table("Papierbank", PAP, 5.2, 8.4, 8.4)
PAPER_W, PAPER_L = 4.4, 3.6
STACK_BLANK = PAP + Vector((0, -2.0, 8.4))
STACK_DONE = PAP + Vector((0, 2.1, 8.4))
box("Papierstapel", (PAPER_W, PAPER_L, 0.32), STACK_BLANK + Vector((0, 0, 0.16)), M["papier"])
box("Druckstapel", (PAPER_W, PAPER_L, 0.16), STACK_DONE + Vector((0, 0, 0.08)), M["papier"])

def sort_arrays(ch, w):
    """One piece of type: body (Kegel) + raised mirrored glyph (Bild) + nick (Signatur).
    Local origin = centre of the body's foot; X mirrored so the face reads backwards from above."""
    parts = []
    body_h = TYPE_H - 0.015 if ch != " " else TYPE_H * 0.72
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w - 0.002, LEAD - 0.002, body_h), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, body_h / 2), verts=bm.verts)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    parts.append((np.array([v.co[:] for v in bm.verts], np.float32), [[v.index for v in f.verts] for f in bm.faces], 0))
    bm.free()
    if ch != " ":
        # nick: a groove-like dark band across the front side
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w - 0.004, 0.006, 0.018), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, -LEAD / 2, body_h * 0.32), verts=bm.verts)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.verts.index_update()
        parts.append((np.array([v.co[:] for v in bm.verts], np.float32), [[v.index for v in f.verts] for f in bm.faces], 2))
        gv, gf, a, b = glyph(ch)
        v = gv.copy()
        v[:, 0] = -(v[:, 0] - (a + b) / 2)          # mirror (Spiegelschrift) and centre on the body
        v[:, 1] += BASE_OFF
        v[:, 2] += body_h
        parts.append((v, [ff[::-1] for ff in gf], 1))
    return parts


def build_mesh(name, parts_list, mats):
    vs, fs, mi, off = [], [], [], 0
    for v, f, m in parts_list:
        vs.append(v)
        fs += [[i + off for i in ff] for ff in f]
        mi += [m] * len(f)
        off += len(v)
    V = np.concatenate(vs)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], fs)
    me.update()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", mi)
    me.update()
    return me


LETTER_MATS = [M["kegel"], M["bild"], M["signatur"]]
# mirrored slot positions: x -> -x (the forme is the mirror image of the page)
forme = empty("Druckform", (0, 0, 0), chase)
line1 = []
for li, row in enumerate(layout):
    y = FORME_Y0 - li * LEAD
    if li == 0:
        for k, (c, x, w) in enumerate(row):
            me = build_mesh(f"Letter_{k:02d}", sort_arrays(c, w), LETTER_MATS)
            o = new_obj(f"Letter_{k:02d}", me)
            line1.append({"obj": o, "ch": c, "slot": Vector((-(x + w / 2), y, 0)), "w": w})
        continue
    parts = []
    for c, x, w in row:
        for v, f, m in sort_arrays(c, w):
            v = v.copy()
            v[:, 0] += -(x + w / 2)
            v[:, 1] += y
            parts.append((v, f, m))
    new_obj(f"Zeile_{li + 1:02d}", build_mesh(f"Zeile_{li + 1:02d}", parts, LETTER_MATS), forme)
# blank sorts filling the indent for the initial (Ausschluss)
parts = []
for li in range(0, 4):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(INIT_W - 0.002, LEAD - 0.002, TYPE_H * 0.72), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(-(FORME_X0 + INIT_W / 2), FORME_Y0 - li * LEAD, TYPE_H * 0.36), verts=bm.verts)
    bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.index_update()
    parts.append((np.array([v.co[:] for v in bm.verts], np.float32), [[v.index for v in f.verts] for f in bm.faces], 0))
    bm.free()
new_obj("Ausschluss_Initiale", build_mesh("Ausschluss_Initiale", parts, LETTER_MATS), forme)

# ---------------------------------------------------------------- ink balls, paper sheets
def ball(name):
    root = empty(name, (0, 0, 0))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=1.0)
    for v in bm.verts:
        z = v.co.z
        v.co.x *= 0.85
        v.co.y *= 0.85
        v.co.z = max(0.42 * (z + 1), 0.03)
    me = bpy.data.meshes.new(name + "_Leder"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(M["leder"])
    new_obj(name + "_Leder", me, root)
    cyl(name + "_Farbflaeche", 0.78, 0.03, (0, 0, 0.012), M["farbe"], root, segs=28)
    cyl(name + "_Teller", 0.62, 0.14, (0, 0, 0.82), M["eiche"], root, wood=True)
    cyl(name + "_Stiel", 0.17, 2.2, (0, 0, 1.95), M["eiche_dunkel"], root, r2=0.13, wood=True)
    return root


ballA, ballB = ball("Ballen_A"), ball("Ballen_B")

bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=0.5)
bmesh.ops.scale(bm, vec=(PAPER_W, PAPER_L, 1), verts=bm.verts)
paper_me = bpy.data.meshes.new("Bogen"); bm.to_mesh(paper_me); bm.free()
paper_me.materials.append(M["papier"])
PAPER_LOCAL = Matrix.Translation((0, FORME_Y - HINGE_Y, -0.03)) @ Matrix.Rotation(math.pi, 4, "Y")   # inked face = local +Z
bogen_deckel = new_obj("Bogen_Deckel", paper_me, deckel)
bogen_deckel.matrix_parent_inverse = Matrix.Identity(4)
bogen_deckel.matrix_basis = PAPER_LOCAL
bogen_lose = new_obj("Bogen_Lose", paper_me)
bogen_druck = new_obj("Bogen_Gedruckt", paper_me.copy())
druck_oben = new_obj("Druckstapel_Oben", paper_me.copy(), loc=STACK_DONE + Vector((0, 0, 0.165)))


# ---------------------------------------------------------------- pose functions (all in seconds)
def car_y(t):
    return Y_OUT + (Y_IN - Y_OUT) * (ramp(t, 37.2, 40.0) - ramp(t, 45.8, 48.4))


def tymp(t):
    return TYMP_OPEN * (1 - ramp(t, 34.5, 36.5) + ramp(t, 48.4, 50.0))


def fris(t):
    return FRIS_OPEN * (1 - ramp(t, 32.6, 34.2) + ramp(t, 50.0, 51.2))


def bar(t):
    if t < 41.2 or t > 44.6:
        return 0.0
    if t < 42.4:
        return BAR_PULL * smooth((t - 41.2) / 1.2)
    if t < 43.2:
        return BAR_PULL
    return BAR_PULL * (1 - smooth((t - 43.2) / 1.4))


def car_M(t):
    return Matrix.Translation((0, car_y(t), Z_CAR))


def deckel_M(t):
    return car_M(t) @ Matrix.Translation(deckel.location) @ Matrix.Rotation(tymp(t), 4, "X")


def paper_on_tympan_M(t):
    return deckel_M(t) @ PAPER_LOCAL


# slot matrices for line-1 sorts
STICK_X0 = STICK.x + 1.35          # line-1 slots in the stick (right-aligned against the frog)


def forme_slot_M(slot, t):
    p = car_M(t) @ Vector((0, FORME_Y, Z_STONE_TOP_L)) + Vector((slot.x, slot.y, 0))
    return Matrix.Translation(p)


def stick_slot_M(slot):
    return Matrix.Translation(Vector((STICK.x + slot.x * 1.0 + 0.0, STICK.y, STICK.z)))


def lerpM(A, B, k, lift=0.0):
    la, ra, _ = A.decompose()
    lb, rb, _ = B.decompose()
    p = la.lerp(lb, k) + Vector((0, 0, lift * math.sin(math.pi * k)))
    return Matrix.Translation(p) @ ra.slerp(rb, k).to_matrix().to_4x4()


N1 = len(line1)
T_SET0, T_SET1 = 6.4, 15.0
FLY = 0.85


def sort_M(k, t):
    s = line1[k]
    stick = stick_slot_M(s["slot"])
    case = Matrix.Translation(case_slot(s["ch"]) + Vector((0, 0, 0.02))) @ Matrix.Rotation(TILT, 4, "X") @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Translation((0, LEAD / 2, -TYPE_H / 2))
    if k == 0:
        hover = Matrix.Translation(stick.to_translation() + Vector((0, -0.15, 0.55)))
        if t < 5.0:
            spin = Matrix.Rotation(2 * math.pi * t / 5.0, 4, "Z") @ Matrix.Rotation(math.radians(-28), 4, "X")
            return hover @ spin
        if t < 5.8:
            return lerpM(hover @ Matrix.Rotation(math.radians(-28), 4, "X"), stick, smooth((t - 5.0) / 0.8))
        pos = stick
    else:
        ts = T_SET0 + (k - 1) * (T_SET1 - T_SET0 - FLY) / max(1, N1 - 2)
        if t < ts:
            return case
        if t < ts + FLY:
            return lerpM(case, stick, smooth((t - ts) / FLY), lift=0.9)
        pos = stick
    # phase 2: the whole line moves from the stick into the forme
    if t < 16.3:
        return pos
    dest = forme_slot_M(s["slot"], t)
    if t < 17.2:
        return Matrix.Translation((0, 0, 0.9 * smooth((t - 16.3) / 0.9))) @ pos
    up_dest = Matrix.Translation((0, 0, 0.9)) @ dest
    if t < 19.4:
        return lerpM(Matrix.Translation((0, 0, 0.9)) @ pos, up_dest, smooth((t - 17.2) / 2.2), lift=0.6)
    if t < 20.3:
        return Matrix.Translation((0, 0, 0.9 * (1 - smooth((t - 19.4) / 0.9)))) @ dest
    return dest


FORME_C_OUT = Vector((0, Y_OUT + FORME_Y, Z_T + 0.01))
SLAB = FARB + Vector((0, 0.2, 8.62))
DABS = [(-0.8, 0.5), (0.7, -0.4), (-0.6, -0.5), (0.8, 0.5), (0.0, 0.0)]


def ball_M(which, t):
    sx = -0.55 if which == 0 else 0.55
    rest = Matrix.Translation(SLAB + Vector((sx, 0, 0)))
    if t < 21.3 or t > 29.0:
        return rest
    if t < 22.3:
        return Matrix.Translation((0, 0, 1.0 * smooth((t - 21.3) / 1.0))) @ rest
    if t < 24.3:   # distribute the ink: balls rub against each other over the slab
        u = (t - 22.3) / 2.0
        a = 2 * math.pi * 2 * u + (0 if which == 0 else math.pi)
        p = SLAB + Vector((0.45 * math.cos(a), 0.35 * math.sin(a), 1.0 * (1 - math.sin(math.pi * u) ** 2) + 0.02))
        return Matrix.Translation(p) @ Matrix.Rotation(0.25 * math.sin(a), 4, "Y")
    above = Matrix.Translation(FORME_C_OUT + Vector((sx * 1.2, 0, 1.0)))
    if t < 25.3:
        return lerpM(Matrix.Translation(SLAB + Vector((0.45 * (1 if which == 0 else -1), 0, 1.0))), above, smooth(t - 24.3), lift=0.8)
    if t < 28.0:
        u = (t - 25.3) / 2.7 * len(DABS)
        i = min(int(u), len(DABS) - 1)
        f = u - i
        dx, dy = DABS[i]
        if which == 1:
            dx, dy = -dx, -dy
        z = 1.0 * (1 - math.sin(math.pi * f) ** 0.6)
        p = FORME_C_OUT + Vector((dx * 0.9 + sx * 0.4, dy * 0.8, z))
        return Matrix.Translation(p) @ Matrix.Rotation(sx * 0.12, 4, "Y")
    return lerpM(above, Matrix.Translation(SLAB + Vector((sx, 0, 0))), smooth(t - 28.0), lift=0.8)


STACK_TOP = Matrix.Translation(STACK_BLANK + Vector((0, 0, 0.325)))
DONE_TOP = Matrix.Translation(STACK_DONE + Vector((0, 0, 0.17)))
HOLD = Matrix.Translation((0, -12.6, 11.2)) @ Matrix.Rotation(math.radians(90), 4, "X")
T_ONTYMP, T_OFFTYMP = 32.0, 51.6


def lose_M(t):
    if t < 29.5:
        return STACK_TOP
    if t < T_ONTYMP:
        return lerpM(STACK_TOP, paper_on_tympan_M(T_ONTYMP), smooth((t - 29.5) / 2.5), lift=1.4)
    return paper_on_tympan_M(T_ONTYMP)


def druck_M(t):
    if t < T_OFFTYMP:
        return paper_on_tympan_M(T_OFFTYMP)
    if t < 53.6:
        return lerpM(paper_on_tympan_M(T_OFFTYMP), HOLD, smooth((t - T_OFFTYMP) / 2.0), lift=1.0)
    if t < 55.8:
        return HOLD
    if t < 57.8:
        return lerpM(HOLD, DONE_TOP, smooth((t - 55.8) / 2.0), lift=0.8)
    return DONE_TOP


# ---------------------------------------------------------------- bake keyframes
frames = np.arange(0, F_END + 1, KEY_STEP, dtype=np.float32)
ts = frames / FPS


def bake_world(obj, fn, scale_fn=None):
    L, Q, S = [], [], []
    for t in ts:
        m = fn(float(t))
        l, q, _ = m.decompose()
        L.append(l[:])
        Q.append(q[:])
        s = scale_fn(float(t)) if scale_fn else 1.0
        S.append((s, s, s))
    obj.parent = None
    write_anim(obj, frames, loc=L, quat=Q, scale=S if scale_fn else None)


for k, s in enumerate(line1):
    bake_world(s["obj"], lambda t, k=k: sort_M(k, t))
bake_world(ballA, lambda t: ball_M(0, t))
bake_world(ballB, lambda t: ball_M(1, t))
bake_world(bogen_lose, lose_M, lambda t: 1.0 if t < T_ONTYMP else 0.0)
bake_world(bogen_druck, druck_M, lambda t: 1.0 if t >= T_OFFTYMP else 0.0)
write_anim(bogen_deckel, frames, scale=[(v, v, v) for v in ((1.0 if T_ONTYMP <= t < T_OFFTYMP else 0.0) for t in ts)])
write_anim(karren, frames, loc=[(0, car_y(t), Z_CAR) for t in ts])
write_anim(deckel, frames, quat=[Quaternion((1, 0, 0), tymp(t))[:] for t in ts])
write_anim(raehmchen, frames, quat=[Quaternion((1, 0, 0), fris(t))[:] for t in ts])
write_anim(kurbel, frames, quat=[Quaternion((1, 0, 0), -(car_y(t) - Y_OUT) / DRUM_R)[:] for t in ts])
write_anim(spindel, frames, loc=[(0, 0, -PLATEN_DROP * bar(t) / BAR_PULL) for t in ts], quat=[Quaternion((0, 0, 1), bar(t))[:] for t in ts])
write_anim(tiegel, frames, loc=[(0, 0, -PLATEN_DROP * bar(t) / BAR_PULL) for t in ts])

# ---------------------------------------------------------------- anchors for annotations
def anchor(name, loc, parent=None):
    return empty("ANCHOR_" + name, loc, parent)


anchor("Gestell", (-W_X - 1.0, -1.3, 15.5))
anchor("Kopf", (-2.5, -1.5, 14.6))
anchor("Spindel", (0.6, -0.5, 12.5))
anchor("Bengel", (6.5, 0, 0.15), bengel)
anchor("Tiegel", (1.6, -1.7, PLATEN_REST + 0.25), tiegel)
anchor("Bruecke", (2.8, -1.2, 10.4))
anchor("Karren", (2.4, -3.3, 0.2), karren)
anchor("Fundament", (2.3, FORME_Y + 1.6, STONE_Z + 0.2), karren)
anchor("Form", (0.9, FORME_Y + 0.6, Z_STONE_TOP_L + TYPE_H + 0.05), karren)
anchor("Deckel", (TY_W / 2 - 0.1, TY_L * 0.75, 0.05), deckel)
anchor("Raehmchen", (TY_W / 2 - 0.1, -TY_L * 0.35, 0.0), raehmchen)
anchor("Kurbel", (2.4, 0, 1.6), kurbel)
anchor("Bahn", (2.1, -10.5, Z_RAIL))
anchor("Setzkasten", (2.4, 1.2, 0.35), kasten)
anchor("Winkelhaken", STICK + Vector((-1.6, -0.1, 0.25)))
anchor("Farbtisch", FARB + Vector((1.1, -0.6, 8.7)))
anchor("Ballen", (0, 0, 3.0), ballA)
anchor("Papier", STACK_BLANK + Vector((1.6, -1.2, 0.35)))
anchor("Druckstapel", STACK_DONE + Vector((1.6, 1.2, 0.2)))
anchor("Bogen", (1.4, 1.2, 0.02), bogen_druck)
anchor("Letter", (0, 0, TYPE_H), line1[0]["obj"])
anchor("Letter_Bild", (0, 0, TYPE_H + 0.02), line1[0]["obj"])
anchor("Letter_Signatur", (0, -LEAD / 2, TYPE_H * 0.32), line1[0]["obj"])
anchor("Letter_Fuss", (line1[0]["w"] / 2, 0, 0.0), line1[0]["obj"])

# ---------------------------------------------------------------- print texture: render the contact image in Blender
def render_print(path, with_initial):
    scene.frame_set(int(T_PRINT * FPS))
    bpy.context.view_layer.update()
    keep = {s["obj"].name for s in line1} | {o.name for o in forme.children}
    hidden = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name not in keep:
            if not o.hide_render:
                o.hide_render = True
                hidden.append(o)
    old = {m: tuple(m.diffuse_color) for m in LETTER_MATS}
    M["kegel"].diffuse_color = (1, 1, 1, 1)
    M["signatur"].diffuse_color = (1, 1, 1, 1)
    M["bild"].diffuse_color = (0.02, 0.02, 0.025, 1)
    ini = None
    if with_initial:
        cu = bpy.data.curves.new("Initiale", "FONT")
        cu.font = FONT
        cu.body = frak("I")
        cu.size = 1.0
        ini = bpy.data.objects.new("Initiale", cu)
        LINK.objects.link(ini)
        bpy.context.view_layer.update()
        bb = [Vector(c) for c in ini.bound_box]
        lo = Vector((min(c.x for c in bb), min(c.y for c in bb), 0))
        hi = Vector((max(c.x for c in bb), max(c.y for c in bb), 0))
        k = min((4 * LEAD - 0.06) / (hi.y - lo.y), (INIT_W + 0.22) / (hi.x - lo.x))   # lines 1–4, may reach into the margin
        mid = (lo + hi) / 2
        x_c = FORME_X0 + INIT_W - 0.05 - k * (hi.x - lo.x) / 2      # page coordinates (unmirrored)
        y_c = FORME_Y0 - 1.5 * LEAD
        ini.matrix_world = (Matrix.Translation((-x_c, Y_IN + FORME_Y + y_c, Z_T + 0.05)) @ Matrix.Scale(-1, 4, (1, 0, 0))
                            @ Matrix.Scale(k, 4) @ Matrix.Translation(-mid))
        ini.data.materials.append(M["rot"])
        M["rot"].diffuse_color = (*srgb("#b3261e"), 1)
    # orthographic camera exactly covering the sheet in its printing position
    cam_d = bpy.data.cameras.new("PrintCam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = PAPER_W
    cam = bpy.data.objects.new("PrintCam", cam_d)
    LINK.objects.link(cam)
    pm = paper_on_tympan_M(T_PRINT)
    c = pm.to_translation()
    cam.matrix_world = Matrix.Translation((c.x, c.y, c.z + 5))
    old_cam, old_eng = scene.camera, scene.render.engine
    scene.camera = cam
    r = scene.render
    r.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type = "FLAT", "MATERIAL"
    sh.show_shadows = sh.show_cavity = False
    old_world = tuple(scene.world.color)
    scene.world.color = (1, 1, 1)
    scene.display.render_aa = "16"
    r.film_transparent = False
    r.resolution_x, r.resolution_y = 2048, int(2048 * PAPER_L / PAPER_W)
    r.resolution_percentage = 100
    r.image_settings.file_format = "PNG"
    raw = os.path.join(TEX_DIR, "print_raw.png")
    r.filepath = raw
    scene.view_settings.view_transform = "Standard"
    bpy.ops.render.render(write_still=True)
    # restore
    for o in hidden:
        o.hide_render = False
    for m, c0 in old.items():
        m.diffuse_color = c0
    scene.camera, r.engine = old_cam, old_eng
    scene.world.color = old_world
    bpy.data.objects.remove(cam)
    if ini:
        bpy.data.objects.remove(ini)
    # post: ink squeeze, paper tone and fibres
    img = bpy.data.images.load(raw, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[..., :3]
    bpy.data.images.remove(img)
    red = np.clip((px[..., 0] - px[..., 1]) * 1.6, 0, 1)
    ink = np.clip(1 - px.max(axis=2), 0, 1) * (red < 0.25)
    blur = (ink + np.roll(ink, 1, 0) + np.roll(ink, -1, 0) + np.roll(ink, 1, 1) + np.roll(ink, -1, 1)) / 5
    rs = np.random.RandomState(5)
    grain = rs.rand(h, w).astype(np.float32)
    grain = (grain + np.roll(grain, 3, 1) + np.roll(grain, 2, 0)) / 3
    density = np.clip(0.75 * ink + 0.35 * blur, 0, 1) * (0.86 + 0.14 * grain)
    paper = np.array([0.94, 0.91, 0.83], np.float32) * (0.97 + 0.03 * grain[..., None])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vign = 1 - 0.05 * (((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2) * 4)
    col = paper * vign[..., None]
    col = col * (1 - density[..., None]) + np.array([0.05, 0.045, 0.05], np.float32) * density[..., None]
    if with_initial:
        rc = np.array([0.70, 0.13, 0.10], np.float32)
        col = col * (1 - red[..., None].clip(0, 1)) + rc * red[..., None].clip(0, 1)
    out = os.path.join(ROOT, "web/models", os.path.basename(path))
    save_np_image(os.path.basename(path).split(".")[0], np.clip(col, 0, 1), out)
    return out


# UVs of the sheet: project each vertex at its printing position into the ortho print camera
pm = paper_on_tympan_M(T_PRINT)
cx, cy = pm.to_translation().x, pm.to_translation().y
for me in (paper_me, bogen_druck.data, druck_oben.data):
    uvl = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for lp in me.loops:
        wv = pm @ paper_me.vertices[lp.vertex_index].co
        u = (wv.x - cx) / PAPER_W + 0.5
        v = (wv.y - cy) / PAPER_L + 0.5
        uvl.data[lp.index].uv = (u, v)

result = {"lines": [" ".join(l) for l in lines], "line1_sorts": N1}
if os.environ.get("GPRESS_NO_RENDER") is None:
    p1 = render_print("bogen.jpg", False)
    p2 = render_print("bogen_rubr.jpg", True)
    img_print = bpy.data.images.load(p1)
    m_print = make_mat("Papier_Gedruckt", "#ffffff", 0.85, image=img_print)
    bogen_druck.data.materials.clear()
    bogen_druck.data.materials.append(m_print)
    druck_oben.data.materials.clear()
    druck_oben.data.materials.append(m_print)

# ---------------------------------------------------------------- timeline + export
timeline = {
    "fps": FPS, "duration": DUR,
    "phases": [{"from": a, "to": b, "key": k} for a, b, k in PH],
    "ink": T_INK, "print": T_PRINT, "rubric": T_RUBRIC,
    "onTympan": [T_ONTYMP, T_OFFTYMP],
    "bar": {"pull": [41.2, 42.4], "hold": 43.2, "release": 44.6, "deg": -80},
    "carriage": {"in": [37.2, 40.0], "out": [45.8, 48.4], "travel_dm": Y_IN - Y_OUT},
    "type": {"sorts": sum(len(r) for r in layout), "lines": len(layout), "line1": N1, "em_dm": EM},
    "text": [" ".join(l) for l in lines],
}
with open(TIMELINE_PATH, "w") as fh:
    json.dump(timeline, fh, indent=1, ensure_ascii=False)

scene.frame_set(0)
if os.environ.get("GPRESS_NO_EXPORT") is None:
    bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB", use_selection=False,
                              export_animations=True, export_animation_mode="SCENE", export_force_sampling=True,
                              export_frame_range=True, export_frame_step=KEY_STEP, export_cameras=False,
                              export_lights=False, export_apply=True, export_yup=True, export_texcoords=True,
                              export_normals=True, export_materials="EXPORT", export_image_format="JPEG",
                              export_jpeg_quality=82,
                              export_optimize_animation_size=True, export_meshopt_compression_enable=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
    result["glb_mb"] = round(os.path.getsize(GLB_PATH) / 1e6, 2)
result["objects"] = len(bpy.data.objects)
result["build_s"] = round(time.time() - t0_build, 1)
print(json.dumps(result, ensure_ascii=False))
