# -*- coding: utf-8 -*-
"""Tests for the layout options exposed through ``options``.

The property being defended: the defaults must generate byte-identical
GraphViz source to the previously hardcoded values, so existing outputs are
stable; non-default values must actually land in the generated source.
"""

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options

HARNESS = """
connectors:
  X1: {pinlabels: [a, b]}
  X2: {pinlabels: [a, b]}
cables:
  W1: {colors: [BK, WH], shield: true}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X1: [1]
    - W1: [s]
    - X2: [1]
"""


def _gv(yaml_text):
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def _with_options(**kwargs):
    lines = "\n".join(f"  {k}: {v}" for k, v in kwargs.items())
    return f"options:\n{lines}\n{HARNESS}"


def test_defaults_are_unchanged():
    source = _gv(HARNESS)
    assert "ranksep=2" in source
    assert "nodesep=0.33" in source
    assert "penwidth" not in source
    assert 'height="2"' in source  # wire colour stripes
    assert 'height="6"' in source  # port cell: 3 bands of 2


def test_explicit_defaults_match_implicit_defaults():
    assert _gv(_with_options(ranksep=2, nodesep=0.33, wire_thickness=2)) == _gv(
        HARNESS
    )


def test_ranksep_and_nodesep_are_emitted():
    source = _gv(_with_options(ranksep=1, nodesep=0.5))
    assert "ranksep=1" in source
    assert "nodesep=0.5" in source


def test_wire_thickness_scales_edges_and_stripes():
    source = _gv(_with_options(wire_thickness=3))
    assert "penwidth=3" in source
    assert 'height="3"' in source  # single stripe band, and thin shield
    assert 'height="9"' in source  # port cell: 3 bands of 3


@pytest.mark.parametrize("attr", ["ranksep", "nodesep", "wire_thickness"])
@pytest.mark.parametrize(
    "bad", [0, -1, "wide", True, float("nan"), float("inf"), float("-inf")]
)
def test_invalid_values_are_rejected(attr, bad):
    with pytest.raises(ValueError):
        Options(**{attr: bad})
