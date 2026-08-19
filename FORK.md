# About this fork

A fork of [wireviz/WireViz](https://github.com/wireviz/WireViz) at v0.4.1, adding
two features to make WireViz safe to drive from a build script when the BOM is a
**build list** rather than a sketch.

Upstream behaviour is unchanged unless you pass the new flags. Existing examples,
tutorials and the documented YAML syntax all work exactly as before.

## `--strict` — refuse to silently drop input

Two WireViz behaviours discard input without failing:

- A connector or cable that no connection set references is omitted from the
  diagram **and the BOM**. This is reported as a warning; the run exits 0.
- Duplicate YAML keys resolve last-wins per the YAML spec, with no diagnostic.
  Two `connectors:` blocks in one document produce output containing only the
  second — easy to hit when concatenating files with `--prepend`.

Both are reasonable when sketching. Neither is safe when someone is buying parts
from the BOM: a missing component is a part that never gets ordered, and nothing
in the output says so.

```console
$ wireviz --strict harness.yml
Error: The following components are not referenced in any connection set, and
are therefore omitted from both the diagram and the BOM: J3, W12
```

Library callers get typed exceptions rather than stdout to scrape:

```python
from wireviz.wv_errors import UnreferencedComponentsError

try:
    wv.parse(data, output_formats=("svg",), strict=True)
except UnreferencedComponentsError as e:
    print(e.components)   # ['J3', 'W12']
```

## `--merge` — one harness from many files

`--prepend` concatenates files as **raw text**, so splitting a harness across
files by subsystem hits the duplicate-key problem above: the second file's
`connections:` silently replaces the first's.

`--merge` combines the sources at the data level instead:

```console
$ wireviz --merge --strict -p common.yml -O harness front.yml rear.yml engine.yml
```

- `connectors` and `cables` are unioned; a name defined in two files is an error
- `connections` and `additional_bom_items` are concatenated in argument order
- `metadata`, `options` and `tweak` are shallow-merged; the same setting given
  **different** values in two files is an error, the same value twice is fine
- unknown top-level keys pass through, so a file of YAML anchors kept under a
  key of its own survives the merge
- `--prepend` files are prepended to **each** input in turn, so anchors defined
  there resolve in every file

Nothing resolves by precedence. Ambiguity about where a definition came from is
reported rather than decided, so the result never depends on argument order.

Splitting a description across files is equivalent to writing it in one file —
`tests/test_merge.py` asserts that the generated GraphViz source is identical
either way.

## `rankdir` — top-to-bottom layout that actually renders

`rankdir` was hardcoded to `LR`, and so were the port compass points every wire
attaches to (`:e` on one end, `:w` on the other). Setting `rankdir=TB` through
`tweak` therefore produced a graph where every edge had to loop sideways to
reach a west-facing port on a node below it — and since wires are drawn as
**multi-colour parallel edges**, the colour stripes splay apart around that
loop. Each wire renders as a lens or squashed oval instead of a line.

`options.rankdir` sets both together:

```yaml
options:
  rankdir: TB
```

`LR` (the default) keeps east/west compass points; `TB` uses south/north. `RL`
and `BT` are rejected rather than silently mis-rendering.

Worth having because `LR` produces extremely wide, short drawings — a real
harness comes out around 15:1, which does not print. `TB` on the same model
gives roughly 2:1.

Under `TB`, every connector and cable table is **transposed**: pins run
horizontally, incoming ports sit on the node's top edge and outgoing ports on
its bottom edge, and cable colour stripes are vertical bars spanning the full
node height. Component info (name, part numbers, type, images, notes) moves
beside the pin strip instead of above it — it has to, because a strip below a
stacked info block would leave its ports interior to the node and route wires
across the info text. Wires therefore attach flush on the faces the graph
flows through, and nothing routes through a node body or label.

All shipped examples render correctly under `TB`; ex14 comes out at roughly
1:3.5 instead of 9:1. Known cosmetic quirk: a pin **loop** on a congested
connector may be drawn on the node's far side.

`LR` output is byte-identical to previous versions (asserted in
`tests/test_tb_layout.py`).

## Layout options — `ranksep`, `nodesep`, `wire_thickness`

Three previously hardcoded density knobs are now settable via `options`:

```yaml
options:
  ranksep: 1          # inches between ranks; was fixed at 2
  nodesep: 0.33       # inches between nodes in a rank (the default)
  wire_thickness: 3   # stripe thickness in points; was fixed at 2
```

`ranksep` is the cheapest way to narrow a too-wide `LR` drawing. `wire_thickness`
scales the edge `penwidth` and the colour-stripe rows inside cable nodes
together, so wires stay flush where they meet the node; useful when pale wires
disappear at print scale. Defaults generate byte-identical GraphViz source to
previous versions.

## `sort_wires` — untangle connection sets written against pin order

Connector pins and cable wire rows are fixed HTML-table ports that GraphViz
cannot reorder, so when a connection set lists pins in a different order than
the wires (`X1: [4-1]` feeding `W1: [1-4]`), the mismatch is drawn as a
crossing knot pinched between the nodes.

```yaml
options:
  sort_wires: by_pin
```

reorders the **displayed** wire rows in each cable by the barycenter of their
endpoint pin positions. Wire numbers, colors and the BOM are untouched; only
the vertical position of each row changes. When both ends of a cable list
pins against pin order, sorting straightens both sides at once. A mismatch on
only one side (the wires genuinely reverse between the two connectors) is
unavoidable, and is deliberately left where it is rather than moved around.

Off by default; the default generates byte-identical GraphViz source.

## `order` — pin down how nodes stack within a rank

GraphViz freely chooses the stacking order of nodes in a rank, and sometimes
chooses badly: in demo02 it places W4 below W3, so W4's two wires cross the
entire W3 bundle on their way to X4. There was no recourse short of raw
`tweak` GV.

```yaml
options:
  order:
    - [W1, W2, W4, W3]   # top-to-bottom under LR, left-to-right under TB
```

Each group becomes a `rank=same` subgraph whose members are chained with
invisible edges, so the listed components share one rank, stacked in the
given order. A single flat list is accepted as one group. Note the shared
rank is part of the contract: listing components that would naturally sit in
different ranks pulls them into one.

Unknown designators are an error rather than a silently ignored hint, and an
unset `order` generates byte-identical GraphViz source.

## `mate_labels` — name the dashed arrows

Mate edges are bare dashed arrows: nothing in the diagram says what they
mean. With `mate_labels: true` each mate edge gets a small label — `mate`
for bidirectional mating arrows (`<-->` / `<=>`) and `into` for directional
insertion arrows (`-->`):

```yaml
options:
  mate_labels: true
```

Labels use the harness font at `fontsize=10` to stay unobtrusive, and apply
to both pin-level (`MatePin`) and component-level (`MateComponent`) mates.
Unset, the generated GraphViz source is byte-identical.

## `wirelabel_detail` — slim down in-cable endpoint labels

Every wire row inside a cable node repeats the full endpoint path on both
sides (`X1:5:GND … X2:1:GND`), duplicating what is already visible at the
connectors and doubling the node's width on dense cables.

```yaml
options:
  wirelabel_detail: pin    # or: full (default), none
```

- `full` — the current behavior: `designator:pin:pinlabel`.
- `pin` — keeps `designator:pin` but drops the pinlabel component; the
  connector's own pinlabel cell still shows it.
- `none` — empties the endpoint cells entirely; the wire number/colour rows
  stay.

Applies under both `rankdir: LR` and `TB`. The default (`full`) generates
byte-identical GraphViz source.

## `routing` — schematic-style right-angle wires

GraphViz routes wires as splines, and draws a multi-colour wire as several
parallel splines whose offsets are computed per control point — on curved
sweeps the stripes splay apart and pinch at bends, so the wire's width
visibly varies like a brush stroke. Its own alternatives don't help:
`splines=ortho` ignores ports entirely, and both `ortho` and `polyline`
collapse the parallel stripes onto shared endpoints, pinching every wire
into a lens.

```yaml
options:
  routing: orthogonal
```

redraws every wire in the SVG (and the HTML page, which embeds it) as a
Manhattan polyline: straight out of the pin, one right-angle turn onto a
cross-rank channel, straight into the far pin — like a hand-drawn
schematic. The colour stripes keep their exact port positions and stay
evenly spaced through the corners, which eliminates the calligraphy
artifact entirely. Wires sharing a channel are staggered onto separate
tracks so their straight runs don't overlap. Works under both `rankdir:
LR` and `TB`.

Scope and limitations:

- It is an SVG post-pass: `svg` and `html` outputs get orthogonal wires;
  `png` and `gv` keep GraphViz's splines.
- Pin loops keep their arc (an orthogonal loop on one node face has no
  sensible shape), and mate arrows keep their dashed curves.
- The router is deliberately simple (one turn per wire, midpoint channel
  with staggering). It does not avoid node boxes; with default `ranksep`
  the channels sit safely between ranks, but extreme stagger fan-out on a
  very congested channel could reach a node.

Off by default; unset, the SVG is byte-identical to the spline output.

Related fix (always on, `TB` only): the colour bar where a wire passes
through a cable node was drawn double-width — GraphViz's default cell
padding of 2 inflates each empty stripe cell to 4pt regardless of its
`width`. The stripe cells now set `cellpadding="0"`, so the bar is exactly
`wire_thickness` per stripe and sits flush with the wire edges.

## `shield_style` — tell shields apart from black wires

An uncoloured shield (`shield: true`) is drawn as a thin plain black line,
visually identical to a black (BK) wire, both in the cable node and on the
edges.

```yaml
options:
  shield_style: dashed
```

draws shield edges dashed while keeping their colors: thin black for bool
shields, the black/color/black sandwich for named-color shields. Inside the
cable node the shield strip gets dashed cell borders (HTML-like labels
cannot dash a filled cell, so the bool shield's solid black fill is replaced
by dashed borders on the wire-facing sides; a named-color shield keeps its
colored fill and its black borders become dashed).

Off by default; the default generates byte-identical GraphViz source.

## `sheets` — split one harness into printable sheets

A real harness rendered as one drawing is too large to read or print. A
top-level `sheets:` mapping renders it as one drawing per sheet instead:

```yaml
sheets:
  power:  [X1, W1, X2]
  signal: [W3, X3]
```

- Only the major components need listing: splices, ferrules and wires are
  **inferred** by following connections from assigned components. A component
  whose neighbors sit on different sheets is ambiguous and must be assigned
  explicitly; a component with no chain to any assigned component cannot be
  placed. Both are errors — a sheet definition never silently drops or
  misplaces anything.
- A connection crossing sheets is drawn on the **cable's** sheet, ending in a
  stub: a reduced copy of the far connector showing only the referenced pins,
  typed `⇒ <sheet>` so the reader knows where to continue. Wire labels keep
  the real designators on every sheet. Mates crossing sheets get stubs too.
- Graphical outputs split into `<name>.<sheet>.<ext>` per sheet; the **BOM
  stays one file** for the whole harness — sheets are views for reading, the
  build list must not fragment.
- Composes with the other options (`rankdir`, `sort_wires`, `order`, …),
  which apply per sheet. With `--merge`, define `sheets:` in one input file.
- HTML output is **one page carrying every sheet** in its own interactive
  viewport, titled `Sheet n of N: <name>`, with the whole-harness BOM below.
  Net tracing spans sheets: stubs keep the real designators, so hovering a
  wire also lights its continuation on the other sheets, and clicking a BOM
  row scrolls to and centers the component's sheet.

## Interactive HTML output

The built-in `simple` HTML template is now interactive; regenerate with
`-f h` and open the `.html` in a browser:

- **Fit, pan and zoom** — the diagram opens fitted to the window; scroll to
  zoom at the cursor, drag to pan, double-click to re-fit. Wide harnesses no
  longer force horizontal page scrolling.
- **Net tracing** — hover any wire to highlight its entire electrical net,
  through splices and daisy-chained cables, while everything else dims.
- **BOM linkage** — click a BOM row to highlight and center its component(s)
  in the diagram; click again, click empty space, or press Escape to clear.

This works because the generator now emits `class` attributes on every node
(`wv-part wv-dsg-<designator>`) and wire edge (`wv-wire` plus `wv-net-…`
tokens naming the cable wire and connector pin it lands on). GraphViz passes
them through to SVG, where the template's script unions the tokens into nets.
The attributes are inert in PNG/SVG-only output and available to any
downstream tooling. Custom templates (e.g. `din-6771`) are unchanged.

## Tests

```sh
pip install -e . pytest && pytest tests/
```
