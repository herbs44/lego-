"""
Saint Pablo Stage im Konzertlicht rendern (Cycles): dunkle Halle, leuchtende Lampen im Raster und an der Plattform,
Dunst mit Lichtkegeln, Spot auf Kanye.
Aufruf:
  blender -b -P saint-pablo/render_konzert.py -- saint-pablo/saint_pablo.mpd out/konzert [Optionen]
Optionen:
  --views '{"name": [az, el, zoom, x, y, z]}'   wie render_cycles.py (Zielpunkt x, y, z in LDU optional)
  --res 1600x1200  --samples 192  --dunst 0.3  --glut 5  --cpu
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
RES = tuple(int(v) for v in opt.get("res", "1600x1200").lower().split("x"))
VIEWS = json.loads(opt["views"]) if "views" in opt else {"konzert": [-14, 11, 1.12, 0, -330, 0], "fans": [8, -4, 1.9, 0, -420, 120]}
GLOW = float(opt.get("glut", 5))


def to_b(x, y, z): return Vector(lb.to_blender([x, y, z]).tolist())


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
t0 = time.time()
obs, parts, lo, hi = lb.build_parts(lb.load_mpd(MODEL))
print(f"Szene: {len(parts):,} Teile ({time.time() - t0:.0f} s)", flush=True)
center = (lo + hi) / 2

# ---------------- Lampen leuchten: Trans-Orange, Trans-Yellow, Trans-Clear ----------------
GLOW_COL = {"57": ((1.0, 0.2, 0.015), 1.0), "46": ((1.0, 0.62, 0.18), 0.8), "47": ((1.0, 0.9, 0.75), 0.9)}
for code, mat in lb.MATS.items():
    if code not in GLOW_COL: continue
    rgb, f = GLOW_COL[code]
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for nm, val in (("Emission Color", (*rgb, 1)), ("Emission Strength", GLOW * f)):
        if nm in bsdf.inputs: bsdf.inputs[nm].default_value = val
# Schwarz etwas glaenzender (Traeger und Raster zeichnen sich im Gegenlicht ab)
for code, mat in lb.MATS.items():
    if code == "0":
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Roughness"].default_value = 0.3

# ---------------- Welt: schwarz mit Dunst ----------------
world = bpy.data.worlds.new("halle"); scene.world = world
if world.node_tree is None: world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1); bg.inputs[1].default_value = 0.0
haze = wn.new("ShaderNodeVolumeScatter"); haze.inputs["Density"].default_value = float(opt.get("dunst", 0.3))
haze.inputs["Anisotropy"].default_value = 0.6
wl.new(haze.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Volume"])

# Hallenboden um die Grundplatte (matt schwarz), damit der Dunst nicht ins Leere faellt
bpy.ops.mesh.primitive_plane_add(size=30, location=(center[0], center[1], -0.0008))
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


# Spot auf Kanye aus dem Raster (warmweiss, sichtbarer Kegel)
KANYE = to_b(-10, -400, -50)
light("SPOT", "kanye", to_b(-10, -800, -60), KANYE, 30.0, (1.0, 0.86, 0.7), size=0.002, spot=7, blend=0.25, haze_gain=1.6)
# orange Kegel aus dem Raster ins Publikum
for i, (x, z, tx, tz) in enumerate(((-300, -300, -260, -160), (320, -260, 240, -120), (-260, 300, -180, 160),
                                     (300, 280, 200, 200), (0, -420, 40, -300))):
    light("SPOT", f"kegel_{i}", to_b(x, -790, z), to_b(tx, 0, tz), 22.0, (1.0, 0.35, 0.06), size=0.003, spot=9, blend=0.4,
          haze_gain=1.3)
# Plattform von unten: warme Flaeche nach unten (Moshpit im Lichtschein)
light("AREA", "unterlicht", to_b(0, -250, 0), to_b(0, 0, 0), 0.6, (1.0, 0.55, 0.2), size=0.12, haze_gain=0.6)
# schwaches Fuell- und Gegenlicht ohne Dunst (Silhouetten lesbar)
light("AREA", "fuell", to_b(-500, -700, -1400), to_b(0, -300, 0), 0.8, (1.0, 0.8, 0.65), size=1.0, haze_gain=0.0)
light("AREA", "gegen", to_b(300, -900, 1300), to_b(0, -300, 0), 1.5, (1.0, 0.5, 0.2), size=1.0, haze_gain=0.0)

# ---------------- Render ----------------
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
