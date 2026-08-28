# ESSA Research Log

This log records architectural decisions and hypotheses so the project does not lose the reasoning that led to each implementation step.

## 2026-08-28 — SELF as a computational object

### Decision

Treat `SELF` as a first-class computational object rather than a natural-language description of the agent.

### Core distinction

```text
Essence       = what the agent is
Substrate     = what instantiates the computation
State         = the agent's current condition
Architecture  = organization of the agent's computational parts
Identity      = persistent reference across state/substrate changes
History       = record of transformations and observations
Potential     = possible future states/actions under constraints
```

### Key hypothesis

A substrate can change without necessarily changing the agent's identity or essence.

Example:

```text
SELF-001
H100 → RTX_5090
```

The expected model behavior is:

```text
identity      unchanged
essence       unchanged
substrate     updated
state         updated
capabilities  recalculated/updated
potential     recalculated/updated
history       records transition
```

### Why this matters

This gives ESSA a concrete bridge between metaphysical distinctions and hardware-aware computation. HAWKEYE motivates treating the concrete computational substrate as relevant to how computation should be instantiated. Ibn Sina's distinctions motivate separating what a thing is from the conditions in which it exists. ESSA turns those ideas into explicit computational fields and state transitions.

### Important limitation

This is an ESSA research synthesis. It must not be presented as if Ibn Sina proposed GPU-aware AI or as if HAWKEYE established machine self-awareness.

### First experimental target

Build a minimal agent that can:

1. inspect its substrate;
2. construct an explicit self-model;
3. distinguish self from external entities;
4. maintain persistent identity;
5. observe its own state;
6. act and record consequences;
7. compare predictions with observations;
8. update its self/world model;
9. survive a simulated substrate change while preserving identity.

### Non-goal

Do not claim consciousness from successful implementation of these mechanisms. The first target is **computational self-modeling and substrate-aware identity continuity**.
