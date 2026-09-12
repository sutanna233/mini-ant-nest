import numpy as np
import trimesh

m = trimesh.load("design/nest_onepiece.stl")


def pv(p, r=0.25):
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(p)
    it = trimesh.boolean.intersection([m, s])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


def pc(p1, p2, r=0.2):
    p1, p2 = np.array(p1, float), np.array(p2, float)
    v = p2 - p1
    L = np.linalg.norm(v)
    c = trimesh.creation.cylinder(radius=r, height=L, sections=24)
    c.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
    c.apply_translation((p1 + p2) / 2)
    it = trimesh.boolean.intersection([m, c])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


cases = [
    ("water cavity (28,20,10)", pv((28, 20, 10)), "void"),
    ("tank floor (28,20,1)", pv((28, 20, 1)), "solid"),
    ("fill hole open (28,1.5,12)", pv((28, 1.5, 12)), "void"),
    ("wall beside fill (10,1.5,12)", pv((10, 1.5, 12)), "solid"),
    ("grill hole (5.5,5.5,18)", pv((5.5, 5.5, 18)), "void"),
    ("plate solid (28,8,18)", pv((28, 8, 18)), "solid"),
    ("plate under tube (28,31,18)", pv((28, 31, 18)), "solid"),
    ("support post (13,13,10)", pv((13, 13, 10)), "solid"),
    ("soil pocket (10,25,30)", pv((10, 25, 30)), "void"),
    ("soil wall (1,25,30)", pv((1, 25, 30)), "solid"),
    ("arena interior (28,31,40)", pv((28, 31, 40)), "void"),
    ("arena wall front (28,12,40)", pv((28, 12, 40)), "solid"),
    ("arena wall back (28,50,40)", pv((28, 50, 40)), "solid"),
    ("door open (28,12,25)", pv((28, 12, 25)), "void"),
]
for name, v, exp in cases:
    ok = "OK " if ((v == 0) == (exp == "void")) else "!! "
    print(f"{ok}{name:32s} vol={v:6.3f} expect={exp}")

print("arena<->soil door path:", round(pc((28, 20, 24), (28, 14, 24)), 3), "(0 = connected)")
print("bounds:", np.round(m.bounds, 1).tolist(), "watertight:", m.is_watertight)
