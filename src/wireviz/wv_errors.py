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


class DuplicateComponentError(WireVizError):
    """A connector or cable name is defined in more than one source.

    Merging cannot choose between them without discarding one, which is the
    behaviour merging exists to avoid.
    """

    def __init__(self, message: str, duplicates: List[tuple]):
        super().__init__(message)
        self.duplicates = duplicates


class SheetError(WireVizError):
    """The sheets definition cannot be applied to the harness.

    Raised for structural mistakes (unknown or doubly-assigned designators,
    malformed definitions) and for components whose sheet cannot be inferred:
    inference follows connections from explicitly assigned components, so a
    component is ambiguous when its neighbors sit on different sheets, and
    unassignable when no chain links it to any assigned component.
    """

    def __init__(self, message: str, components: List[str] = None):
        super().__init__(message)
        self.components = components or []


class ConflictingValueError(WireVizError):
    """A setting is given different values in different sources.

    Unlike component definitions these could be resolved by precedence, but
    silently picking one would make the result depend on argument order.
    """

    def __init__(self, message: str, conflicts: List[tuple]):
        super().__init__(message)
        self.conflicts = conflicts
