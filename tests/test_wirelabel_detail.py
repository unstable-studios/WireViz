# -*- coding: utf-8 -*-
"""Tests for ``options.wirelabel_detail``.

The property being defended: every wire row inside a cable node repeats the
full endpoint path (``X1:1:GND``) on both sides, duplicating information
already visible at the connectors and widening the cable node on dense
harnesses. ``wirelabel_detail`` trims those in-cable endpoint labels only:
``"full"`` (the default) keeps the current output byte-for-byte, ``"pin"``
keeps ``designator:pin`` but drops the pinlabel component, and ``"none"``
leaves the endpoint cells empty while the wire number/colour rows and the
connectors' own pinlabel cells stay untouched. Any other value is rejected.
"""

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options

YAML = """
connectors:
  X1: {pincount: 2, pinlabels: [GND, VCC]}
  X2: {pincount: 2, pinlabels: [GND, VCC]}
cables:
  W1: {colors: [BK, RD]}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
"""


def _gv(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def _cable_label(source, name="W1"):
    """The HTML label of the cable node."""
    start = source.index(f"{name} [label=<")
    end = source.index("]", source.index("</table>", start))
    return source[start:end]


def test_default_output_is_unchanged():
    assert _gv(YAML) == _gv(YAML, wirelabel_detail="full")
    assert "<td>X1:1:GND</td>" in _cable_label(_gv(YAML))


def test_pin_keeps_designator_and_pin_but_drops_pinlabel():
    source = _gv(YAML, wirelabel_detail="pin")
    cable = _cable_label(source)
    assert "<td>X1:1</td>" in cable
    assert "<td>X2:2</td>" in cable
    assert "GND" not in cable and "VCC" not in cable
    # the connector's own pinlabel cell still shows it
    assert "GND" in source and "VCC" in source


def test_none_leaves_no_endpoint_text_in_the_cable_node():
    source = _gv(YAML, wirelabel_detail="none")
    cable = _cable_label(source)
    assert "X1" not in cable and "X2" not in cable
    assert "GND" not in cable
    # wire number/colour rows are untouched
    assert "BK" in cable and "RD" in cable
    # connectors themselves are untouched
    assert "GND" in source and "VCC" in source


def test_works_under_tb_rankdir_too():
    full = _cable_label(_gv(YAML, rankdir="TB"))
    assert "X1:1:GND" in full
    pin = _cable_label(_gv(YAML, rankdir="TB", wirelabel_detail="pin"))
    assert "X1:1" in pin and "GND" not in pin
    none = _cable_label(_gv(YAML, rankdir="TB", wirelabel_detail="none"))
    assert "X1" not in none and "X2" not in none


def test_invalid_value_is_rejected():
    with pytest.raises(ValueError):
        Options(wirelabel_detail="short")
