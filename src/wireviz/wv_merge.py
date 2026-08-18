# -*- coding: utf-8 -*-
"""Merging several YAML sources into one harness description.

WireViz's --prepend concatenates files as raw text. YAML resolves duplicate
mapping keys last-wins, so two files that each define `connections:` produce a
document containing only the second one's -- silently. Splitting a harness
across files by subsystem is therefore unsafe with text concatenation alone.

This module merges at the data level instead, so that splitting a description
across files is equivalent to writing it in one file, and any ambiguity about
where a definition came from is an error rather than a silent choice.
"""

from typing import Any, Dict, Iterable, List, Mapping, Tuple, Union

from wireviz.wv_errors import ConflictingValueError, DuplicateComponentError

# Merged by union of their keys; a name defined twice is an error.
SECTION_DICTS = ("connectors", "cables")
# Concatenated in source order.
SECTION_LISTS = ("connections", "additional_bom_items")
# Shallow-merged; the same subkey set to different values in two files is an
# error. Setting it to the same value in both is not.
SECTION_MAPS = ("metadata", "options", "tweak")


def merge(
    sources: Union[
        Mapping[str, Dict[str, Any]], Iterable[Tuple[str, Dict[str, Any]]]
    ]
) -> Dict[str, Any]:
    """Merge parsed YAML documents into one.

    Args:
        sources: the parsed contents of each source, in order, as either a
            mapping of label to contents or a sequence of (label, contents)
            pairs. Labels are usually filenames and are used in error
            messages. A sequence is accepted so that the same label may
            appear twice -- passing one file to the merge twice is a mistake
            worth reporting, not deduplicating. Order determines the order of
            concatenated connection sets.

    Returns:
        A single dict suitable for wireviz.parse().

    Raises:
        DuplicateComponentError: a connector or cable name is defined in more
            than one source.
        ConflictingValueError: a scalar setting is given different values in
            different sources.
    """
    merged: Dict[str, Any] = {}
    origin: Dict[Any, str] = {}
    duplicates: List[tuple] = []
    conflicts: List[tuple] = []

    items = sources.items() if isinstance(sources, Mapping) else sources
    for label, data in items:
        for key, value in (data or {}).items():
            if key in SECTION_DICTS:
                section = merged.setdefault(key, {})
                for name, body in value.items():
                    if name in section:
                        duplicates.append((key, name, origin[(key, name)], label))
                        continue
                    section[name] = body
                    origin[(key, name)] = label
            elif key in SECTION_LISTS:
                merged.setdefault(key, []).extend(value)
            elif key in SECTION_MAPS:
                section = merged.setdefault(key, {})
                for name, body in value.items():
                    if name in section and section[name] != body:
                        conflicts.append(
                            (f"{key}.{name}", origin[(key, name)], label)
                        )
                        continue
                    section[name] = body
                    origin.setdefault((key, name), label)
            else:
                # Unknown top-level keys are passed through. WireViz ignores
                # them, but they are load-bearing for callers who keep YAML
                # anchors under a key of their own.
                if key in origin and merged[key] != value:
                    conflicts.append((key, origin[key], label))
                    continue
                merged[key] = value
                origin.setdefault(key, label)

    if duplicates:
        raise DuplicateComponentError(
            "The same component is defined in more than one source:\n"
            + "\n".join(
                f"  {section[:-1]} {name!r}: {first} and {second}"
                for section, name, first, second in duplicates
            ),
            duplicates,
        )
    if conflicts:
        raise ConflictingValueError(
            "The same setting is given different values in different sources:\n"
            + "\n".join(
                f"  {name}: {first} and {second}" for name, first, second in conflicts
            ),
            conflicts,
        )
    return merged
