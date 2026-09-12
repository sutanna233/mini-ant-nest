import numpy as np
import trimesh
import trimesh.transformations as tf

m = trimesh.load("design/nest_base.stl")


def probe_point(p, r=0.25):
    """Return material volume inside a tiny sphere at point p."""
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(p)
    inter = trimesh.boolean.intersection([m, s])
    return 0.0 if inter is None or inter.is_empty else abs(inter.volume)


def probe_cylinder(p1, p2, r=0.2):
    """Material volume inside a thin cylinder from p1 to p2."""
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    v = p2 - p1
    length = np.linalg.norm(v)
    c = trimesh.creation.cylinder(radius=r, height=length, sections=32)
    T = trimesh.geometry.align_vectors([0, 0, 1], v / length)
    c.apply_transform(T)
    c.apply_translation((p1 + p2) / 2.0)
    inter = trimesh.boolean.intersection([m, c])
    return 0.0 if inter is None or inter.is_empty else abs(inter.volume)


D = np.array([57.0, 32.0])
Wl = np.array([67.0, 23.0])
d = (Wl - D) / np.linalg.norm(Wl - D)
n = np.array([-d[1], d[0]])

print("== point probes (material volume; 0 = void) ==")
pts = {
    "well interior z10": (67, 23, 10),
    "chamber D z10": (57, 32, 10),
    "outworld z8": (17, 23, 8),
    "well floor z1": (67, 23, 1),
    "base floor z1": (50, 23, 1),
}
for k, p in pts.items():
    print(f"  {probe_point(p):7.3f} mm^3  {k}")

print("== slit connectivity (cylinder along D->well @z10, r=0.2) ==")
for off in (-2.0, 0.0, 2.0, 3.5):
    q1 = np.append(D + n * off, 10.0)
    q2 = np.append(Wl + n * off, 10.0)
    vol = probe_cylinder(q1, q2)
    tag = "OPEN (good)" if vol < 1e-6 else "BLOCKED"
    print(f"  offset {off:+.1f}: vol={vol:7.4f}  {tag}")

print("== slit ends above z=6 (check at z=3, expect BLOCKED) ==")
q1 = np.append(D, 3.0)
q2 = np.append(Wl, 3.0)
print(f"  z=3 vol={probe_cylinder(q1, q2):7.4f} (should be >0)")
