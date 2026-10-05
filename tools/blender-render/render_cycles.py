"""
LDraw-Modell (.mpd/.ldr) in Blender fotorealistisch rendern (Cycles)
====================================================================
Aufruf:
  blender -b -P tools/blender-render/render_cycles.py -- <modell.mpd> <out/prefix> [Optionen]

Optionen:
  --views '{"name": [az, el, zoom]}'   Ansichten; az 0 = von vorne (LDraw -z), -90 = von links (LDraw -x),
                                        el 90 = von oben; optional [az, el, zoom, x, y, z] mit Zielpunkt in LDU
  --res 1600x1200                       Bildgroesse (Standard: Relief 1500x1500, sonst 1600x1200)
  --samples 128                         Cycles-Samples (mit Denoiser)
  --cpu                                 GPU nicht verwenden
  --blend datei.blend                   Szene zusaetzlich speichern

Standardansichten: Reliefs (flach, Noppen nach oben) "front", "schraeg" und "nah", sonst "hero" und "seite".
LDraw-Bibliothek und Import: siehe ldraw_blender.py
Ausgabe: <prefix>_<ansicht>.png
"""
import json, math, os, sys, time, warnings
import numpy as np
import bpy
from mathutils import Matrix, Vector

warnings.filterwarnings("ignore", category=DeprecationWarning)      # use_nodes (Blender 5.x)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ldraw_blender as lb

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    sys.exit(__doc__)
MODEL, PREFIX = argv[0], argv[1]
opt = {}
k = 2
while k < len(argv):
    if argv[k] == "--cpu": opt["cpu"] = True; k += 1
    else: opt[argv[k].lstrip("-")] = argv[k + 1]; k += 2
SAMPLES = int(opt.get("samples", 128))
print("LDraw-Bibliothek:", lb.LIB or "(keine) - nur Cache", flush=True)

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
obs, parts, lo, hi = lb.build_parts(lb.load_mpd(MODEL))
print(f"Szene: {len(parts):,} Teile, {sum(len(o.data.polygons) for o in obs):,} Dreiecke in {len(obs)} Farben "
      f"({time.time() - t0:.0f} s)", flush=True)

size = hi - lo
center = (lo + hi) / 2
flat = size[2] < 0.2 * min(size[0], size[1])
DEFAULT = {"front": [180, 90, 1.0], "schraeg": [155, 50, 1.1], "nah": [165, 55, 2.6]} if flat else \
          {"hero": [-55, 24, 1.0], "seite": [-125, 20, 1.0]}
VIEWS = json.loads(opt["views"]) if "views" in opt else DEFAULT
RES = tuple(int(v) for v in opt.get("res", "1500x1500" if flat else "1600x1200").lower().split("x"))

# Welt, Render
world = bpy.data.worlds.new("welt"); scene.world = world
if world.node_tree is None: world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.9, 0.9, 0.92, 1); bg.inputs[1].default_value = 0.7
try: scene.render.engine = "CYCLES"
except TypeError as e: print(e)
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
if not opt.get("cpu"): lb.enable_gpu(scene)

cam_data = bpy.data.cameras.new("kamera"); cam_data.lens = 50; cam_data.clip_start = 0.01; cam_data.clip_end = 200
cam = bpy.data.objects.new("kamera", cam_data); scene.collection.objects.link(cam); scene.camera = cam
sun_data = bpy.data.lights.new("sonne", "SUN"); sun_data.energy = 3.2; sun_data.angle = math.radians(6)
sun = bpy.data.objects.new("sonne", sun_data); scene.collection.objects.link(sun)
corners = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]

os.makedirs(os.path.dirname(os.path.abspath(PREFIX)), exist_ok=True)
for name, v in VIEWS.items():
    az, el, zoom = math.radians(v[0]), math.radians(v[1]), v[2] if len(v) > 2 else 1.0
    target = Vector(center) if len(v) < 6 else Vector(lb.to_blender(v[3:6]).tolist())
    back = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))  # Ziel -> Kamera
    fwd = -back
    up_hint = Vector((0, 0, 1)) if abs(el) < math.radians(89) else Vector((math.sin(az), -math.cos(az), 0)) * -1
    right = fwd.cross(up_hint).normalized(); up = right.cross(fwd).normalized()
    # Abstand so, dass alle Ecken der Bounding-Box ins Bild passen
    aspect = RES[0] / RES[1]                  # tan(halber Bildwinkel) horizontal / vertikal
    sw, sh = (36 / 2 / cam_data.lens, 36 / 2 / cam_data.lens / aspect) if aspect >= 1 else \
             (36 / 2 / cam_data.lens * aspect, 36 / 2 / cam_data.lens)
    d = 0.0
    for c in corners:
        p = c - target
        d = max(d, abs(p.dot(right)) / sw - p.dot(fwd), abs(p.dot(up)) / sh - p.dot(fwd))
    d = d * 1.06 / zoom
    cam.matrix_world = Matrix((
        (right.x, up.x, -fwd.x, target.x - fwd.x * d),
        (right.y, up.y, -fwd.y, target.y - fwd.y * d),
        (right.z, up.z, -fwd.z, target.z - fwd.z * d),
        (0, 0, 0, 1)))
    # Licht von links oben (aus Sicht der Kamera), flach genug fuer Schatten im Relief
    L = (-right * 0.65 + up * 0.55 + back * 0.45).normalized()
    sun.rotation_euler = L.to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = os.path.abspath(f"{PREFIX}_{name}.png")
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"-> {scene.render.filepath} ({time.time() - t1:.0f} s)", flush=True)

if "blend" in opt:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt["blend"]))
if lb.MISSING: print("Fehlende Teile:", ", ".join(sorted(lb.MISSING)))
