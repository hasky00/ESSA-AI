# ESSA-AI

**Essence — Substrate — State — Architecture**

ESSA-AI is an open research project exploring a non-LLM-centered architecture for artificial intelligence.

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

## Research status

**Experimental / hypothesis-driven.**

The project deliberately avoids assuming that a language model is the fundamental cognitive engine. A language model may eventually be used as an interface or component, but it is not the assumed primitive of ESSA.

See [`docs/ESSA_FOUNDATION.md`](docs/ESSA_FOUNDATION.md) and [`docs/SYMBOLIC_CORE.md`](docs/SYMBOLIC_CORE.md).
