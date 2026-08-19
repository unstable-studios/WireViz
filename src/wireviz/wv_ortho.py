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
takes that SVG and rewrites each wire edge's paths into an offset polyline:
port, straight run, one right-angle turn onto a shared cross rank channel,
straight run into the far port. The parallel offsets are preserved through
the corners, so the stripes stay flush and evenly spaced -- no calligraphy.

Only wire edges (``class="... wv-wire ..."``) are rewritten. Mates keep
their dashed arrows, and pin loops (both ends on the same component) keep
GraphViz's arc, which an orthogonal path cannot represent sensibly.

Edges whose straight runs would overlap in the same channel are staggered
sideways so each wire keeps its own track.
"""

import re
from typing import List, Optional, Tuple

# GraphViz entity-escapes hyphens in SVG attribute values: wv-wire appears
# as wv&#45;wire in the file (browsers decode it back before classList sees it)
EDGE_RE = re.compile(
    r'<g id="[^"]*" class="edge [^"]*wv(?:-|&#45;)wire[^"]*">.*?</g>', re.S
)
TITLE_RE = re.compile(r"<title>([^<]*)</title>")
PATH_D_RE = re.compile(r'(<path[^>]* d=")([^"]*)(")')
NUM = r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"
COORD_RE = re.compile(rf"({NUM}),({NUM})")


def _endpoints(d: str) -> Optional[Tuple[float, float, float, float]]:
    coords = COORD_RE.findall(d)
    if len(coords) < 2:
        return None
    (sx, sy), (ex, ey) = coords[0], coords[-1]
    return float(sx), float(sy), float(ex), float(ey)


def _fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


class _Edge:
    def __init__(self, block: str, vertical: bool):
        self.block = block
        self.vertical = vertical
        self.paths = []  # (prefix, d, suffix, sx, sy, ex, ey)
        for m in PATH_D_RE.finditer(block):
            ends = _endpoints(m.group(2))
            if ends:
                self.paths.append((m.group(1), m.group(2), m.group(3)) + ends)
        # centerline endpoints: the median stripe's own endpoints
        mid = self.paths[len(self.paths) // 2]
        self.sx, self.sy, self.ex, self.ey = mid[3:]

    @property
    def channel(self) -> float:
        """Natural coordinate of the straight cross run (midway between ports)."""
        if self.vertical:
            return (self.sy + self.ey) / 2
        return (self.sx + self.ex) / 2

    def rewritten(self, channel: float) -> str:
        """The edge's <g> block with every path redrawn orthogonally."""
        block = self.block
        for prefix, d, suffix, sx, sy, ex, ey in self.paths:
            if self.vertical:
                # V-H-V: offsets live in x; the cross run is horizontal
                o = sx - self.sx
                s1 = 1 if ey >= sy else -1
                dxs = 0 if abs(self.ex - self.sx) < 0.5 else (1 if self.ex > self.sx else -1)
                if dxs == 0:
                    new = f"M{_fmt(sx)},{_fmt(sy)} L{_fmt(ex)},{_fmt(ey)}"
                else:
                    run = channel - dxs * s1 * o
                    new = (
                        f"M{_fmt(sx)},{_fmt(sy)} L{_fmt(sx)},{_fmt(run)} "
                        f"L{_fmt(ex)},{_fmt(run)} L{_fmt(ex)},{_fmt(ey)}"
                    )
            else:
                # H-V-H: offsets live in y; the cross run is vertical
                o = sy - self.sy
                s1 = 1 if ex >= sx else -1
                dys = 0 if abs(self.ey - self.sy) < 0.5 else (1 if self.ey > self.sy else -1)
                if dys == 0:
                    new = f"M{_fmt(sx)},{_fmt(sy)} L{_fmt(ex)},{_fmt(ey)}"
                else:
                    run = channel + dys * s1 * o
                    new = (
                        f"M{_fmt(sx)},{_fmt(sy)} L{_fmt(run)},{_fmt(sy)} "
                        f"L{_fmt(run)},{_fmt(ey)} L{_fmt(ex)},{_fmt(ey)}"
                    )
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
        members.sort(key=lambda i: edges[i].sx if edges[i].vertical else edges[i].sy)
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

    # one track per bundle: bundle width plus a gap
    max_stripes = max(len(e.paths) for e in edges)
    spacing = max_stripes * wire_thickness + 4
    channels = _stagger(edges, spacing)

    out = []
    last = 0
    for edge, channel, (start, end) in zip(edges, channels, spans):
        out.append(svg[last:start])
        out.append(edge.rewritten(channel))
        last = end
    out.append(svg[last:])
    return "".join(out)
