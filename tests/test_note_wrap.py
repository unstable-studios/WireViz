# -*- coding: utf-8 -*-
"""Tests for ``options.note_wrap``.

The property being defended: GraphViz HTML-like labels never wrap text, so
a single-line ``notes:`` field sets the width of its entire node and a long
note dominates the drawing. ``note_wrap: N`` wraps note text at ~N columns
at render time. Author-typed line breaks are kept as paragraph breaks, long
unbreakable tokens are not split, and an unset ``note_wrap`` generates
byte-identical GraphViz source. (Notes never appear in the BOM, so the
build list is unaffected by construction.)
"""

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options
from wireviz.wv_helper import wrap_text

LONG_NOTE = (
    "This connector must be installed with the locking tab facing the "
    "engine block and torqued to specification before the harness is "
    "routed through the firewall grommet."
)

YAML = f"""
connectors:
  X1:
    pincount: 2
    notes: {LONG_NOTE}
  X2: {{pincount: 2}}
cables:
  W1:
    colors: [BK, RD]
    notes: {LONG_NOTE}
connections:
  - - X1: [1-2]
    - W1: [1-2]
    - X2: [1-2]
"""


def _harness(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    return wireviz.parse(yaml_text, return_types="harness", output_name="t")


def _gv(yaml_text, **options):
    return _harness(yaml_text, **options).graph.source


def test_default_output_is_unchanged():
    assert "note_wrap" not in _gv(YAML)  # sanity: option leaves no trace
    assert _gv(YAML).count("<br />") == 0
    assert LONG_NOTE in _gv(YAML)


def test_notes_wrap_in_connector_and_cable_nodes():
    source = _gv(YAML, note_wrap=40)
    # the one-line note now spans several rendered lines in both nodes
    assert LONG_NOTE not in source
    first_line = "This connector must be installed with"
    assert source.count(f"{first_line}<br />") == 2  # X1 and W1
    # no rendered line exceeds the requested width
    for chunk in source.split("<br />"):
        for line in chunk.splitlines():
            if "locking tab" in line or "firewall" in line:
                assert len(line) <= 40


def test_author_line_breaks_are_kept_as_paragraph_breaks():
    yaml_text = YAML.replace(
        f"notes: {LONG_NOTE}\n  X2",
        'notes: "first paragraph\\n\\nsecond paragraph"\n  X2',
    )
    source = _gv(yaml_text, note_wrap=40)
    assert "first paragraph<br /><br />second paragraph" in source


def test_long_tokens_are_not_split():
    token = "PN-" + "X" * 60
    yaml_text = YAML.replace(LONG_NOTE, f"see part {token}", 1)
    source = _gv(yaml_text, note_wrap=40)
    assert token in source  # intact, not broken mid-token


def test_works_under_tb_rankdir_too():
    source = _gv(YAML, rankdir="TB", note_wrap=40)
    assert LONG_NOTE not in source
    assert "This connector must be installed with<br />" in source


def test_links_do_not_count_toward_the_width():
    # 60 chars of markup around 9 chars of text must wrap as 9 chars
    note = '<a href="https://example.com/a/very/long/path/to/the/doc">datasheet</a> attached'
    assert wrap_text(note, 20) == "datasheet attached"


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "40"])
def test_invalid_values_are_rejected(bad):
    with pytest.raises(ValueError):
        Options(note_wrap=bad)


def test_none_and_non_string_pass_through():
    assert wrap_text(LONG_NOTE, None) == LONG_NOTE
    assert wrap_text(None, 40) is None
