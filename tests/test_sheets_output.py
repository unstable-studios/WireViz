# -*- coding: utf-8 -*-
"""Tests for the file outputs of a multi-sheet harness.

The property being defended: graphical outputs split into one file per
sheet, but the BOM stays whole -- sheets are views for reading, the build
list must not fragment. A bad sheets definition fails even for
return-only callers, and sheet numbering metadata is stamped in
definition order.
"""

import shutil

import pytest

from wireviz import wireviz, wv_sheets
from wireviz.wv_errors import SheetError

HARNESS = """
sheets:
  main: [X1, W1, X2]
  aux: [W3, X3]
connectors:
  X1: {pincount: 3}
  X2: {pincount: 2}
  X3: {pincount: 1}
cables:
  W1: {colors: [BK, RD]}
  W3: {colors: [GN]}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
  - - X1: [3]
    - W3: [1]
    - X3: [1]
"""


def test_graphical_outputs_split_but_the_bom_stays_whole(tmp_path):
    wireviz.parse(
        HARNESS, output_formats=("gv", "tsv"), output_dir=tmp_path, output_name="t"
    )
    assert (tmp_path / "t.main.gv").exists()
    assert (tmp_path / "t.aux.gv").exists()
    assert not (tmp_path / "t.gv").exists()
    # one BOM for the whole harness, listing components from both sheets
    bom = (tmp_path / "t.bom.tsv").read_text(encoding="utf-8")
    assert not (tmp_path / "t.main.bom.tsv").exists()
    assert "W1" in bom and "W3" in bom

    main = (tmp_path / "t.main.gv").read_text(encoding="utf-8")
    aux = (tmp_path / "t.aux.gv").read_text(encoding="utf-8")
    assert "W1" in main and "W3" not in main
    assert "W3" in aux and "W1" not in aux


def test_sheet_names_are_sanitized_for_filenames(tmp_path):
    dodgy = HARNESS.replace("aux:", "aux sheet/2:")
    wireviz.parse(
        dodgy, output_formats=("gv",), output_dir=tmp_path, output_name="t"
    )
    assert (tmp_path / "t.aux_sheet_2.gv").exists()


def test_colliding_sanitized_sheet_names_are_an_error(tmp_path):
    # "aux/1" and "aux 1" both sanitize to "aux_1"; overwriting silently
    # would lose a sheet, so it must fail instead
    colliding = HARNESS.replace(
        "  main: [X1, W1, X2]\n  aux: [W3, X3]",
        "  aux/1: [X1, W1, X2]\n  aux 1: [W3, X3]",
    )
    with pytest.raises(SheetError) as excinfo:
        wireviz.parse(
            colliding, output_formats=("gv",), output_dir=tmp_path, output_name="t"
        )
    assert "aux_1" in str(excinfo.value)


def test_bom_only_output_renders_no_graphs(tmp_path):
    # tsv alone must not touch GraphViz or emit per-sheet files
    wireviz.parse(
        HARNESS, output_formats=("tsv",), output_dir=tmp_path, output_name="t"
    )
    assert (tmp_path / "t.bom.tsv").exists()
    assert list(tmp_path.glob("t.main.*")) == []


@pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz not installed")
def test_html_is_one_page_with_a_viewport_per_sheet(tmp_path):
    wireviz.parse(
        HARNESS, output_formats=("html",), output_dir=tmp_path, output_name="t"
    )
    page = (tmp_path / "t.html").read_text(encoding="utf-8")
    assert not (tmp_path / "t.main.html").exists()
    assert page.count('class="wv-viewport"') == 2
    assert "Sheet 1 of 2: main" in page
    assert "Sheet 2 of 2: aux" in page
    # both sheets' SVGs are embedded; the whole-harness BOM sits below
    assert page.count("<svg") == 2
    assert "W1" in page and "W3" in page


def test_sheet_diagram_html_escapes_names_and_strips_prologs():
    from wireviz.wv_html import _sheet_diagram_html

    blocks = _sheet_diagram_html(
        [("a<b", '<?xml version="1.0"?>\n<!DOCTYPE svg>\n<svg/>')]
    )
    assert "a&lt;b" in blocks
    assert "<?xml" not in blocks


def test_bad_definition_fails_even_without_outputs():
    broken = HARNESS.replace("aux: [W3, X3]", "aux: [W9]")
    with pytest.raises(SheetError):
        wireviz.parse(broken, return_types="harness", output_name="t")


def test_prepare_stamps_sheet_metadata():
    harness = wireviz.parse(HARNESS, return_types="harness", output_name="t")
    subs = wv_sheets.prepare(harness, {"main": ["X1", "W1", "X2"], "aux": ["W3", "X3"]})
    assert [s.metadata["sheet_current"] for s in subs.values()] == [1, 2]
    assert all(s.metadata["sheet_total"] == 2 for s in subs.values())
    assert subs["aux"].metadata["sheet_name"] == "aux"


def test_harnesses_without_sheets_are_unchanged(tmp_path):
    plain = HARNESS.split("connectors:")[1]
    wireviz.parse(
        "connectors:" + plain,
        output_formats=("gv",),
        output_dir=tmp_path,
        output_name="t",
    )
    assert (tmp_path / "t.gv").exists()
