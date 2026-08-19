# -*- coding: utf-8 -*-
"""Tests for ``options.order`` node-ordering hints.

The property being defended: GraphViz freely chooses how nodes stack
within a rank, and the only prior recourse was hand-written tweak GV.
``order`` chains the listed designators with invisible constraint edges;
unset must generate byte-identical source, and unknown names must be an
error rather than a silently ignored hint.
"""

import re

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options

HARNESS = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 1}
  X3: {pincount: 1}
cables:
  W1: {colors: [BK]}
  W2: {colors: [RD]}
connections:
  - - X1: [1]
    - W1: [1]
    - X2: [1]
  - - X1: [2]
    - W2: [1]
    - X3: [1]
"""


def _gv(yaml_text, order=None):
    if order is not None:
        yaml_text = f"options:\n  order: {order}\n{yaml_text}"
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def _invis_chains(source):
    return re.findall(r"(\S+) -- (\S+)$", source, re.M)


def test_default_output_is_unchanged():
    source = _gv(HARNESS)
    assert "invis" not in source
    assert "rank=same" not in source
    assert source == _gv(HARNESS, order="null")


def test_groups_emit_same_rank_invisible_chains():
    source = _gv(HARNESS, order="[[W1, W2], [X2, X3]]")
    assert _invis_chains(source) == [("W1", "W2"), ("X2", "X3")]
    # each group is a rank=same subgraph with invisible edges
    assert source.count("rank=same") == 2
    assert source.count("edge [style=invis]") == 2


def test_flat_list_is_one_group():
    assert _gv(HARNESS, order="[W1, W2]") == _gv(HARNESS, order="[[W1, W2]]")


def test_unknown_designator_is_an_error():
    with pytest.raises(ValueError) as excinfo:
        _gv(HARNESS, order="[[W1, W9]]")
    assert "W9" in str(excinfo.value)


def test_hints_do_not_affect_wires_or_nets():
    plain = _gv(HARNESS)
    hinted = _gv(HARNESS, order="[[W1, W2]]")
    wire_edges = [l for l in plain.splitlines() if "wv-wire" in l]
    assert wire_edges == [l for l in hinted.splitlines() if "wv-wire" in l]


@pytest.mark.parametrize(
    "bad",
    ["not-a-list", [], [[]], [["W1"]], [["W1", 2]], [["W1", "W1"]], ["W1"]],
)
def test_invalid_order_is_rejected(bad):
    with pytest.raises(ValueError):
        Options(order=bad)
