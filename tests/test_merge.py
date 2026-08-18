# -*- coding: utf-8 -*-
"""Tests for merging several sources into one harness.

The property being defended: splitting a description across files must be
equivalent to writing it in one file. Text concatenation is not, because YAML
resolves duplicate top-level keys last-wins and silently discards the earlier
block.
"""

import pytest

from wireviz import wv_merge, wv_yaml
from wireviz.wv_errors import ConflictingValueError, DuplicateComponentError

PART_A = """
connectors:
  X1: {type: D-Sub, pinlabels: [a]}
cables:
  W1: {colors: [BK]}
connections:
  - - X1: [1]
    - W1: [1]
    - X1: [1]
"""

PART_B = """
connectors:
  X2: {type: Molex, pinlabels: [a]}
cables:
  W2: {colors: [RD]}
connections:
  - - X2: [1]
    - W2: [1]
    - X2: [1]
"""


def _load(*texts):
    return [(f"f{i}", wv_yaml.safe_load(t)) for i, t in enumerate(texts)]


def test_merge_unions_components_and_concatenates_connections():
    merged = wv_merge.merge(_load(PART_A, PART_B))
    assert sorted(merged["connectors"]) == ["X1", "X2"]
    assert sorted(merged["cables"]) == ["W1", "W2"]
    assert len(merged["connections"]) == 2


def test_connection_order_follows_source_order():
    forward = wv_merge.merge(_load(PART_A, PART_B))["connections"]
    reverse = wv_merge.merge(_load(PART_B, PART_A))["connections"]
    assert forward == list(reversed(reverse))


def test_component_defined_twice_is_an_error():
    with pytest.raises(DuplicateComponentError) as excinfo:
        wv_merge.merge(_load(PART_A, PART_A))
    # Both the connector and the cable collide.
    names = {name for _, name, _, _ in excinfo.value.duplicates}
    assert names == {"X1", "W1"}


def test_all_duplicates_are_reported_at_once():
    # Reporting only the first would mean one round trip per collision.
    with pytest.raises(DuplicateComponentError) as excinfo:
        wv_merge.merge(_load(PART_A, PART_A))
    assert len(excinfo.value.duplicates) == 2


def test_same_setting_with_different_values_is_an_error():
    with pytest.raises(ConflictingValueError):
        wv_merge.merge(
            _load("metadata: {title: One}\n", "metadata: {title: Two}\n")
        )


def test_same_setting_with_identical_values_is_fine():
    merged = wv_merge.merge(
        _load("metadata: {title: Same}\n", "metadata: {title: Same}\n")
    )
    assert merged["metadata"]["title"] == "Same"


def test_settings_from_different_files_combine():
    merged = wv_merge.merge(
        _load("metadata: {title: T}\n", "metadata: {pn: P}\n")
    )
    assert merged["metadata"] == {"title": "T", "pn": "P"}


def test_unknown_top_level_keys_pass_through():
    # Callers keep YAML anchors under a key of their own; WireViz ignores it,
    # but dropping it here would break a prepended template file.
    merged = wv_merge.merge(_load("templates: {a: 1}\n", PART_B))
    assert merged["templates"] == {"a": 1}


def test_empty_source_is_harmless():
    merged = wv_merge.merge(_load(PART_A, ""))
    assert sorted(merged["connectors"]) == ["X1"]


def test_merging_halves_equals_writing_one_file():
    """The property the whole feature exists to provide."""
    import wireviz.wireviz as wv

    combined = """
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
  - - X2: [1]
    - W2: [1]
    - X2: [1]
"""
    from_one_file = wv.parse(combined, return_types="harness", strict=True)
    from_two_files = wv.parse(
        wv_merge.merge(_load(PART_A, PART_B)), return_types="harness", strict=True
    )

    # Compare the generated GraphViz source: it reflects components, wires and
    # every connection between them, so equality here is equality of the
    # harness as drawn.
    assert from_two_files.graph.source == from_one_file.graph.source


def test_mapping_input_is_also_accepted():
    merged = wv_merge.merge({"a": wv_yaml.safe_load(PART_A)})
    assert list(merged["connectors"]) == ["X1"]


def test_same_source_twice_is_reported_not_deduplicated():
    # Deduplicating would be silent, which is the behaviour this module exists
    # to eliminate.
    with pytest.raises(DuplicateComponentError):
        wv_merge.merge([("same.yml", wv_yaml.safe_load(PART_A))] * 2)
