# First implementation slice

This repository's first executable slice is intentionally smaller than the full
protocol described in `README.md`.

It proves one invariant from issue #2:

> An observation can arrive, become a wake candidate, and correctly end in
> **hold / no escalation** with a durable, replayable reason.

## Included

- typed `Observation`, `WakeCandidate`, and `ActivationDecision` objects;
- a deterministic `HoldPolicy`;
- a minimal `SelfWakeRuntime` that persists each causal stage;
- an append-only SQLite event store using only the Python standard library;
- stable event identities, idempotent equivalent retries, and conflict detection;
- replay that validates causal ordering and reconstructs the hold decision;
- tests that close and reopen the durable store before inspecting the result.

## Deliberately absent

- model or cognition adapters;
- CPC or another continuation policy;
- authority-bearing execution;
- intervention, outcome, and verification machinery;
- a daemon, scheduler, timer integration, or Flow deployment adapter;
- distribution or release packaging;
- claims of full protocol conformance.

Those boundaries remain open until a later vertical slice justifies them.

## Run the proof

```bash
python -m unittest discover -s tests -v
```

Python 3.11 or newer is required. No third-party runtime or test dependency
is required.
