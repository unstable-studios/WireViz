# -*- coding: utf-8 -*-
"""Tests for ``options.sort_wires: by_pin``.

The property being defended: connector pins and cable wire rows are fixed
HTML-table ports that GraphViz cannot reorder, so a mismatch between pin
order and wire order is drawn as a crossing knot. ``by_pin`` reorders the
displayed wire rows by the barycenter of their endpoint pin positions:
when both sides list pins against pin order, sorting straightens both
sides at once; a mismatch on only one side is unavoidable and must be
left untouched rather than moved around. With the option unset the
generated source must be unchanged.
"""

import re

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options

# Connection set written against pin order on BOTH sides: X1 pins 4..1 feed
# wires 1..4, which feed X2 pins 4..1. Row order 4,3,2,1 straightens both.
BOTH_REVERSED = """
connectors:
  X1: {pincount: 4}
  X2: {pincount: 4}
cables:
  W1: {colors: [WH, BN, GN, YE]}
connections:
  - - X1: [4-1]
    - W1: [1-4]
    - X2: [4-1]
"""

# The wires genuinely reverse between the connectors (the ex14 case): any
# row order shows the crossing on one side or the other.
ONE_SIDE_REVERSED = BOTH_REVERSED.replace("X2: [4-1]", "X2: [1-4]")


def _gv(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def _wire_row_order(source):
    """Wire numbers in the order their rows appear in the cable label."""
    return [int(n) for n in re.findall(r'port="w(\d+)"', source)]


def test_default_output_is_unchanged():
    assert _gv(BOTH_REVERSED) == _gv(BOTH_REVERSED, sort_wires="null")
    assert _wire_row_order(_gv(BOTH_REVERSED)) == [1, 2, 3, 4]


def test_by_pin_straightens_a_reversed_connection_set():
    source = _gv(BOTH_REVERSED, sort_wires="by_pin")
    # X1 pin 1 drives wire 4, which drives X2 pin 1, etc.
    assert _wire_row_order(source) == [4, 3, 2, 1]


def test_unavoidable_crossing_is_left_in_place():
    # All barycenters tie; the stable sort must not shuffle the rows.
    assert _gv(ONE_SIDE_REVERSED, sort_wires="by_pin") == _gv(ONE_SIDE_REVERSED)


def test_by_pin_is_noop_when_orders_already_match():
    aligned = BOTH_REVERSED.replace("[4-1]", "[1-4]")
    assert _gv(aligned, sort_wires="by_pin") == _gv(aligned)


def test_unconnected_wires_keep_wire_order_after_sorted_ones():
    partial = """
connectors:
  X1: {pincount: 2}
cables:
  W1: {colors: [WH, BN, GN, YE]}
connections:
  - - X1: [2, 1]
    - W1: [1-2]
"""
    source = _gv(partial, sort_wires="by_pin")
    assert _wire_row_order(source) == [2, 1, 3, 4]


def test_shield_is_unaffected():
    shielded = BOTH_REVERSED.replace(
        "colors: [WH, BN, GN, YE]", "colors: [WH, BN, GN, YE], shield: true"
    )
    source = _gv(shielded, sort_wires="by_pin")
    assert _wire_row_order(source) == [4, 3, 2, 1]
    # shield row still rendered after the wire rows
    assert source.index('port="ws"') > source.index('port="w1"')


def test_invalid_value_is_rejected():
    with pytest.raises(ValueError):
        Options(sort_wires="alphabetical")
