"""
Circus Maximus Stage im Konzertlicht rendern (Cycles): dunkle Arena, der Videoring leuchtet als LED-Feuerwand,
Flammen und Lampen gluehen, weisse Lichtkegel im Dunst fallen auf den Felsweg.
Aufruf:
  blender -b -P circus-maximus/render_konzert.py -- circus-maximus/circus_maximus_stage.mpd out/cm_konzert [Optionen]
Optionen:
  --views '{"name": [az, el, zoom, x, y, z]}'   wie render_cycles.py (Zielpunkt x, y, z in LDU optional)
  --res 1600x1000  --samples 192  --dunst 0.08  --glut 3  --screen 0.8  --cpu
Ausgabe: <prefix>_<ansicht>.png
"""
import json, math, os, sys, time, warnings
import bpy
from mathutils import Matrix, Vector

warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "blender-render"))
import ldraw_blender as lb

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2: sys.exit(__doc__)
MODEL, PREFIX = argv[0], argv[1]
opt = {}
k = 2
while k < len(argv):
    if argv[k] == "--cpu": opt["cpu"] = True; k += 1
    else: opt[argv[k].lstrip("-")] = argv[k + 1]; k += 2
RES = tuple(int(v) for v in opt.get("res", "1600x1000").lower().split("x"))
VIEWS = json.loads(opt["views"]) if "views" in opt else {
    "konzert": [-22, 9, 1.25, 0, -380, 0], "publikum": [-8, 2, 2.1, 120, -330, 60]}
GLOW = float(opt.get("glut", 3))
SCREEN = float(opt.get("screen", 0.8))


def to_b(x, y, z): return Vector(lb.to_blender([x, y, z]).tolist())


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
t0 = time.time()
obs, parts, lo, hi = lb.build_parts(lb.load_mpd(MODEL))
print(f"Szene: {len(parts):,} Teile ({time.time() - t0:.0f} s)", flush=True)
center = (lo + hi) / 2


def emit(code, rgb, strength):
    mat = lb.MATS.get(code)
    if mat is None: return
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for nm, val in (("Emission Color", (*rgb, 1)), ("Emission Strength", strength)):
        if nm in bsdf.inputs: bsdf.inputs[nm].default_value = val


# Flammen, Uplights, Lampen (transparent) und die LED-Wand des Rings (Rot/Orange/Gelb, nur dort verwendet)
for code, rgb, f in (("57", (1.0, 0.25, 0.02), 1.0), ("46", (1.0, 0.6, 0.12), 1.0), ("47", (1.0, 0.93, 0.85), 0.8),
                     ("36", (1.0, 0.05, 0.02), 1.0)):
    emit(code, rgb, GLOW * f)
for code, rgb, f in (("14", (1.0, 0.75, 0.1), 1.0), ("191", (1.0, 0.5, 0.08), 1.0), ("25", (1.0, 0.3, 0.02), 1.0),
                     ("4", (0.9, 0.04, 0.01), 0.9), ("320", (0.45, 0.02, 0.01), 0.7)):
    emit(code, rgb, SCREEN * f)

world = bpy.data.worlds.new("arena"); scene.world = world
if world.node_tree is None: world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1); bg.inputs[1].default_value = 0.0
haze = wn.new("ShaderNodeVolumeScatter"); haze.inputs["Density"].default_value = float(opt.get("dunst", 0.08))
haze.inputs["Anisotropy"].default_value = 0.6
wl.new(haze.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Volume"])
bpy.ops.mesh.primitive_plane_add(size=2.2, location=(center[0], center[1], -0.0008))
floor = bpy.context.object
fm = bpy.data.materials.new("hallenboden"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fb.inputs["Base Color"].default_value = (0.003, 0.003, 0.003, 1); fb.inputs["Roughness"].default_value = 0.85
floor.data.materials.append(fm)


def light(kind, name, pos, target, energy, color, size=0.0, spot=0.0, blend=0.3, haze_gain=1.0):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == "SPOT": d.spot_size = math.radians(spot); d.spot_blend = blend; d.shadow_soft_size = size
    elif kind == "AREA": d.size = size
    if hasattr(d, "volume_factor"): d.volume_factor = haze_gain
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o)
    o.location = pos; o.rotation_euler = (Vector(pos) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    return o


TRUSS_Y = -1056                                                 # Unterkante Traversen-Raster (Generator)
# weisse Kegel aus dem Raster schraeg auf den Felsweg (wie die Beam-Faecher auf den Fotos)
for i, x in enumerate(range(-780, 800, 160)):
    for side in (-1, 1):
        light("SPOT", f"beam_{i}_{side}", to_b(x, TRUSS_Y + 30, side * 420), to_b(x + 60 * side, -80, side * 40),
              45.0, (0.95, 0.97, 1.0), size=0.002, spot=4, blend=0.15, haze_gain=2.0)
# Performer oben auf dem Block (Generator: BLOCK_X um -740) im warmen Spot
light("SPOT", "performer", to_b(-700, TRUSS_Y + 30, -60), to_b(-730, -430, -60), 30.0, (1.0, 0.85, 0.65), size=0.002,
      spot=6, blend=0.25, haze_gain=1.5)
# weisse Uplights am Felsfuss strahlen die Felsen von unten an (Konzertfoto)
for i, x in enumerate(range(-640, 800, 160)):
    for side in (-1, 1):
        light("AREA", f"uplight_{i}_{side}", to_b(x, -12, side * 230), to_b(x, -160, side * 60), 0.1, (0.9, 0.95, 1.0),
              size=0.03, haze_gain=0.6)
# rotes Grundlicht von unten (Glut) und schwaches Fuelllicht ohne Dunst
light("AREA", "glut", to_b(0, -40, 0), to_b(0, -400, 0), 2.0, (1.0, 0.25, 0.05), size=0.6, haze_gain=0.0)
light("AREA", "fuell", to_b(-600, -900, -1700), to_b(0, -200, 0), 1.6, (0.85, 0.85, 1.0), size=1.2, haze_gain=0.0)
light("AREA", "gegen", to_b(600, -1100, 1600), to_b(0, -200, 0), 4.0, (1.0, 0.45, 0.2), size=1.2, haze_gain=0.0)

try: scene.render.engine = "CYCLES"
except TypeError as e: print(e)
scene.cycles.samples = int(opt.get("samples", 192))
scene.cycles.use_denoising = True
scene.cycles.volume_step_rate = 2.0
scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError: pass
if not opt.get("cpu"): lb.enable_gpu(scene)

cam_data = bpy.data.cameras.new("kamera"); cam_data.lens = 40; cam_data.clip_start = 0.01; cam_data.clip_end = 50
cam = bpy.data.objects.new("kamera", cam_data); scene.collection.objects.link(cam); scene.camera = cam
corners = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
os.makedirs(os.path.dirname(os.path.abspath(PREFIX)), exist_ok=True)
for name, v in VIEWS.items():
    az, el, zoom = math.radians(v[0]), math.radians(v[1]), v[2] if len(v) > 2 else 1.0
    target = Vector(center) if len(v) < 6 else to_b(*v[3:6])
    back = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    fwd = -back
    right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
    aspect = RES[0] / RES[1]
    sw, sh = 36 / 2 / cam_data.lens, 36 / 2 / cam_data.lens / aspect
    d = max(max(abs((c - target).dot(right)) / sw - (c - target).dot(fwd), abs((c - target).dot(up)) / sh - (c - target).dot(fwd))
            for c in corners) * 1.04 / zoom
    cam.matrix_world = Matrix(((right.x, up.x, -fwd.x, target.x - fwd.x * d), (right.y, up.y, -fwd.y, target.y - fwd.y * d),
                               (right.z, up.z, -fwd.z, target.z - fwd.z * d), (0, 0, 0, 1)))
    scene.render.filepath = os.path.abspath(f"{PREFIX}_{name}.png")
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"-> {scene.render.filepath} ({time.time() - t1:.0f} s)", flush=True)
if lb.MISSING: print("Fehlende Teile:", ", ".join(sorted(lb.MISSING)))
