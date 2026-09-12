import numpy as np
import trimesh

m = trimesh.load("design/nest_body.stl")
lid = trimesh.load("design/nest_lid.stl")


def pv(o, p, r=0.25):
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(p)
    it = trimesh.boolean.intersection([o, s])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


cases = [
    ("outworld cavity (19,28,10)", (19, 28, 10), "void"),
    ("outworld floor  (19,28,1)", (19, 28, 1), "solid"),
    ("dry plaster cavity (68,41,10)", (68, 41, 10), "void"),
    ("wet plaster cavity (68,15,10)", (68, 15, 10), "void"),
    ("dry/wet divider (68,29.5,10)", (68, 29.5, 10), "solid"),
    ("divider above plaster (68,29.5,26)", (68, 29.5, 26), "solid"),
    ("outer wall (0.5,28,15)", (0.5, 28, 15), "solid"),
    ("door->dry open (36.5,43,22)", (36.5, 43, 22), "void"),
    ("door->wet open (36.5,13,22)", (36.5, 13, 22), "void"),
    ("wall between doors (36.5,28,22)", (36.5, 28, 22), "solid"),
    ("lid vent hole (7,28,1)", (7, 28, 1), "void"),
    ("lid solid (60,28,1)", (60, 28, 1), "solid"),
]
for name, p, exp in cases:
    o = lid if name.startswith("lid") else m
    v = pv(o, p)
    ok = "OK " if ((v == 0) == (exp == "void")) else "!! "
    print(f"{ok}{name:34s} vol={v:6.3f} expect={exp}")
print("body watertight", m.is_watertight, "| lid watertight", lid.is_watertight)
