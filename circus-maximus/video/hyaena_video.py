"""
Circus Maximus Stage - Buehnen-Video zu "HYAENA" (Travis Scott) im orangen Konzertlicht
=====================================================================================
Vor dem Drop wird die Buehne praesentiert (Totale ueber das Publikum, Fahrt an den Steinkoepfen entlang, Orbit um
den Felsblock, Kranfahrt hinab zur Lift-Klappe im Weg). Kurz vor dem Drop: POV einer Minifigur im dunklen Schacht
unter der Buehne, die Kamera zittert immer staerker. Auf dem Drop fliegt die Klappe auf, die Figur wird nach oben
geschleudert (POV), Flammen schiessen hoch, Strobe - dann Aussenansicht: Travis landet mit einer Drehung auf der
Buehne. Danach Schnitte auf den Beats, Ring und Flammen pulsieren mit der Musik, Travis huepft auf den Kicks.

Aufruf (aus dem Repo-Ordner):
  blender -b -P circus-maximus/video/hyaena_video.py -- "<HYAENA.mp3>" out/hyaena
  Vorschau ohne Musik:  ... -- - out/hyaena_test --drop 20 --probe
Optionen:
  --probe              Standbilder an Schluesselstellen (<prefix>_probe/)
  --res 1920x1080  --fps 30  --samples 32  --frames a-b  --blend datei.blend
  --vorlauf 22         Sekunden Musik vor dem Drop        --nachlauf 16   Sekunden nach dem Drop
  --drop <s>           Drop-Zeitpunkt im Song von Hand (sonst automatisch erkannt)
  --ohne-fans          Publikum ausblenden
Ausgabe: <prefix>/frames/####.png, <prefix>_timing.json, <prefix>.mp4 (per ffmpeg). Die Musik kommt nicht ins Repo.
"""
import json, math, os, random, shutil, subprocess, sys, time, warnings
import numpy as np
import bpy
from mathutils import Vector

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender-render"))
import ldraw_blender as lb

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2: sys.exit(__doc__)
MUSIC, PREFIX = argv[0], os.path.abspath(argv[1])
opt, k = {}, 2
while k < len(argv):
    if argv[k] in ("--probe", "--ohne-fans"): opt[argv[k].lstrip("-")] = True; k += 1
    else: opt[argv[k].lstrip("-")] = argv[k + 1]; k += 2
FPS = int(opt.get("fps", 30))
RES = tuple(int(v) for v in opt.get("res", "1920x1080").lower().split("x"))
MODEL = os.path.join(HERE, "..", "circus_maximus_stage.mpd")
VOR, NACH = float(opt.get("vorlauf", 22)), float(opt.get("nachlauf", 16))
TAIL = 0.4
random.seed(5)


# ---------------- 1. Audio: Drop, Kicks, Lautstaerke ----------------
def load(path):
    import aud
    s = aud.Sound(path); sr = int(s.specs[0])
    x = np.asarray(s.data(), np.float32)
    return (x.mean(1) if x.ndim == 2 else x), sr


def envelopes(x, sr, n, hop):
    fr = 1 + (len(x) - n) // hop
    t = (np.arange(fr) * hop + n / 2) / sr
    rms = np.zeros(fr, np.float32); kick = np.zeros(fr, np.float32)
    win = np.hanning(n).astype(np.float32); f = np.fft.rfftfreq(n, 1 / sr); prev = None
    for a in range(0, fr, 2000):
        idx = np.arange(n)[None, :] + hop * np.arange(a, min(fr, a + 2000))[:, None]
        blk = x[idx]; rms[a:a + len(blk)] = np.sqrt((blk ** 2).mean(1))
        L = np.log1p(100 * np.abs(np.fft.rfft(blk * win, axis=1)))
        d = np.maximum(np.diff(np.vstack([L[:1] if prev is None else prev[None], L]), axis=0), 0)
        kick[a:a + len(blk)] = d[:, f < 120].sum(1); prev = L[-1]
    k2 = np.maximum(kick - np.convolve(kick, np.ones(41) / 41, "same"), 0)
    return t, rms, k2 / (np.percentile(k2, 99.5) + 1e-9)


def peaks(t, v, thr, gap, lo=0, hi=1e9):
    out = []
    for i in range(1, len(v) - 1):
        if v[i] > thr and v[i] >= v[i - 1] and v[i] >= v[i + 1] and lo <= t[i] < hi:
            if not out or t[i] - out[-1][0] > gap: out.append((float(t[i]), float(v[i])))
            elif v[i] > out[-1][1]: out[-1] = (float(t[i]), float(v[i]))
    return out


def mean_in(t, v, a, b):
    m = (t >= a) & (t < b); return float(v[m].mean()) if m.any() else 0.0


if MUSIC != "-":
    xm, sr = load(MUSIC)
    tm, rm, km = envelopes(xm, sr, 2048, 256)
    MUS_DUR = len(xm) / sr
    KICKS = [t0 for t0, _ in peaks(tm, km, 0.4, 0.2)]
    if "drop" in opt: DROP = float(opt["drop"])
    else:                                                       # groesster Lautstaerke-Sprung auf einem Kick
        cand = [t0 for t0 in KICKS if 8 < t0 < min(MUS_DUR - NACH, 150)]
        DROP = max(cand, key=lambda t0: mean_in(tm, rm, t0 + 0.05, t0 + 1.5) - mean_in(tm, rm, t0 - 3.0, t0 - 0.2))
    DROP = min(KICKS, key=lambda t0: abs(t0 - DROP)) if KICKS else DROP
    LVL = np.percentile(rm, 95)
else:                                                           # Vorschau ohne Musik: gleichmaessige Beats
    DROP = float(opt.get("drop", 20)); MUS_DUR = DROP + NACH + 5
    KICKS = [i * 0.31 for i in range(int((DROP + NACH) / 0.31) + 1)]
    tm = np.arange(0, MUS_DUR, 0.01)
    rm = np.where(tm < DROP - 6, 0.3, np.where(tm < DROP - 2.5, 0.0, np.where(tm < DROP, 0.4, 1.0))).astype(np.float32); LVL = 1.0
START = max(0.0, DROP - VOR)
END = min(MUS_DUR, DROP + NACH)
# Pause vor dem Drop (Stille-Luecken): Blackout und Schacht-POV; LEAD = Ende der letzten Stille (Anlauf zum Drop)
runs, cur = [], None
for t0 in np.arange(DROP - 12.0, DROP, 0.05):
    q = mean_in(tm, rm, t0, t0 + 0.25) < 0.03 * LVL
    if q and cur is None: cur = t0
    if not q and cur is not None:
        if t0 - cur >= 0.4: runs.append((cur, t0))
        cur = None
while len(runs) > 1 and runs[-1][0] - runs[-2][1] < 2.0:          # Luecken kurz hintereinander = eine Pause
    runs[-2:] = [(runs[-2][0], runs[-1][1])]
runs = runs[-1:]                                                  # nur die letzte Pause vor dem Drop
SIL0, LEAD = (runs[0][0], runs[-1][1] + 0.2) if runs else (DROP - 3.0, DROP - 3.0)
if LEAD > DROP - 1.2: LEAD = DROP - 1.2
# Tempo nach dem Drop (Autokorrelation der Bass-Einsaetze), Beat-Raster ab dem Drop, auf Kicks eingerastet
if "bpm" in opt: BEAT = 60.0 / float(opt["bpm"])
elif MUSIC != "-":
    m_ = (tm > DROP) & (tm < min(DROP + 30, MUS_DUR)); v_ = km[m_] - km[m_].mean()
    ac = np.correlate(v_, v_, "full")[len(v_) - 1:]; lag = np.arange(len(ac)) * (tm[1] - tm[0])
    ok = (lag > 60 / 180) & (lag < 60 / 70); BEAT = float(lag[ok][np.argmax(ac[ok])])
else: BEAT = 0.62
GRID = []
n_ = 1
while DROP + n_ * BEAT < END - 0.2:
    g_ = DROP + n_ * BEAT
    near = [k_ for k_ in KICKS if abs(k_ - g_) < 0.08]
    GRID.append(min(near, key=lambda k_: abs(k_ - g_)) if near else g_); n_ += 1
POST = GRID
PRE = [t0 for t0 in KICKS if START < t0 < SIL0]
print(f"Drop {DROP:.2f} s | Pause {SIL0:.2f}-{LEAD:.2f} s | Tempo {60 / BEAT:.1f} BPM | Video {START:.2f}-{END:.2f} s", flush=True)


def F(t):                                                       # Songzeit -> Frame
    return 1 + (t - START) * FPS


def snap(t, lo=None, hi=None):                                   # naechster Kick (fuer Schnitte)
    c = [k_ for k_ in KICKS if (lo is None or k_ >= lo) and (hi is None or k_ <= hi)]
    return min(c, key=lambda k_: abs(k_ - t)) if c else t


# ---------------- 2. Szene: Buehne ohne Lift-Saeule und Block-Performer, Travis als eigene Figur ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
main = lb.load_mpd(MODEL)
skip = {"15_performer.ldr", "16_lift.ldr"} | ({"14_fans.ldr"} if opt.get("ohne-fans") else set())
lb.MPD["video_buehne"] = [l for l in lb.MPD[main] if not (l.split()[:1] == ["1"] and l.split()[-1].lower() in skip)]


def note(sub, tag):
    return [float(v) for v in next(l for l in lb.MPD[sub] if l.startswith(f"0 // {tag}")).split()[3:]]


LIFT = note("16_lift.ldr", "LIFT")                               # Klappen-Oberkante (x, y, z) in LDU
FIG = note("15_performer.ldr", "FIGUR")                          # Standpunkt des Performers auf dem Block
PARTS = list(lb.iter_parts("video_buehne"))
flame = np.array([1.0 if p[0] == "85959" else 0.0 for p in PARTS], np.float32)
org = np.array([lb.to_blender(p[3]) for p in PARTS], np.float32)
obs, _, LO, HI = lb.build_parts("video_buehne", attrs={"flamme": flame, "ox": org[:, 0], "oy": org[:, 1], "oz": org[:, 2]})
fig_obs, _, _, _ = lb.build_parts("15_performer.ldr")
print(f"Szene: {len(PARTS):,} Teile + Travis", flush=True)


def to_b(x, y, z): return Vector(lb.to_blender([x, y, z]).tolist())


EDIT = bpy.context.preferences.edit
EDIT.keyframe_new_interpolation_type = "BEZIER"


def fcurves(idb):
    """F-Curves eines animierten Datenblocks (Blender 4.x Action und 5.x Layered Action)"""
    act = idb.animation_data.action if idb.animation_data else None
    if act is None: return []
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []): out += list(bag.fcurves)
    return out


# Flammen: Geometry Nodes skalieren jedes Flammenteil um seinen Ursprung (Duese), Groesse per Wert-Knoten animiert
ng = bpy.data.node_groups.new("Flamme", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes, ng.links
gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
def attr(name):
    a = N.new("GeometryNodeInputNamedAttribute"); a.data_type = "FLOAT"; a.inputs["Name"].default_value = name; return a.outputs[0]
comb = N.new("ShaderNodeCombineXYZ")
for i, nm in enumerate(("ox", "oy", "oz")): L.new(attr(nm), comb.inputs[i])
pos = N.new("GeometryNodeInputPosition")
sub_ = N.new("ShaderNodeVectorMath"); sub_.operation = "SUBTRACT"; L.new(pos.outputs[0], sub_.inputs[0]); L.new(comb.outputs[0], sub_.inputs[1])
SIZE = N.new("ShaderNodeValue"); SIZE.name = "Groesse"; SIZE.outputs[0].default_value = 1.0
m1 = N.new("ShaderNodeMath"); m1.operation = "SUBTRACT"; L.new(SIZE.outputs[0], m1.inputs[0]); m1.inputs[1].default_value = 1.0
m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; L.new(m1.outputs[0], m2.inputs[0]); L.new(attr("flamme"), m2.inputs[1])
sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; L.new(sub_.outputs[0], sc.inputs[0]); L.new(m2.outputs[0], sc.inputs["Scale"])
sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(sc.outputs[0], sp.inputs["Offset"])
L.new(sp.outputs[0], go.inputs[0])
for ob in obs:
    if ob.name.split(".")[0] in ("farbe_57", "farbe_46", "farbe_47"):
        ob.modifiers.new("Flamme", "NODES").node_group = ng

# Emission: Flammen/Glut/Lampen (transparent) und LED-Wand des Rings (Rot, Orange, Gelb - nur im Ring verwendet)
EMIT = {}
for code, rgb in (("57", (1.0, 0.25, 0.02)), ("46", (1.0, 0.6, 0.12)), ("47", (1.0, 0.93, 0.85)), ("36", (1.0, 0.05, 0.02)),
                  ("14", (1.0, 0.75, 0.1)), ("191", (1.0, 0.5, 0.08)), ("25", (1.0, 0.3, 0.02)), ("4", (0.9, 0.04, 0.01)),
                  ("320", (0.45, 0.02, 0.01))):
    m = lb.MATS.get(code)
    if m is None: continue
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if "Emission Color" in b.inputs: b.inputs["Emission Color"].default_value = (*rgb, 1)
    EMIT[code] = b.inputs["Emission Strength"]
lb.eevee_alpha_glass(0.45)
_blk = next(n for n in lb.MATS["0"].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
_blk.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1); _blk.inputs["Roughness"].default_value = 0.35

# Travis: Figur an einen Empty haengen (Drehpunkt = Fusspunkt), damit sie fliegen, drehen und huepfen kann
FIG_B = to_b(FIG[0], FIG[1], FIG[2])
travis = bpy.data.objects.new("travis", None); scene.collection.objects.link(travis); travis.location = FIG_B
bpy.context.view_layer.update()
for o in fig_obs:
    o.parent = travis; o.matrix_parent_inverse = travis.matrix_world.inverted()
LAND = Vector((LIFT[0], LIFT[1], LIFT[2]))                       # Landepunkt (LDU): auf der Klappe
EYE = 86                                                         # Augenhoehe ueber dem Fuss (LDU)
APEX = -640                                                      # Scheitel des Wurfs (Auge, LDU)

# Lift-Klappe (Requisite): schwarze Platte 2x2, Scharnier an der Vorderkante, klappt auf dem Drop auf
hinge = bpy.data.objects.new("klappe_scharnier", None); scene.collection.objects.link(hinge)
hinge.location = to_b(LAND.x, LAND.y + 4, LAND.z - 19)
bpy.ops.mesh.primitive_cube_add(size=1)
hatch = bpy.context.active_object; hatch.name = "klappe"
hatch.scale = (35 * lb.SCALE, 35 * lb.SCALE, 8 * lb.SCALE)
hatch.location = to_b(LAND.x, LAND.y + 4, LAND.z)
hatch.data.materials.append(lb.MATS["0"])
bpy.context.view_layer.update()
hatch.parent = hinge; hatch.matrix_parent_inverse = hinge.matrix_world.inverted()

# ---------------- 3. Welt, Dunst, Licht ----------------
world = bpy.data.worlds.new("arena"); scene.world = world
if world.node_tree is None: world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND"); bg.inputs[0].default_value = (0, 0, 0, 1); bg.inputs[1].default_value = 0.0
haze = wn.new("ShaderNodeVolumeScatter"); haze.inputs["Density"].default_value = float(opt.get("dunst", 0.25))
haze.inputs["Anisotropy"].default_value = 0.55
wl.new(haze.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Volume"])
cen = (LO + HI) / 2
bpy.ops.mesh.primitive_plane_add(size=2.2, location=(cen[0], cen[1], -0.0008))
fl = bpy.context.object; fm = bpy.data.materials.new("hallenboden"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fb.inputs["Base Color"].default_value = (0.003, 0.003, 0.003, 1); fb.inputs["Roughness"].default_value = 0.85
fl.data.materials.append(fm)


def light(kind, name, pos, target, energy, color, size=0.0, spot=0.0, blend=0.3, haze_gain=1.0):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == "SPOT": d.spot_size = math.radians(spot); d.spot_blend = blend; d.shadow_soft_size = size
    elif kind in ("AREA",): d.size = size
    elif kind == "POINT": d.shadow_soft_size = size
    if hasattr(d, "volume_factor"): d.volume_factor = haze_gain
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o)
    o.location = pos; o.rotation_euler = (Vector(pos) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    return d


TRUSS_Y = -1056
BEAMS = []
for i, x in enumerate(range(-780, 800, 160)):
    for side in (-1, 1):
        BEAMS.append(light("SPOT", f"beam_{i}_{side}", to_b(x, TRUSS_Y + 30, side * 420), to_b(x + 60 * side, -80, side * 40),
                           45.0, (0.95, 0.97, 1.0), size=0.002, spot=4, blend=0.15, haze_gain=2.0))
UPL = [light("AREA", f"uplight_{i}_{s}", to_b(x, -12, s * 230), to_b(x, -160, s * 60), 0.1, (0.9, 0.95, 1.0), size=0.03, haze_gain=0.6)
       for i, x in enumerate(range(-560, 800, 320)) for s in (-1, 1)]
TSPOT = light("SPOT", "travis_spot", to_b(LAND.x, TRUSS_Y + 30, LAND.z - 80), to_b(LAND.x, LAND.y, LAND.z), 0.0,
              (1.0, 0.82, 0.6), size=0.002, spot=6, blend=0.3, haze_gain=1.8)
SHAFT = light("POINT", "schacht", to_b(LAND.x, -20, LAND.z), to_b(LAND.x, -100, LAND.z), 0.004, (1.0, 0.25, 0.05), size=0.002,
              haze_gain=0.0)
GLUT = light("AREA", "glut", to_b(0, -40, 0), to_b(0, -400, 0), 1.4, (1.0, 0.25, 0.05), size=0.6, haze_gain=0.0)
FILL = light("AREA", "fuell", to_b(-600, -900, -1700), to_b(0, -200, 0), 1.6, (0.85, 0.85, 1.0), size=1.2, haze_gain=0.0)
BACK = light("AREA", "gegen", to_b(600, -1100, 1600), to_b(0, -200, 0), 4.0, (1.0, 0.45, 0.2), size=1.2, haze_gain=0.0)
BLOCK = light("SPOT", "block_spot", to_b(-740, TRUSS_Y + 30, -520), to_b(-740, -300, -80), 30.0, (1.0, 0.8, 0.6), size=0.004,
              spot=14, blend=0.4, haze_gain=1.2)
STROBE = light("AREA", "strobe", to_b(0, -1000, -600), to_b(0, -100, 0), 0.0, (1, 1, 1), size=2.0, haze_gain=0.4)

for d in [GLUT, STROBE]:                                        # nur grosse Flaechenlichter ohne Schatten (Tempo)
    if hasattr(d, "use_shadow"): d.use_shadow = False

# ---------------- 4. Licht- und Effekt-Choreografie ----------------
def keyval(sock_or_obj, path, pts):
    for t0, v in sorted(pts):
        setattr(sock_or_obj, path, v); sock_or_obj.keyframe_insert(path, frame=F(t0))


# Ring/LED-Wand: atmet mit der Lautstaerke (alle 3 Frames), nach dem Drop deutlich heller
step = 3 / FPS
ring_pts = []
t0 = START
while t0 <= END + TAIL:
    lv = min(1.5, mean_in(tm, rm, t0 - 0.05, t0 + 0.05) / (LVL + 1e-9))
    base = 0.4 if t0 < DROP else 0.85
    ring_pts.append((t0, base * (0.12 + 1.0 * lv)))
    t0 += step
for code in ("14", "191", "25", "4", "320"):
    if code in EMIT: keyval(EMIT[code], "default_value", ring_pts)
# Flammen: vor dem Drop kleine Zuendflammen, auf dem Drop Riesenstoss, danach Stoss auf jedem Kick
fpts = [(START, 0.25), (SIL0 - 1 / FPS, 0.25), (SIL0 + 0.1, 0.12), (DROP - 1 / FPS, 0.12), (DROP + 0.06, 1.9), (DROP + 0.7, 1.05)]
gpts = [(START, 0.8), (SIL0 - 1 / FPS, 0.8), (SIL0 + 0.1, 0.15), (LEAD, 0.15), (DROP - 1 / FPS, 0.5), (DROP + 0.06, 9.0),
        (DROP + 0.7, 3.0)]
for kk in POST:
    fpts += [(kk - 1 / FPS, 1.0), (kk + 0.05, 1.45), (kk + 0.35, 1.0)]
    gpts += [(kk - 1 / FPS, 3.0), (kk + 0.05, 6.0), (kk + 0.35, 3.0)]
keyval(SIZE.outputs[0], "default_value", fpts)
for code in ("57", "46", "36"):
    if code in EMIT: keyval(EMIT[code], "default_value", gpts)
if "47" in EMIT: keyval(EMIT["47"], "default_value", [(START, 1.5), (DROP - 1 / FPS, 1.5), (DROP + 0.06, 8.0), (DROP + 0.7, 2.6)])
# Lichtkegel: vor dem Drop gedimmt, auf dem Drop voll, auf den Kicks ein Blitz
for i, d in enumerate(BEAMS):
    pts = [(START, 10.0), (SIL0 - 1 / FPS, 10.0), (SIL0 + 0.05, 0.0), (LEAD, 0.0), (DROP - 1 / FPS, 14.0),
           (DROP + 0.04, 120.0), (DROP + 0.5, 45.0)]
    for kk in POST[i % 2::2]: pts += [(kk - 1 / FPS, 45.0), (kk + 0.04, 90.0), (kk + 0.3, 45.0)]
    keyval(d, "energy", pts)
for d in UPL: d.energy = 0.1
keyval(TSPOT, "energy", [(START, 0.0), (DROP + 1.2, 0.0), (DROP + 1.7, 35.0)])
sh_pts, t0 = [(START, 0.0), (SIL0 - 0.1, 0.0)], SIL0
while t0 < DROP:                                                  # Glut im Schacht flackert mit der Musik, steigt im Anlauf
    lv = min(1.5, mean_in(tm, rm, t0 - 0.04, t0 + 0.04) / (LVL + 1e-9))
    ramp = 0.0 if t0 < LEAD else (t0 - LEAD) / max(0.1, DROP - LEAD)
    sh_pts.append((t0, 0.002 + 0.03 * lv + 0.06 * ramp * ramp)); t0 += 2 / FPS
sh_pts += [(DROP, 0.05), (DROP + 0.25, 0.0)]
keyval(SHAFT, "energy", sh_pts)
for d in UPL + [GLUT, FILL, BACK]:                                # Blackout in der Pause
    e = d.energy
    keyval(d, "energy", [(START, e), (SIL0 - 1 / FPS, e), (SIL0 + 0.05, e * 0.08), (LEAD, e * 0.08), (DROP - 1 / FPS, e * 0.4),
                         (DROP + 0.05, e * 1.6), (DROP + 0.6, e)])
keyval(STROBE, "energy", [(START, 0.0), (DROP - 1 / FPS, 0.0), (DROP + 0.02, 60.0), (DROP + 0.12, 0.0), (DROP + 0.2, 45.0),
                          (DROP + 0.3, 0.0)] + sum([[(kk - 1 / FPS, 0.0), (kk + 0.02, 10.0), (kk + 0.1, 0.0)] for kk in POST[3::4]], []))
# Klappe: auf dem Drop auf (nach oben weggeschlagen), nach dem Wurf wieder zu (Travis landet darauf)
keyval(hinge, "rotation_euler", [(START, (0, 0, 0)), (DROP - 1 / FPS, (0, 0, 0)), (DROP + 0.12, (math.radians(115), 0, 0)),
                                 (DROP + 0.9, (math.radians(115), 0, 0)), (DROP + 1.15, (0, 0, 0))])

# Travis: unsichtbar bis zum Scheitel, dann Fall mit einer Drehung, Landung auf der Klappe, Huepfer auf den Kicks
T_APEX, T_LAND = DROP + 0.8, DROP + 1.75
land_b = to_b(LAND.x, LAND.y, LAND.z)
apex_b = to_b(LAND.x, APEX + EYE, LAND.z)
for o in [travis] + fig_obs:
    o.hide_render = True; o.keyframe_insert("hide_render", frame=F(START))
    o.hide_render = True; o.keyframe_insert("hide_render", frame=F(T_APEX) - 1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=F(T_APEX))
pts = [(START, apex_b), (T_APEX, apex_b)]
n_fall = 8
for i in range(1, n_fall + 1):                                   # Fall mit Schwerkraft (quadratisch)
    u = i / n_fall
    pts.append((T_APEX + u * (T_LAND - T_APEX), apex_b.lerp(land_b, u * u)))
hops = [kk for kk in POST if kk > T_LAND + 0.2]
for kk in hops:
    pts += [(kk - 0.02, land_b), (kk + 0.13, land_b + Vector((0, 0, 12 * lb.SCALE))), (kk + 0.28, land_b)]
keyval(travis, "location", pts)
for fc in fcurves(travis):
    if fc.data_path == "location":
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
keyval(travis, "rotation_euler", [(START, (0, 0, 0)), (T_APEX, (0, 0, 0)), (T_LAND, (0, 0, math.radians(-360)))])

# ---------------- 5. Kameras und Schnitte ----------------
CAMS = []


def camera(name, lens=30):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.0008; cd.clip_end = 40
    cam = bpy.data.objects.new(name, cd); scene.collection.objects.link(cam)
    tg = bpy.data.objects.new(name + "_ziel", None); scene.collection.objects.link(tg)
    c = cam.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    return cam, tg


def shot(name, t_a, t_b, cam_pts, tgt_pts, lens=30, shake=0.0):
    """cam_pts/tgt_pts: Listen (u 0..1, (x, y, z) LDU) ueber die Shot-Dauer"""
    cam, tg = camera(name, lens)
    for u, p in cam_pts: cam.location = to_b(*p); cam.keyframe_insert("location", frame=F(t_a + u * (t_b - t_a)))
    for u, p in tgt_pts: tg.location = to_b(*p); tg.keyframe_insert("location", frame=F(t_a + u * (t_b - t_a)))
    if shake:
        for fc in fcurves(cam):
            mo = fc.modifiers.new("NOISE"); mo.scale = 3.0; mo.strength = shake * lb.SCALE; mo.phase = random.uniform(0, 100)
    CAMS.append((t_a, cam))
    return cam


def path_z(x):                                                    # Weg-Mittellinie wie zc() im Generator (LDU)
    c_ = x / 20.0
    if c_ <= -30.0: return -60.0
    return 20 * (-3.0 + 4.2 * math.sin((c_ + 30.0) * 2 * math.pi / 34.0) + 1.2 * math.sin((c_ + 30.0) * 2 * math.pi / 13.0))


V = SIL0 - START
c1, c2, c3 = snap(START + 0.27 * V, START + 2, SIL0 - 6), snap(START + 0.53 * V, None, SIL0 - 4), snap(START + 0.76 * V, None, SIL0 - 2)
c4 = SIL0
K1 = LEAD + 0.55 * (DROP - LEAD)
# Vor dem Drop: Praesentation
shot("totale", START, c1, [(0, (-420, -300, -1700)), (1, (-150, -240, -1250))], [(0, (0, -360, 0)), (1, (0, -300, 0))], lens=32)
shot("koepfe", c1, c2, [(0, (-620, -240, -640)), (1, (420, -240, -600))], [(0, (-480, -130, -60)), (1, (560, -130, -40))], lens=35)
shot("block", c2, c3, [(0, (-1200, -340, -700)), (0.5, (-860, -320, -760)), (1, (-480, -300, -700))],
     [(0, (-760, -300, -100)), (1, (-700, -280, -80))], lens=30)
shot("kran", c3, c4, [(0, (LAND.x - 60, -900, LAND.z - 420)), (1, (LAND.x, -150, LAND.z - 90))],
     [(0, (LAND.x, -200, LAND.z)), (1, (LAND.x, -80, LAND.z))], lens=30)
# Schacht-POV: Blick nach oben auf die Klappe, Zittern nimmt zu
eye0 = (LAND.x, -30, LAND.z)
pov = shot("schacht", c4, LEAD, [(0, eye0), (1, eye0)], [(0, (LAND.x + 1, -900, LAND.z + 2)), (1, (LAND.x + 1, -900, LAND.z + 2))],
           lens=16, shake=0.8)
kx = LAND.x + 230
shot("klappe", LEAD, K1, [(0, (LAND.x + 150, -260, LAND.z + 60)), (1, (LAND.x + 110, -220, LAND.z + 45))],
     [(0, (LAND.x, -82, LAND.z)), (1, (LAND.x, -82, LAND.z))], lens=30, shake=0.4)
shot("schacht2", K1, DROP, [(0, eye0), (1, eye0)], [(0, (LAND.x + 1, -900, LAND.z + 2)), (1, (LAND.x + 1, -900, LAND.z + 2))],
     lens=16, shake=3.0)
# Drop: Wurf nach oben (POV), Blick kippt von oben nach vorne auf Buehne und Publikum
wurf_cam = [(0, eye0)]
for i in range(1, 9):
    u = i / 8
    wurf_cam.append((u, (LAND.x, -30 + (APEX + 30) * (1 - (1 - u) ** 3), LAND.z - 40 * u)))
shot("wurf", DROP, T_APEX, wurf_cam, [(0, (LAND.x + 1, -1400, LAND.z + 2)), (0.45, (LAND.x + 60, -1100, LAND.z - 500)),
                                       (1, (LAND.x + 120, -150, LAND.z - 900))], lens=16, shake=2.5)
# Landung von aussen
shot("landung", T_APEX, T_LAND + 0.6, [(0, (LAND.x + 420, -360, LAND.z + 30)), (1, (LAND.x + 300, -330, LAND.z + 20))],
     [(0, (LAND.x, APEX + EYE - 40, LAND.z)), (0.7, (LAND.x, -140, LAND.z)), (1, (LAND.x, -145, LAND.z))], lens=30)
# Nach dem Drop: Schnitte auf jedem zweiten Kick durch einen Pool von Einstellungen
X, Z = LAND.x, LAND.z
POOL = [
    ("nah", [(0, (X + 200, -340, Z + 30)), (1, (X + 160, -320, Z + 20))], [(0, (X, -165, Z)), (1, (X, -165, Z))], 35),
    ("weit", [(0, (-260, -110, -940)), (1, (60, -110, -900))], [(0, (0, -330, 0)), (1, (60, -330, 0))], 28),
    ("orbit", [(0, (X + 170, -370, Z - 150)), (0.5, (X + 230, -360, Z)), (1, (X + 170, -350, Z + 150))],
     [(0, (X, -160, Z)), (1, (X, -160, Z))], 30),
    ("ring", [(0, (X + 160, -290, Z)), (1, (X + 120, -300, Z + 10))], [(0, (X - 260, -860, Z - 240)), (1, (X - 100, -860, Z - 300))], 18),
    ("seite", [(0, (720, -300, 520)), (1, (420, -300, 500))], [(0, (300, -140, 0)), (1, (60, -140, -40))], 30),
    ("oben", [(0, (X + 40, -1250, Z - 260)), (1, (X - 40, -1150, Z - 220))], [(0, (X, -80, Z)), (1, (X, -80, Z))], 24),
]
cuts = [T_LAND + 0.6]
for kk in POST:
    if kk - cuts[-1] >= float(opt.get("schnitt", 1.2)) and kk < END - 0.6: cuts.append(kk)
cuts.append(END + TAIL)
for i in range(len(cuts) - 1):
    nm, cp, tp, lens = POOL[i % len(POOL)]
    shot(f"{nm}_{i}", cuts[i], cuts[i + 1], cp, tp, lens=lens, shake=0.6 if nm in ("nah", "orbit") else 0.0)
# Kamerawechsel per Marker
CAMS.sort(key=lambda c: c[0])
for t_a, cam in CAMS:
    mk = scene.timeline_markers.new(cam.name, frame=int(round(F(t_a)))); mk.camera = cam
scene.camera = CAMS[0][1]
print("Schnitte:", " | ".join(f"{t_a - START:.2f}s {cam.name}" for t_a, cam in CAMS), flush=True)
json.dump(dict(drop=DROP, pause=[SIL0, LEAD], tempo_bpm=60 / BEAT, start=START, ende=END, beats_nach=POST, schnitte=[(t_a, cam.name) for t_a, cam in CAMS]),
          open(PREFIX + "_timing.json", "w", encoding="utf-8"), indent=1)

# ---------------- 6. Rendern ----------------
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: scene.render.engine = eng; break
    except TypeError: pass
ee = scene.eevee
ee.taa_render_samples = int(opt.get("samples", 16))
for a_, v_ in (("use_raytracing", False), ("use_shadows", True), ("use_volumetric_shadows", False), ("volumetric_tile_size", "4"),
               ("volumetric_samples", 64), ("volumetric_start", 0.002), ("volumetric_end", 6.0), ("volumetric_light_clamp", 0.0),
               ("use_bloom", True)):
    if hasattr(ee, a_):
        try: setattr(ee, a_, v_)
        except (TypeError, ValueError) as e: print("EEVEE", a_, e)
scene.render.use_motion_blur = True
if hasattr(scene.render, "motion_blur_shutter"): scene.render.motion_blur_shutter = 0.4
try: scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError: pass
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.frame_start, scene.frame_end = 1, int(round(F(END + TAIL)))
if "frames" in opt:
    a_, b_ = opt["frames"].split("-"); scene.frame_start, scene.frame_end = int(a_), int(b_)
scene.render.image_settings.file_format = "PNG"
if "blend" in opt: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt["blend"]))

if opt.get("probe"):
    out = PREFIX + "_probe"; os.makedirs(out, exist_ok=True)
    scene.render.resolution_percentage = 50
    probe = [START + 1.0, (START + c1) / 2 + 2, (c1 + c2) / 2, (c2 + c3) / 2, (c3 + c4) / 2, (SIL0 + LEAD) / 2, (LEAD + K1) / 2, DROP - 0.2,
             DROP + 0.15, DROP + 0.45, T_APEX + 0.1, T_LAND - 0.1, T_LAND + 0.4] + [(cuts[i] + cuts[i + 1]) / 2 for i in range(min(6, len(cuts) - 1))]
    for n, t0 in enumerate(probe):
        f = int(round(F(t0))); scene.frame_set(f)
        for t_a, cam in reversed(CAMS):
            if t_a <= t0: scene.camera = cam; break
        scene.render.filepath = os.path.join(out, f"{n:02d}_{t0 - START:05.2f}s.png")
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print(f"  {n:02d} {t0 - START:5.2f} s {scene.camera.name} ({time.time() - t1:.1f} s)", flush=True)
    sys.exit(0)

os.makedirs(PREFIX + "/frames", exist_ok=True)
scene.render.filepath = PREFIX + "/frames/"
t1 = time.time()
bpy.ops.render.render(animation=True)
print(f"Frames fertig ({(time.time() - t1) / 60:.1f} min)", flush=True)

ff = shutil.which("ffmpeg")
if ff and "frames" not in opt:
    dur = END + TAIL - START
    vf = f"fade=t=in:st=0:d=0.6,fade=t=out:st={dur - TAIL - 0.1:.3f}:d={TAIL + 0.1:.3f},format=yuv420p"
    cmd = [ff, "-y", "-v", "error", "-framerate", str(FPS), "-start_number", "1", "-i", PREFIX + "/frames/%04d.png"]
    if MUSIC != "-":
        cmd += ["-ss", f"{START:.3f}", "-i", MUSIC, "-map", "0:v", "-map", "1:a",
                "-af", f"afade=t=in:st=0:d=0.8,afade=t=out:st={dur - TAIL - 0.3:.3f}:d={TAIL + 0.3:.3f}", "-c:a", "aac", "-b:a", "256k"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-t", f"{dur:.3f}", PREFIX + ".mp4"]
    subprocess.run(cmd, check=True)
    print("Video:", PREFIX + ".mp4", flush=True)
