# -*- coding: utf-8 -*-
"""Split a parsed harness into per-sheet sub-harnesses.

A real harness rendered as one drawing is too large to read or print. A
top-level ``sheets:`` mapping assigns components to named sheets:

.. code-block:: yaml

    sheets:
      power: [X1, W1]
      data:  [X3, W2, X4]

Only the major components need listing: everything else (auto-generated
splices, ferrules, wires) is **inferred** by following connections from
assigned components until a fixpoint. A component whose neighbors sit on
different sheets is ambiguous and must be assigned explicitly; a component
with no chain to any assigned component cannot be placed. Both are errors --
consistent with `--strict`, a sheet definition never silently drops or
misplaces a component.

A connection crossing sheets is drawn on the **cable's** sheet, ending in a
stub: a reduced copy of the far connector showing only the referenced pins,
typed ``⇒ <sheet>`` so the reader knows where to continue. Mates crossing
sheets get stubs the same way.
"""

import copy
from typing import Dict, List, Optional

from wireviz.DataClasses import Connector, MatePin, Side
from wireviz.Harness import Harness
from wireviz.wv_errors import SheetError

STUB_TYPE_PREFIX = "⇒ "  # ⇒ <sheet name>


def _validate(harness: Harness, sheets: dict) -> Dict[str, str]:
    """Check the definition's structure; return designator -> sheet."""
    if not isinstance(sheets, dict) or not sheets:
        raise SheetError(
            f"sheets must be a non-empty mapping of sheet name to a list of "
            f"designators, got {sheets!r}"
        )
    known = harness.connectors.keys() | harness.cables.keys()
    assignment = {}
    unknown = []
    for sheet, members in sheets.items():
        if not isinstance(sheet, str):
            raise SheetError(f"sheet names must be strings, got {sheet!r}")
        if not isinstance(members, list) or not all(
            isinstance(m, str) for m in members
        ):
            raise SheetError(
                f"sheet {sheet!r} must list designators, got {members!r}"
            )
        for name in members:
            if name in assignment:
                raise SheetError(
                    f"{name} is assigned to both sheet "
                    f"{assignment[name]!r} and sheet {sheet!r}",
                    components=[name],
                )
            if name not in known:
                unknown.append(name)
            assignment[name] = sheet
    if unknown:
        unknown = list(dict.fromkeys(unknown))
        raise SheetError(
            f"sheets definition references unknown designators: "
            f"{', '.join(unknown)}",
            components=unknown,
        )
    return assignment


def _adjacency(harness: Harness) -> Dict[str, set]:
    """Component graph: cable<->connector via connections, plus mates."""
    adjacent = {name: set() for name in harness.connectors}
    adjacent.update({name: set() for name in harness.cables})

    def link(a: Optional[str], b: Optional[str]) -> None:
        if a is not None and b is not None:
            adjacent[a].add(b)
            adjacent[b].add(a)

    for cable in harness.cables.values():
        for connection in cable.connections:
            link(cable.name, connection.from_name)
            link(cable.name, connection.to_name)
    for mate in harness.mates:
        link(mate.from_name, mate.to_name)
    return adjacent


def assign(harness: Harness, sheets: dict) -> Dict[str, str]:
    """Full designator -> sheet map, inferring unassigned components.

    Repeatedly assigns each unassigned component to the sheet its assigned
    neighbors agree on, until nothing changes. Disagreement is ambiguity;
    components left over touch no assigned component at all.
    """
    assignment = _validate(harness, sheets)
    adjacent = _adjacency(harness)
    unassigned = [name for name in adjacent if name not in assignment]

    while True:
        progress = False
        ambiguous = []
        for name in list(unassigned):
            neighbor_sheets = {
                assignment[n] for n in adjacent[name] if n in assignment
            }
            if len(neighbor_sheets) > 1:
                ambiguous.append((name, sorted(neighbor_sheets)))
            elif len(neighbor_sheets) == 1:
                assignment[name] = next(iter(neighbor_sheets))
                unassigned.remove(name)
                progress = True
        if ambiguous:
            detail = "; ".join(
                f"{name} touches sheets {', '.join(names)}"
                for name, names in ambiguous
            )
            raise SheetError(
                f"cannot infer a sheet: {detail}. Assign these components "
                f"explicitly.",
                components=[name for name, _ in ambiguous],
            )
        if not progress:
            break

    if unassigned:
        raise SheetError(
            f"components not connected to any assigned component: "
            f"{', '.join(unassigned)}. Assign them to a sheet explicitly.",
            components=list(unassigned),
        )
    return assignment


def _stub(original: Connector, pins: List, sheet: str) -> Connector:
    """A reduced copy of a far-sheet connector: referenced pins only."""
    if original.style == "simple" or not pins:
        return Connector(
            name=original.name,
            style="simple",
            type=f"{STUB_TYPE_PREFIX}{sheet}",
        )
    pinlabels = []
    if original.pinlabels:
        for pin in pins:
            index = original.pins.index(pin)
            pinlabels.append(
                original.pinlabels[index]
                if index < len(original.pinlabels)
                else ""
            )
    return Connector(
        name=original.name,
        pins=list(pins),
        pinlabels=pinlabels if any(pinlabels) else [],
        type=f"{STUB_TYPE_PREFIX}{sheet}",
        show_pincount=False,
    )


def split(harness: Harness, sheets: dict) -> "Dict[str, Harness]":
    """One sub-harness per sheet, in definition order.

    Components keep their identity and order; a connection whose far
    connector lives on another sheet is drawn against a stub carrying the
    same designator, so wire labels read identically on every sheet. A
    harness split onto a single sheet reproduces the original graph
    byte-identically.
    """
    assignment = assign(harness, sheets)
    result = {}

    for sheet in sheets:
        sub = Harness(
            metadata=copy.deepcopy(harness.metadata),
            options=copy.deepcopy(harness.options),
            tweak=copy.deepcopy(harness.tweak),
        )

        # components of this sheet, in original insertion order
        for name, connector in harness.connectors.items():
            if assignment[name] == sheet:
                connector = copy.deepcopy(connector)
                connector.ports_left = False
                connector.ports_right = False
                connector.visible_pins = {}
                # loop pins are made visible at construction, not by connect;
                # re-activate them so hide_disconnected_pins can't hide a loop
                for loop in connector.loops:
                    for pin in loop:
                        connector.activate_pin(pin, None)
                sub.connectors[name] = connector
        for name, cable in harness.cables.items():
            if assignment[name] == sheet:
                cable = copy.deepcopy(cable)
                cable.connections = []
                sub.cables[name] = cable

        # collect far-sheet references so each gets one stub with all pins
        stub_pins = {}  # far designator -> ordered pin list

        def reference(name: Optional[str], pin=None) -> None:
            if name is None or assignment[name] == sheet:
                return
            pins = stub_pins.setdefault(name, [])
            if pin is not None and pin not in pins:
                pins.append(pin)

        for name, cable in harness.cables.items():
            if assignment[name] != sheet:
                continue
            for connection in cable.connections:
                reference(connection.from_name, connection.from_pin)
                reference(connection.to_name, connection.to_pin)
        for mate in harness.mates:
            sides = {assignment[mate.from_name], assignment[mate.to_name]}
            if sheet not in sides:
                continue
            if isinstance(mate, MatePin):
                reference(mate.from_name, mate.from_pin)
                reference(mate.to_name, mate.to_pin)
            else:
                reference(mate.from_name)
                reference(mate.to_name)

        for name, pins in stub_pins.items():
            original = harness.connectors[name]
            ordered = [p for p in original.pins if p in pins]
            sub.connectors[name] = _stub(original, ordered, assignment[name])

        # Reconnect this sheet's cables from the already-resolved connections.
        # Harness.connect() is deliberately bypassed: it resolves pin labels
        # to pin ids, and re-running that on resolved ids can remap or reject
        # a pin id that happens to match another pin's label.
        for name, cable in harness.cables.items():
            if assignment[name] != sheet:
                continue
            for c in cable.connections:
                sub.cables[name].connect(
                    c.from_name, c.from_pin, c.via_port, c.to_name, c.to_pin
                )
                if c.from_name in sub.connectors:
                    sub.connectors[c.from_name].activate_pin(c.from_pin, Side.RIGHT)
                if c.to_name in sub.connectors:
                    sub.connectors[c.to_name].activate_pin(c.to_pin, Side.LEFT)

        # mates with at least one end on this sheet
        for mate in harness.mates:
            sides = {assignment[mate.from_name], assignment[mate.to_name]}
            if sheet not in sides:
                continue
            if isinstance(mate, MatePin):
                sub.add_mate_pin(
                    mate.from_name, mate.from_pin, mate.to_name, mate.to_pin,
                    mate.shape,
                )
            else:
                sub.add_mate_component(mate.from_name, mate.to_name, mate.shape)

        result[sheet] = sub

    return result
