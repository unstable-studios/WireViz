# -*- coding: utf-8 -*-
"""Tests for junction dots under ``options.routing: orthogonal``.

The property being defended: a dot marks every point where a wire
branches off another wire of the same electrical net -- a corner sitting
on the shared trunk -- and nowhere else. Crossings never get a dot, not
even between same-net wires (they are joined at the pin, not where the
router happens to cross them), the default spline output gets no dots at
all, and each dot carries its net's ``wv-net-*`` tokens so the HTML
viewer can highlight it with the net.
"""

import re
import shutil
from types import SimpleNamespace

import pytest

from wireviz import wireviz
from wireviz.wv_ortho import _junctions

needs_dot = pytest.mark.skipif(
    shutil.which("dot") is None, reason="graphviz not installed"
)

# X1's two pins each feed two cables: a daisy chain from one pin
DAISY = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 2}
  X3: {pincount: 2}
cables:
  W1: {colors: [BK, RD]}
  W2: {colors: [BK, RD]}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X1: [1-2]
    - W2: [1-2]
    - X3: [1-2]
"""

# two independent nets whose wires cross (X1:1 -> X2:2 and X1:2 -> X2:1)
CROSSED = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 2}
cables:
  W1: {colors: [BK, RD]}
connections:
  - - X1: [1, 2]
    - W1: [1, 2]
    - X2: [2, 1]
"""


def _harness(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    return wireviz.parse(yaml_text, return_types="harness", output_name="t")


def _dots(svg):
    """[(classes, cx, cy, fill)] for every junction dot in the SVG."""
    result = []
    for m in re.finditer(r'<g class="(wv-junction[^"]*)"><circle ([^>]*)/></g>', svg):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
        result.append(
            (m.group(1).split(), float(attrs["cx"]), float(attrs["cy"]), attrs["fill"])
        )
    return result


def _wire_paths(svg):
    """{(classes, d)} for the median stripe of every wv-wire edge."""
    result = {}
    for m in re.finditer(
        r'<g id="[^"]*" class="(edge [^"]*wv(?:-|&#45;)wire[^"]*)">.*?</g>', svg, re.S
    ):
        ds = re.findall(r'<path[^>]* d="([^"]*)"', m.group(0))
        classes = m.group(1).replace("&#45;", "-").split()
        result[tuple(classes)] = ds[len(ds) // 2]
    return result


def _points(d):
    return [tuple(map(float, c.split(","))) for c in re.findall(r"[-\d.]+,[-\d.]+", d)]


@needs_dot
@pytest.mark.parametrize("rankdir", ["LR", "TB"])
def test_daisy_chain_gets_one_dot_per_shared_pin(rankdir):
    svg = _harness(DAISY, rankdir=rankdir, routing="orthogonal").svg
    dots = _dots(svg)
    assert len(dots) == 2
    tokens = sorted(c for classes, *_ in dots for c in classes if c != "wv-junction")
    assert tokens == ["wv-net-X1-p1", "wv-net-X1-p2"]


@needs_dot
def test_dot_sits_where_the_branch_leaves_the_trunk():
    svg = _harness(DAISY, rankdir="TB", routing="orthogonal").svg
    paths = _wire_paths(svg)
    for classes, cx, cy, fill in _dots(svg):
        pin = [c for c in classes if c.startswith("wv-net-X1-p")][0]
        # the two half-edges leaving that pin
        runs = [_points(d) for cls, d in paths.items() if pin in cls and "X1" in cls[-1]]
        assert len(runs) == 2
        # the dot is the first corner of the wire that turns off first ...
        corners = sorted((pts[1] for pts in runs), key=lambda p: p[1])
        assert (cx, cy) == pytest.approx(corners[0], abs=0.01)
        # ... and lies on the other wire's trunk segment
        trunk = [pts for pts in runs if pts[1] != corners[0]][0]
        (x0, y0), (x1, y1) = trunk[0], trunk[1]
        assert cx == pytest.approx(x0, abs=0.01) == pytest.approx(x1, abs=0.01)
        assert min(y0, y1) < cy < max(y0, y1)


@needs_dot
def test_dot_takes_the_wire_colour():
    svg = _harness(DAISY, routing="orthogonal").svg
    fills = {tuple(c for c in cls if c != "wv-junction")[0]: fill for cls, _, _, fill in _dots(svg)}
    assert fills == {"wv-net-X1-p1": "#000000", "wv-net-X1-p2": "#ff0000"}


@needs_dot
def test_dot_radius_scales_with_wire_thickness():
    def radius(**options):
        svg = _harness(DAISY, routing="orthogonal", **options).svg
        return float(re.search(r'<g class="wv-junction[^>]*><circle [^>]*r="([^"]*)"', svg).group(1))

    # 3 stripes of 2pt: half the bundle plus 1.5 wires; doubles with the thickness
    assert radius() == 6
    assert radius(wire_thickness=4) == 12


@needs_dot
def test_unrelated_crossing_wires_get_no_dot():
    svg = _harness(CROSSED, routing="orthogonal").svg
    assert _dots(svg) == []


@needs_dot
def test_default_spline_output_has_no_dots():
    assert _dots(_harness(DAISY).svg) == []
    assert "wv-junction" not in _harness(DAISY).svg


@needs_dot
def test_dots_are_drawn_above_the_wires():
    svg = _harness(DAISY, routing="orthogonal").svg
    assert svg.rfind("wv-junction") > svg.rfind('class="edge')
    # inside the transformed graph group, not after it
    assert svg.rfind("wv-junction") < svg.rfind("</g>\n</svg>")


# --- the geometry itself, on synthetic routes ---------------------------


def _edge(tokens, color="#000"):
    return SimpleNamespace(tokens=frozenset(tokens), color=color)


def test_branch_off_a_trunk_is_a_junction():
    trunk = [(10, 0), (10, 50), (40, 50), (40, 80)]
    branch = [(10, 0), (10, 30), (-20, 30), (-20, 80)]
    dots = _junctions([(_edge({"wv-net-a"}), trunk), (_edge({"wv-net-a"}), branch)])
    assert [(u, v) for u, v, *_ in dots] == [(10, 30)]
    assert dots[0][2] == {"wv-net-a"}


def test_same_net_wires_crossing_downstream_are_not_a_junction():
    # two branches off one pin that cross again later: joined at the pin,
    # not at the crossing, so no dot there
    a = [(10, 0), (10, 30), (60, 30), (60, 80)]
    b = [(10, 0), (10, 50), (90, 50), (90, 80)]
    dots = _junctions([(_edge({"wv-net-a"}), a), (_edge({"wv-net-a"}), b)])
    assert [(u, v) for u, v, *_ in dots] == [(10, 30)]  # only the branch


def test_dot_takes_the_branching_wires_colour():
    # whichever side of the pair the branch is on, its own colour wins
    trunk = [(10, 0), (10, 50), (40, 50), (40, 80)]
    branch = [(10, 0), (10, 30), (-20, 30), (-20, 80)]
    a, b = _edge({"wv-net-a"}, "#000"), _edge({"wv-net-a"}, "#f00")
    assert _junctions([(a, trunk), (b, branch)])[0][3] == "#f00"
    assert _junctions([(b, branch), (a, trunk)])[0][3] == "#f00"


def test_different_nets_never_junction():
    trunk = [(10, 0), (10, 50), (40, 50), (40, 80)]
    branch = [(10, 0), (10, 30), (-20, 30), (-20, 80)]
    cross = [(0, 20), (30, 20)]
    assert _junctions([
        (_edge({"wv-net-a"}), trunk),
        (_edge({"wv-net-b"}), branch),
        (_edge({"wv-net-c"}), cross),
    ]) == []


def test_shared_endpoints_and_shared_corners_are_not_junctions():
    # two wires that only touch at the port (no overlap) and a pair whose
    # run ends exactly at the other's corner
    a = [(10, 0), (10, 50), (40, 50)]
    b = [(10, 0), (-10, 0), (-10, 50)]
    c = [(40, 50), (40, 80)]
    assert _junctions([
        (_edge({"wv-net-a"}), a),
        (_edge({"wv-net-a"}), b),
        (_edge({"wv-net-a"}), c),
    ]) == []


def test_coincident_junctions_merge_their_tokens():
    trunk = [(10, 0), (10, 50)]
    branch = [(10, 0), (10, 30), (40, 30)]
    other = [(10, 0), (10, 30), (-40, 30)]
    dots = _junctions([
        (_edge({"wv-net-a", "wv-net-x"}), trunk),
        (_edge({"wv-net-a", "wv-net-y"}), branch),
        (_edge({"wv-net-a", "wv-net-x"}), other),
    ])
    assert len(dots) == 1
    assert dots[0][2] == {"wv-net-a", "wv-net-x"}
