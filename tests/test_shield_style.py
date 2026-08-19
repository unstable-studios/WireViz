# -*- coding: utf-8 -*-
"""Tests for ``options.shield_style: dashed``.

The property being defended: an uncoloured cable shield is drawn as a thin
plain black line, indistinguishable from a black (BK) wire. Under
``shield_style: dashed`` shield edges are dashed (keeping their colors:
thin black for bool shields, black/color/black sandwich for named-color
shields) and the in-node shield strip is drawn with dashed cell borders.
GraphViz edge attributes persist, so a wire edge that follows a dashed
shield edge must switch the style back to bold. With the option unset the
generated source must be byte-identical to before.
"""

import re

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options

SHIELDED = """
connectors:
  X1: {pincount: 3}
  X2: {pincount: 3}
cables:
  W1: {colors: [BK, RD], shield: true}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X1: [3]
    - W1: s
    - X2: [3]
"""

COLORED_SHIELD = SHIELDED.replace("shield: true", "shield: GN")


def _gv(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def _edge_attr_lines(source):
    return re.findall(r"edge \[.*\]", source)


def test_default_output_is_unchanged():
    assert _gv(SHIELDED) == _gv(SHIELDED, shield_style="null")
    assert "dashed" not in _gv(SHIELDED)
    assert "dashed" not in _gv(COLORED_SHIELD)


def test_dashed_applies_only_to_shield_edges():
    source = _gv(SHIELDED, shield_style="dashed")
    dashed = [line for line in _edge_attr_lines(source) if "dashed" in line]
    # only the bool shield's edge attr is dashed, and it stays thin black
    assert dashed == ['edge [color="#000000" style="dashed,bold"]']
    # wire edges after a shield edge switch the persistent style back
    shield_first = SHIELDED.replace(
        "connections:", "connections:\n  - - X1: [3]\n    - W1: s"
    )
    source = _gv(shield_first, shield_style="dashed")
    shield_pos = source.index('style="dashed,bold"')
    assert "style=bold" in source[shield_pos:]


def test_colored_shield_keeps_its_color_sandwich():
    source = _gv(COLORED_SHIELD, shield_style="dashed")
    assert 'edge [color="#000000:#00ff00:#000000" style="dashed,bold"]' in source


def test_node_strip_is_dashed_lr():
    source = _gv(SHIELDED, shield_style="dashed")
    # bool shield: dashed top/bottom borders instead of a solid black fill
    assert re.search(
        r'<td colspan="3" cellpadding="0" height="2" border="1" '
        r'sides="tb" style="dashed" port="ws">',
        source,
    )
    colored = _gv(COLORED_SHIELD, shield_style="dashed")
    assert 'border="2" sides="tb" style="dashed" port="ws"' in colored


def test_node_strip_is_dashed_tb():
    source = _gv(SHIELDED, shield_style="dashed", rankdir="TB")
    assert re.search(
        r'<td cellpadding="0" width="2" border="1" '
        r'sides="lr" style="dashed" port="ws">',
        source,
    )
    colored = _gv(COLORED_SHIELD, shield_style="dashed", rankdir="TB")
    assert 'border="2" sides="lr" style="dashed" port="ws"' in colored
    dashed = [line for line in _edge_attr_lines(source) if "dashed" in line]
    assert dashed == ['edge [color="#000000" style="dashed,bold"]']


def test_default_output_is_unchanged_tb():
    assert _gv(SHIELDED, rankdir="TB") == _gv(
        SHIELDED, rankdir="TB", shield_style="null"
    )
    assert "dashed" not in _gv(SHIELDED, rankdir="TB")


def test_invalid_value_is_rejected():
    with pytest.raises(ValueError):
        Options(shield_style="dotted")
