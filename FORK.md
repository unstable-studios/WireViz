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

## Tests

```sh
pip install -e . pytest && pytest tests/
```
