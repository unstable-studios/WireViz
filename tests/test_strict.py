# -*- coding: utf-8 -*-
"""Tests for --strict.

Both failures these cover are silent by default: WireViz prints a warning (or
nothing at all) and exits 0 while omitting real components from the BOM. A
caller building hardware from that BOM would be missing parts, so the point of
these tests is that the errors keep being raised, not merely logged.
"""

import pytest

import wireviz.wireviz as wv
from wireviz.wv_errors import DuplicateKeyError, UnreferencedComponentsError

# X2 and W2 are declared but no connection set mentions them.
UNREFERENCED = """
connectors:
  X1: {type: D-Sub, pinlabels: [a]}
  X2: {type: Molex, pinlabels: [a]}
cables:
  W1: {colors: [BK]}
  W2: {colors: [RD]}
connections:
  - - X1: [1]
    - W1: [1]
    - X1: [1]
"""

# Two `connectors:` keys. YAML keeps the last, so X1 vanishes entirely.
DUPLICATE_TOP_LEVEL = """
connectors:
  X1: {type: D-Sub, pinlabels: [a]}
cables:
  W1: {colors: [BK]}
connections:
  - - X1: [1]
    - W1: [1]
    - X1: [1]
connectors:
  X2: {type: Molex, pinlabels: [a]}
"""

DUPLICATE_NESTED = """
connectors:
  X1: {type: D-Sub, pinlabels: [a]}
  X1: {type: Molex, pinlabels: [a]}
cables:
  W1: {colors: [BK]}
connections:
  - - X1: [1]
    - W1: [1]
    - X1: [1]
"""

# `<<:` legitimately supplies a key that the mapping then overrides. This must
# keep working -- it is the mechanism shared component libraries rely on.
ANCHOR_OVERRIDE = """
templates:
  base: &base {type: D-Sub, subtype: generic, pinlabels: [a]}
connectors:
  X1:
    <<: *base
    subtype: specific
cables:
  W1: {colors: [BK]}
connections:
  - - X1: [1]
    - W1: [1]
    - X1: [1]
"""


def _parse(yaml_str, **kwargs):
    return wv.parse(yaml_str, return_types="harness", **kwargs)


def test_unreferenced_components_warn_by_default(capsys):
    _parse(UNREFERENCED)
    assert "not referenced" in capsys.readouterr().out


def test_unreferenced_components_raise_when_strict():
    with pytest.raises(UnreferencedComponentsError) as excinfo:
        _parse(UNREFERENCED, strict=True)
    assert sorted(excinfo.value.components) == ["W2", "X2"]


def test_duplicate_top_level_key_silently_drops_a_block_by_default():
    # Documents the default behaviour this flag exists to defend against:
    # the first `connectors:` block is discarded without any diagnostic.
    harness = _parse(DUPLICATE_TOP_LEVEL.replace("X1: [1]", "X2: [1]"))
    assert "X1" not in harness.connectors


def test_duplicate_top_level_key_raises_when_strict():
    with pytest.raises(DuplicateKeyError) as excinfo:
        _parse(DUPLICATE_TOP_LEVEL, strict=True)
    assert excinfo.value.key == "connectors"


def test_duplicate_nested_key_raises_when_strict():
    with pytest.raises(DuplicateKeyError) as excinfo:
        _parse(DUPLICATE_NESTED, strict=True)
    assert excinfo.value.key == "X1"


def test_duplicate_key_error_reports_the_line():
    with pytest.raises(DuplicateKeyError) as excinfo:
        _parse(DUPLICATE_NESTED, strict=True)
    assert excinfo.value.line == 4


def test_anchor_override_is_not_a_duplicate():
    harness = _parse(ANCHOR_OVERRIDE, strict=True)
    assert harness.connectors["X1"].subtype == "specific"


def test_strict_is_silent_on_a_clean_harness(capsys):
    _parse(ANCHOR_OVERRIDE, strict=True)
    assert "not referenced" not in capsys.readouterr().out
