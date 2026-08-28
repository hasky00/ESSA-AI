# ESSA Self Model — v0.1 Experimental Specification

## Purpose

This document defines `SELF` as a computational object in ESSA. It is an engineering hypothesis, not a claim that the system is conscious.

The central requirement is that `SELF` must be more than a text description retrieved from memory. It must be a persistent, updateable object whose identity, substrate, state, architecture, capabilities, observations, predictions, and history can be represented and related.

## 1. Identity and persistence

A SELF instance has a persistent identity:

```text
SELF-001
```

The identity is not identical to its current substrate or current state.

```text
IDENTITY = persistent agent reference
ESSENCE  = what the agent is
SUBSTRATE = what computational conditions instantiate it
STATE = current condition
ARCHITECTURE = organization of its computational parts
```

A substrate transition should therefore be representable without automatically destroying identity:

```text
SELF-001
  substrate: H100
      ↓
  substrate: RTX_5090
```

The system should preserve the historical transition and update capabilities and potential accordingly.

## 2. Self state

`SELF` maintains a state that can include:

```text
current_task
current_goals
uncertainty
resource_state
available_capabilities
current_substrate
recent_actions
recent_observations
predictions
prediction_errors
```

State is mutable. Identity and essence are persistent references unless an explicit operation changes the ontology of the agent.

## 3. Self observation

ESSA must distinguish observations about the external world from observations about the agent itself.

```text
WORLD OBSERVATION
  SELF → observes → GPU

SELF OBSERVATION
  SELF → observes → SELF_STATE
```

Examples of self-observation include computational load, available memory, active task, uncertainty, recent action, and observed consequence.

The initial prototype should expose these as explicit observations rather than natural-language statements.

## 4. Self/world boundary

`SELF` is a first-class entity and must be distinguishable from external entities.

```text
SELF-001
   │
   ├── interacts_with → GPU
   ├── observes → ENVIRONMENT
   └── observes → SELF_STATE
```

The distinction must exist in the symbolic model, not only in generated language.

## 5. Substrate awareness

The agent should be able to inspect or receive measurements about the substrate on which it is instantiated.

The substrate model may include:

```text
hardware_identity
memory_capacity
available_compute
supported_operations
resource_usage
constraints
performance_observations
```

A substrate change should trigger model reconciliation:

```text
same identity
+ changed substrate
→ changed capabilities / potential / state
```

## 6. Prediction and consequence

SELF should maintain a relation between an action, a predicted outcome, and an observed outcome.

```text
PREDICTION
  action A → expected result Rₚ

ACTION
  execute A

OBSERVATION
  actual result Rₐ

ERROR
  Rₚ ≠ Rₐ

UPDATE
  revise transition/performance model
```

This makes learning a state/model update rather than merely acquisition of additional text.

## 7. Potentiality

ESSA should explicitly represent possible future states rather than treating capability as identical to current activity.

```text
CURRENT STATE
     +
SUBSTRATE
     +
ARCHITECTURE
     +
CONSTRAINTS
     ↓
POTENTIAL ACTIONS
     ↓
PREDICTED FUTURE STATES
```

Potential is therefore substrate-dependent but not identical to substrate.

## 8. Language interface

Language is an interface to the model rather than the model's fundamental state representation.

For example:

```text
"I am running on an H100"
```

should correspond to structured relations such as:

```text
SELF-001 → instantiated_on → H100
SELF-001 → current_state → EXECUTING
```

The symbolic relations should exist even when no sentence is generated.

## 9. Minimal computational API

The first implementation should expose operations conceptually equivalent to:

```text
SELF.identify()
SELF.observe_world()
SELF.observe_self()
SELF.inspect_substrate()
SELF.predict(action)
SELF.act(action)
SELF.compare_prediction(observation)
SELF.update_state(observation)
SELF.update_self_model(observation)
SELF.record_transition(...)
```

These names are an initial design target, not a frozen API.

## 10. First experiment

### Experiment: substrate continuity

1. Instantiate `SELF-001` on substrate A.
2. Let it inspect and record substrate A.
3. Perform actions and record observations.
4. Replace or simulate the substrate with substrate B.
5. Let SELF observe the change.
6. Test whether it preserves identity and essence.
7. Test whether it updates substrate, state, capabilities, and potential.
8. Test whether the transition is preserved in history.

Expected symbolic result:

```text
IDENTITY:      unchanged
ESSENCE:       unchanged
SUBSTRATE:     A → B
STATE:         updated
CAPABILITIES:  updated
POTENTIAL:     updated
HISTORY:       transition preserved
```

## 11. What this does not establish

A successful self-model does not by itself establish consciousness, subjective experience, or philosophical selfhood. The initial claim is narrower and testable:

> ESSA can maintain and update an explicit computational model of itself as an entity situated in a changing substrate and state.

That distinction must remain explicit throughout the project.
