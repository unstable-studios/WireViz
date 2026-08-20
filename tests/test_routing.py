# -*- coding: utf-8 -*-
"""Tests for ``options.routing: orthogonal`` and the TB stripe-width fix.

The property being defended: with orthogonal routing every wire edge in
the SVG is a Manhattan polyline (line segments only, port-exact at both
ends, parallel colour stripes offset consistently through the corners),
edges sharing a rank channel are staggered apart, and pin loops and mate
arrows keep GraphViz's curves. In the cable nodes, the TB colour bar is
exactly ``wire_thickness`` per stripe, flush with the edge bundle. Unset,
the outputs are byte-identical to GraphViz's splines.
"""

import re
import shutil

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options
from wireviz.wv_ortho import orthogonalize

needs_dot = pytest.mark.skipif(
    shutil.which("dot") is None, reason="graphviz not installed"
)

YAML = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 2}
cables:
  W1: {colors: [BK], gauge: 18 AWG}
  W2: {colors: [YERD]}
connections:
  - - X1: [1]
    - W1: [1]
    - X2: [1]
  - - X1: [2]
    - W2: [1]
    - X2: [2]
"""


def _harness(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    return wireviz.parse(yaml_text, return_types="harness", output_name="t")


def _wire_paths(svg):
    """{edge title: [path d strings]} for every wv-wire edge in the SVG."""
    result = {}
    for m in re.finditer(
        r'<g id="[^"]*" class="edge [^"]*wv(?:-|&#45;)wire[^"]*">.*?</g>', svg, re.S
    ):
        title = re.search(r"<title>([^<]*)</title>", m.group(0)).group(1)
        title = title.replace("&#45;", "-")
        result[title] = re.findall(r'<path[^>]* d="([^"]*)"', m.group(0))
    return result


@needs_dot
@pytest.mark.parametrize("rankdir", ["LR", "TB"])
def test_wire_edges_become_manhattan_polylines(rankdir):
    svg = _harness(YAML, rankdir=rankdir, routing="orthogonal").svg
    paths = _wire_paths(svg)
    assert paths, "no wire edges found"
    for title, ds in paths.items():
        for d in ds:
            assert "C" not in d, f"{title} still has a curve: {d}"
            # every segment is axis-parallel
            coords = [
                tuple(map(float, c.split(",")))
                for c in re.findall(r"[-\d.]+,[-\d.]+", d)
            ]
            for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
                assert x1 == x2 or y1 == y2, f"{title} has a diagonal in: {d}"


@needs_dot
def test_orthogonal_paths_keep_port_endpoints():
    plain = _wire_paths(_harness(YAML, routing="orthogonal").svg)
    spline = _wire_paths(_harness(YAML).svg)
    num = re.compile(r"[-\d.]+,[-\d.]+")
    for title, ds in spline.items():
        for before, after in zip(ds, plain[title]):
            b, a = num.findall(before), num.findall(after)
            assert a[0] == b[0] or [round(float(v), 1) for v in a[0].split(",")] == [
                round(float(v), 1) for v in b[0].split(",")
            ]
            assert a[-1].split(",")[0] == b[-1].split(",")[0] or float(
                a[-1].split(",")[0]
            ) == pytest.approx(float(b[-1].split(",")[0]), abs=0.1)


@needs_dot
def test_parallel_stripes_stay_evenly_spaced_through_corners():
    svg = _harness(YAML, rankdir="TB", routing="orthogonal").svg
    paths = _wire_paths(svg)
    # find the multicolour bundle (5 stripes) with a corner
    for ds in paths.values():
        if len(ds) < 3 or "L" not in ds[0]:
            continue
        runs = []
        for d in ds:
            ys = [float(c.split(",")[1]) for c in re.findall(r"[-\d.]+,[-\d.]+", d)]
            if len(set(ys)) > 2:  # has a horizontal run at its own y
                runs.append(sorted(set(ys))[1])
        if len(runs) >= 3:
            gaps = [b - a for a, b in zip(sorted(runs), sorted(runs)[1:])]
            assert max(gaps) - min(gaps) < 0.05, f"uneven spacing: {sorted(runs)}"
            return
    pytest.fail("no multicolour cornered bundle found")


@needs_dot
def test_same_channel_edges_are_staggered():
    svg = _harness(YAML, rankdir="TB", routing="orthogonal").svg
    # both X1->cable edges share the X1/cable rank gap; their center runs
    # must sit on distinct tracks
    runs = []
    for title, ds in _wire_paths(svg).items():
        if not title.startswith("X1:"):
            continue
        d = ds[len(ds) // 2]
        ys = [float(c.split(",")[1]) for c in re.findall(r"[-\d.]+,[-\d.]+", d)]
        mid = [y for y in ys if min(ys) < y < max(ys)]
        if mid:
            runs.append(mid[0])
    assert len(runs) == 2 and abs(runs[0] - runs[1]) >= 4


def test_pin_loops_keep_their_arc():
    svg_in = (
        '<g id="edge1" class="edge wv&#45;wire">'
        "<title>X1:p3r:e&#45;&#45;X1:p4r:e</title>"
        '<path fill="none" stroke="#000000" d="M10,-20C40,-20 40,-60 10,-60"/>'
        "</g>"
    )
    assert orthogonalize(svg_in, "TB", 2) == svg_in


def test_mates_are_untouched():
    svg_in = (
        '<g id="edge1" class="edge wv&#45;mate">'
        "<title>X1&#45;&#45;X2</title>"
        '<path fill="none" stroke="#000000" d="M10,-20C40,-20 40,-60 80,-60"/>'
        "</g>"
    )
    assert orthogonalize(svg_in, "TB", 2) == svg_in


@needs_dot
def test_default_wires_stay_splines():
    # with routing unset, no post-pass runs: wires keep GraphViz's curves
    paths = _wire_paths(_harness(YAML).svg)
    assert paths and all("C" in d for ds in paths.values() for d in ds)


def test_edge_without_parsable_paths_is_left_alone():
    # a wv-wire group whose paths carry no coordinates must not crash the
    # rewriter (regression: _Edge indexed an empty path list)
    svg_in = (
        '<g id="edge1" class="edge wv&#45;wire">'
        "<title>X1:s&#45;&#45;W1:n</title>"
        '<path fill="none" stroke="#000000" d="Z"/>'
        "</g>"
    )
    assert orthogonalize(svg_in, "TB", 2) == svg_in


def test_gv_source_is_unchanged_by_routing():
    # routing is an SVG post-pass: the GraphViz source must not change
    assert (
        _harness(YAML, routing="orthogonal").graph.source
        == _harness(YAML).graph.source
    )


def test_invalid_value_is_rejected():
    with pytest.raises(ValueError):
        Options(routing="ortho")


# A diamond with an order group and wide middle-rank nodes: W3's edges span
# several ranks, and the wide W2 sits directly under the naive descent, so a
# one-turn router draws the wire straight through its box (issue #38).
DIAMOND = """
options:
  rankdir: TB
  routing: orthogonal
  order:
    - [W1, W3]
connectors:
  X1: {pincount: 4}
  X2: {pincount: 2, notes: a very wide middle rank component with a long note so that any wire crossing this rank must pass through its box}
  X3: {pincount: 4}
cables:
  W1: {colors: [BK, RD]}
  W2: {colors: [BK, RD], notes: a very wide cable node with a long note so the long descent from W3 to X3 has to pass through this box on its way down}
  W3: {colors: [GN, YE]}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X2: [1-2]
    - W2: [1-2]
    - X3: [3-4]
  - - X1: [3-4]
    - W3: [1-2]
    - X3: [1-2]
"""


def _node_bboxes(svg):
    """{node title: (x0, y0, x1, y1)} from the rendered polygons."""
    result = {}
    for m in re.finditer(r'<g id="[^"]*" class="node[^"]*">.*?</g>', svg, re.S):
        title = re.search(r"<title>([^<]*)</title>", m.group(0)).group(1)
        coords = [
            tuple(map(float, pair.split(",")))
            for pm in re.finditer(r'points="([^"]*)"', m.group(0))
            for pair in pm.group(1).split()
        ]
        xs, ys = [c[0] for c in coords], [c[1] for c in coords]
        result[title] = (min(xs), min(ys), max(xs), max(ys))
    return result


def _assert_no_node_crossings(svg):
    boxes = _node_bboxes(svg)
    routed = fallbacks = 0
    for title, ds in _wire_paths(svg).items():
        ends = {part.split(":")[0] for part in title.split("--")}
        for d in ds:
            if "C" in d:  # tier-3 fallback: spline kept, exempt by design
                fallbacks += 1
                continue
            routed += 1
            pts = [
                tuple(map(float, c.split(",")))
                for c in re.findall(r"[-\d.]+,[-\d.]+", d)
            ]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                for name, (bx0, by0, bx1, by1) in boxes.items():
                    if name in ends:
                        continue
                    crosses = (
                        max(x1, x2) > bx0
                        and min(x1, x2) < bx1
                        and max(y1, y2) > by0
                        and min(y1, y2) < by1
                    )
                    assert not crosses, f"{title} crosses {name} in: {d}"
    assert routed, "no orthogonally routed wires found"
    return fallbacks


@needs_dot
def test_multi_rank_wires_avoid_node_boxes():
    # without avoidance, W3->X3 descends straight through W2's box
    fallbacks = _assert_no_node_crossings(_harness(DIAMOND).svg)
    # the repro is solvable: the gutters are clear, so nothing falls back
    assert fallbacks == 0


@needs_dot
def test_multi_rank_wires_avoid_node_boxes_lr():
    _assert_no_node_crossings(_harness(DIAMOND.replace("rankdir: TB", "rankdir: LR")).svg)


def test_boxed_in_wire_falls_back_to_the_spline():
    # an edge whose every candidate route collides keeps GraphViz's curve:
    # a wall across the gap, plus side walls covering the detour lanes
    spline = 'd="M50,-100C50,-80 50,-40 50,-20"'
    svg_in = (
        '<g id="node1" class="node"><title>A</title>'
        '<polygon points="40,-95 60,-95 60,-105 40,-105"/></g>'
        '<g id="node2" class="node"><title>B</title>'
        '<polygon points="40,-15 60,-15 60,-25 40,-25"/></g>'
        '<g id="node3" class="node"><title>WALL</title>'
        '<polygon points="-1000,-70 1000,-70 1000,-50 -1000,-50"/></g>'
        '<g id="node4" class="node"><title>LEFT</title>'
        '<polygon points="-1100,-200 -990,-200 -990,0 -1100,0"/></g>'
        '<g id="node5" class="node"><title>RIGHT</title>'
        '<polygon points="990,-200 1100,-200 1100,0 990,0"/></g>'
        '<g id="edge1" class="edge wv&#45;wire"><title>A:s&#45;&#45;B:n</title>'
        f'<path fill="none" stroke="#000000" {spline}/></g>'
    )
    out = orthogonalize(svg_in, "TB", 2)
    assert spline in out  # unchanged: truly enclosed


def test_blocked_wire_detours_around_the_box():
    # a finite obstacle between the pins: the route must jog around it
    svg_in = (
        '<g id="node1" class="node"><title>A</title>'
        '<polygon points="40,-95 60,-95 60,-105 40,-105"/></g>'
        '<g id="node2" class="node"><title>B</title>'
        '<polygon points="140,-15 160,-15 160,-25 140,-25"/></g>'
        '<g id="node3" class="node"><title>BLOCK</title>'
        '<polygon points="20,-70 180,-70 180,-50 20,-50"/></g>'
        '<g id="edge1" class="edge wv&#45;wire"><title>A:s&#45;&#45;B:n</title>'
        '<path fill="none" stroke="#000000" d="M50,-100C80,-80 120,-40 150,-20"/></g>'
    )
    out = orthogonalize(svg_in, "TB", 2)
    d = re.search(r'class="edge [^"]*"><title>[^<]*</title><path[^>]* d="([^"]*)"', out).group(1)
    assert "C" not in d
    xs = [float(c.split(",")[0]) for c in re.findall(r"[-\d.]+,[-\d.]+", d)]
    # the lane must leave the obstacle's x-range (20..180) to get past it
    assert min(xs) < 20 - 2 or max(xs) > 180 + 2


def test_tb_stripe_bar_matches_wire_thickness():
    source = _harness(YAML, rankdir="TB").graph.source
    # every stripe cell carries cellpadding="0" so its width is honored;
    # GraphViz's default padding of 2 used to double the bar's width
    stripes = re.findall(r'<td width="2" cellpadding="0" bgcolor="#', source)
    assert stripes, "no stripe cells found"
