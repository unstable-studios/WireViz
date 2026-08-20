# -*- coding: utf-8 -*-
"""Rewrite wire edges in rendered SVG as orthogonal (Manhattan) polylines.

GraphViz cannot draw schematic-style right-angle wires itself:

- ``splines=ortho`` ignores ports entirely -- every edge is routed to the
  node border and then jogs sideways to reach its pin;
- ``splines=ortho`` and ``splines=polyline`` both collapse the parallel
  splines of a multi-colour wire onto shared endpoints, so the colour
  stripes pinch into a lens instead of staying parallel.

The default ``splines`` mode, however, lands every individual colour stripe
exactly on its port with correct parallel offsets at both ends. This module
takes that SVG and rewrites each wire edge's paths into an offset polyline.
The parallel offsets are preserved through every corner, so the stripes stay
flush and evenly spaced -- no calligraphy.

Routing is collision-aware. Every node's bounding box is an obstacle, and
each wire is planned in escalating tiers:

1. the one-turn route (pin, straight run, turn onto a cross-rank channel,
   straight into the far pin) -- tried on the staggered channel, then on
   the gutters just past the source and just before the destination;
2. a two-turn detour: out of the source gutter, across to a clear lane
   beside the blocking boxes, down the lane, in through the destination
   gutter;
3. if every candidate collides, the wire keeps GraphViz's spline -- a
   mixed drawing degrades gracefully instead of drawing wires over nodes.

Only wire edges (``class="... wv-wire ..."``) are rewritten. Mates keep
their dashed arrows, and pin loops (both ends on the same component) keep
GraphViz's arc, which an orthogonal path cannot represent sensibly.

Edges whose straight runs would share a channel are staggered onto
separate tracks.
"""

import re
from typing import List, Optional, Tuple

# GraphViz entity-escapes hyphens in SVG attribute values: wv-wire appears
# as wv&#45;wire in the file (browsers decode it back before classList sees it)
EDGE_RE = re.compile(
    r'<g id="[^"]*" class="edge [^"]*wv(?:-|&#45;)wire[^"]*">.*?</g>', re.S
)
NODE_RE = re.compile(r'<g id="[^"]*" class="node[^"]*">.*?</g>', re.S)
TITLE_RE = re.compile(r"<title>([^<]*)</title>")
PATH_D_RE = re.compile(r'(<path[^>]* d=")([^"]*)(")')
POINTS_RE = re.compile(r'points="([^"]*)"')
NUM = r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"
COORD_RE = re.compile(rf"({NUM}),({NUM})")

CLEARANCE = 12  # how far past a node face the gutter channels sit


def _endpoints(d: str) -> Optional[Tuple[float, float, float, float]]:
    coords = COORD_RE.findall(d)
    if len(coords) < 2:
        return None
    (sx, sy), (ex, ey) = coords[0], coords[-1]
    return float(sx), float(sy), float(ex), float(ey)


def _fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _node_boxes(svg: str, vertical: bool) -> List[Tuple[float, float, float, float]]:
    """Node bounding boxes as (u0, v0, u1, v1) in routing coordinates."""
    boxes = []
    for m in NODE_RE.finditer(svg):
        xs, ys = [], []
        for pm in POINTS_RE.finditer(m.group(0)):
            for pair in pm.group(1).split():
                x, y = pair.split(",")
                xs.append(float(x))
                ys.append(float(y))
        if not xs:
            continue
        if vertical:  # u = x, v = y
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
        else:  # u = y, v = x
            boxes.append((min(ys), min(xs), max(ys), max(xs)))
    return boxes


def _hits(pts, boxes, margin: float):
    """The boxes any segment of the axis-parallel polyline passes through."""
    hit = []
    for (u1, v1), (u2, v2) in zip(pts, pts[1:]):
        ulo, uhi = min(u1, u2), max(u1, u2)
        vlo, vhi = min(v1, v2), max(v1, v2)
        for box in boxes:
            b0, c0, b1, c1 = box
            if (
                uhi > b0 - margin
                and ulo < b1 + margin
                and vhi > c0 - margin
                and vlo < c1 + margin
            ):
                hit.append(box)
    return hit


class _Edge:
    """One wire bundle, worked in (u, v): u across the flow, v along it."""

    def __init__(self, block: str, vertical: bool):
        self.block = block
        self.vertical = vertical
        self.paths = []  # (prefix, d, suffix, su, sv, eu, ev)
        for m in PATH_D_RE.finditer(block):
            ends = _endpoints(m.group(2))
            if ends:
                sx, sy, ex, ey = ends
                if vertical:
                    self.paths.append((m.group(1), m.group(2), m.group(3), sx, sy, ex, ey))
                else:
                    self.paths.append((m.group(1), m.group(2), m.group(3), sy, sx, ey, ex))
        # centerline endpoints: the median stripe's own endpoints
        self.su = self.sv = self.eu = self.ev = 0.0
        if self.paths:
            mid = self.paths[len(self.paths) // 2]
            self.su, self.sv, self.eu, self.ev = mid[3:]

    @property
    def channel(self) -> float:
        """Natural coordinate of the straight cross run (midway between ports)."""
        return (self.sv + self.ev) / 2

    def plan(self, channel: float, boxes, margin: float):
        """Centerline corner points avoiding `boxes`, or None to fall back."""
        own = [
            box
            for box in boxes
            if (box[0] - 1 <= self.su <= box[2] + 1 and box[1] - 1 <= self.sv <= box[3] + 1)
            or (box[0] - 1 <= self.eu <= box[2] + 1 and box[1] - 1 <= self.ev <= box[3] + 1)
        ]
        obstacles = [box for box in boxes if box not in own]

        direction = 1 if self.ev >= self.sv else -1
        span = abs(self.ev - self.sv)
        blockers = []

        if abs(self.eu - self.su) < 0.5:
            pts = [(self.su, self.sv), (self.eu, self.ev)]  # straight through
            hit = _hits(pts, obstacles, margin)
            if not hit:
                return pts
            blockers.extend(hit)
        else:
            candidates = [channel]
            if span > 3 * CLEARANCE:
                candidates.append(self.sv + direction * CLEARANCE)  # source gutter
                candidates.append(self.ev - direction * CLEARANCE)  # destination gutter
            for v in candidates:
                pts = [(self.su, self.sv), (self.su, v), (self.eu, v), (self.eu, self.ev)]
                hit = _hits(pts, obstacles, margin)
                if not hit:
                    return pts
                blockers.extend(hit)

        # two-turn detour: gutter out, clear lane beside the blockers, gutter in
        if span > 3 * CLEARANCE:
            v1 = self.sv + direction * CLEARANCE
            v2 = self.ev - direction * CLEARANCE
            lanes = []
            for box in blockers:
                lanes.append(box[0] - margin - CLEARANCE)
                lanes.append(box[2] + margin + CLEARANCE)
            lanes.sort(key=lambda u: abs(u - (self.su + self.eu) / 2))
            for lane in lanes:
                pts = [
                    (self.su, self.sv),
                    (self.su, v1),
                    (lane, v1),
                    (lane, v2),
                    (self.eu, v2),
                    (self.eu, self.ev),
                ]
                if not _hits(pts, obstacles, margin):
                    return pts

        return None  # tier 3: keep the spline

    def rewritten(self, pts) -> str:
        """The edge's <g> block with every stripe redrawn along `pts`.

        Each stripe is the centerline offset by its own port offset, carried
        through every corner with the rotate-90 rule (flow segments shift
        across, cross segments shift along), so the bundle stays parallel.
        """
        s1 = 1 if pts[1][1] >= pts[0][1] else -1
        block = self.block
        for prefix, d, suffix, su, sv, eu, ev in self.paths:
            offset = su - self.su
            delta = offset * s1
            out = [(su, sv)]
            for k in range(1, len(pts) - 1):
                (ua, va), (ub, vb) = pts[k - 1], pts[k]
                (uc, vc) = pts[k + 1]
                if ua == ub:  # corner between a flow segment and a cross segment
                    flow_dir = 1 if vb >= va else -1
                    cross_dir = 1 if uc >= ub else -1
                    corner_u = (su if k == 1 else ub + delta * flow_dir)
                    corner_v = vb - delta * cross_dir
                else:  # corner between a cross segment and a flow segment
                    cross_dir = 1 if ub >= ua else -1
                    flow_dir = 1 if vc >= vb else -1
                    corner_u = (eu if k == len(pts) - 2 else ub + delta * flow_dir)
                    corner_v = vb - delta * cross_dir
                out.append((corner_u, corner_v))
            out.append((eu, ev))
            if self.vertical:
                coords = [f"{_fmt(u)},{_fmt(v)}" for u, v in out]
            else:
                coords = [f"{_fmt(v)},{_fmt(u)}" for u, v in out]
            new = "M" + " L".join(coords)
            block = block.replace(prefix + d + suffix, prefix + new + suffix, 1)
        return block


def _stagger(edges: List[_Edge], spacing: float) -> List[float]:
    """A channel coordinate per edge, spreading same-channel runs apart.

    Edges whose natural channels fall within one track of each other are
    clustered and fanned out symmetrically around the cluster's mean, so
    straight runs sharing a rank gap do not draw on top of each other.
    """
    order = sorted(range(len(edges)), key=lambda i: edges[i].channel)
    result = [0.0] * len(edges)
    cluster: List[int] = []

    def assign(members: List[int]) -> None:
        mean = sum(edges[i].channel for i in members) / len(members)
        # fan out in port order to keep crossings down
        members.sort(key=lambda i: edges[i].su)
        for j, i in enumerate(members):
            result[i] = mean + (j - (len(members) - 1) / 2) * spacing

    for i in order:
        if cluster and edges[i].channel - edges[cluster[-1]].channel > spacing:
            assign(cluster)
            cluster = []
        cluster.append(i)
    if cluster:
        assign(cluster)
    return result


def orthogonalize(svg: str, rankdir: str, wire_thickness: float) -> str:
    """Rewrite every wire edge in `svg` as an orthogonal polyline."""
    vertical = rankdir == "TB"
    boxes = _node_boxes(svg, vertical)
    edges = []
    spans = []
    for m in EDGE_RE.finditer(svg):
        block = m.group(0)
        title = TITLE_RE.search(block)
        if title:
            names = [part.split(":")[0] for part in title.group(1).split("&#45;&#45;")]
            if len(names) == 2 and names[0] == names[1]:
                continue  # pin loop: keep GraphViz's arc
        edge = _Edge(block, vertical)
        if not edge.paths:
            continue
        edges.append(edge)
        spans.append(m.span())

    if not edges:
        return svg

    # one track per bundle: bundle width plus a gap; obstacle margin covers
    # the stripes fanning out around the planned centerline
    max_stripes = max(len(e.paths) for e in edges)
    spacing = max_stripes * wire_thickness + 4
    margin = max_stripes * wire_thickness / 2 + 2
    channels = _stagger(edges, spacing)

    out = []
    last = 0
    for edge, channel, (start, end) in zip(edges, channels, spans):
        pts = edge.plan(channel, boxes, margin)
        out.append(svg[last:start])
        out.append(edge.rewritten(pts) if pts else edge.block)
        last = end
    out.append(svg[last:])
    return "".join(out)
