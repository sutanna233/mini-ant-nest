import numpy as np
import trimesh

m = trimesh.load("design/nest_body.stl")


def pv(p, r=0.22):
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(p)
    it = trimesh.boolean.intersection([m, s])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


cases = [
    ("activity floor   (20,18,5)", (20, 18, 5), "solid"),
    ("activity cavity  (20,18,20)", (20, 18, 20), "void"),
    ("well cavity      (50,18,20)", (50, 18, 20), "void"),
    ("well floor       (50,18,1)", (50, 18, 1), "solid"),
    ("gypsum pocket    (30,65,5)", (30, 65, 5), "void"),
    ("nest chamber     (30,65,20)", (30, 65, 20), "void"),
    ("partition wall1  (21.5,65,20)", (21.5, 65, 20), "solid"),
    ("gypsum notch     (21.5,60,5)", (21.5, 60, 5), "void"),
    ("ant door wall1   (21.5,77,15)", (21.5, 77, 15), "void"),
    ("ant door wall2   (38.5,57,15)", (38.5, 57, 15), "void"),
    ("wall2 solid      (38.5,70,15)", (38.5, 70, 15), "solid"),
    ("well->nest chnl  (49,39,5)", (49, 39, 5), "void"),
    ("divider wall     (30,39,5)", (30, 39, 5), "solid"),
    ("door act->nest   (17,39,15)", (17, 39, 15), "void"),
    ("magnet pocket    (6,6,35.5)", (6, 6, 35.5), "void"),
    ("below pocket     (6,6,32)", (6, 6, 32), "solid"),
    ("corner pad       (6,11,20)", (6, 11, 20), "solid"),
    ("outer wall       (1.5,50,20)", (1.5, 50, 20), "solid"),
]
bad = 0
for n, p, e in cases:
    v = pv(p)
    ok = (v == 0) == (e == "void")
    bad += 0 if ok else 1
    print(f"{'OK ' if ok else '!! '}{n:30s} vol={v:6.3f} {e}")
print("watertight", m.is_watertight, "| failures", bad)
