# -*- coding: utf-8 -*-
"""Tests for splitting a harness into sheets.

The property being defended: a sheets definition never silently drops or
misplaces a component (assignment is complete, inference is unambiguous,
mistakes raise typed errors), and the per-sheet drawings stay faithful --
wire labels keep the real designators, far-sheet connectors appear as
stubs naming their sheet, and a single-sheet split reproduces the
original graph byte-identically.
"""

import pytest

from wireviz import wireviz, wv_sheets
from wireviz.wv_errors import SheetError

HARNESS = """
connectors:
  X1: {pincount: 4}
  X2: {pincount: 2}
  X3: {pincount: 2}
  S1: {style: simple, type: Splice}
  S2: {style: simple, type: Splice}
cables:
  W1: {colors: [BK, RD]}
  W2: {colors: [BK, RD]}
  W3: {colors: [GN], shield: true}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - [S1, S2]
    - W2: [1-2]
    - X2: [1-2]
  - - X1: [3]
    - W3: [1]
    - X3: [1]
  - - X1: [4]
    - W3: [s]
    - X3: [2]
"""

MATED = HARNESS + """
  - - X2: [2]
    - -->
    - X3: [2]
"""


def _harness(yaml_text):
    return wireviz.parse(yaml_text, return_types="harness", output_name="t")


def test_inference_follows_connections():
    # S1/S2 are not listed; both their cable neighbors sit on "main"
    assignment = wv_sheets.assign(
        _harness(HARNESS),
        {"main": ["X1", "W1", "W2", "X2"], "aux": ["W3", "X3"]},
    )
    assert assignment["S1"] == "main"
    assert assignment["S2"] == "main"


def test_ambiguous_components_are_an_error():
    # S1/S2 sit between W1 (left) and W2 (right): no sheet can be inferred
    with pytest.raises(SheetError) as excinfo:
        wv_sheets.assign(
            _harness(HARNESS),
            {"left": ["X1", "W1"], "right": ["W2", "X2"], "aux": ["W3", "X3"]},
        )
    assert "S1" in excinfo.value.components
    assert "explicitly" in str(excinfo.value)


def test_explicit_assignment_resolves_ambiguity():
    assignment = wv_sheets.assign(
        _harness(HARNESS),
        {
            "left": ["X1", "W1", "S1", "S2"],
            "right": ["W2", "X2"],
            "aux": ["W3", "X3"],
        },
    )
    assert assignment["S1"] == "left"


def test_disconnected_cluster_must_be_assigned_explicitly():
    # two internally connected chains with no link between them
    islands = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 2}
  X3: {pincount: 1}
  X4: {pincount: 1}
cables:
  W1: {colors: [BK, RD]}
  W3: {colors: [GN]}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X3: [1]
    - W3: [1]
    - X4: [1]
"""
    sheets = {"main": ["X1", "W1", "X2"]}
    with pytest.raises(SheetError) as excinfo:
        wv_sheets.assign(_harness(islands), sheets)
    assert set(excinfo.value.components) == {"X3", "W3", "X4"}
    # assigning any one member lets the rest of the cluster infer
    sheets["aux"] = ["W3"]
    assert wv_sheets.assign(_harness(islands), sheets)["X3"] == "aux"


def test_unknown_designator_is_an_error():
    with pytest.raises(SheetError) as excinfo:
        wv_sheets.assign(_harness(HARNESS), {"main": ["X1", "W9"]})
    assert excinfo.value.components == ["W9"]


def test_double_assignment_is_an_error():
    with pytest.raises(SheetError):
        wv_sheets.assign(
            _harness(HARNESS), {"a": ["X1"], "b": ["X1"]}
        )


@pytest.mark.parametrize("bad", [None, {}, {"a": "X1"}, {"a": [1]}, {1: ["X1"]}])
def test_malformed_definitions_are_rejected(bad):
    with pytest.raises(SheetError):
        wv_sheets.assign(_harness(HARNESS), bad)


def test_single_sheet_split_is_byte_identical():
    harness = _harness(HARNESS)
    (sub,) = wv_sheets.split(
        harness, {"all": list(harness.connectors) + list(harness.cables)}
    ).values()
    assert sub.graph.source == harness.graph.source


def test_cross_sheet_connections_end_in_stubs():
    harness = _harness(HARNESS)
    result = wv_sheets.split(
        harness, {"main": ["X1", "W1", "W2", "X2"], "aux": ["W3", "X3"]}
    )
    assert list(result) == ["main", "aux"]

    aux = result["aux"].graph.source
    # the aux sheet draws W3 against a stub of X1 naming the far sheet
    assert f"{wv_sheets.STUB_TYPE_PREFIX}main" in aux
    # the stub carries only the referenced pins, in original pin order
    flat = "".join(aux.split())
    assert '<tdport="p1r">3</td>' in flat
    assert '<tdport="p2r">4</td>' in flat
    assert "p3r" not in flat  # pins 1 and 2 are not referenced from aux
    # wire labels keep the real designator
    assert "X1:3" in aux
    # the main sheet does not mention the aux-only cable
    assert "W3" not in result["main"].graph.source


def test_stub_pins_keep_original_pin_order():
    harness = _harness(HARNESS.replace("- X1: [3]", "- X1: [4]").replace(
        "- X1: [4]\n    - W3: [s]", "- X1: [3]\n    - W3: [s]"
    ))
    result = wv_sheets.split(
        harness, {"main": ["X1", "W1", "W2", "X2"], "aux": ["W3", "X3"]}
    )
    # referenced as 4 then 3; stub still lists 3 before 4
    flat = "".join(result["aux"].graph.source.split())
    assert '<tdport="p1r">3</td>' in flat
    assert '<tdport="p2r">4</td>' in flat


def test_cross_sheet_mates_get_stubs_on_both_sheets():
    harness = _harness(MATED)
    result = wv_sheets.split(
        harness, {"main": ["X1", "W1", "W2", "X2"], "aux": ["W3", "X3"]}
    )
    main = result["main"].graph.source
    aux = result["aux"].graph.source
    # each sheet draws the mate against a stub of the far connector
    assert f"{wv_sheets.STUB_TYPE_PREFIX}aux" in main
    assert f"{wv_sheets.STUB_TYPE_PREFIX}main" in aux
    assert 'class="wv-mate"' in main
    assert 'class="wv-mate"' in aux


def test_shield_connections_cross_sheets():
    harness = _harness(HARNESS)
    aux = wv_sheets.split(
        harness, {"main": ["X1", "W1", "W2", "X2"], "aux": ["W3", "X3"]}
    )["aux"].graph.source
    assert 'port="ws"' in aux  # shield row rendered on the cable's sheet
