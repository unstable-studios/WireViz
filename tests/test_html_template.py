# -*- coding: utf-8 -*-
"""Tests for the rendered HTML page.

The property being defended: the simple template ships a print stylesheet
and a dark-mode theme, and both must survive the placeholder substitution
performed by generate_html_output.
"""

from wireviz.DataClasses import Metadata, Options
from wireviz.wv_html import generate_html_output

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'


def _render(tmp_path):
    base = tmp_path / "t"
    (tmp_path / "t.tmp.svg").write_text(SVG, encoding="utf-8")
    bom_list = [["Id", "Description", "Qty"], ["1", "Wire", "2"]]
    generate_html_output(base, bom_list, Metadata(), Options())
    return (tmp_path / "t.html").read_text(encoding="utf-8")


def test_output_contains_print_stylesheet(tmp_path):
    assert "@media print" in _render(tmp_path)


def test_output_contains_dark_mode(tmp_path):
    assert "@media (prefers-color-scheme: dark)" in _render(tmp_path)
