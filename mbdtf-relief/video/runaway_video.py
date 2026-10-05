"""
MBDTF-Relief x "Runaway" - 20-Sekunden-Motion-Clip in Blender, auf die Musik geschnitten
=======================================================================================
Stil: ruhig und clean wie ein Produktfilm - schwarzer Hintergrund, weiches Licht, gleichmaessige Fahrten
und Orbits in einem Abstandsbereich (kein Rein-und-raus, keine Makros, kein Zoom-Punch), 30 fps mit
leichter Bewegungsunschaerfe.
Ablauf: die letzten 10 Klaviertoene - jeder Ton laesst eine Welle Teile einfallen (Stoff, Aufkleber,
Leinwand, Rahmen, Figur, zuletzt das Weinglas), Schnitt alle 2 Toene. Drop: Licht fährt hoch, Schnitt alle
2 Schlaege, zuletzt die Draufsicht wie das Cover. Harter Schnitt auf Schwarz auf dem naechsten Downbeat.

Aufruf (aus dem Repo-Ordner):
  blender -b -P mbdtf-relief/video/runaway_video.py -- "<runaway.mp3>" out/runaway20 [Optionen]
Optionen:
  --probe             je Einstellung ein Standbild (out/runaway20_shots/), schnell zum Pruefen
  --res 1920x1080     Aufloesung            --fps 30
  --samples 32        EEVEE-Samples         --frames 100-200   nur diese Frames
  --laenge 20         Cliplaenge in s       --takte 2          Takte nach dem Drop
  --blend datei.blend Szene speichern (mit Ton im Sequencer, zum Nachbearbeiten)
Ausgabe: <prefix>/frames/####.png, <prefix>_schnitt.json, <prefix>.mp4 (mit Ton, per ffmpeg)
Die Audiodatei wird nicht ins Repo kopiert.
"""
import json, math, os, shutil, subprocess, sys, time, warnings
import numpy as np
import aud
import bpy
from mathutils import Vector

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender-render"))
import ldraw_blender as lb

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2: sys.exit(__doc__)
AUDIO, PREFIX = argv[0], os.path.abspath(argv[1])
opt, k = {}, 2
while k < len(argv):
    if argv[k] in ("--probe",): opt[argv[k][2:]] = True; k += 1
    else: opt[argv[k].lstrip("-")] = argv[k + 1]; k += 2
FPS = int(opt.get("fps", 30))
RES = tuple(int(v) for v in opt.get("res", "1920x1080").lower().split("x"))
LENGTH = float(opt.get("laenge", 20))
BARS_AFTER = int(opt.get("takte", 2))
TAIL = 0.2                                                      # Schwarz nach dem Schlussschnitt
MODEL = os.path.join(HERE, "..", "mbdtf_relief.mpd")


# ---------------- 1. Musik analysieren ----------------
def analyse(path):
    snd = aud.Sound(path)
    sr = int(snd.specs[0])
    x = np.asarray(snd.data(), np.float32)
    x = x.mean(1) if x.ndim == 2 else x
    dur = len(x) / sr
    n, hop = 2048, 512
    frames = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(frames)[:, None]
    win = np.hanning(n).astype(np.float32)
    t = (np.arange(frames) * hop + n / 2) / sr
    rms = np.zeros(frames, np.float32); flux = np.zeros(frames, np.float32)
    prev = None
    for a in range(0, frames, 2000):                          # blockweise (Speicher)
        blk = x[idx[a:a + 2000]]
        rms[a:a + 2000] = np.sqrt((blk ** 2).mean(1))
        L = np.log1p(100 * np.abs(np.fft.rfft(blk * win, axis=1)))
        d = np.diff(np.vstack([L[:1] if prev is None else prev[None], L]), axis=0)
        flux[a:a + 2000] = np.maximum(d, 0).sum(1); prev = L[-1]
    fr = sr / hop
    on = flux - np.convolve(flux, np.ones(43) / 43, "same")
    on = np.maximum(on, 0); on /= np.percentile(on, 99) + 1e-9
    # Drop: Lautstaerke (1-s-Mittel) steigt vom Intro-Niveau auf halbe Hoehe des lauten Teils
    w = int(fr)
    rs = np.convolve(rms, np.ones(w) / w, "full")[w - 1:len(rms) + w - 1]     # Fenster ab t nach vorne
    base = np.median(rs[t < 10])
    i = int(np.argmax((rs > base + 0.5 * (np.percentile(rs, 95) - base)) & (t > 5)))
    ws = max(1, int(0.3 * fr))                                  # genauer: kurzes Fenster (0,3 s) ab t
    rq = np.convolve(rms, np.ones(ws) / ws, "full")[ws - 1:len(rms) + ws - 1]
    bq = np.median(rq[t < 10])
    j = i + int(np.argmax(rq[i:] > bq + 0.5 * (np.percentile(rq, 95) - bq)))
    win_i = np.where((t > t[j] - 0.05) & (t < t[j] + 0.35))[0]
    drop = float(t[win_i[np.argmax(on[win_i])]])
    # Klaviertoene im Intro
    pk = [j for j in range(1, len(on) - 1) if on[j] > 0.3 and on[j] >= on[j - 1] and on[j] >= on[j + 1] and t[j] < drop - 0.25]
    notes = []
    for j in pk:
        if not notes or t[j] - notes[-1] > 0.6: notes.append(float(t[j]))
        elif on[j] > on[int(round((notes[-1] * sr - n / 2) / hop))]: notes[-1] = float(t[j])
    # Schlag: Toene liegen 2 Schlaege auseinander; Periode und Phase am Beat verfeinern
    p0 = float(np.median(np.diff(notes))) / 2 if len(notes) > 4 else 60 / 87
    best = (-1, p0)
    for p in np.linspace(0.97 * p0, 1.03 * p0, 121):
        g = drop + p * np.arange(int((dur - drop) / p))
        s = on[np.clip(np.round((g * sr - n / 2) / hop).astype(int), 0, len(on) - 1)].sum()
        if s > best[0]: best = (s, p)
    per = float(best[1])
    return dict(dur=dur, drop=drop, notes=notes, beat=per, bpm=60 / per)


A = analyse(AUDIO)
BEAT = A["beat"]
CUT = A["drop"] + 4 * BARS_AFTER * BEAT                         # Schnitt auf Schwarz (Downbeat)
START = max(0.0, CUT + TAIL - LENGTH)                           # Ausschnitt im Song
V = lambda t: t - START                                         # Songzeit -> Clipzeit
DROP, END = V(A["drop"]), V(CUT)
NOTES = [V(n) for n in A["notes"] if n > START + 0.3]
BEATS = [DROP + BEAT * m for m in range(4 * BARS_AFTER)]
print(f"Musik: Ausschnitt {START:.2f}-{CUT + TAIL:.2f} s, {len(NOTES)} Klaviertoene, Drop bei {DROP:.2f} s "
      f"(Clipzeit), {A['bpm']:.1f} BPM", flush=True)


def F(t):
    """Clipzeit (s) -> Frame"""
    return 1 + t * FPS


# ---------------- 2. Szene: Relief mit Einbauzeit je Teil ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
main = lb.load_mpd(MODEL)
PARTS = list(lb.iter_parts(main))


# Reliefgroesse aus dem Modell, Bildbereiche aus zonen.json (passt zu 96x96, 128x128 usw.)
WL = float(2 * (max(max(abs(p[3][0]), abs(p[3][2])) for p in PARTS if not p[0].startswith(("4186", "3811"))) + 10))
KS = WL / 1920                                                  # Kamera-Abstaende sind fuer 96 Noppen ausgelegt
ZONES = {z["name"]: z for z in json.load(open(os.path.join(HERE, "..", "zonen.json"), encoding="utf-8"))}
def rect(name): return tuple(ZONES[name]["von"]), tuple(ZONES[name]["bis"])
CANVAS = rect("Leinwand")
_fr = [rect(n) for n in ZONES if n.startswith("Rahmen aussen")]
FRAME = ((min(a[0] for a, b in _fr), min(a[1] for a, b in _fr)), (max(b[0] for a, b in _fr), max(b[1] for a, b in _fr)))
STICKER = rect("Parental Advisory") if "Parental Advisory" in ZONES else None
GLASS = [tuple(ZONES[n]["mitte"]) for n in ("Weinglas", "Rotwein") if n in ZONES]


def uv(pos):
    """LDraw-Position -> Bildkoordinaten (u nach rechts, v nach unten, 0..1) und Hoehe in Platten"""
    return 0.5 - pos[0] / WL, pos[2] / WL + 0.5, -pos[1] / 8


def inside(u, v, r):
    return r[0][0] <= u <= r[1][0] and r[0][1] <= v <= r[1][1]


phase = []
for name, col, M, pos, inv in PARTS:
    u, v, h = uv(pos)
    if name.startswith(("4186", "3811")): ph = "platten"
    elif any(abs(u - gu) < 0.006 and abs(v - gv) < 0.006 for gu, gv in GLASS) and h > 4: ph = "glas"
    elif STICKER and inside(u, v, STICKER): ph = "aufkleber"
    elif inside(u, v, CANVAS): ph = "leinwand" if h <= 4 else "figur"
    elif inside(u, v, FRAME): ph = "rahmen"
    else: ph = "stoff"
    phase.append(ph)
NN = len(NOTES)
def nr(frac): return min(NN - 1, int(round(frac * (NN - 1))))
PH_NOTES = {"platten": (0, 0), "stoff": (0, nr((3 if STICKER else 4) / 9)), "aufkleber": (nr(4 / 9), nr(4 / 9)),
            "leinwand": (nr(5 / 9), nr(6 / 9)), "rahmen": (nr(7 / 9), nr(7 / 9)),
            "figur": (nr(8 / 9), nr(8 / 9)), "glas": (NN - 1, NN - 1)}
if not STICKER: del PH_NOTES["aufkleber"]
T0 = np.zeros(len(PARTS))
SPREAD = 0.62 * float(np.median(np.diff(NOTES)))                # Welle je Ton, endet vor dem naechsten
for ph, (n0, n1) in PH_NOTES.items():
    ids = [i for i, p in enumerate(phase) if p == ph]
    ids.sort(key=lambda i: (round(uv(PARTS[i][3])[2]), sum(uv(PARTS[i][3])[:2])))   # unten zuerst, dann diagonal
    k = n1 - n0 + 1
    for r, i in enumerate(ids):
        T0[i] = n0 + min(k - 1, r * k // len(ids))
T0n = T0.copy()
for n in range(NN):                                             # innerhalb eines Tons als Welle verteilen
    ids = list(np.where(T0n == n)[0])
    ids.sort(key=lambda i: (phase[i] != "platten", round(uv(PARTS[i][3])[2]), sum(uv(PARTS[i][3])[:2])))
    for r, i in enumerate(ids):
        T0[i] = F(NOTES[n] + (r / max(1, len(ids))) * SPREAD)
print("Einbau:", {ph: sum(1 for p in phase if p == ph) for ph in PH_NOTES}, flush=True)

obs, _, LO, HI = lb.build_parts(main, attrs={"t0": T0})
print(f"Szene: {len(PARTS):,} Teile in {len(obs)} Farben", flush=True)

# Teil erscheint zur Zeit t0 und senkt sich weich (Ease-out) an seinen Platz; Glas fuer EEVEE
lb.add_build_anim(obs, 0.045, 0.32 * FPS)
lb.eevee_alpha_glass()

# ---------------- 3. Licht: schwarzer Raum, weiches Licht, faehrt zum Drop hoch ----------------
EDIT = bpy.context.preferences.edit
def interp(kind): EDIT.keyframe_new_interpolation_type = kind
world = bpy.data.worlds.new("welt"); scene.world = world
if world.node_tree is None: world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.012, 0.012, 0.014, 1)


def sun(name, rot, energy, color=(1, 1, 1), angle=12):
    d = bpy.data.lights.new(name, "SUN"); d.energy = energy; d.color = color; d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o)
    o.rotation_euler = Vector(rot).normalized().to_track_quat("Z", "Y").to_euler()
    return o.data


key_l = sun("key", (0.55, -0.45, 0.75), 1.0)                   # weich von links oben (Bild)
rim = sun("rim", (-0.6, 0.7, 0.3), 1.0, (1.0, 0.86, 0.7), 10)  # warmes Gegenlicht von rechts unten
fill = sun("fill", (0.0, 0.9, 0.45), 0.5, (0.85, 0.9, 1.0), 20)
def ramp(data, path, pts):
    for t, val in pts:
        setattr(data, path, val); data.keyframe_insert(path, frame=F(t))
interp("BEZIER")
kpts = [(0, 1.1)]
for n in NOTES:                                                 # dezenter Lichtatmer je Ton
    kpts += [(n - 1 / FPS, 1.1), (n + 0.12, 1.7), (n + 0.9, 1.1)]
kpts += [(DROP - 1 / FPS, 1.1), (DROP + 0.18, 5.2), (END, 5.2)]
ramp(key_l, "energy", kpts)
ramp(rim, "energy", [(0, 1.2), (DROP - 1 / FPS, 1.2), (DROP + 0.18, 2.2)])
ramp(fill, "energy", [(0, 0.25), (DROP - 1 / FPS, 0.25), (DROP + 0.18, 0.9)])
bgs = bg.inputs[1]
for t, val in ((0, 0.3), (DROP - 1 / FPS, 0.3), (DROP + 0.18, 1.0)):
    bgs.default_value = val; bgs.keyframe_insert("default_value", frame=F(t))

# ---------------- 4. Kameras: gleichmaessige Fahrten, Schnitte auf die Musik ----------------
def P(u, v, h=0.0):
    """Bildkoordinaten (u, v in 0..1, Hoehe in Platten) -> Blender-Punkt"""
    return Vector(lb.to_blender([(0.5 - u) * WL, -h * 8, (v - 0.5) * WL]).tolist())
def sph(tgt, az, el, dist):
    a, e = math.radians(az), math.radians(el)
    return tgt + dist * Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
EASE = {"sanft": lambda x: 0.5 - 0.5 * math.cos(math.pi * x),
        "aus": lambda x: 1 - (1 - x) ** 3,
        "schnell": lambda x: (1 - 2 ** (-8 * x)) / (1 - 2 ** -8)}

C = P(0.5, 0.5, 3)
# Einstellung: (Name, Ziel a -> b, az a -> b, el a -> b, Abstand a -> b, Brennweite, Easing)
def S(name, ta, tb, az, el, d, lens=50, ease="sanft"):
    return dict(name=name, ta=ta, tb=tb, az=az, el=el, d=(d[0] * KS, d[1] * KS), lens=lens, ease=ease)
INTRO = [
    S("Grundplatten, Stoff - Orbit", C, C, (206, 194), (52, 50), (1.32, 1.32), 50),
    S("Stoff - seitliche Fahrt", P(0.22, 0.72, 2), P(0.50, 0.76, 2), (180, 180), (34, 34), (0.62, 0.62), 50),
    S("Aufkleber, Leinwand - Orbit" if STICKER else "Stoff, Leinwand - Orbit", P(0.88, 0.88, 2), P(0.72, 0.72, 2), (204, 214), (40, 40), (0.72, 0.72), 50),
    S("Leinwand, Rahmen - Fahrt", P(0.40, 0.50, 4), P(0.60, 0.50, 4), (180, 180), (38, 38), (0.64, 0.64), 50),
    S("Figur, Glas - Orbit", P(0.46, 0.50, 8), P(0.46, 0.50, 8), (214, 226), (36, 36), (0.52, 0.52), 50),
]
AFTER = [
    S("Drop - Hero", C, C, (148, 162), (24, 29), (0.84, 0.84), 40, "schnell"),
    S("Gegenseite", P(0.5, 0.5, 5), P(0.5, 0.5, 5), (218, 206), (30, 30), (0.86, 0.86), 45, "schnell"),
    S("Frontal, Fahrt", P(0.40, 0.50, 6), P(0.60, 0.50, 6), (180, 180), (22, 22), (0.70, 0.70), 45, "schnell"),
    S("Cover", C, C, (180, 180), (88, 88), (2.12, 2.04), 50, "aus"),
]
cuts = [0.0] + [NOTES[i] for i in range(2, NN, 2) if NOTES[i] < DROP - 1.0] + [DROP]
shots = [(cuts[i], cuts[i + 1], INTRO[min(i, len(INTRO) - 1)]) for i in range(len(cuts) - 1)]
after = BEATS[::2] + [END]                                      # nach dem Drop alle 2 Schlaege
for i in range(len(after) - 1):
    shots.append((after[i], after[i + 1], AFTER[min(i, len(AFTER) - 2)] if i < len(after) - 2 else AFTER[-1]))

interp("LINEAR")
for n, (a, b, s) in enumerate(shots):
    cd = bpy.data.cameras.new(f"cam{n:02d}"); cd.clip_start = 0.005; cd.clip_end = 50; cd.lens = s["lens"]
    cam = bpy.data.objects.new(f"{n:02d}_{s['name']}", cd); scene.collection.objects.link(cam)
    tg = bpy.data.objects.new(f"{n:02d}_ziel", None); scene.collection.objects.link(tg)
    c = cam.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    f0, f1 = int(round(F(a))), int(round(F(b)))
    for f in range(f0, f1 + 1):                                 # Bahn je Frame mit eigenem Easing
        x = EASE[s["ease"]](min(1.0, max(0.0, ((f - 1) / FPS - a) / (b - a))))
        tgt = s["ta"].lerp(s["tb"], x)
        lerp = lambda p: p[0] + (p[1] - p[0]) * x
        tg.location = tgt; tg.keyframe_insert("location", frame=f)
        cam.location = sph(tgt, lerp(s["az"]), lerp(s["el"]), lerp(s["d"])); cam.keyframe_insert("location", frame=f)
    m = scene.timeline_markers.new(f"{n:02d} {s['name']}", frame=f0); m.camera = cam
    if n == 0: scene.camera = cam

json.dump(dict(ausschnitt=[round(START, 3), round(CUT + TAIL, 3)], drop=round(DROP, 3), bpm=round(A["bpm"], 2),
               toene=[round(x, 3) for x in NOTES],
               schnitte=[dict(nr=n, name=s["name"], von=round(a, 3), bis=round(b, 3), frame=int(round(F(a))))
                         for n, (a, b, s) in enumerate(shots)]),
          open(PREFIX + "_schnitt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Schnitte: {len(shots)}: " + ", ".join(f"{a:.2f}" for a, _, _ in shots), flush=True)

# ---------------- 5. Rendern ----------------
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: scene.render.engine = eng; break
    except TypeError: pass
ee = scene.eevee
ee.taa_render_samples = int(opt.get("samples", 32))
for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True)):
    if hasattr(ee, attr): setattr(ee, attr, val)
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
    se = scene.sequence_editor_create()
    snd = (se.strips if hasattr(se, "strips") else se.sequences).new_sound("Runaway", AUDIO, 1, int(round(F(-START))))
except Exception as e:
    print("Ton im Sequencer nicht angelegt:", e)
scene.render.use_sequencer = False
if "blend" in opt:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt["blend"]))

if opt.get("probe"):                                            # je Einstellung ein Standbild
    out = PREFIX + "_shots"; os.makedirs(out, exist_ok=True)
    scene.render.resolution_percentage = 50
    for n, (a, b, s) in enumerate(shots):
        scene.frame_set(int(round(F(a + 0.6 * (b - a)))))
        scene.render.filepath = os.path.join(out, f"{n:02d}.png")
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print(f"  {n:02d} {a:5.2f}-{b:5.2f} s {s['name']} ({time.time() - t1:.1f} s)", flush=True)
    sys.exit(0)

os.makedirs(PREFIX + "/frames", exist_ok=True)
scene.render.filepath = PREFIX + "/frames/"
t1 = time.time()
bpy.ops.render.render(animation=True)
print(f"Frames fertig ({(time.time() - t1) / 60:.1f} min)", flush=True)

ff = shutil.which("ffmpeg")
if ff and "frames" not in opt:
    total = END + TAIL
    cmd = [ff, "-y", "-v", "error", "-framerate", str(FPS), "-start_number", "1", "-i", PREFIX + "/frames/%04d.png",
           "-ss", f"{START:.3f}", "-t", f"{total:.3f}", "-i", AUDIO, "-map", "0:v", "-map", "1:a",
           "-vf", f"fade=t=in:st=0:d=0.4,tpad=stop_mode=add:stop_duration={TAIL}:color=black,format=yuv420p",
           "-af", f"afade=t=in:st=0:d=0.4,afade=t=out:st={END:.3f}:d={TAIL}",
           "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-c:a", "aac", "-b:a", "256k",
           "-t", f"{total:.3f}", PREFIX + ".mp4"]
    subprocess.run(cmd, check=True)
    print("Video:", PREFIX + ".mp4", flush=True)
