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

🛑 **`TB` is not finished.** It lays the graph out correctly and the wires are
drawn as lines rather than lens shapes, but wires are routed **through other
nodes**, crossing their labels.

The cause is structural. Connector ports are named `p{n}l` and `p{n}r`: every
pin sits on the **left or right edge** of the node's HTML table, because those
tables are built for left-to-right flow. Under `TB` an edge attaches to the
south face of a right-edge cell and then travels down across whatever node is
below it.

Finishing `TB` means transposing every connector and cable table so pins sit on
the top and bottom edges — a rework of the label builder in `wv_gv_html.py`,
not a flag. Until then `TB` is useful for experimenting and not for output.

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
