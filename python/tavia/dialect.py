"""The realtime wire dialect: standard event names and the standard session shape.

"ga" (the default) is the standard realtime event names and nested session; "beta" keeps the earlier names and the
flat session, for integrations written against it.
"""

from collections.abc import Mapping
from typing import Any, Literal

from tavia.generated.spec import DIALECT
from tavia.generated.types import SessionConfig, WireSession

__all__ = ["RENAMES", "Dialect", "standard_event", "standard_type", "wire_session"]

Dialect = Literal["ga", "beta"]
# Each beta server event type that has a different standard name, and that name.
RENAMES: Mapping[str, str] = DIALECT["renames"]
_PATHS: Mapping[str, str] = DIALECT["sessionPaths"]


def standard_type(kind: str) -> str:
    """The standard name of a server event type: a beta name maps to its standard one, others are unchanged."""
    return RENAMES.get(kind, kind)


def standard_event(event: dict) -> dict:
    """The event with its type under its standard name."""
    kind = event.get("type")
    if not isinstance(kind, str) or kind not in RENAMES:
        return event
    return {**event, "type": RENAMES[kind]}


def _set_at(target: dict, path: list[str], value: Any) -> None:
    for key in path[:-1]:
        target = target.setdefault(key, {})
    target[path[-1]] = value


def wire_session(session: SessionConfig, with_events: bool = False) -> WireSession:
    """Session options in the standard shape: audio settings under "audio", Tavia's own options under "tavia".

    with_events also asks for the turn events, which the friendly events are built from.
    """
    out: dict = {"type": "realtime"}
    for key, value in session.items():
        _set_at(out, _PATHS.get(key, f"{DIALECT['extrasKey']}.{key}").split("."), value)
    if with_events:
        _set_at(out, [DIALECT["extrasKey"], DIALECT["extrasField"]], True)
    return out  # type: ignore[return-value]
