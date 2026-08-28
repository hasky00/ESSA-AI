# ESSA-AI

**Essence — Substrate — State — Architecture**

ESSA-AI is an open research project and executable prototype for a non-LLM-centered architecture for artificial intelligence.

The core hypothesis is that intelligence should not be fundamentally defined as next-token prediction. ESSA instead treats **entities, relations, states, transformations, self-modeling, and substrate awareness** as first-class computational objects.

## Core idea

```text
LLM:   token → token → token → token

ESSA:  state → relation → transformation → new state
                                  ↓
                             observation
                                  ↓
                             model update
```

## The four distinctions

```text
Essence       What is it?
Substrate     Through what does it exist?
State         In what condition does it exist now?
Architecture  How are its components organized?
```

## Core loop

```text
EXIST
  ↓
REPRESENT
  ↓
OBSERVE
  ↓
ESSENCE / SUBSTRATE / STATE / ARCHITECTURE
  ↓
MODEL POTENTIAL
  ↓
PREDICT
  ↓
ACT
  ↓
OBSERVE CONSEQUENCE
  ↓
UPDATE STATE
  ↓
UPDATE WORLD MODEL
  ↓
UPDATE SELF-MODEL
  ↓
ACT AGAIN
```

## Intellectual foundation

ESSA is an original synthesis inspired by two different bodies of work:

- **Ibn Sina:** distinctions involving essence, existence, self-awareness, potentiality, and actuality provide a philosophical vocabulary for an explicit self/world ontology.
- **HAWKEYE:** hardware-aware GPU optimization motivates treating the concrete computational substrate as part of the problem rather than as an invisible execution layer.

ESSA does **not** claim that Ibn Sina wrote about AI or GPUs. The synthesis is a modern research hypothesis.

## v0.1 goal

Build the smallest working system that can:

1. represent entities and relations;
2. maintain Essence, Substrate, State, and Architecture;
3. maintain a persistent self-model;
4. represent and predict state transitions;
5. act on an environment;
6. observe consequences;
7. revise its world and self models;
8. expose language as an interface rather than the fundamental state representation.

## Executable SELF prototype

The repository now includes a dependency-light Python implementation of a minimal computational `SELF`.

```python
from essa import SelfModel, RuntimeSubstrateInspector

self_model = SelfModel()
self_model.inspect_substrate(RuntimeSubstrateInspector())
prediction = self_model.predict("transition_state")
self_model.act("transition_state", {"status": "completed"}, prediction=prediction)
self_model.save("self.json")
```

The implementation deliberately keeps the core symbolic and state-transition based:

- `Identity` and `Essence` are persistent.
- `SubstrateSnapshot`, `state`, `capabilities`, and `potential` are mutable.
- `SelfModel.observe_self()` and `SelfModel.observe_world()` keep the self/world boundary explicit.
- `SelfModel.inspect_substrate()` updates substrate-dependent capabilities and potential while preserving identity.
- `SelfModel.predict()`, `SelfModel.act()`, and `SelfModel.transition_state()` record predictions, observations, consequences, and history.
- JSON persistence allows the model to be saved and restored without introducing a database or LLM dependency.

Run the executable tests with:

```bash
python3 -m unittest discover -s tests
```

## Research status

**Experimental / hypothesis-driven.**

The project deliberately avoids assuming that a language model is the fundamental cognitive engine. A language model may eventually be used as an interface or component, but it is not the assumed primitive of ESSA.

See [`docs/ESSA_FOUNDATION.md`](docs/ESSA_FOUNDATION.md) and [`docs/SYMBOLIC_CORE.md`](docs/SYMBOLIC_CORE.md).
