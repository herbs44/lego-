"""
Yeezus Stage - 360-Grad-Diorama-Video zu "Coldest Winter", Aufbau im Zeitraffer auf einen Lego-Bau-Sound
=======================================================================================================
Der Song beginnt mit knapp 3 s Stille - darin laeuft der Bau-Sound: jeder Klick laesst eine Lage des
Dioramas einfallen (alles gleichzeitig, von unten nach oben), der Schlussschlag des Sounds faellt auf den
Einsatz der Musik: Traverse und Licht landen, die Lichtkegel gehen an (weisse Strahlen von oben durch Dunst,
Bodennebel), die Moving Heads schalten sich auf den ersten Kicks zu. Die Kamera faehrt ohne Schnitt einmal
um das Diorama (schwarzer Sockel, dunkler Raum, rein unbunt). Auf dem naechsten grossen Einsatz im Song
blitzt das Licht auf, danach harter Schnitt auf Schwarz.

Aufruf (aus dem Repo-Ordner):
  blender -b -P yeezus-stage/video/coldest_winter_video.py -- "<Coldest Winter.mp3>" "<lego-build.mp3>" out/coldest_winter
Optionen:
  --probe             Standbilder an Schluesselstellen (out/coldest_winter_probe/)
  --res 1920x1080     --fps 30     --samples 32     --frames a-b     --blend datei.blend
Ausgabe: <prefix>/frames/####.png, <prefix>_timing.json, <prefix>.mp4 (Musik + Bau-Sound, per ffmpeg)
Die Audiodateien werden nicht ins Repo kopiert.
"""
import json, math, os, random, shutil, subprocess, sys, time, warnings
import numpy as np
import aud
import bpy
from mathutils import Vector

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender-render"))
import ldraw_blender as lb

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 3: sys.exit(__doc__)
MUSIC, SFX, PREFIX = argv[0], argv[1], os.path.abspath(argv[2])
opt, k = {}, 3
while k < len(argv):
    if argv[k] == "--probe": opt["probe"] = True; k += 1
    else: opt[argv[k].lstrip("-")] = argv[k + 1]; k += 2
FPS = int(opt.get("fps", 30))
RES = tuple(int(v) for v in opt.get("res", "1920x1080").lower().split("x"))
MODEL = os.path.join(HERE, "..", "yeezus_stage.mpd")
TAIL = 0.25
random.seed(3)


def F(t):
    return 1 + t * FPS


# ---------------- 1. Audio ----------------
def load(path):
    s = aud.Sound(path); sr = int(s.specs[0])
    x = np.asarray(s.data(), np.float32)
    return (x.mean(1) if x.ndim == 2 else x), sr


def envelopes(x, sr, n, hop):
    fr = 1 + (len(x) - n) // hop
    t = (np.arange(fr) * hop + n / 2) / sr
    rms = np.zeros(fr, np.float32); flux = np.zeros(fr, np.float32); kick = np.zeros(fr, np.float32)
    win = np.hanning(n).astype(np.float32); f = np.fft.rfftfreq(n, 1 / sr); prev = None
    for a in range(0, fr, 2000):
        idx = np.arange(n)[None, :] + hop * np.arange(a, min(fr, a + 2000))[:, None]
        blk = x[idx]; rms[a:a + len(blk)] = np.sqrt((blk ** 2).mean(1))
        L = np.log1p(100 * np.abs(np.fft.rfft(blk * win, axis=1)))
        d = np.maximum(np.diff(np.vstack([L[:1] if prev is None else prev[None], L]), axis=0), 0)
        flux[a:a + len(blk)] = d.sum(1); kick[a:a + len(blk)] = d[:, f < 120].sum(1); prev = L[-1]
    def norm(v, w):
        v = np.maximum(v - np.convolve(v, np.ones(w) / w, "same"), 0); return v / (np.percentile(v, 99.5) + 1e-9)
    return t, rms, norm(flux, 41), norm(kick, 41)


def peaks(t, v, thr, gap, lo=0, hi=1e9):
    out = []
    for i in range(1, len(v) - 1):
        if v[i] > thr and v[i] >= v[i - 1] and v[i] >= v[i + 1] and lo <= t[i] < hi:
            if not out or t[i] - out[-1][0] > gap: out.append((float(t[i]), float(v[i])))
            elif v[i] > out[-1][1]: out[-1] = (float(t[i]), float(v[i]))
    return out


def mean_in(t, v, a, b):
    m = (t >= a) & (t < b); return float(v[m].mean()) if m.any() else 0.0


# Bau-Sound: Klicks und Schlussschlag
xs, sr = load(SFX)
ts, rs, fs, _ = envelopes(xs, sr, 512, 128)
SFX_DUR = len(xs) / sr
jump = [mean_in(ts, rs, t0, t0 + 0.2) - mean_in(ts, rs, t0 - 0.2, t0) for t0 in ts]
SFX_FINAL = float(ts[int(np.argmax(jump))])
CLICKS = [t0 for t0, _ in peaks(ts, fs, 0.12, 0.03, hi=SFX_FINAL - 0.02)]
# Musik: Einsatz nach der Stille und der naechste grosse Einsatz
xm, sr = load(MUSIC)
tm, rm, fm, km = envelopes(xm, sr, 2048, 256)
MUS_DUR = len(xm) / sr
lvl = np.median(rm[(tm > 4) & (tm < 20)])
w = int(0.25 * sr / 256)
r025 = np.convolve(rm, np.ones(w) / w, "full")[w - 1:len(rm) + w - 1]
t_loud = float(tm[int(np.argmax(r025 > 0.5 * lvl))])
KICKS = [t0 for t0, _ in peaks(tm, km, 0.4, 0.2)]
ENTRY = next(t0 for t0 in KICKS if t0 >= t_loud - 0.1)
cand = [t0 for t0 in KICKS if ENTRY + 10 < t0 < ENTRY + 22]
HIT = max(cand, key=lambda t0: mean_in(tm, rm, t0, t0 + 0.5) - mean_in(tm, rm, t0 - 0.6, t0 - 0.1))
END = HIT + 1.0                                                 # harter Schnitt auf Schwarz
SFX_OFF = ENTRY - SFX_FINAL                                     # Schlussschlag des Bau-Sounds = Musikeinsatz
PULSES = [t0 for t0, v in peaks(tm, km, 0.55, 0.25, ENTRY + 0.05, END)]
print(f"Bau-Sound: {len(CLICKS)} Klicks, Schlussschlag {SFX_FINAL:.2f} s -> im Video ab {SFX_OFF:.2f} s", flush=True)
print(f"Musik: Einsatz {ENTRY:.2f} s, grosser Einsatz {HIT:.2f} s, Schnitt {END:.2f} s, {len(PULSES)} Kicks", flush=True)

# ---------------- 2. Diorama mit Einbauzeit je Teil ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
main = lb.load_mpd(MODEL)
PARTS, SUBS = [], []
for l in lb.MPD[main]:
    t_ = l.split()
    if t_ and t_[0] == "1":
        sub = t_[-1].lower(); ps = list(lb.iter_parts(sub)); PARTS += ps; SUBS += [sub] * len(ps)
assert len(PARTS) == sum(1 for _ in lb.iter_parts(main))
HANG = ("09_line_arrays.ldr", "10_licht.ldr")                   # haengt unter der Traverse: landet zuletzt
order = sorted((i for i in range(len(PARTS)) if SUBS[i] not in HANG),
               key=lambda i: (PARTS[i][0] != "3811", -PARTS[i][3][1], PARTS[i][3][0]))
T0 = np.zeros(len(PARTS))
for r, i in enumerate(order):                                   # Lagen gleichmaessig auf die Klicks verteilt
    T0[i] = F(SFX_OFF + CLICKS[r * len(CLICKS) // len(order)] + random.uniform(0, 0.05))
for i in range(len(PARTS)):
    if SUBS[i] in HANG: T0[i] = F(ENTRY - 0.1 + random.uniform(0, 0.06))
obs, _, LO, HI = lb.build_parts(main, attrs={"t0": T0})
lb.add_build_anim(obs, 0.02, 0.12 * FPS, power=4.0)
lb.eevee_alpha_glass(0.35)
_blk = next(n for n in lb.MATS["0"].node_tree.nodes if n.type == "BSDF_PRINCIPLED")      # Schwarz neutral (ohne Blaustich)
_blk.inputs["Base Color"].default_value = (0.0035, 0.0035, 0.0035, 1)
print(f"Szene: {len(PARTS):,} Teile, Aufbau {SFX_OFF + CLICKS[0]:.2f}-{ENTRY:.2f} s", flush=True)


def to_b(x, y, z): return Vector(lb.to_blender([x, y, z]).tolist())


def mat(name, rgb, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    if m.node_tree is None: m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def box(name, lo, hi, material):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    o.location = [(a + b) / 2 for a, b in zip(lo, hi)]; o.scale = [b - a for a, b in zip(lo, hi)]
    if material: o.data.materials.append(material)
    return o


# Sockel und Boden
cx, cy = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
box("sockel", (LO[0] - 0.02, LO[1] - 0.02, -0.045), (HI[0] + 0.02, HI[1] + 0.02, -0.0017), mat("sockel", (0.006, 0.006, 0.007), 0.18))
box("boden", (cx - 4, cy - 4, -0.06), (cx + 4, cy + 4, -0.045), mat("boden", (0.012, 0.012, 0.012), 0.62))

# Dunst im Raum (Welt-Volumen) und Bodennebel (Volumen-Quader mit Rauschen)
world = bpy.data.worlds.new("welt"); scene.world = world
if world.node_tree is None: world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1); bg.inputs[1].default_value = 0.0
wout = next(n for n in wn if n.type == "OUTPUT_WORLD")
haze = wn.new("ShaderNodeVolumeScatter"); haze.inputs["Density"].default_value = float(opt.get("dunst", 0.28))
haze.inputs["Anisotropy"].default_value = 0.55
wl.new(haze.outputs[0], wout.inputs["Volume"])

fog = box("bodennebel", (LO[0] - 0.12, LO[1] - 0.12, -0.045), (HI[0] + 0.12, HI[1] + 0.12, 0.07), None)
fm_ = bpy.data.materials.new("bodennebel")
if fm_.node_tree is None: fm_.use_nodes = True
N, L = fm_.node_tree.nodes, fm_.node_tree.links
for n in list(N):
    if n.type == "BSDF_PRINCIPLED": N.remove(n)
out_ = next(n for n in N if n.type == "OUTPUT_MATERIAL")
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 2.2
nz.inputs["Detail"].default_value = 4.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
def mnode(op, a, b):
    m = N.new("ShaderNodeMath"); m.operation = op
    for s, val in ((0, a), (1, b)):
        if isinstance(val, (int, float)): m.inputs[s].default_value = val
        else: L.new(val, m.inputs[s])
    return m.outputs[0]
fall = mnode("POWER", mnode("MAXIMUM", mnode("SUBTRACT", 0.5, sep.outputs["Z"]), 0.0), 2.0)   # unten dicht
dens = mnode("MULTIPLY", mnode("MULTIPLY", mnode("MAXIMUM", mnode("SUBTRACT", nz.outputs["Fac"], 0.42), 0.0), fall), 110.0)
vs = N.new("ShaderNodeVolumeScatter"); vs.inputs["Anisotropy"].default_value = 0.3
L.new(dens, vs.inputs["Density"]); L.new(vs.outputs[0], out_.inputs["Volume"])
fog.data.materials.append(fm_)
wv = nz.inputs["W"]
wv.default_value = 0.0; wv.keyframe_insert("default_value", frame=1)
wv.default_value = 1.6; wv.keyframe_insert("default_value", frame=int(F(END)) + 5)

# ---------------- 3. Licht (weiss, von oben durch den Dunst) ----------------
EDIT = bpy.context.preferences.edit
EDIT.keyframe_new_interpolation_type = "BEZIER"
COOL = (1.0, 1.0, 1.0)                                         # rein unbunt: neutrales Weiss


def spot(name, pos, target, size, blend, color=COOL, radius=0.004, haze_gain=5.0):
    d = bpy.data.lights.new(name, "SPOT"); d.spot_size = math.radians(size); d.spot_blend = blend
    d.color = color; d.shadow_soft_size = radius; d.energy = 0.0
    if hasattr(d, "volume_factor"): d.volume_factor = haze_gain            # sichtbare Strahlen im Dunst
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o)
    o.location = pos; o.rotation_euler = (Vector(pos) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    return d


def keys(data, pts, path="energy"):
    for t0, v in pts:
        setattr(data, path, v); data.keyframe_insert(path, frame=F(t0))


APEX = to_b(240, -456, 0)                                       # Gipfel (generate_yeezus_stage.APEX)
ARENA = [spot("strahl_1", (APEX.x - 0.22, APEX.y + 0.30, 1.25), APEX + Vector((0, 0, 0.02)), 7, 0.35),
         spot("strahl_2", (APEX.x + 0.18, APEX.y - 0.34, 1.30), APEX, 8, 0.35),
         spot("strahl_3", (APEX.x - 0.55, APEX.y - 0.15, 1.20), to_b(-440, -96, 0), 11, 0.4)]
AR_E = [260.0, 230.0, 200.0]
heads = {}
for (name, col, M, pos, inv), sub in zip(PARTS, SUBS):
    if sub == "10_licht.ldr" and name == "4032a":
        heads[(round(pos[0]), round(pos[2]))] = pos
HEADS = []
for (x, z), pos in sorted(heads.items()):
    p = to_b(x, pos[1] + 12, z)
    tgt = to_b(x * 0.45 + 60, -96, z * 0.25)                    # schraeg nach unten zur Buehnenmitte
    HEADS.append(spot(f"head_{x}_{z}", p, tgt, 12, 0.3, radius=0.002, haze_gain=3.0))
fill = bpy.data.lights.new("aufsicht", "AREA"); fill.size = 1.2; fill.color = COOL
fo = bpy.data.objects.new("aufsicht", fill); scene.collection.objects.link(fo); fo.location = (cx, cy, 1.4)
rim = bpy.data.lights.new("gegenlicht", "AREA"); rim.size = 0.8; rim.color = COOL
ro = bpy.data.objects.new("gegenlicht", rim); scene.collection.objects.link(ro)
rim.size = 1.5; ro.location = (cx + 2.0, cy - 1.0, 1.2); ro.rotation_euler = (Vector(ro.location) - Vector((cx, cy, 0.1))).to_track_quat("Z", "Y").to_euler()

for d_ in (fill, rim):                                          # Flaechenlichter leuchten den Dunst nicht aus
    if hasattr(d_, "volume_factor"): d_.volume_factor = 0.0
ramp_on = 0.12
keys(fill, [(0, 0.0), (0.5, 0.0), (SFX_OFF, 24.0), (ENTRY - 0.02, 24.0), (ENTRY + ramp_on, 7.0)])
keys(rim, [(0, 0.0), (SFX_OFF, 14.0), (ENTRY - 0.02, 14.0), (ENTRY + ramp_on, 20.0)])
for d, e in zip(ARENA, AR_E):
    pts = [(0, 0.0), (ENTRY - 0.02, 0.0), (ENTRY + ramp_on, e)]
    for p in PULSES:                                            # dezenter Atmer auf den Kicks
        if p < HIT - 0.3: pts += [(p - 1 / FPS, e), (p + 0.06, e * 1.22), (p + 0.4, e)]
    pts += [(HIT - 1 / FPS, e), (HIT + 0.05, e * 2.0), (HIT + 0.6, e * 1.3), (END, e * 1.3)]
    keys(d, sorted(pts))
on_times = [p for p in PULSES if p > ENTRY + 0.2][:len(HEADS)]
while len(on_times) < len(HEADS): on_times.append((on_times[-1] if on_times else ENTRY) + 0.35)
for d, t_on in zip(HEADS, on_times):
    keys(d, [(0, 0.0), (t_on - 1 / FPS, 0.0), (t_on + 0.06, 22.0), (HIT - 1 / FPS, 22.0), (HIT + 0.05, 40.0),
             (HIT + 0.6, 28.0), (END, 28.0)])

# ---------------- 4. Kamera: eine 360-Grad-Fahrt ohne Schnitt ----------------
ZLO, ZHI = -0.045, HI[2]                                        # Sockel bis Traverse
TGT = Vector((cx, cy, (ZLO + ZHI) / 2 - 0.01))
cd = bpy.data.cameras.new("kamera"); cd.lens = float(opt.get("lens", 30)); cd.clip_start = 0.01; cd.clip_end = 30
cam = bpy.data.objects.new("kamera", cd); scene.collection.objects.link(cam); scene.camera = cam
tg = bpy.data.objects.new("ziel", None); scene.collection.objects.link(tg); tg.location = TGT
c = cam.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
EL, AZ0 = math.radians(float(opt.get("hoehe", 21))), -128.0
# Abstand: ein fester Wert, bei dem das Diorama aus jedem Winkel der Fahrt ganz ins Bild passt
corners = [Vector((x, y, z)) - TGT for x in (LO[0] - 0.02, HI[0] + 0.02) for y in (LO[1] - 0.02, HI[1] + 0.02)
           for z in (ZLO, ZHI)]
sw = 18 / cd.lens; sh = sw * RES[1] / RES[0]
R = 0.0
for deg in range(0, 360, 3):
    a = math.radians(deg)
    back = Vector((math.sin(a) * math.cos(EL), -math.cos(a) * math.cos(EL), math.sin(EL))); fwd = -back
    right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
    for p in corners:
        R = max(R, abs(p.dot(right)) / sw - p.dot(fwd), abs(p.dot(up)) / sh - p.dot(fwd))
R *= float(opt.get("rand", 1.07))
print(f"Kamera: Abstand {R:.2f} m, Hoehe {math.degrees(EL):.0f} Grad, {cd.lens:.0f} mm", flush=True)
ACC = 1.5                                                       # sanft anfahren, dann gleichmaessig
omega = 360.0 / (END - ACC / 2)
EDIT.keyframe_new_interpolation_type = "LINEAR"
for f in range(1, int(round(F(END))) + 1):
    t0 = (f - 1) / FPS
    ang = AZ0 + (omega * t0 * t0 / (2 * ACC) if t0 < ACC else omega * (t0 - ACC / 2))
    a = math.radians(ang)
    cam.location = TGT + R * Vector((math.sin(a) * math.cos(EL), -math.cos(a) * math.cos(EL), math.sin(EL)))
    cam.keyframe_insert("location", frame=f)

json.dump(dict(bau_sound=dict(klicks=CLICKS, schlussschlag=SFX_FINAL, versatz=SFX_OFF),
               musik=dict(einsatz=ENTRY, grosser_einsatz=HIT, schnitt=END, kicks=PULSES)),
          open(PREFIX + "_timing.json", "w", encoding="utf-8"), indent=1)

# ---------------- 5. Rendern ----------------
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: scene.render.engine = eng; break
    except TypeError: pass
ee = scene.eevee
ee.taa_render_samples = int(opt.get("samples", 32))
for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_volumetric_shadows", True),
                  ("volumetric_tile_size", "4"), ("volumetric_samples", 96), ("volumetric_start", 0.05),
                  ("volumetric_end", 6.0), ("volumetric_light_clamp", 0.0)):
    if hasattr(ee, attr):
        try: setattr(ee, attr, val)
        except (TypeError, ValueError) as e: print("EEVEE", attr, e)
scene.render.use_motion_blur = True
if hasattr(scene.render, "motion_blur_shutter"): scene.render.motion_blur_shutter = 0.35
try: scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError: pass
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.frame_start, scene.frame_end = 1, int(round(F(END))) - 1
if "frames" in opt:
    a_, b_ = opt["frames"].split("-"); scene.frame_start, scene.frame_end = int(a_), int(b_)
scene.render.image_settings.file_format = "PNG"
try:
    se = scene.sequence_editor_create(); col = se.strips if hasattr(se, "strips") else se.sequences
    col.new_sound("Coldest Winter", MUSIC, 1, 1); col.new_sound("Lego-Bau", SFX, 2, int(round(F(SFX_OFF))))
except Exception as e:
    print("Ton im Sequencer nicht angelegt:", e)
scene.render.use_sequencer = False
if "blend" in opt:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt["blend"]))

if opt.get("probe"):
    out = PREFIX + "_probe"; os.makedirs(out, exist_ok=True)
    scene.render.resolution_percentage = 50
    probe_t = [0.6, SFX_OFF + CLICKS[len(CLICKS) // 3], SFX_OFF + CLICKS[2 * len(CLICKS) // 3], ENTRY - 0.05,
               ENTRY + 0.4, ENTRY + 4, (ENTRY + HIT) / 2, HIT - 2, HIT + 0.15, END - 0.1]
    for n, t0 in enumerate(probe_t):
        scene.frame_set(int(round(F(t0))))
        scene.render.filepath = os.path.join(out, f"{n:02d}_{t0:05.2f}s.png")
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print(f"  {n:02d} {t0:5.2f} s ({time.time() - t1:.1f} s)", flush=True)
    sys.exit(0)

os.makedirs(PREFIX + "/frames", exist_ok=True)
scene.render.filepath = PREFIX + "/frames/"
t1 = time.time()
bpy.ops.render.render(animation=True)
print(f"Frames fertig ({(time.time() - t1) / 60:.1f} min)", flush=True)

ff = shutil.which("ffmpeg")
if ff and "frames" not in opt:
    total = END + TAIL
    ms = int(round(SFX_OFF * 1000))
    af = (f"[1:a]atrim=0:{total:.3f},afade=t=out:st={END:.3f}:d={TAIL}[m];"
          f"[2:a]adelay={ms}|{ms},volume=0.9[s];[m][s]amix=inputs=2:normalize=0:duration=first[a]")
    cmd = [ff, "-y", "-v", "error", "-framerate", str(FPS), "-start_number", "1", "-i", PREFIX + "/frames/%04d.png",
           "-i", MUSIC, "-i", SFX, "-filter_complex", af, "-map", "0:v", "-map", "[a]",
           "-vf", f"fade=t=in:st=0:d=0.4,tpad=stop_mode=add:stop_duration={TAIL}:color=black,format=yuv420p",
           "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-c:a", "aac", "-b:a", "256k",
           "-t", f"{total:.3f}", PREFIX + ".mp4"]
    subprocess.run(cmd, check=True)
    print("Video:", PREFIX + ".mp4", flush=True)
