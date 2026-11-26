"""The first, deliberately narrow, executable self-wake vertical slice.

This module proves one protocol invariant only:

    observation -> wake candidate -> hold / no escalation -> durable replay

It intentionally contains no cognition adapter, continuation policy, executor,
verifier, CPC implementation, or authority-bearing action path.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol, Self
from uuid import NAMESPACE_URL, uuid5

EVENT_SCHEMA_VERSION = 1
_ID_NAMESPACE = uuid5(NAMESPACE_URL, "https://github.com/mutual-mind/self-wake")


class EventKind(StrEnum):
    """Durable event kinds implemented by the first vertical slice."""

    OBSERVATION_RECORDED = "observation.recorded"
    CANDIDATE_CREATED = "candidate.created"
    ACTIVATION_DECIDED = "activation.decided"


class DecisionKind(StrEnum):
    """Activation dispositions implemented by the first vertical slice."""

    HOLD = "hold"


class EventConflictError(RuntimeError):
    """A stable event identity was reused for different causal content."""


class ReplayError(RuntimeError):
    """A durable event stream violates the implemented causal invariants."""


def _require_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_tier(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    _require_text("timestamp", value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ReplayError("durable timestamp is not valid ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReplayError("durable timestamps must be timezone-aware")
    return parsed.astimezone(UTC)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("event data must be finite JSON data") from exc


def _json_object_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    encoded = _canonical_json(dict(value))
    decoded = json.loads(encoded)
    if not isinstance(
        decoded, dict
    ):  # defensive; Mapping should always encode as an object
        raise TypeError("payload must encode as a JSON object")
    return decoded


def _stable_id(kind: str, *parts: str) -> str:
    for index, part in enumerate(parts):
        _require_text(f"identity part {index}", part)
    material = "\x00".join((kind, *parts))
    return str(uuid5(_ID_NAMESPACE, material))


def _data_text(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReplayError(f"{key} must be a non-empty string")
    return value


def _data_tier(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReplayError(f"{key} must be a non-negative integer")
    return value


@dataclass(frozen=True, slots=True)
class Observation:
    """A fact received from the world or the system itself."""

    observation_id: str
    source: str
    observed_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)
    deduplication_key: str | None = None

    def __post_init__(self) -> None:
        _require_text("observation_id", self.observation_id)
        _require_text("source", self.source)
        _utc_iso(self.observed_at)
        object.__setattr__(
            self, "payload", MappingProxyType(_json_object_copy(self.payload))
        )
        if self.deduplication_key is not None:
            _require_text("deduplication_key", self.deduplication_key)


@dataclass(frozen=True, slots=True)
class WakeCandidate:
    """A durable claim that an observation may deserve cognition."""

    candidate_id: str
    observation_id: str
    locus: str
    reason: str

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("observation_id", self.observation_id)
        _require_text("locus", self.locus)
        _require_text("candidate reason", self.reason)


@dataclass(frozen=True, slots=True)
class ActivationDecision:
    """The admission result for one wake candidate."""

    decision_id: str
    candidate_id: str
    locus: str
    current_tier: int
    target_tier: int
    kind: DecisionKind
    reason: str

    def __post_init__(self) -> None:
        _require_text("decision_id", self.decision_id)
        _require_text("candidate_id", self.candidate_id)
        _require_text("locus", self.locus)
        _require_tier("current_tier", self.current_tier)
        _require_tier("target_tier", self.target_tier)
        _require_text("decision reason", self.reason)
        if not isinstance(self.kind, DecisionKind):
            raise TypeError("kind must be a DecisionKind")
        if self.kind is DecisionKind.HOLD and self.target_tier != self.current_tier:
            raise ValueError(
                "a hold decision must preserve the current activation tier"
            )


@dataclass(frozen=True, slots=True)
class StoredEvent:
    """One append-only event from the durable causal trace."""

    sequence: int
    event_id: str
    kind: EventKind
    schema_version: int
    recorded_at: datetime
    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence <= 0
        ):
            raise ValueError("sequence must be a positive integer")
        _require_text("event_id", self.event_id)
        if not isinstance(self.kind, EventKind):
            raise TypeError("kind must be an EventKind")
        if self.schema_version != EVENT_SCHEMA_VERSION:
            raise ReplayError(
                f"unsupported event schema version: {self.schema_version}"
            )
        _utc_iso(self.recorded_at)
        object.__setattr__(self, "data", MappingProxyType(_json_object_copy(self.data)))


class ActivationPolicy(Protocol):
    """Minimal admission-policy boundary needed by this vertical slice."""

    def decide(self, candidate: WakeCandidate, current_tier: int) -> ActivationDecision:
        """Return a bounded activation decision for ``candidate``."""


@dataclass(frozen=True, slots=True)
class HoldPolicy:
    """A deterministic policy that explicitly declines escalation."""

    reason: str

    def __post_init__(self) -> None:
        _require_text("hold reason", self.reason)

    def decide(self, candidate: WakeCandidate, current_tier: int) -> ActivationDecision:
        _require_tier("current_tier", current_tier)
        return ActivationDecision(
            decision_id=_stable_id("activation-decision", candidate.candidate_id),
            candidate_id=candidate.candidate_id,
            locus=candidate.locus,
            current_tier=current_tier,
            target_tier=current_tier,
            kind=DecisionKind.HOLD,
            reason=self.reason,
        )


class SQLiteEventStore:
    """A dependency-free, append-only, durable event store.

    Stable event identities make retries idempotent when their causal content is
    byte-for-byte equivalent after canonical JSON encoding. Reusing an identity
    for different content is a conflict rather than an update.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, timeout=10.0)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = FULL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                schema_version INTEGER NOT NULL,
                recorded_at TEXT NOT NULL,
                data_json TEXT NOT NULL
            )
            """
        )
        self._connection.commit()
        self._closed = False

    def append(
        self,
        *,
        event_id: str,
        kind: EventKind,
        data: Mapping[str, Any],
    ) -> StoredEvent:
        self._ensure_open()
        _require_text("event_id", event_id)
        data_json = _canonical_json(dict(data))
        recorded_at = _utc_iso(datetime.now(UTC))

        try:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    INSERT INTO events (
                        event_id, kind, schema_version, recorded_at, data_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        kind.value,
                        EVENT_SCHEMA_VERSION,
                        recorded_at,
                        data_json,
                    ),
                )
                sequence = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            existing = self._connection.execute(
                """
                SELECT sequence, event_id, kind, schema_version, recorded_at, data_json
                FROM events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()
            if existing is None:
                raise
            if (
                existing["kind"] == kind.value
                and existing["schema_version"] == EVENT_SCHEMA_VERSION
                and existing["data_json"] == data_json
            ):
                return self._row_to_event(existing)
            raise EventConflictError(
                f"event identity {event_id!r} already exists with different content"
            ) from exc

        row = self._connection.execute(
            """
            SELECT sequence, event_id, kind, schema_version, recorded_at, data_json
            FROM events
            WHERE sequence = ?
            """,
            (sequence,),
        ).fetchone()
        if row is None:  # pragma: no cover - SQLite must return the row just inserted
            raise RuntimeError("inserted event could not be read back")
        return self._row_to_event(row)

    def read_all(self) -> tuple[StoredEvent, ...]:
        self._ensure_open()
        rows = self._connection.execute(
            """
            SELECT sequence, event_id, kind, schema_version, recorded_at, data_json
            FROM events
            ORDER BY sequence ASC
            """
        ).fetchall()
        return tuple(self._row_to_event(row) for row in rows)

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def __enter__(self) -> Self:
        self._ensure_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("event store is closed")

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> StoredEvent:
        try:
            kind = EventKind(row["kind"])
        except ValueError as exc:
            raise ReplayError(f"unknown event kind: {row['kind']!r}") from exc
        try:
            data = json.loads(row["data_json"])
        except json.JSONDecodeError as exc:
            raise ReplayError("stored event data is not valid JSON") from exc
        if not isinstance(data, dict):
            raise ReplayError("stored event data must be a JSON object")
        return StoredEvent(
            sequence=int(row["sequence"]),
            event_id=str(row["event_id"]),
            kind=kind,
            schema_version=int(row["schema_version"]),
            recorded_at=_parse_utc(str(row["recorded_at"])),
            data=data,
        )


class SelfWakeRuntime:
    """The minimum runtime needed to produce a durable hold decision."""

    def __init__(
        self,
        *,
        store: SQLiteEventStore,
        policy: ActivationPolicy,
        locus: str = "system",
        current_tier: int = 1,
    ) -> None:
        _require_text("locus", locus)
        _require_tier("current_tier", current_tier)
        self._store = store
        self._policy = policy
        self._locus = locus
        self._current_tier = current_tier

    def ingest(
        self,
        observation: Observation,
        *,
        candidate_reason: str,
    ) -> ActivationDecision:
        """Persist an observation, derive a candidate, and admit it.

        Each stage is appended independently. A retry after interruption is safe
        when it presents the same stable observation identity and the same causal
        content; already-written events are returned rather than duplicated.
        """

        _require_text("candidate_reason", candidate_reason)
        self._store.append(
            event_id=f"observation:{observation.observation_id}",
            kind=EventKind.OBSERVATION_RECORDED,
            data=_observation_data(observation),
        )

        candidate = WakeCandidate(
            candidate_id=_stable_id("wake-candidate", observation.observation_id),
            observation_id=observation.observation_id,
            locus=self._locus,
            reason=candidate_reason,
        )
        self._store.append(
            event_id=f"candidate:{candidate.candidate_id}",
            kind=EventKind.CANDIDATE_CREATED,
            data=_candidate_data(candidate),
        )

        decision = self._policy.decide(candidate, self._current_tier)
        self._validate_policy_output(candidate, decision)
        self._store.append(
            event_id=f"decision:{decision.decision_id}",
            kind=EventKind.ACTIVATION_DECIDED,
            data=_decision_data(decision),
        )
        return decision

    def _validate_policy_output(
        self,
        candidate: WakeCandidate,
        decision: ActivationDecision,
    ) -> None:
        if decision.candidate_id != candidate.candidate_id:
            raise ValueError("policy decision refers to a different candidate")
        if decision.locus != candidate.locus:
            raise ValueError("policy decision refers to a different activation locus")
        if decision.current_tier != self._current_tier:
            raise ValueError("policy decision changed the declared current tier")


def _observation_data(observation: Observation) -> dict[str, Any]:
    return {
        "observation_id": observation.observation_id,
        "source": observation.source,
        "observed_at": _utc_iso(observation.observed_at),
        "payload": dict(observation.payload),
        "deduplication_key": observation.deduplication_key,
    }


def _candidate_data(candidate: WakeCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "observation_id": candidate.observation_id,
        "locus": candidate.locus,
        "reason": candidate.reason,
    }


def _decision_data(decision: ActivationDecision) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "candidate_id": decision.candidate_id,
        "locus": decision.locus,
        "current_tier": decision.current_tier,
        "target_tier": decision.target_tier,
        "kind": decision.kind.value,
        "reason": decision.reason,
    }


def _observation_from_data(data: Mapping[str, Any]) -> Observation:
    payload = data.get("payload")
    if not isinstance(payload, dict):
        raise ReplayError("observation payload must be a JSON object")
    deduplication_key = data.get("deduplication_key")
    if deduplication_key is not None and not isinstance(deduplication_key, str):
        raise ReplayError("deduplication_key must be a string or null")
    observed_at = _data_text(data, "observed_at")
    try:
        return Observation(
            observation_id=_data_text(data, "observation_id"),
            source=_data_text(data, "source"),
            observed_at=_parse_utc(observed_at),
            payload=payload,
            deduplication_key=deduplication_key,
        )
    except ValueError as exc:
        raise ReplayError("invalid observation event") from exc


def _candidate_from_data(data: Mapping[str, Any]) -> WakeCandidate:
    try:
        return WakeCandidate(
            candidate_id=_data_text(data, "candidate_id"),
            observation_id=_data_text(data, "observation_id"),
            locus=_data_text(data, "locus"),
            reason=_data_text(data, "reason"),
        )
    except ValueError as exc:
        raise ReplayError("invalid candidate event") from exc


def _decision_from_data(data: Mapping[str, Any]) -> ActivationDecision:
    try:
        kind = DecisionKind(_data_text(data, "kind"))
        return ActivationDecision(
            decision_id=_data_text(data, "decision_id"),
            candidate_id=_data_text(data, "candidate_id"),
            locus=_data_text(data, "locus"),
            current_tier=_data_tier(data, "current_tier"),
            target_tier=_data_tier(data, "target_tier"),
            kind=kind,
            reason=_data_text(data, "reason"),
        )
    except ValueError as exc:
        raise ReplayError("invalid activation decision event") from exc


@dataclass(frozen=True, slots=True)
class ReplayProjection:
    """State reconstructed solely from the durable event stream."""

    observations: Mapping[str, Observation]
    candidates: Mapping[str, WakeCandidate]
    decisions: Mapping[str, ActivationDecision]
    candidate_by_observation: Mapping[str, str]
    decision_by_candidate: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "observations", MappingProxyType(dict(self.observations))
        )
        object.__setattr__(self, "candidates", MappingProxyType(dict(self.candidates)))
        object.__setattr__(self, "decisions", MappingProxyType(dict(self.decisions)))
        object.__setattr__(
            self,
            "candidate_by_observation",
            MappingProxyType(dict(self.candidate_by_observation)),
        )
        object.__setattr__(
            self,
            "decision_by_candidate",
            MappingProxyType(dict(self.decision_by_candidate)),
        )

    def decision_for_observation(
        self, observation_id: str
    ) -> ActivationDecision | None:
        candidate_id = self.candidate_by_observation.get(observation_id)
        if candidate_id is None:
            return None
        decision_id = self.decision_by_candidate.get(candidate_id)
        if decision_id is None:
            return None
        return self.decisions[decision_id]


def replay(events: Iterable[StoredEvent]) -> ReplayProjection:
    """Reconstruct the implemented protocol state from append-only events."""

    observations: dict[str, Observation] = {}
    candidates: dict[str, WakeCandidate] = {}
    decisions: dict[str, ActivationDecision] = {}
    candidate_by_observation: dict[str, str] = {}
    decision_by_candidate: dict[str, str] = {}
    previous_sequence = 0

    for event in events:
        if event.sequence <= previous_sequence:
            raise ReplayError("event sequence is not strictly increasing")
        previous_sequence = event.sequence

        if event.kind is EventKind.OBSERVATION_RECORDED:
            observation = _observation_from_data(event.data)
            if event.event_id != f"observation:{observation.observation_id}":
                raise ReplayError(
                    "observation event identity disagrees with its payload"
                )
            if observation.observation_id in observations:
                raise ReplayError("observation identity appears more than once")
            observations[observation.observation_id] = observation
            continue

        if event.kind is EventKind.CANDIDATE_CREATED:
            candidate = _candidate_from_data(event.data)
            if event.event_id != f"candidate:{candidate.candidate_id}":
                raise ReplayError("candidate event identity disagrees with its payload")
            observation = observations.get(candidate.observation_id)
            if observation is None:
                raise ReplayError("candidate refers to an observation not yet recorded")
            if candidate.candidate_id in candidates:
                raise ReplayError("candidate identity appears more than once")
            if candidate.observation_id in candidate_by_observation:
                raise ReplayError(
                    "first slice permits only one candidate per observation"
                )
            candidates[candidate.candidate_id] = candidate
            candidate_by_observation[candidate.observation_id] = candidate.candidate_id
            continue

        if event.kind is EventKind.ACTIVATION_DECIDED:
            decision = _decision_from_data(event.data)
            if event.event_id != f"decision:{decision.decision_id}":
                raise ReplayError("decision event identity disagrees with its payload")
            candidate = candidates.get(decision.candidate_id)
            if candidate is None:
                raise ReplayError("decision refers to a candidate not yet recorded")
            if decision.locus != candidate.locus:
                raise ReplayError("decision locus differs from candidate locus")
            if decision.decision_id in decisions:
                raise ReplayError("decision identity appears more than once")
            if decision.candidate_id in decision_by_candidate:
                raise ReplayError("first slice permits only one decision per candidate")
            decisions[decision.decision_id] = decision
            decision_by_candidate[decision.candidate_id] = decision.decision_id
            continue

        raise ReplayError(f"unhandled event kind: {event.kind}")

    return ReplayProjection(
        observations=observations,
        candidates=candidates,
        decisions=decisions,
        candidate_by_observation=candidate_by_observation,
        decision_by_candidate=decision_by_candidate,
    )
