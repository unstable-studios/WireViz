# -*- coding: utf-8 -*-
"""Tests for the transposed node tables under ``rankdir: TB``.

The property being defended: under TB, every pin and wire port must sit on
a top or bottom node face (ports run horizontally, one column per pin/wire),
because edges attach with north/south compass points; a port left on a
left/right edge routes its wire straight through the node below. And LR
output must remain byte-identical to a build without any rankdir setting.
"""

from wireviz import wireviz

HARNESS = """
connectors:
  X1:
    pincount: 2
    pinlabels: [VCC, GND]
    pincolors: [RD, BK]
  X2: {pincount: 2}
cables:
  W1: {colors: [RD, BK], shield: true}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X1: [2]
    - W1: [s]
    - X2: [2]
"""


def _gv(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def test_lr_output_is_unchanged():
    assert _gv(HARNESS, rankdir="LR") == _gv(HARNESS)


def test_tb_pin_ports_share_one_row():
    source = _gv(HARNESS, rankdir="TB")
    # all outgoing ports of X1 in a single table row, one column per pin
    assert '<tr><td port="p1r">1</td><td port="p2r">2</td></tr>' in source
    # all incoming ports of X2 likewise
    assert '<tr><td port="p1l">1</td><td port="p2l">2</td></tr>' in source


def test_tb_pinlabels_and_colors_are_columns():
    source = _gv(HARNESS, rankdir="TB")
    assert "<tr><td>VCC</td><td>GND</td></tr>" in source
    assert '<td sides="tlr">RD</td>' in source  # color text above its swatch
    assert '<td sides="blr">' in source


def test_tb_wire_ports_are_vertical_stripes():
    source = _gv(HARNESS, rankdir="TB")
    # stripe cell is the port; bands are fixed-width columns with no height,
    # so they stretch to the full strip height
    assert '<td port="w1" cellpadding="0" width="6">' in source
    assert '<td width="2" bgcolor="#ff0000" border="0"></td>' in source
    assert 'height="2"' not in source


def test_tb_shield_is_a_vertical_stripe():
    source = _gv(HARNESS, rankdir="TB")
    assert '<td cellpadding="0" width="2" bgcolor="#000000" border="0" port="ws">' in source


def test_tb_info_block_sits_beside_the_strip():
    source = _gv(HARNESS, rankdir="TB")
    assert '<td valign="middle">' in source


def test_tb_edges_attach_north_south():
    source = _gv(HARNESS, rankdir="TB")
    assert ":s -- " in source
    assert ":e -- " not in source
