# -*- coding: utf-8 -*-
"""YAML loading for WireViz.

PyYAML follows the YAML spec in resolving duplicate mapping keys last-wins,
which is silent. For a harness description that is dangerous: two `connectors:`
blocks in one document produce a drawing and a BOM containing only the second,
with no diagnostic at all. `SafeLineLoader` rejects duplicates instead.
"""

import yaml

from wireviz.wv_errors import DuplicateKeyError

MERGE_TAG = "tag:yaml.org,2002:merge"


class StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys."""


def _construct_mapping(loader, node, deep=False):
    # Check the keys written literally in this mapping, BEFORE flatten_mapping
    # merges any anchor in. Overriding an inherited field (`<<: *anchor` then
    # `subtype: ...`) is legitimate YAML; the same key typed twice is not.
    seen = set()
    for key_node, _ in node.value:
        if key_node.tag == MERGE_TAG:
            continue
        key = key_node.value
        if key in seen:
            line = key_node.start_mark.line + 1
            raise DuplicateKeyError(
                f"Duplicate key {key!r} at line {line}. YAML would keep only "
                f"the last one, discarding the earlier value silently.",
                key,
                line,
            )
        seen.add(key)
    # Hand off to SafeConstructor, which resolves `<<` merge keys as usual.
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def safe_load(stream, strict: bool = False):
    """Parse a YAML document. With strict=True, duplicate keys raise."""
    return yaml.load(stream, Loader=StrictSafeLoader if strict else yaml.SafeLoader)
