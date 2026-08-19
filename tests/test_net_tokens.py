# -*- coding: utf-8 -*-
"""Tests for the correctness of the wv-net-* tokens behind net tracing.

The property being defended: hovering a wire in the HTML output must
highlight exactly its electrical net. The template's script merges edges
that share a class token, so two things must hold:

1. **Injectivity** -- the token mapping must never send two distinct
   identities (a cable wire, or a connector pin) to the same sanitized
   token string. A collision silently merges two unrelated nets.
2. **Emission** -- every wire edge in the generated source must carry
   exactly the tokens of its model identities: its cable wire and the
   connector pin it lands on. A wrong token attaches an edge to the
   wrong net.

Together these guarantee the token-derived partition equals the
model-derived partition, for any harness.
"""

import os
import re
from glob import glob
from pathlib import Path

import pytest

from wireviz import wireviz
from wireviz.Harness import gv_class

EXAMPLE_DIR = Path(__file__).parent.parent / "examples"
TUTORIAL_DIR = Path(__file__).parent.parent / "tutorial"
YAML_FILES = sorted(EXAMPLE_DIR.glob("*.yml")) + sorted(TUTORIAL_DIR.glob("*.yml"))
# check additional harness files with e.g.
#   WIREVIZ_NET_TEST_FILES='/path/to/*.yml' pytest tests/test_net_tokens.py
YAML_FILES += [
    Path(p) for p in sorted(glob(os.environ.get("WIREVIZ_NET_TEST_FILES", "")))
]


def _harness(path):
    return wireviz.parse(path, return_types="harness")


def _sanitize(token):
    return gv_class(token)["class"]


def _model_identities(harness):
    """Every (kind, token) identity the model can emit, unsanitized."""
    identities = set()
    for cable in harness.cables.values():
        for connection in cable.connections:
            port = (
                f"w{connection.via_port}"
                if isinstance(connection.via_port, int)
                else "ws"
            )
            identities.add(("cable", f"wv-net-{cable.name}-{port}"))
            for name, pin in (
                (connection.from_name, connection.from_pin),
                (connection.to_name, connection.to_pin),
            ):
                if name is not None and pin is not None:
                    identities.add(("pin", f"wv-net-{name}-p{pin}"))
    for connector in harness.connectors.values():
        for loop in connector.loops:
            identities.add(("pin", f"wv-net-{connector.name}-p{loop[0]}"))
            identities.add(("pin", f"wv-net-{connector.name}-p{loop[1]}"))
    return identities


def _expected_edge_token_sets(harness):
    """The exact token multiset each emitted wire edge must carry."""
    expected = []
    for cable in harness.cables.values():
        for connection in cable.connections:
            port = (
                f"w{connection.via_port}"
                if isinstance(connection.via_port, int)
                else "ws"
            )
            wire_token = _sanitize(f"wv-net-{cable.name}-{port}")
            if connection.from_pin is not None:
                expected.append(
                    frozenset(
                        [
                            wire_token,
                            _sanitize(
                                f"wv-net-{connection.from_name}-p{connection.from_pin}"
                            ),
                        ]
                    )
                )
            if connection.to_pin is not None:
                expected.append(
                    frozenset(
                        [
                            wire_token,
                            _sanitize(
                                f"wv-net-{connection.to_name}-p{connection.to_pin}"
                            ),
                        ]
                    )
                )
    for connector in harness.connectors.values():
        for loop in connector.loops:
            expected.append(
                frozenset(
                    [
                        _sanitize(f"wv-net-{connector.name}-p{loop[0]}"),
                        _sanitize(f"wv-net-{connector.name}-p{loop[1]}"),
                    ]
                )
            )
    return sorted(expected, key=sorted)


def _actual_edge_token_sets(harness):
    """Token sets of every wv-wire edge in the generated GraphViz source."""
    actual = []
    for match in re.finditer(r'class="([^"]*)"', harness.graph.source):
        classes = match.group(1).split()
        if "wv-wire" not in classes:
            continue
        actual.append(
            frozenset(c for c in classes if c.startswith("wv-net-"))
        )
    return sorted(actual, key=sorted)


@pytest.mark.parametrize("path", YAML_FILES, ids=lambda p: p.stem)
def test_token_mapping_is_injective(path):
    # sanitization must not merge two distinct identities into one token
    identities = _model_identities(_harness(path))
    sanitized = {}
    for kind, raw in identities:
        token = _sanitize(raw)
        assert sanitized.setdefault(token, (kind, raw)) == (kind, raw), (
            f"token collision: {sanitized[token]} and {(kind, raw)} both "
            f"sanitize to {token!r}, which would merge two unrelated nets"
        )


@pytest.mark.parametrize("path", YAML_FILES, ids=lambda p: p.stem)
def test_every_edge_carries_exactly_its_model_tokens(path):
    harness = _harness(path)
    assert _actual_edge_token_sets(harness) == _expected_edge_token_sets(harness)


def test_collision_is_detectable():
    # sanity-check the injectivity oracle itself: two designators that
    # differ only in characters the sanitizer folds must be flagged
    assert _sanitize("wv-net-S 1-p1") == _sanitize("wv-net-S_1-p1")
