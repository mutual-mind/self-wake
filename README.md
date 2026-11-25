# self-wake

**A small runtime protocol for endogenous, bounded, verifiable AI waking.**

self-wake defines how a persistent AI system can remain mostly quiescent, notice meaningful changes, decide whether cognition is warranted, instantiate only the cognition needed, make bounded causal commitments, verify consequences, and return to quiescence.

It is not an agent framework, scheduler, workflow engine, memory system, or model wrapper.

It is the layer that answers a prior question:

> **Should cognition happen now at all; if so, what kind, under what authority, and how do we know what actually happened?**

This repository begins with this README intentionally. The protocol should be understandable before there is an implementation.

---

## 1. Motivation

Most agent systems begin after activation.

A timer fires. A message arrives. A workflow starts. An agent is invoked. Once running, the system is structurally biased toward doing something.

Persistent autonomous systems need a layer before that.

A self-waking system should be able to:

- observe without invoking expensive cognition;
- accumulate and metabolize state cheaply;
- distinguish novelty from noise, echo, and repetition;
- decide that nothing currently deserves cognition;
- select an appropriate cognition tier when something does;
- bound the authority, time, tools, and effect classes of that cognition;
- separate proposal from execution when consequences warrant it;
- verify outcomes independently enough to detect failure or self-confirmation;
- persist enough state that interruption and restart do not duplicate commitments;
- preserve slack for future discovery rather than converting every signal into urgency.

The central design premise is:

> **Wake is a decision, not merely an event.**

An event may create a wake candidate. It does not, by itself, require a cognitive run.

---

## 2. Scope

self-wake owns the transition between **quiescent persistence** and **bounded cognition**.

It defines:

1. how observations become state deltas;
2. how state deltas can produce wake candidates;
3. how wake candidates are admitted, deferred, merged, suppressed, or rejected;
4. how an admitted wake receives an authority envelope;
5. how cognition produces proposals or portfolios;
6. how execution is bounded;
7. how outcomes are verified;
8. how verified transitions update persistent state;
9. how the system safely returns to quiescence.

self-wake does **not** prescribe:

- a particular language model;
- a particular agent framework;
- a particular database;
- a particular scheduler;
- a particular tool protocol;
- a particular memory architecture;
- a particular wake policy;
- a particular planning algorithm;
- a particular execution backend.

Those are adapters or policies around the protocol.

---

## 3. Self-wake versus policy

The **self-wake runtime** determines whether and how cognition becomes active.

A **wake policy** determines how wake candidates are evaluated.

A **continuation policy** determines what causal commitments an active cognition should make.

The **Causal Portfolio Controller (CPC)** is one possible continuation policy. CPC is not the definition of self-waking.

A minimal deployment might use a deterministic threshold policy:

> Wake when a monitored variable crosses a boundary.

A richer deployment might use CPC to reason over consequence, slack, recoverability, common-cause groups, cut sets, competing opportunities, and exploration preservation.

Both should fit the same runtime protocol.

---

## 4. Primitive objects

### Observation

A fact received from the world or from the system itself.

Examples include a file change, message arrival, sensor delta, timer, process failure, dependency recovery, explicit request for attention, or completion of some other computation.

An observation is not yet an interpretation.

### StateDelta

A normalized statement of what changed relative to known state.

Useful fields may include source, previous value, current value, confidence, timestamp, novelty estimate, causal provenance, and a deduplication key.

### WakeCandidate

A claim that some state delta may deserve cognition.

A candidate should carry enough information to evaluate it without immediately launching cognition.

Useful fields may include reason, urgency, expected consequence, uncertainty, expiration, estimated cognition cost, common-cause group, recent related wakes, and requested cognition tier.

### WakeDecision

The runtime's disposition of one or more wake candidates.

At minimum:

- IGNORE
- DEFER
- MERGE
- WAKE

A valid WakeDecision may explicitly conclude:

> Nothing deserves cognition now.

That is a first-class successful outcome.

### AuthorityEnvelope

The maximum authority granted to a cognitive run.

It may constrain:

- wall-clock duration;
- model or cognition tier;
- tool-call count;
- token or monetary budget;
- readable resources;
- writable resources;
- allowed effect classes;
- maximum reversibility class;
- whether human approval is required;
- whether independent verification is required.

Cognition may act within this envelope. It may not enlarge it.

### CognitiveRun

A bounded instantiation of cognition created by an admitted wake.

A cognitive run may investigate, estimate, propose, plan, select a portfolio, request execution, or decide that no intervention is justified.

The runtime owns its envelope and lifecycle.

### Portfolio

A set of proposed causal commitments considered together rather than independently.

A portfolio may contain no interventions, one intervention, several compatible interventions, investigations, reversible experiments, or deferred commitments.

The portfolio abstraction is optional for simple policies but central to CPC.

### Intervention

A bounded action with declared intended effects and constraints.

An intervention should be identifiable and idempotent enough that restart does not accidentally execute it twice.

### Outcome

The observed result of an attempted intervention.

An outcome is not assumed to equal the intended effect.

### Verification

An assessment of whether the claimed outcome is supported by observation.

Verification should be logically separable from proposal and, when consequence warrants it, operationally independent.

### VerifiedTransition

The durable state update produced after verification.

This is the point at which the runtime may safely revise its persistent model of the world.

---

## 5. Governing cycle

~~~text
              ┌──────────────────┐
              │      WORLD       │
              └────────┬─────────┘
                       │
                 observations
                       │
                       ▼
              ┌──────────────────┐
              │ STATE METABOLISM │
              └────────┬─────────┘
                       │
                  state deltas
                       │
                       ▼
              ┌──────────────────┐
              │ WAKE CANDIDATES  │
              └────────┬─────────┘
                       │
                  wake policy
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       ignore        defer         wake
          │            │            │
          └──────► quiescence       ▼
                                ┌───────────────┐
                                │ COGNITIVE RUN │
                                └───────┬───────┘
                                        │
                              proposal / portfolio
                                        │
                       ┌────────────────┼───────────────┐
                       │                │               │
                       ▼                ▼               ▼
                    no-op          investigate       execute
                       │                │               │
                       └────────────────┼───────────────┘
                                        ▼
                                ┌──────────────┐
                                │ VERIFICATION │
                                └───────┬──────┘
                                        │
                               verified transition
                                        │
                                        ▼
                                      WORLD
~~~

There are legitimate exits back to quiescence at multiple stages.

The system is not required to reach execution.

---

## 6. Protocol invariants

An implementation claiming conformance with self-wake should preserve the following invariants.

### Observation does not imply cognition

Receiving an event is not equivalent to waking.

### Cognition does not imply action

A cognitive run may legitimately conclude that no intervention is justified.

### Wake may conclude in quiescence

Ignoring, deferring, suppressing, merging, and no-op cognition are normal protocol outcomes, not failures.

### Authority is externally bounded

A cognitive run cannot expand its own authority envelope.

Any escalation requires a new decision by a component authorized to grant it.

### Consequential actions are identifiable

Interventions must carry stable identities or equivalent idempotency mechanisms sufficient to avoid duplicate causal commitments after retries or restart.

### State transitions are durable

The runtime must persist enough information to recover the causal stage it had reached before interruption.

### Replay is possible

Given the same durable inputs and deterministic policy components, wake admission and runtime transitions should be replayable for inspection.

Model-dependent cognition may be nondeterministic, but the surrounding causal record must remain inspectable.

### Proposal and verification are distinct roles

The component that proposes an intervention must not be treated as authoritative evidence that the intervention succeeded.

### Verification strength tracks consequence

Low-consequence reversible actions may need lightweight verification.

Irreversible or high-consequence actions require stronger, preferably independent verification.

### Slack is first-class

The runtime must permit preserving capacity, attention, uncertainty, and future option value.

It must not structurally force all available budget toward immediate action.

### Quiescence is a stable state

A healthy persistent system can spend most of its time doing almost nothing.

---

## 7. Authority model

A central purpose of self-wake is to prevent cognition from being synonymous with unrestricted agency.

Authority should be granted explicitly and minimally.

An illustrative envelope might look like:

~~~yaml
authority:
  cognition_tier: deep
  wall_seconds: 900
  max_tool_actions: 20

  effects:
    - read_only_observation
    - own_state
    - reversible_local_change

  forbidden_effects:
    - external_commitment
    - destructive_change

  verification:
    required: true
    independent: true
~~~

This schema is illustrative, not yet normative.

The important protocol property is that the runtime can answer:

> **What was this cognition allowed to do?**

before answering:

> **What did it choose to do?**

---

## 8. Wake sources

self-wake should support many sources without privileging any one transport.

Examples:

- filesystem events;
- timers;
- cron or systemd;
- database changes;
- MQTT;
- webhooks;
- inbox changes;
- sensor streams;
- process supervision;
- health checks;
- human messages;
- model-generated internal events;
- explicit continuation requests.

These are observation sources or input channels, not direct wake authorities. Adapters normalize them into observations.

Cron, systemd timers, MQTT, webhooks, sensor streams, and similar mechanisms must not directly invoke cognition merely because an event arrived. They only supply material from which low-level features, deltas, and other wake evidence are derived.

Whether cognition is warranted is evaluated endogenously from the resulting maintained state and wake evidence. A source therefore need not know, and must not decide, whether Self-Wake escalates to further feature extraction or higher cognition.

---

## 9. State metabolism

State metabolism is the cheap layer between raw observation and wake admission.

Its purpose is to reduce the amount of expensive cognition needed.

Possible responsibilities:

- normalize observations;
- deduplicate repeated events;
- debounce noisy sources;
- aggregate small changes;
- detect novelty;
- maintain rolling statistics;
- detect threshold crossings;
- group common causes;
- expire stale candidates;
- update cheap deterministic derived state;
- produce wake candidates.

This layer should be able to run continuously or frequently even when no model is active.

---

## 10. Wake admission

Wake admission asks:

> **Given the current state, candidate set, budget, and policy, should cognition instantiate now?**

Admission may consider consequence, urgency, novelty, uncertainty, reversibility, deadline, expected information gain, cognition cost, available slack, overlap with already-running work, common cause, recent wake history, and self-excitation risk.

Wake admission should be inspectable.

For every admitted or rejected candidate, the runtime should be able to preserve a reason sufficient for later audit.

---

## 11. Cognition tiers

A runtime may support several cognition tiers, for example:

1. deterministic rule;
2. cheap classifier;
3. lightweight model;
4. deep model;
5. adversarial or verifier model;
6. human participation.

A wake policy may escalate through tiers rather than jumping immediately to the most expensive cognition available.

The protocol does not prescribe the tiers. It requires the chosen tier to be represented in the authority envelope and durable trace.

---

## 12. CPC as a reference continuation policy

The Causal Portfolio Controller can be implemented as an optional policy package hosted by self-wake.

Its governing idea is:

> **Protect enough recoverability to keep choosing, while using that recoverability to discover and create futures worth choosing.**

A CPC policy may reason over:

- consequence;
- slack;
- recoverability;
- coverage;
- cut sets;
- common-cause groups;
- conflicting commitments;
- exploration value;
- option value;
- false urgency;
- self-excitation;
- verification availability.

Its canonical cycle is:

~~~text
sense / discover
        ↓
estimate
        ↓
select constrained portfolio
        ↓
bounded delegate / execute
        ↓
independently verify
        ↓
update
~~~

CPC remains optional.

self-wake must still be useful with simpler policies.

---

## 13. Persistence and replay

The protocol should be event-sourced or event-source-compatible.

A durable trace should be able to reconstruct:

- what was observed;
- what changed;
- which wake candidates existed;
- why a wake was admitted or rejected;
- what authority was granted;
- what cognition produced;
- what interventions were requested;
- which interventions actually executed;
- what outcomes were observed;
- what was verified;
- what state transition followed.

The durable trace is not merely logging.

It is part of causal correctness.

---

## 14. Crash and restart semantics

A persistent system must assume interruption.

After restart, it should be possible to determine whether a causal commitment was:

- never started;
- started but unresolved;
- completed but unverified;
- verified and committed.

The runtime must not silently repeat an intervention merely because the cognitive process that requested it disappeared.

Execution backends should expose stable intervention identities and completion records wherever possible.

---

## 15. Verification

Verification exists because proposal, execution, and reality can diverge.

Verification may inspect process state, filesystem state, API responses, external observations, independent sensors, checksums, model-independent predicates, a separately instantiated verifier, or human confirmation.

The verifier should answer a narrower question than the planner:

> **What actually changed, and does the evidence support the claimed outcome?**

Where independence is impossible, the limitation should be explicit.

---

## 16. Self-excitation and echo suppression

A self-waking system can accidentally wake on the consequences of its own waking.

Implementations should therefore track causal provenance sufficiently to distinguish:

- new exogenous information;
- expected consequences of recent actions;
- repeated observations;
- delayed echoes;
- state changes produced by the runtime itself.

A wake policy should be able to suppress or discount self-generated echoes while still noticing unexpected consequences.

---

## 17. Minimal conformance

A system minimally conforms to the self-wake protocol if it can demonstrate all of the following:

1. observations can be ingested without automatically invoking model cognition;
2. observations can produce explicit wake candidates;
3. a wake decision can reject or defer cognition;
4. an admitted wake receives a bounded authority envelope;
5. cognition can terminate without execution;
6. consequential interventions have stable identity or equivalent deduplication semantics;
7. outcomes are distinguished from intended effects;
8. verification is represented explicitly;
9. interruption does not require blindly replaying causal commitments;
10. durable traces are sufficient to inspect why a wake and subsequent transition occurred;
11. quiescence is treated as a normal persistent state.

This is intentionally behavioral.

A conforming implementation does not need to use any particular class hierarchy, database, model, or workflow engine.

---

## 18. Reference architecture

~~~text
sources
  ↓
observation normalizer
  ↓
state metabolizer
  ↓
candidate store
  ↓
wake policy
  ↓
runtime / authority gate
  ↓
cognition adapter
  ↓
continuation policy
  ↓
executor
  ↓
verifier
  ↓
event store / state projection
~~~

The reference implementation should favor:

- explicit typed objects;
- small interfaces;
- deterministic components where possible;
- a dependency-light core;
- pluggable persistence;
- event replay;
- testable policies;
- no hidden authority escalation.

---

## 19. Possible future Python package shape

This section is intentionally provisional.

~~~text
selfwake/
    events.py
    observations.py
    state.py
    candidates.py
    authority.py
    runtime.py
    policies/
        wake.py
        cpc.py
    cognition/
        base.py
    execution/
        base.py
    verification/
        base.py
    persistence/
        base.py
~~~

The package structure should be generated only after the protocol has stabilized enough that these boundaries are justified.

---

## 20. What self-wake is not

self-wake is not:

- a daemon that periodically calls an LLM;
- an always-running autonomous agent;
- a replacement for systemd, cron, Temporal, LangGraph, or other workflow engines;
- a generic memory framework;
- a prompt library;
- a requirement to use CPC;
- a claim that all decisions should be delegated to AI.

A system that merely invokes an agent every N minutes is scheduled cognition, not necessarily self-waking.

The missing property is **endogenous admission**: the system itself evaluates whether current conditions justify cognition, under explicit bounded authority.

---

## 21. Design test

The protocol should eventually make this question answerable:

> **Given an arbitrary persistent AI system, what must be true for us to say that it is genuinely using self-wake, rather than merely running periodically or reacting to events?**

If two independent implementations can read this specification and agree on the observable answer, the protocol is becoming precise enough.

---

## 22. Development order

Before implementation:

1. refine the ontology;
2. refine lifecycle and state-transition semantics;
3. define the authority envelope;
4. define persistence and idempotency requirements;
5. define minimal conformance tests;
6. specify extension points for wake and continuation policies;
7. specify CPC separately as the first rich reference policy.

Only then should the reference Python package be generated.

The README is therefore not downstream documentation.

**For now, the README is the system definition.**

