import numpy as np
import trimesh

P = {n: trimesh.load(f"design/{n}.stl") for n in
     ("water_tank", "slider", "nest_tray", "arena", "arena_lid")}


def pv(m, p, r=0.25):
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(p)
    it = trimesh.boolean.intersection([m, s])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


def run(title, cases):
    print(f"== {title} ==")
    for name, (m, p), exp in cases:
        v = pv(m, p)
        ok = "OK " if ((v == 0) == (exp == "void")) else "!! "
        print(f"  {ok} {name:34s} vol={v:6.3f}  expect={exp}")


run("water tank", [
    ("cavity (28,28,10) void", (P["water_tank"], (28, 28, 10)), "void"),
    ("floor  (28,28,1) solid", (P["water_tank"], (28, 28, 1)), "solid"),
    ("wall   (1,28,10) solid", (P["water_tank"], (1, 28, 10)), "solid"),
    ("fill mouth open (28,1.5,12)", (P["water_tank"], (28, 1.5, 12)), "void"),
    ("wall btwn mouth/rail (12,1.5,12)", (P["water_tank"], (12, 1.5, 12)), "solid"),
])

run("nest tray", [
    ("soil pocket (28,28,10) void", (P["nest_tray"], (28, 28, 10)), "void"),
    ("top opening 34mm (28,28,19) void", (P["nest_tray"], (28, 28, 19)), "void"),
    ("ledge ring x=9 (9,28,19) solid", (P["nest_tray"], (9, 28, 19)), "solid"),
    ("floor solid (28,28,2)", (P["nest_tray"], (28, 28, 2)), "solid"),
    ("grill hole (5.5,5.5,2) void", (P["nest_tray"], (5.5, 5.5, 2)), "void"),
    ("grill through lip (5.5,5.5,-2) void", (P["nest_tray"], (5.5, 5.5, -2)), "void"),
    ("underside rim (5.5,5.5,-1.5) solid", (P["nest_tray"], (5.9, 4.9, -1.5)), "solid"),
    ("underside centre open (28,28,-2) void", (P["nest_tray"], (28, 28, -2)), "void"),
])

run("arena", [
    ("tunnel (28,28,5) void", (P["arena"], (28, 28, 5)), "void"),
    ("base solid (12,28,5)", (P["arena"], (12, 28, 5)), "solid"),
    ("cylinder wall (28,9,25) solid", (P["arena"], (28, 9.2, 25)), "solid"),
    ("inside cylinder (28,28,30) void", (P["arena"], (28, 28, 30)), "void"),
    ("dike (28,8.2,11) solid", (P["arena"], (28, 36.2, 10.5)), "solid"),
])

run("lid", [
    ("centre vent (28,28,1) void", (P["arena_lid"], (28, 28, 1)), "void"),
    ("solid disc (36,28,1) solid", (P["arena_lid"], (36, 28, 1)), "solid"),
    ("plug ring (28,45,0) solid", (P["arena_lid"], (28, 44.8, 0)), "solid"),
])

print("== fit ==")
print("  nest lip z-range", P["nest_tray"].bounds[0][2], "-> tank cavity 3..18")
print("  tank cavity inner 50x50, nest lip outer 48x48  -> clearance 1mm/side")
