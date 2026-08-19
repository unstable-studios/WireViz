# -*- coding: utf-8 -*-
"""Tests for ``options.mate_labels: true``.

The property being defended: mate edges are bare dashed arrows that carry
no hint of their meaning, so ``mate_labels`` names them -- "mate" for
bidirectional mating arrows (``<-->`` / ``<=>``) and "into" for directional
insertion arrows (``-->``) -- in a small font that stays unobtrusive. With
the option unset the generated source must be byte-identical to before.
"""

import re

import pytest

from wireviz import wireviz
from wireviz.DataClasses import Options

# One bidirectional component-level mate (X1 <=> X2) and one directional
# pin-level insertion (X2.1 --> X3.1), as in examples/ex14.yml.
MATED = """
connectors:
  X1: {pincount: 2}
  X2: {pincount: 2}
  X3: {pincount: 2}
cables:
  W1: {wirecount: 2}
connections:
  - - X1: [1-2]
    - W1: [1-2]
  - - X1: [1-2]
    - <=>
    - X2: [1-2]
  - - X2: [1]
    - -->
    - X3: [1]
"""


def _gv(yaml_text, **options):
    if options:
        lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        yaml_text = f"options:\n{lines}\n{yaml_text}"
    harness = wireviz.parse(yaml_text, return_types="harness", output_name="t")
    return harness.graph.source


def _mate_edges(source):
    """The lines carrying class "wv-mate"."""
    return [line for line in source.splitlines() if 'class="wv-mate"' in line]


def test_default_output_is_unchanged():
    assert _gv(MATED) == _gv(MATED, mate_labels="false")
    assert not re.search(r"label=(mate|into)", _gv(MATED))


def test_bidirectional_mate_is_labeled_mate():
    source = _gv(MATED, mate_labels="true")
    (edge,) = [e for e in _mate_edges(source) if "X1" in e]
    assert "label=mate" in edge


def test_directional_insertion_is_labeled_into():
    source = _gv(MATED, mate_labels="true")
    (edge,) = [e for e in _mate_edges(source) if "X3" in e]
    assert "label=into" in edge


def test_labels_are_small_and_use_the_harness_font():
    # a non-default fontname proves the labels follow options.fontname
    # rather than a hard-coded default
    source = _gv(MATED, mate_labels="true", fontname="courier")
    for edge in _mate_edges(source):
        assert "fontsize=10" in edge
        assert "fontname=courier" in edge


def test_only_mate_edges_are_labeled():
    source = _gv(MATED, mate_labels="true")
    for line in source.splitlines():
        if re.search(r"label=(mate|into)", line):
            assert 'class="wv-mate"' in line


def test_non_bool_is_rejected():
    with pytest.raises(ValueError):
        Options(mate_labels="yes please")
