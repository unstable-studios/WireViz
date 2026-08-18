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

## Tests

```sh
pip install -e . pytest && pytest tests/
```
