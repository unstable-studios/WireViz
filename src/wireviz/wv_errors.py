# -*- coding: utf-8 -*-
"""Exceptions raised by WireViz.

These exist so that callers driving WireViz as a library can react to specific
problems programmatically, rather than scraping stdout for warning text.
"""

from typing import List


class WireVizError(Exception):
    """Base class for all WireViz errors."""


class UnreferencedComponentsError(WireVizError):
    """A declared connector or cable is not used by any connection set.

    WireViz omits such a component from both the diagram and the BOM. That is
    reasonable when sketching, but silent data loss when the BOM is a build
    list, so `strict` mode turns it into an error.
    """

    def __init__(self, message: str, components: List[str]):
        super().__init__(message)
        self.components = components


class DuplicateKeyError(WireVizError):
    """The same key appears twice in one YAML mapping.

    YAML resolves duplicate keys last-wins, so the earlier value is discarded
    without any diagnostic. At the top level that silently deletes an entire
    `connectors:` or `connections:` block.
    """

    def __init__(self, message: str, key: str, line: int):
        super().__init__(message)
        self.key = key
        self.line = line
