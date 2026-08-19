# -*- coding: utf-8 -*-
"""Tests for the class attributes emitted for SVG interactivity.

The property being defended: the HTML template's net tracing and BOM
linkage need stable, parseable class tokens on every node and wire edge.
GraphViz strips port names from SVG edge titles, so these classes are the
only machine-readable link between an SVG element and the harness model.
"""

from wireviz import wireviz

HARNESS = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 2}
cables:
  W1: {colors: [BK, RD], shield: true}
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


def test_nodes_carry_designator_classes():
    source = _gv(HARNESS)
    for designator in ("X1", "X2", "W1"):
        assert f'class="wv-part wv-dsg-{designator}"' in source


def test_wire_edges_carry_net_tokens():
    source = _gv(HARNESS)
    # each half-edge names its cable wire and the connector pin it lands on
    assert 'class="wv-wire wv-net-W1-w1 wv-net-X1-p1"' in source
    assert 'class="wv-wire wv-net-W1-w1 wv-net-X2-p1"' in source
    assert 'class="wv-wire wv-net-W1-w2 wv-net-X1-p2"' in source


def test_shield_edges_carry_net_tokens():
    source = _gv(HARNESS)
    assert 'class="wv-wire wv-net-W1-ws wv-net-X1-p1"' in source


def test_tokens_are_sanitized_to_css_class_names():
    from wireviz.Harness import gv_class

    assert gv_class("wv-dsg-W 1.a", "wv-net-X#1-p2") == {
        "class": "wv-dsg-W_1_a wv-net-X_1-p2"
    }
