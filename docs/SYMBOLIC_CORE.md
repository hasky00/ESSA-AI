# ESSA Symbolic Core — v0.1

ESSA begins with a symbolic world model. This is deliberately small: the goal is to define the computational primitives before choosing a large learning model.

## First-class objects

```text
ENTITY
ESSENCE
SUBSTRATE
STATE
ARCHITECTURE
RELATION
CAPABILITY
CONSTRAINT
POTENTIAL
ACTION
OBSERVATION
TRANSITION
SELF
```

## Entity

An entity is a persistent identifiable object in the ESSA world model.

```text
Entity {
  id
  essence
  substrate
  state
  architecture
  relations[]
  capabilities[]
  constraints[]
  history[]
}
```

## Self

`SELF` is a first-class entity, not a paragraph retrieved from memory.

```text
SELF
 ├─ essence
 ├─ instantiated_on → SUBSTRATE
 ├─ has_state → STATE
 ├─ has_architecture → ARCHITECTURE
 ├─ has_capability → CAPABILITY
 ├─ has_constraint → CONSTRAINT
 └─ has_history → EVENT*
```

The self-model must be persistent and updateable from observations.

## Relations

```text
RELATION(subject, predicate, object, confidence, evidence)
```

Examples:

```text
SELF → instantiated_on → H100
SELF → current_state → STATE_001
SELF → can_perform → KERNEL_OPTIMIZATION
H100 → provides → WGMMA
STATE_001 → constrained_by → MEMORY_BANDWIDTH
```

## State transition

```text
S(t+1) = T(S(t), A(t), E(t))
```

Where:

- `S(t)` = current state
- `A(t)` = action/intervention
- `E(t)` = substrate/environment conditions
- `T` = specified or learned transition model

The transition, not the next word, is the central computational event.

## Potential

```text
POTENTIAL(state, action, expected_result, constraints)
```

Potential is not actuality. It represents a reachable or hypothesized future state.

## Observation

```text
OBSERVATION {
  source
  target
  measured_value
  timestamp
  confidence
  evidence
}
```

Observations have priority over unsupported internal belief.

## Learning

Learning is model revision:

```text
hypothesis
  ↓
prediction
  ↓
action
  ↓
observation
  ↓
error / confirmation
  ↓
update relation or transition model
```

## Non-linguistic primacy

Natural language is a projection into and out of the symbolic world model:

```text
WORLD MODEL
    ↕
LANGUAGE INTERFACE
```

The sentence is not the primary state.
