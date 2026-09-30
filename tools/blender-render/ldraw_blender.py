"""
LDraw-Modelle in Blender laden (gemeinsam fuer render_cycles.py und die Video-Skripte)
==================================================================================
- Bibliothek: $LDRAWDIR, sonst die von Stud.io, sonst der Teile-Cache von tools/ldraw-render
- Farben aus LDConfig.ldr, Materialien fuer Kunststoff, Transparent, Chrom, Perlmutt, Gummi
- Geometrie mit BFC-Windungsrichtung, je Teil entdoppelt, je Farbe ein Objekt
- build_parts(..., attrs=...) haengt pro Teil Werte als Punkt-Attribut an (z. B. Einbauzeit fuer Animationen)
Koordinaten: LDraw (y nach unten) -> Blender (z nach oben), 1 LDU = 0,4 mm.
"""
import math, os, re
from collections import defaultdict
import numpy as np
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 0.0004
TO_B = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float) * SCALE

CANDIDATES = [os.environ.get("LDRAWDIR", ""), r"D:\Programme\Studio 2.0\ldraw", r"C:\Program Files\Studio 2.0\ldraw",
              os.path.expanduser(r"~\AppData\Local\Stud.io\ldraw"), r"C:\LDraw", os.path.expanduser("~/ldraw")]
LIB = next((c for c in CANDIDATES if c and os.path.isfile(os.path.join(c, "LDConfig.ldr"))), None)
CACHE = os.path.join(HERE, "..", "ldraw-render", "cache")
DIRS = [os.path.join(LIB, d) for d in ("parts", "p", os.path.join("UnOfficial", "parts"), os.path.join("UnOfficial", "p"))] \
    if LIB else []


def to_blender(p):
    """LDraw-Punkt(e) -> Blender-Koordinaten"""
    return np.asarray(p, float) @ TO_B.T


def find_file(name):
    rel = name.replace("\\", "/").lower()
    for d in DIRS:
        f = os.path.join(d, rel)
        if os.path.isfile(f): return f
    for pre in ("parts/", "p/", ""):                          # Cache von tools/ldraw-render (parts__x.dat)
        f = os.path.join(CACHE, (pre + rel).replace("/", "__"))
        if os.path.isfile(f): return f
    return None


# ---------------- Farben ----------------
def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


COLORS = {}
EXTRA = {"353": ("FF6D77", 255, "")}          # Vibrant Coral fehlt im LDConfig von Stud.io
_cfg = os.path.join(LIB, "LDConfig.ldr") if LIB else os.path.join(CACHE, "LDConfig.ldr")
if os.path.isfile(_cfg):
    for _l in open(_cfg, encoding="utf-8", errors="replace"):
        m = re.match(r"0\s+!COLOUR\s+(\S+)\s+CODE\s+(\d+)\s+VALUE\s+#([0-9A-Fa-f]{6})(.*)", _l.strip())
        if not m: continue
        rest = m.group(4).upper()
        a = re.search(r"ALPHA\s+(\d+)", rest)
        kind = next((w for w in ("CHROME", "PEARLESCENT", "METAL", "RUBBER", "GLITTER", "SPECKLE") if w in rest), "")
        COLORS[m.group(2)] = dict(rgb=m.group(3), alpha=int(a.group(1)) if a else 255, kind=kind, name=m.group(1))
for _c, (_v, _a, _k) in EXTRA.items():
    COLORS.setdefault(_c, dict(rgb=_v, alpha=_a, kind=_k, name=_c))


def color_info(code):
    if code.lower().startswith("0x2"): return dict(rgb=code[3:9], alpha=255, kind="", name=code)
    if code not in COLORS:
        print("  Farbe fehlt:", code, "-> grau", flush=True)
        COLORS[code] = dict(rgb="808080", alpha=255, kind="", name=code)
    return COLORS[code]


MATS = {}


def material(code):
    if code in MATS: return MATS[code]
    ci = color_info(code)
    rgb = [srgb2lin(int(ci["rgb"][i:i + 2], 16) / 255) for i in (0, 2, 4)]
    mat = bpy.data.materials.new(f"ldraw_{code}_{ci['name']}")
    if mat.node_tree is None: mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    def inp(*names):
        return next((bsdf.inputs[n] for n in names if n in bsdf.inputs), None)
    inp("Base Color").default_value = (*rgb, 1)
    inp("Roughness").default_value = 0.22
    if inp("Coat Weight"): inp("Coat Weight").default_value = 0.15
    kind = ci["kind"]
    if ci["alpha"] < 255:
        inp("Transmission Weight", "Transmission").default_value = 1.0
        inp("Roughness").default_value = 0.04
        inp("IOR").default_value = 1.5
        if hasattr(mat, "use_raytrace_refraction"): mat.use_raytrace_refraction = True     # EEVEE: echte Durchsicht
        if hasattr(mat, "surface_render_method"): mat.surface_render_method = "BLENDED"
    elif kind == "CHROME": inp("Metallic").default_value = 1.0; inp("Roughness").default_value = 0.08
    elif kind in ("PEARLESCENT", "METAL"): inp("Metallic").default_value = 0.7; inp("Roughness").default_value = 0.3
    elif kind == "RUBBER": inp("Roughness").default_value = 0.6
    MATS[code] = mat
    return mat


# ---------------- LDraw lesen (mit BFC-Windungsrichtung) ----------------
MPD = {}             # Unterdateien im MPD
FLAT = {}            # Dateiname -> {Farbe: Dreiecke (n,3,3)} lokal, Windung CCW
PROTO = {}           # Teil -> {Farbe: (Punkte, Dreiecke)} entdoppelt
MISSING = set()


def read_lines(path):
    return open(path, encoding="utf-8", errors="replace").read().splitlines()


def load_mpd(path):
    """liest ein MPD/LDR und gibt den Namen des Hauptmodells zurueck"""
    lines = read_lines(path)
    main, cur = None, None
    for l in lines:
        s = l.strip()
        if s.startswith("0 FILE "):
            cur = s[7:].strip().lower(); MPD[cur] = []
            main = main or cur
        elif s.startswith("0 NOFILE"): cur = None
        elif cur is not None: MPD[cur].append(l)
    if main is None:
        main = os.path.basename(path).lower(); MPD[main] = lines
    return main


def _lines_of(key):
    if key in MPD: return MPD[key]
    f = find_file(key)
    if f is None:
        if key not in MISSING: print("  Teil fehlt:", key, flush=True)
        MISSING.add(key); return None
    return read_lines(f)


def _ref(t):
    v = [float(x) for x in t[2:14]]
    return t[1], np.array(v[3:12]).reshape(3, 3), np.array(v[0:3]), " ".join(t[14:]).replace("\\", "/").lower()


def flatten(name):
    key = name.replace("\\", "/").lower()
    if key in FLAT: return FLAT[key]
    lines = _lines_of(key)
    out = defaultdict(list)
    cw, invnext = False, False
    for l in lines or []:
        t = l.split()
        if not t: continue
        if t[0] == "0":
            if len(t) >= 2 and t[1] == "BFC":
                w = " ".join(t[2:]).upper()
                if "INVERTNEXT" in w: invnext = True
                if w.endswith("CW") and not w.endswith("CCW"): cw = True
                elif w.endswith("CCW"): cw = False
            continue
        if t[0] == "1" and len(t) >= 15:
            col, M, pos, sub = _ref(t)
            flip = invnext ^ (np.linalg.det(M) < 0)
            for sc, tris in flatten(sub).items():
                tt = tris @ M.T + pos
                if flip: tt = tt[:, [0, 2, 1]]
                out[col if sc == "16" else sc].append(tt)
            invnext = False
        elif t[0] in ("3", "4"):
            n = int(t[0])
            p = np.array([float(x) for x in t[2:2 + 3 * n]]).reshape(n, 3)
            if cw: p = p[::-1]
            out[t[1]].append(p[None, [0, 1, 2]] if n == 3 else p[[[0, 1, 2], [0, 2, 3]]])
            invnext = False
    FLAT[key] = {c: np.concatenate(v) for c, v in out.items()}
    return FLAT[key]


def proto(name):
    """Teil-Geometrie je Farbe, Punkte entdoppelt (fuer glatte Normalen)"""
    if name in PROTO: return PROTO[name]
    res = {}
    for c, tris in flatten(name).items():
        if c == "24": continue
        v = tris.reshape(-1, 3)
        q = np.round(v * 100).astype(np.int64)
        _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
        f = inv.reshape(-1, 3)
        f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
        res[c] = (v[first], f.astype(np.int64))
    PROTO[name] = res
    return res


def iter_parts(name, color="16", M=np.eye(3), pos=np.zeros(3), inv=False):
    """alle Bibliotheksteile eines Modells (Untermodelle aufgeloest): (Teil, Farbe, Matrix, Position, gespiegelt)"""
    key = name.replace("\\", "/").lower()
    invnext = False
    for l in MPD.get(key, []):
        t = l.split()
        if not t: continue
        if t[0] == "0":
            if "INVERTNEXT" in l.upper(): invnext = True
            continue
        if t[0] != "1" or len(t) < 15: continue
        c, m, p, sub = _ref(t)
        c = color if c == "16" else c
        MM, PP = M @ m, M @ p + pos
        fl = inv ^ invnext ^ (np.linalg.det(m) < 0)
        if sub in MPD: yield from iter_parts(sub, c, MM, PP, fl)
        else: yield sub, c, MM, PP, fl
        invnext = False


def make_mesh(name, verts, faces, code, attrs=None, collection=None):
    """Blender-Objekt aus LDraw-Punkten (n,3) und Dreiecken (m,3)"""
    v = to_blender(verts).astype(np.float32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v)); me.vertices.foreach_set("co", v.ravel())
    me.loops.add(faces.size); me.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
    me.polygons.add(len(faces)); me.polygons.foreach_set("loop_start", np.arange(0, faces.size, 3, dtype=np.int32))
    me.update()
    try:
        me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(35))
    except AttributeError:
        pass
    for an, av in (attrs or {}).items():
        at = me.attributes.new(an, "FLOAT", "POINT"); at.data.foreach_set("value", np.asarray(av, np.float32))
    me.materials.append(material(code))
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def build_parts(main, attrs=None, collection=None):
    """Modell als je ein Objekt pro Farbe aufbauen.
    attrs: {Name: Werte je Teil in der Reihenfolge von iter_parts(main)} -> Punkt-Attribute.
    Rueckgabe: (Objekte, Teileliste, bbox_min, bbox_max) in Blender-Koordinaten"""
    parts = list(iter_parts(main))
    buck = defaultdict(lambda: ([], [], []))
    off = defaultdict(int)
    for pid, (name, col, M, pos, inv) in enumerate(parts):
        for sc, (v, f) in proto(name).items():
            c = col if sc == "16" else sc
            vs, fs, ps = buck[c]
            vs.append(v @ M.T + pos); fs.append((f[:, [0, 2, 1]] if inv else f) + off[c]); ps.append(np.full(len(v), pid))
            off[c] += len(v)
    obs, lo, hi = [], np.full(3, np.inf), np.full(3, -np.inf)
    for c, (vs, fs, ps) in sorted(buck.items()):
        V, F, P = np.concatenate(vs), np.concatenate(fs), np.concatenate(ps)
        a = {k: np.asarray(val, np.float32)[P] for k, val in (attrs or {}).items()}
        ob = make_mesh(f"farbe_{c}", V, F, c, a, collection)
        b = to_blender(V); lo = np.minimum(lo, b.min(0)); hi = np.maximum(hi, b.max(0))
        obs.append(ob)
    return obs, parts, lo, hi


def add_build_anim(obs, height, frames, power=5.0):
    """Geometry Nodes: jedes Teil erscheint zur Zeit seines Punkt-Attributs "t0" (Frame) und senkt sich in
    `frames` Frames aus `height` (m) mit Ease-out an seinen Platz"""
    ng = bpy.data.node_groups.new("Einbau", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    at = N.new("GeometryNodeInputNamedAttribute"); at.data_type = "FLOAT"; at.inputs["Name"].default_value = "t0"
    st = N.new("GeometryNodeInputSceneTime")
    def m(op, a, b=None, clamp=False):
        nd = N.new("ShaderNodeMath"); nd.operation = op; nd.use_clamp = clamp
        for s, val in ((0, a), (1, b)):
            if val is None: continue
            if isinstance(val, (int, float)): nd.inputs[s].default_value = val
            else: L.new(val, nd.inputs[s])
        return nd.outputs[0]
    fr, t0 = st.outputs["Frame"], at.outputs[0]
    u = m("DIVIDE", m("SUBTRACT", fr, t0), float(frames), clamp=True)
    fall = m("MULTIPLY", m("POWER", m("SUBTRACT", 1.0, u), power), height)
    xyz = N.new("ShaderNodeCombineXYZ"); L.new(fall, xyz.inputs["Z"])
    sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(xyz.outputs[0], sp.inputs["Offset"])
    dg = N.new("GeometryNodeDeleteGeometry"); dg.domain = "POINT"
    L.new(sp.outputs[0], dg.inputs["Geometry"]); L.new(m("LESS_THAN", fr, t0), dg.inputs["Selection"])
    L.new(dg.outputs[0], go.inputs[0])
    for ob in obs:
        ob.modifiers.new("Einbau", "NODES").node_group = ng
    return ng


def eevee_alpha_glass(alpha=0.28):
    """EEVEE: transparente Farben als Alpha-Glas mit Glanz (Refraktion wirkt dort sonst grau und opak)"""
    for code, mat in MATS.items():
        if color_info(code)["alpha"] >= 255: continue
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        for nm, val in (("Transmission Weight", 0.0), ("Alpha", alpha), ("Roughness", 0.03), ("Coat Weight", 1.0)):
            if nm in bsdf.inputs: bsdf.inputs[nm].default_value = val
        if hasattr(mat, "surface_render_method"): mat.surface_render_method = "BLENDED"
        if hasattr(mat, "use_transparency_overlap"): mat.use_transparency_overlap = True


def enable_gpu(scene, verbose=True):
    """Cycles auf der GPU rendern, falls vorhanden (OptiX, CUDA, HIP, oneAPI, Metal)"""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = dev; prefs.get_devices()
        except TypeError:
            continue
        gpus = [d for d in prefs.devices if d.type == dev]
        if gpus:
            for d in prefs.devices: d.use = d.type == dev
            scene.cycles.device = "GPU"
            if verbose: print("GPU:", dev, ", ".join(d.name for d in gpus), flush=True)
            return True
    if verbose: print("keine GPU gefunden - rendere auf der CPU", flush=True)
    return False
