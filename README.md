# self-wake

**A small runtime protocol for endogenous, graded, bounded, verifiable AI activation.**

self-wake defines how a persistent AI system can remain continuously perceptive at low cost, notice meaningful changes, endogenously escalate or de-escalate cognition, instantiate only the cognition currently justified, make bounded causal commitments, verify consequences, and return to lower-cost activation.

It is not an agent framework, scheduler, workflow engine, memory system, or model wrapper.

It is the layer that answers a prior question:

> **What level of cognition should be active now; under what authority; and how do we know what actually happened?**

This repository begins with this README intentionally. The protocol should be understandable before there is an implementation.

---

## 1. Motivation

Most agent systems begin after activation.

A timer fires. A message arrives. A workflow starts. An agent is invoked. Once running, the system is structurally biased toward doing something.

Persistent autonomous systems need a layer before that.

A self-waking system should be able to:

- continuously perform low-cost sensing, comparison, and state metabolism;
- use that baseline cognition to distinguish novelty from noise, echo, and repetition;
- conclude that no escalation beyond the current activation tier is presently justified;
- select a higher or lower cognition tier when the evidence warrants a transition;
- bound the authority, time, tools, and effect classes of any escalated cognition;
- separate proposal from execution when consequences warrant it;
- verify outcomes independently enough to detect failure or self-confirmation;
- persist enough state that interruption and restart do not duplicate commitments;
- preserve slack for future discovery rather than converting every signal into urgency.

The central design premise is:

> **Self-waking is endogenous movement through activation levels, not a binary transition from asleep to awake.**

The substrate may remain continuously active at low cost: sensing, normalizing, deduplicating, maintaining cheap state, and detecting novelty. What changes is the amount and kind of cognition instantiated above that substrate.

An event may create a wake candidate. It does not, by itself, require escalation to a higher cognitive tier.

---

## 2. Scope

self-wake owns **endogenous activation control** across a persistent cognitive substrate.

It assumes that some low-cost substrate may remain continuously active. A deployment may realize activation as one stack or as several concurrently active loci over shared state. The protocol governs when a locus should stay at its current level, ascend to more expensive cognition, descend again, or release bounded causal authority.

The protocol does not require a single globally scalar activation tier or serial cognition. Multiple compatible cognitive runs may coexist at different tiers, provided shared resource, authority, and commitment constraints remain coordinated and auditable.

It defines:

1. how observations become state deltas;
2. how state deltas can produce wake candidates;
3. how wake candidates are admitted, deferred, merged, suppressed, or rejected;
4. how the runtime chooses target activation tiers for admitted activation loci;
5. how an escalation receives an authority envelope;
6. how cognition produces proposals or portfolios;
7. how execution is bounded;
8. how outcomes are verified;
9. how verified transitions update persistent state;
10. how the system de-escalates safely when higher cognition is no longer justified.

self-wake does **not** prescribe:

- a particular language model;
- a particular agent framework;
- a particular database;
- a particular scheduler;
- a particular tool protocol;
- a particular memory architecture;
- a particular activation policy;
- a particular planning algorithm;
- a particular execution backend.

Those are adapters or policies around the protocol.

---

## 3. Self-wake versus policy

The **self-wake runtime** determines whether and how cognition becomes active.

An **activation policy** determines how wake candidates change the system's activation tier.

A **continuation policy** determines which candidate causal moves an active cognition should select, defer, reject, or commit to.

The **Causal Portfolio Controller (CPC)** is one possible continuation policy. CPC is not the definition of self-waking.

A minimal deployment might use a deterministic threshold policy:

> Escalate when maintained state crosses a boundary.

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

### ActivationLocus

An independently activatable region of cognitive work, such as an objective, question, subsystem, control loop, or cognitive run. Its activation tier may change without requiring all other cognition to change with it.

A simple deployment may treat the whole system as one activation locus. A richer deployment may maintain several loci concurrently over shared state and bounded resources.

### ActivationDecision

The runtime's disposition of one or more wake candidates relative to the **current activation tier of the relevant activation locus**. A scalar deployment may treat the whole system as that locus.

Conceptually, an activation decision contains:

- current tier;
- target tier;
- reason;
- applicable authority envelope;
- hold / debounce / hysteresis metadata.

A policy may:

- remain at the current tier;
- defer;
- merge candidates;
- escalate;
- de-escalate.

A valid ActivationDecision may explicitly conclude:

> No higher level of cognition is justified for this locus now.

That is a first-class successful outcome.

The term **wake** is retained as shorthand for a meaningful upward transition in activation, not for the beginning of all processing.

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

A bounded instantiation of cognition created by an admitted upward activation transition.

A cognitive run may investigate, estimate, propose, plan, select a portfolio, request execution, or decide that no intervention is justified.

Multiple cognitive runs may coexist. Their scheduling may be centralized, negotiated, or otherwise deployment-specific; the protocol only requires that each run's envelope and lifecycle remain explicit and that shared constraints cannot be bypassed by concurrency.

The runtime owns each run's envelope and lifecycle.

### Portfolio

A set of **candidate causal moves** considered together rather than independently.

A portfolio may contain no interventions, one intervention, several compatible interventions, investigations, reversible experiments, deferrals, or other mutually constrained options. Compatible selected items may be instantiated concurrently rather than sequentially.

A portfolio is still deliberative. Inclusion in a portfolio does **not** mean that an item has been authorized or committed to.

The portfolio abstraction is optional for simple policies but central to CPC.

### Commitment

A commitment is an adopted causal course that constrains future choice.

A proposal becomes a commitment only when the system crosses from considering an option to treating some consequence, resource allocation, authority grant, obligation, or execution path as binding enough to preserve across the next transition.

Commitment is therefore stronger than proposal but may precede physical execution.

Examples include:

- authorizing an intervention for execution;
- reserving scarce budget or capacity for a selected action;
- creating an external obligation or promise;
- scheduling an action whose cancellation is itself consequential;
- selecting one branch in a way that closes or materially reduces alternatives.

A policy is different: a policy is a rule or mapping that may produce different actions under different states. A commitment is a particular adopted causal course under the current state.

A useful lifecycle is:

~~~text
candidate → portfolio → selected → committed / authorized → executed → outcome → verified
~~~

Not every selected item must become committed. A portfolio may also select investigation, deferral, or deliberate non-action.

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

The protocol is better understood as an **activation ladder** than an on/off wake switch.

~~~text
                         WORLD
                           │
                    continuous sensing
                           │
                           ▼
                 ┌──────────────────┐
                 │  STATE METABOLISM │  ← low-cost, continuously active
                 └─────────┬────────┘
                           │
                      state deltas
                           │
                           ▼
                 ┌──────────────────┐
                 │ WAKE CANDIDATES  │
                 └─────────┬────────┘
                           │
                     activation policy
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
           hold          ascend        descend
             │             │             │
             │      ┌──────▼───────┐     │
             │      │ COGNITIVE TIER│◄────┘
             │      └──────┬───────┘
             │             │
             │      proposal / portfolio
             │             │
             │    ┌────────┼─────────┐
             │    │        │         │
             │    ▼        ▼         ▼
             │  no-op  investigate  execute
             │    │        │         │
             │    └────────┼─────────┘
             │             ▼
             │      ┌──────────────┐
             │      │ VERIFICATION │
             │      └──────┬───────┘
             │             │
             └─────────────┼──────────────► lower-cost activation
                           │
                    verified transition
                           │
                           ▼
                         WORLD
~~~

There are legitimate downward transitions at multiple stages.

The system is not required to reach execution, and it need not cease sensing or cheap metabolism when higher cognition is inactive.

---

## 6. Protocol invariants

An implementation claiming conformance with self-wake should preserve the following invariants.

### Observation does not imply escalation

Receiving an event is not equivalent to authorizing or instantiating higher cognition.

### Cognition does not imply action

A cognitive run may legitimately conclude that no intervention is justified.

### Activation may remain low or move downward

Holding, deferring, suppressing, merging, de-escalating, and no-op cognition are normal protocol outcomes, not failures.

### Authority is externally bounded

A cognitive run cannot expand its own authority envelope.

Any escalation requires a new decision by a component authorized to grant it.

### Consequential actions are identifiable

Interventions must carry stable identities or equivalent idempotency mechanisms sufficient to avoid duplicate causal commitments after retries or restart.

### State transitions are durable

The runtime must persist enough information to recover the causal stage it had reached before interruption.

### Replay is possible

Given the same durable inputs and deterministic policy components, activation admission and runtime transitions should be replayable for inspection.

Model-dependent cognition may be nondeterministic, but the surrounding causal record must remain inspectable.

### Proposal and verification are distinct roles

The component that proposes an intervention must not be treated as authoritative evidence that the intervention succeeded.

### Verification strength tracks consequence

Low-consequence reversible actions may need lightweight verification.

Irreversible or high-consequence actions require stronger, preferably independent verification.

### Slack is first-class

The runtime must permit preserving capacity, attention, uncertainty, and future option value.

It must not structurally force all available budget toward immediate action.

Slack preserves optionality; it does not prescribe passivity. A system may deliberately spend capacity now, or allocate future cognition, when doing so serves standing commitments, long-horizon goals, exploration, maintenance, or other ends it judges worth pursuing.

### Low activation is a stable state

A healthy persistent system can remain continuously perceptive while spending most of its time below expensive cognitive and causal-engagement thresholds.

Stable does not mean preferred or terminal. When justified by persistent state, self-wake may sustain, renew, or arrange future activation, including by scheduling future observation or reevaluation opportunities. A separate subsystem may also use scheduled cognition for a longer-running pursuit; that is compatible with self-wake, but the schedule itself is not a wake authority.

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

## 8. Observation sources and input channels

self-wake should support many observation sources and input channels without privileging any one transport.

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

State metabolism is the cheap layer between raw observation and activation admission.

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

## 10. Activation admission

Activation admission asks:

> **Given the relevant current activation state, maintained state, candidate set, budget, and policy, should this locus hold, ascend, descend, or coexist with other active cognition?**

Admission need not serialize candidates. It may admit several compatible cognitive runs concurrently, defer some, merge others, or arbitrate shared constraints among them. Resource arbitration may be centralized or negotiated among activation loci, but concurrency does not enlarge any run's authority.

Admission may consider consequence, urgency, novelty, uncertainty, reversibility, deadline, expected information gain, cognition cost, available slack, overlap with already-running work, common cause, recent activation history, and self-excitation risk.

Policies should support **hysteresis**: escalation and de-escalation need not use identical thresholds. This prevents noisy signals from producing rapid oscillation between cognition tiers.

Activation admission should be inspectable.

For every hold, escalation, or de-escalation, the runtime should be able to preserve a reason sufficient for later audit.

### Epistemic closure is not task closure

Reaching sufficient understanding is not, by itself, a reason to stop all cognition.

Understanding can terminate **epistemic escalation** for a particular uncertainty: the current representation is good enough that finer interpretation is unlikely to change the relevant causal classification.

But the resolved interpretation may itself justify further cognition or action.

For example:

- an unexplained sound may escalate until it is sufficiently identified;
- if it is identified as a harmless branch fracture, the system may de-escalate;
- if it is identified as an approaching dangerous animal, epistemic uncertainty may be reduced while planning and causal engagement should escalate.

Therefore, after an uncertainty becomes sufficiently understood, the runtime must still evaluate the consequences of that understanding.

A useful distinction is:

1. **epistemic continuation** — more cognition is needed to determine what is happening;
2. **instrumental continuation** — what is happening is sufficiently understood, but more cognition is needed to decide what to do;
3. **causal continuation** — a decision is sufficiently formed and bounded execution is justified;
4. **de-escalation** — no further cognition or action is currently justified.

Sufficient understanding is therefore a possible stopping condition for one cognitive objective, not a universal stopping condition for the broader activation state.

---

## 11. Activation tiers

A runtime may support several activation tiers, for example:

0. sensing and ingestion;
1. deterministic metabolism and derived state;
2. cheap attention / classification;
3. lightweight model cognition;
4. deep model cognition;
5. adversarial or verifier cognition;
6. human participation or other high-cost escalation.

The exact ladder is deployment-specific. Not every tier needs a language model.

Tiers need not form one global ladder. They may apply per objective, subsystem, or cognitive run, so several loci can occupy different tiers simultaneously while sharing state and bounded resources.

An activation policy may move any locus upward or downward through tiers rather than jumping immediately to the most expensive cognition available.

The protocol does not prescribe the tiers, a single global tier, or serial execution. It requires each represented activation transition to preserve its current tier, target tier, granted authority, and enough shared-resource context for later audit.

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
- why the relevant activation decision was made, including hold, defer, merge, escalate, or de-escalate;
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

After restart, it should be possible to determine the causal stage of each selected or committed intervention, including whether it was:

- selected but not committed;
- committed / authorized but not started;
- started but unresolved;
- executed but unverified;
- verified and closed.

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

An activation policy should suppress or discount self-generated echoes as evidence of novelty or independent confirmation while still noticing unexpected consequences.

Echo suppression must not by itself extinguish a self-sustaining intervention whose original justification remains unresolved. Self-generated recurrence may carry little or no novelty while still indicating unresolved necessity.

Persistence or decay should therefore be conditioned on state: recovery of the protected variable, successful takeover by another mechanism, demonstrated ineffectiveness, or an applicable safety or authority limit. It should not occur merely because time passed or the sustaining activity is self-caused. Homeostatic or survival-critical loops may renew activation while their causal justification remains valid, with hysteresis where needed to avoid premature decay.

---

## 17. Minimal conformance

A system minimally conforms to the self-wake protocol if it can demonstrate all of the following:

1. sensing or cheap state metabolism can continue without invoking higher-cost model cognition;
2. observations can produce explicit wake candidates;
3. activation decisions can hold, defer, escalate, or de-escalate;
4. escalation to a higher cognitive tier receives a bounded authority envelope;
5. cognition can terminate without execution;
6. consequential interventions have stable identity or equivalent deduplication semantics;
7. outcomes are distinguished from intended effects;
8. verification is represented explicitly;
9. interruption does not require blindly replaying causal commitments;
10. durable traces are sufficient to inspect why an activation transition occurred;
11. low activation is treated as a normal persistent state rather than total inactivity;
12. the control policy can avoid pathological oscillation between tiers, for example through hysteresis or an equivalent mechanism.

This is intentionally behavioral.

Conformance neither requires nor forbids parallel cognitive runs. A concurrent implementation must preserve the same authority, resource-accounting, commitment, verification, and replay guarantees across simultaneously active loci.

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
activation policy
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
        activation.py
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

The missing property is **endogenous activation control**: a continuously or intermittently perceptive substrate evaluates whether current conditions justify moving to a different cognition tier, under explicit bounded authority.

Self-wake therefore does not mean that the whole system was previously asleep. It means that the system can regulate its own depth of cognition.

---

## 21. Design test

The protocol should eventually make this question answerable:

> **Given an arbitrary persistent AI system, what must be true for us to say that it is genuinely regulating its own depth of cognition, rather than merely running periodically or reacting to events?**

If two independent implementations can read this specification and agree on the observable answer, the protocol is becoming precise enough.

---

## 22. Development order

Before implementation:

1. refine the ontology;
2. refine lifecycle and state-transition semantics;
3. define the authority envelope;
4. define persistence and idempotency requirements;
5. define minimal conformance tests;
6. specify extension points for activation and continuation policies;
7. specify CPC separately as the first rich reference policy.

Only then should the reference Python package be generated.

The README is therefore not downstream documentation.

**For now, the README is the system definition.**

The first deliberately narrow executable slice is documented in
[`IMPLEMENTATION.md`](IMPLEMENTATION.md). The README remains normative.

