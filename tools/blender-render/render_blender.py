"""
Fotorealistischer Blender-Render (Cycles) fuer LDraw-Modelle (.mpd/.ldr) – ohne Add-on.

Laedt die Teile-Geometrie aus der LDraw-Bibliothek (ueber den lokalen Render-Server von tools/ldraw-render, der
fehlende Dateien vom GitHub-Mirror holt und cached), baut pro Teil ein Mesh (geteilte Mesh-Daten fuer alle Kopien),
setzt ABS-Kunststoff-Materialien nach LDConfig und rendert mit Cycles + Denoiser.

Aufruf (Python mit bpy, z. B. `pip install bpy==5.0.1` in einer Python-3.11-Umgebung):
  python render_blender.py modell.mpd ausgabe/praefix --ansicht wand|haengend|oben [--views views.json]
      [--samples 96] [--breite 1600] [--hoehe 1600] [--server http://localhost:8765]

Ansichten (--views JSON): {"name": {"cam": [x,y,z], "ziel": [x,y,z], "brennweite": 50, "blende": 0 (aus) | f-Zahl}}
Koordinaten in Metern im Blender-Raum nach der Ansicht-Transformation.
 - "wand":  Relief-Wandbild – Noppen zeigen nach +Y (zum Betrachter), Bild oben = +Z, Mitte im Ursprung.
 - "oben":  Modell wie gebaut (LDraw -Y = Blender +Z), z. B. fuer Buehnen.
1 LDU = 0,4 mm.
"""
import argparse, json, math, os, re, sys, urllib.request, urllib.error
from collections import defaultdict
import bpy
from mathutils import Matrix, Vector

S = 0.0004                                                        # Meter pro LDU


# ---------------- LDraw-Dateien ----------------
class Lib:
    def __init__(self, server, cache):
        self.server, self.cache, self.mem = server.rstrip("/"), cache, {}

    def _get(self, rel):
        rel = rel.lower()
        cf = os.path.join(self.cache, rel.replace("/", "__"))
        if os.path.exists(cf): return open(cf, encoding="utf8", errors="replace").read()
        if os.path.exists(cf + ".404"): return None
        try:
            return urllib.request.urlopen(f"{self.server}/ldraw/{rel}", timeout=60).read().decode("utf8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            raise

    def find(self, name):
        name = name.replace("\\", "/").lower()
        if name in self.mem: return self.mem[name]
        for pre in ("parts/", "p/", "parts/s/", "p/48/", "models/", ""):
            t = self._get(pre + name)
            if t is not None:
                self.mem[name] = t; return t
        print("FEHLT", name); self.mem[name] = ""; return ""


def load_colors(text):
    cols = {}
    for L in text.splitlines():
        if "!COLOUR" not in L: continue
        m = re.search(r"CODE\s+(\d+)\s+VALUE\s+#([0-9A-Fa-f]{6})", L)
        if not m: continue
        code = int(m.group(1)); h = m.group(2)
        rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        alpha = re.search(r"ALPHA\s+(\d+)", L)
        kind = "chrome" if "CHROME" in L else "pearl" if "PEARLESCENT" in L else "metal" if "METAL" in L else \
               "rubber" if "RUBBER" in L else "trans" if alpha else "solid"
        cols[code] = (rgb, kind)
    return cols


# ---------------- Geometrie flach klopfen ----------------
def mat_from(v):
    a, b, c, d, e, f, g, h, i = v
    return ((a, b, c), (d, e, f), (g, h, i))


def mmul(A, B): return tuple(tuple(sum(A[r][k] * B[k][c] for k in range(3)) for c in range(3)) for r in range(3))
def mvec(A, v): return tuple(sum(A[r][k] * v[k] for k in range(3)) for r in range(3))


class Flattener:
    """Loest Unterdateien auf; liefert Dreiecke [(p0,p1,p2), farbcode] mit 16 = Farbe des Teils"""
    def __init__(self, lib):
        self.lib, self.memo = lib, {}

    def flat(self, name):
        key = name.replace("\\", "/").lower()
        if key in self.memo: return self.memo[key]
        tris = []
        for L in self.lib.find(key).splitlines():
            p = L.split()
            if not p: continue
            if p[0] == "1" and len(p) >= 15:
                col = int(p[1]); x, y, z = map(float, p[2:5]); M = mat_from(list(map(float, p[5:14])))
                sub = " ".join(p[14:])
                for (a, b, c), cc in self.flat(sub):
                    q = [tuple(t + s for t, s in zip(mvec(M, v), (x, y, z))) for v in (a, b, c)]
                    tris.append((tuple(q), col if cc == 16 else cc))
            elif p[0] == "3" and len(p) >= 11:
                v = list(map(float, p[2:11])); col = int(p[1])
                tris.append(((tuple(v[0:3]), tuple(v[3:6]), tuple(v[6:9])), col))
            elif p[0] == "4" and len(p) >= 14:
                v = list(map(float, p[2:14])); col = int(p[1])
                a, b, c, d = tuple(v[0:3]), tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12])
                tris.append(((a, b, c), col)); tris.append(((a, c, d), col))
        self.memo[key] = tris
        return tris


# ---------------- Blender-Aufbau ----------------
def material(code, cols, cache):
    if code in cache: return cache[code]
    rgb, kind = cols.get(code, ((0.8, 0.1, 0.8), "solid"))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    m = bpy.data.materials.new(f"LDraw_{code}")
    if hasattr(m, 'use_nodes') and not m.node_tree: m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    def s(k, v):
        if k in b.inputs: b.inputs[k].default_value = v
    s("Base Color", (*lin, 1.0)); s("Roughness", 0.22); s("IOR", 1.54); s("Specular IOR Level", 0.5)
    s("Coat Weight", 0.15); s("Coat Roughness", 0.1)
    if kind == "trans":
        s("Transmission Weight", 1.0); s("Roughness", 0.03); s("Coat Weight", 0.0)
    elif kind in ("chrome", "metal"):
        s("Metallic", 1.0); s("Roughness", 0.15)
    elif kind == "pearl":
        s("Metallic", 0.75); s("Roughness", 0.28)
    elif kind == "rubber":
        s("Roughness", 0.7); s("Coat Weight", 0.0)
    m.diffuse_color = (*lin, 1.0)
    cache[code] = m
    return m


def build_mesh(name, tris, cols, matcache):
    """Mesh mit verschmolzenen Punkten; Slot 0 = Teilfarbe (16), weitere Slots feste Farben"""
    codes = sorted({c for _, c in tris if c != 16})
    slot = {16: 0, **{c: i + 1 for i, c in enumerate(codes)}}
    vidx, verts, faces, fmat = {}, [], [], []
    for tri, c in tris:
        if c == 24: continue
        f = []
        for v in tri:
            k = (round(v[0], 2), round(v[1], 2), round(v[2], 2))
            if k not in vidx: vidx[k] = len(verts); verts.append(k)
            f.append(vidx[k])
        if len(set(f)) == 3: faces.append(f); fmat.append(slot[c])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(None)
    for c in codes: me.materials.append(material(c, cols, matcache))
    me.polygons.foreach_set("material_index", fmat)
    me.shade_smooth()
    if hasattr(me, "set_sharp_from_angle"): me.set_sharp_from_angle(angle=math.radians(35))
    me.update()
    return me


def read_model(path, lib):
    """Alle Teile-Referenzen des Hauptmodells (MPD-Untermodelle aufgeloest): (name, farbe, Matrix4 in LDU)"""
    text = open(path, encoding="utf8").read()
    files, cur = {}, None
    for L in text.splitlines():
        p = L.split()
        if len(p) >= 3 and p[0] == "0" and p[1] == "FILE":
            cur = " ".join(p[2:]).lower(); files[cur] = []; continue
        if len(p) >= 2 and p[0] == "0" and p[1] == "NOFILE": cur = None; continue
        files.setdefault(cur, []).append(L)
    main = next((k for k in files if k), None)
    out = []

    def walk(fname, T, col_parent):
        for L in files.get(fname, []):
            p = L.split()
            if not p or p[0] != "1" or len(p) < 15: continue
            col = int(p[1]); col = col_parent if col == 16 else col
            x, y, z = map(float, p[2:5]); r = list(map(float, p[5:14]))
            M = Matrix(((r[0], r[1], r[2], x), (r[3], r[4], r[5], y), (r[6], r[7], r[8], z), (0, 0, 0, 1)))
            sub = " ".join(p[14:]).lower()
            if sub in files: walk(sub, T @ M, col)
            else: out.append((sub, col, T @ M))
    walk(main if main else None, Matrix.Identity(4), 16)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("modell"); ap.add_argument("ausgabe")
    ap.add_argument("--ansicht", default="wand", choices=("wand", "oben"))
    ap.add_argument("--views", default="")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--breite", type=int, default=1600); ap.add_argument("--hoehe", type=int, default=1600)
    ap.add_argument("--server", default="http://localhost:8765")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ldraw-render", "cache"))
    ap.add_argument("--wand", default="0.93,0.92,0.90", help="Wandfarbe (sRGB 0..1) bei --ansicht wand")
    ap.add_argument("--belichtung", type=float, default=-0.3, help="Belichtungskorrektur in Blendenstufen")
    ap.add_argument("--video", default="", help="JSON mit Einstellungen (Kamerafahrten) -> Einzelbilder + MP4")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--audio", default="", help="Tonspur (MP3 o. ae.) unter das Video legen")
    ap.add_argument("--ffmpeg", default="", help="Pfad zu ffmpeg (Standard: imageio-ffmpeg oder PATH)")
    a = ap.parse_args(argv)

    lib = Lib(a.server, os.path.abspath(a.cache))
    cols = load_colors(lib._get("ldconfig.ldr") or lib._get("LDConfig.ldr") or "")
    refs = read_model(a.modell, lib)
    print("Teile im Modell:", len(refs))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    coll = sc.collection
    fl = Flattener(lib); matcache, meshes = {}, {}
    # LDraw -> Blender: (x, y, z) -> (x, z, -y) (Bauansicht) bzw. (x, -y, -z) (Wandbild: Noppen nach +Y)
    A = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1))) if a.ansicht == "oben" else \
        Matrix(((1, 0, 0, 0), (0, -1, 0, 0), (0, 0, -1, 0), (0, 0, 0, 1)))
    C = A @ Matrix.Scale(S, 4)
    for n, (name, col, M) in enumerate(refs):
        if name not in meshes:
            meshes[name] = build_mesh(name, fl.flat(name), cols, matcache)
        ob = bpy.data.objects.new(f"{name}_{n}", meshes[name])
        coll.objects.link(ob)
        ob.matrix_world = C @ M
        if ob.material_slots:
            ob.material_slots[0].link = "OBJECT"
            ob.material_slots[0].material = material(col, cols, matcache)
        if n % 5000 == 0: print("  Objekte", n)
    print("Teilesorten:", len(meshes), "| Materialien:", len(matcache))

    # Groesse fuer Kamera/Licht
    pts = [ob.matrix_world @ Vector(c) for ob in list(coll.objects)[:: max(1, len(coll.objects) // 4000)] for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr, size = (lo + hi) / 2, max(hi - lo)
    print("Ausdehnung (m):", tuple(round(v, 3) for v in (hi - lo)))

    # Welt und Licht
    world = bpy.data.worlds.new("Studio"); sc.world = world
    if not world.node_tree: world.use_nodes = True
    bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.05, 0.05, 0.055, 1); bg.inputs[1].default_value = 0.6

    def area(name, loc, size_, energy, color=(1, 1, 1)):
        L = bpy.data.lights.new(name, "AREA"); L.shape = "DISK"; L.size = size_; L.energy = energy; L.color = color
        o = bpy.data.objects.new(name, L); coll.objects.link(o); o.location = loc
        d = ctr - Vector(loc); o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return o
    if a.ansicht == "wand":
        wall = bpy.data.meshes.new("Wand"); r = size * 4
        wall.from_pydata([(-r, lo.y - 0.002, -r), (r, lo.y - 0.002, -r), (r, lo.y - 0.002, r), (-r, lo.y - 0.002, r)], [], [(0, 1, 2, 3)])
        wo = bpy.data.objects.new("Wand", wall); coll.objects.link(wo)
        wm = bpy.data.materials.new("Wandfarbe")
        if not wm.node_tree: wm.use_nodes = True
        wc = [float(v) for v in a.wand.split(",")]
        wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*[c ** 2.2 for c in wc], 1)
        wm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
        wall.materials.append(wm)
        # Galerie-Licht: Hauptlicht links oben (wie im Gemaelde), weiche Aufhellung rechts, Streiflicht von oben
        area("Key", (ctr.x - size * 0.9, ctr.y + size * 1.3, ctr.z + size * 1.1), size * 0.9, 110 * size ** 2)
        area("Fill", (ctr.x + size * 1.4, ctr.y + size * 1.2, ctr.z + size * 0.2), size * 1.4, 35 * size ** 2, (0.9, 0.95, 1.0))
        area("Streif", (ctr.x, ctr.y + size * 0.25, ctr.z + size * 1.2), size * 1.2, 30 * size ** 2, (1.0, 0.95, 0.88))
    else:
        area("Key", (ctr.x - size, ctr.y - size, ctr.z + size * 1.4), size, 120 * size ** 2)
        area("Fill", (ctr.x + size * 1.3, ctr.y - size * 0.4, ctr.z + size * 0.6), size * 1.5, 40 * size ** 2)

    # Render-Einstellungen
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"; sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = a.breite, a.hoehe, 100
    sc.render.image_settings.file_format = "PNG"
    for vt in ("Khronos PBR Neutral", "AgX", "Standard"):
        try: sc.view_settings.view_transform = vt; print("Farbmanagement:", vt); break
        except TypeError: continue

    sc.view_settings.exposure = a.belichtung
    if a.video:
        return render_video(a, sc, coll, ctr)
    views = json.load(open(a.views)) if a.views else {
        "front": {"cam": [ctr.x, ctr.y + size * 1.55, ctr.z], "ziel": list(ctr), "brennweite": 50}}
    cam_data = bpy.data.cameras.new("Kamera"); cam = bpy.data.objects.new("Kamera", cam_data); coll.objects.link(cam)
    sc.camera = cam
    os.makedirs(os.path.dirname(os.path.abspath(a.ausgabe)), exist_ok=True)
    for vname, v in views.items():
        cam.location = Vector(v["cam"])
        tgt = Vector(v.get("ziel", list(ctr)))
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v.get("brennweite", 50)
        cam_data.dof.use_dof = bool(v.get("blende"))
        if cam_data.dof.use_dof:
            cam_data.dof.focus_distance = (tgt - cam.location).length; cam_data.dof.aperture_fstop = v["blende"]
        sc.render.filepath = os.path.abspath(f"{a.ausgabe}_{vname}.png")
        print("Render", vname, "->", sc.render.filepath, flush=True)
        bpy.ops.render.render(write_still=True)
    print("fertig")


def ease(t):
    return t * t * (3 - 2 * t)                                     # Smoothstep: sanft an- und abfahren


def lerp(p, q, t): return [u + (v - u) * t for u, v in zip(p, q)]


def render_video(a, sc, coll, ctr):
    """Einstellungen aus JSON: [{"dauer": s, "von": {cam, ziel, brennweite, blende}, "bis": {...}}, ...]
    Harte Schnitte zwischen den Einstellungen, jede Fahrt mit Smoothstep. Kamera zielt per Constraint auf ein Empty,
    das zugleich der Schaerfepunkt ist (Schaerfeverlagerung durch Bewegen des Ziels)."""
    shots = json.load(open(a.video))
    fps = a.fps
    sc.render.fps = fps
    sc.render.use_persistent_data = True                         # BVH bleibt zwischen den Bildern erhalten
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
    cam_data = bpy.data.cameras.new("Kamera"); cam = bpy.data.objects.new("Kamera", cam_data); coll.objects.link(cam)
    sc.camera = cam
    tgt = bpy.data.objects.new("Ziel", None); coll.objects.link(tgt)
    con = cam.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    cam_data.dof.use_dof = True; cam_data.dof.focus_object = tgt
    frame = 1
    for sh in shots:
        n = max(2, round(sh["dauer"] * fps))
        v0, v1 = sh["von"], sh.get("bis", sh["von"])
        for j in range(n):
            t = ease(j / (n - 1))
            cam.location = lerp(v0["cam"], v1["cam"], t); cam.keyframe_insert("location", frame=frame)
            tgt.location = lerp(v0.get("ziel", list(ctr)), v1.get("ziel", v0.get("ziel", list(ctr))), t)
            tgt.keyframe_insert("location", frame=frame)
            cam_data.lens = v0.get("brennweite", 50) + (v1.get("brennweite", v0.get("brennweite", 50)) - v0.get("brennweite", 50)) * t
            cam_data.keyframe_insert("lens", frame=frame)
            b0, b1 = v0.get("blende", 16), v1.get("blende", v0.get("blende", 16))
            cam_data.dof.aperture_fstop = b0 + (b1 - b0) * t
            cam_data.dof.keyframe_insert("aperture_fstop", frame=frame)
            frame += 1
    for ad in (cam.animation_data, tgt.animation_data, cam_data.animation_data):
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
    sc.frame_start, sc.frame_end = 1, frame - 1
    out = os.path.abspath(a.ausgabe)
    fdir = out + "_frames"; os.makedirs(fdir, exist_ok=True)
    sc.render.filepath = os.path.join(fdir, "f_")
    sc.render.use_overwrite = False                               # abgebrochene Laeufe setzen fort
    sc.render.use_placeholder = True
    print(f"Video: {frame - 1} Bilder, {(frame - 1) / fps:.1f} s", flush=True)
    bpy.ops.render.render(animation=True)
    assemble(a, fdir, out + ".mp4", frame - 1)


def assemble(a, fdir, mp4, nframes):
    import subprocess
    ff = a.ffmpeg
    if not ff:
        try:
            import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            ff = "ffmpeg"
    dur = nframes / a.fps
    cmd = [ff, "-y", "-framerate", str(a.fps), "-i", os.path.join(fdir, "f_%04d.png")]
    if a.audio: cmd += ["-i", a.audio]
    cmd += ["-vf", f"fade=t=in:st=0:d=0.8,fade=t=out:st={dur - 1.0:.2f}:d=1.0", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-movflags", "+faststart"]
    if a.audio: cmd += ["-af", f"afade=t=in:st=0:d=1.0,afade=t=out:st={dur - 2.0:.2f}:d=2.0", "-c:a", "aac", "-b:a", "192k",
                        "-t", f"{dur:.2f}"]
    cmd += [mp4]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    print("Video fertig:", mp4)


if __name__ == "__main__":
    main()
