from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from selfwake import (
    DecisionKind,
    EventConflictError,
    EventKind,
    HoldPolicy,
    Observation,
    SelfWakeRuntime,
    SQLiteEventStore,
    replay,
)


class SimulatedInterruption(RuntimeError):
    pass


class InterruptBeforeCandidateStore(SQLiteEventStore):
    """Fail once after the observation event has been committed."""

    def __init__(self, path: str | Path) -> None:
        super().__init__(path)
        self._append_calls = 0

    def append(self, **kwargs):  # type: ignore[no-untyped-def]
        self._append_calls += 1
        if self._append_calls == 2:
            raise SimulatedInterruption
        return super().append(**kwargs)


class DurableHoldTests(unittest.TestCase):
    def test_observation_candidate_hold_is_durable_and_replayable(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "events.sqlite3"
            observation = Observation(
                observation_id="obs-001",
                source="test.sensor",
                observed_at=datetime(2026, 11, 26, 10, 0, tzinfo=UTC),
                payload={"value": 0.12, "baseline": 0.10},
                deduplication_key="test.sensor:value:2026-11-26T10:00Z",
            )

            with SQLiteEventStore(database) as store:
                runtime = SelfWakeRuntime(
                    store=store,
                    policy=HoldPolicy(
                        "Novelty is below the configured escalation threshold."
                    ),
                    locus="sensor-watch",
                    current_tier=1,
                )
                decision = runtime.ingest(
                    observation,
                    candidate_reason="The sensor changed relative to maintained state.",
                )

                self.assertEqual(decision.kind, DecisionKind.HOLD)
                self.assertEqual(decision.current_tier, 1)
                self.assertEqual(decision.target_tier, 1)
                self.assertEqual(
                    [event.kind for event in store.read_all()],
                    [
                        EventKind.OBSERVATION_RECORDED,
                        EventKind.CANDIDATE_CREATED,
                        EventKind.ACTIVATION_DECIDED,
                    ],
                )

            with SQLiteEventStore(database) as reopened:
                projection = replay(reopened.read_all())

            replayed = projection.decision_for_observation("obs-001")
            self.assertIsNotNone(replayed)
            assert replayed is not None
            self.assertEqual(replayed, decision)
            self.assertEqual(
                replayed.reason,
                "Novelty is below the configured escalation threshold.",
            )

    def test_restart_resumes_after_interruption_between_durable_stages(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "events.sqlite3"
            observation = Observation(
                observation_id="obs-interrupted",
                source="test.process",
                observed_at=datetime(2026, 11, 26, 10, 3, tzinfo=UTC),
                payload={"state": "changed"},
            )

            with InterruptBeforeCandidateStore(database) as interrupted_store:
                runtime = SelfWakeRuntime(
                    store=interrupted_store,
                    policy=HoldPolicy("The change does not justify escalation."),
                )
                with self.assertRaises(SimulatedInterruption):
                    runtime.ingest(
                        observation,
                        candidate_reason="A process state changed.",
                    )
                self.assertEqual(len(interrupted_store.read_all()), 1)

            with SQLiteEventStore(database) as resumed_store:
                runtime = SelfWakeRuntime(
                    store=resumed_store,
                    policy=HoldPolicy("The change does not justify escalation."),
                )
                decision = runtime.ingest(
                    observation,
                    candidate_reason="A process state changed.",
                )
                events = resumed_store.read_all()
                projection = replay(events)

            self.assertEqual(len(events), 3)
            self.assertEqual(
                projection.decision_for_observation("obs-interrupted"), decision
            )

    def test_retry_is_idempotent_and_does_not_duplicate_the_trace(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "events.sqlite3"
            observation = Observation(
                observation_id="obs-retry",
                source="test.timer",
                observed_at=datetime(2026, 11, 26, 10, 5, tzinfo=UTC),
                payload={"tick": 1},
            )

            with SQLiteEventStore(database) as store:
                runtime = SelfWakeRuntime(
                    store=store,
                    policy=HoldPolicy("No maintained state requires escalation."),
                )
                first = runtime.ingest(
                    observation,
                    candidate_reason="A timer observation requires admission evaluation.",
                )
                second = runtime.ingest(
                    observation,
                    candidate_reason="A timer observation requires admission evaluation.",
                )

                self.assertEqual(first, second)
                self.assertEqual(len(store.read_all()), 3)

    def test_retry_cannot_rewrite_an_existing_causal_claim(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "events.sqlite3"
            observation = Observation(
                observation_id="obs-conflict",
                source="test.file",
                observed_at=datetime(2026, 11, 26, 10, 10, tzinfo=UTC),
                payload={"path": "/tmp/example"},
            )

            with SQLiteEventStore(database) as store:
                runtime = SelfWakeRuntime(
                    store=store,
                    policy=HoldPolicy("No escalation is justified."),
                )
                runtime.ingest(
                    observation,
                    candidate_reason="The file metadata changed.",
                )

                with self.assertRaises(EventConflictError):
                    runtime.ingest(
                        observation,
                        candidate_reason="A different retrospective explanation.",
                    )

                self.assertEqual(len(store.read_all()), 3)


if __name__ == "__main__":
    unittest.main()
