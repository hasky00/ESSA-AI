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

Run the simple self-aware agent example with:

```bash
python3 -m examples.simple_self_aware_agent
```

The example prints a structured SELF cycle: identity and essence remain stable,
the agent distinguishes self-observations from world-observations, inspects its
runtime substrate, predicts a state transition, acts, and records whether the
prediction was confirmed.

Run the hidden-rule learning environment with:

```bash
python3 -m examples.hidden_rule_environment
python3 -m examples.hidden_rule_environment --cycles 20
python3 -m examples.hidden_rule_environment --forever --delay 1
python3 -m examples.hidden_rule_environment --week
```

That example repeats an autonomous ESSA loop over a changing environment whose
true rules are not exposed to the agent:

```text
observe -> detect -> hypothesize -> predict -> act -> evaluate -> update -> next_task
```

The environment changes one cycle at a time. ESSA sees only visible conditions
such as signal, drift, noise, energy, and uncertainty. Hidden constraints can
drift as turns pass. ESSA keeps a north star, a world model of beliefs with
confidence scores, competing hypotheses, written predictions before action, and
model updates after every surprise. There are no punishment penalties: every
unexpected result becomes learning pressure and changes confidence.

Each text cycle prints:

```text
OBSERVED
SURPRISES
HYPOTHESES
CHOSEN ACTION + PREDICTION
RESULT
MODEL UPDATE
NEXT TASK
```

Use `--json` when you want machine-readable cycle reports.

Run the notification-energy core belief lab with:

```bash
python3 -m examples.notification_energy_lab --cycles 10
python3 -m examples.notification_energy_lab --forever --delay 5
```

This lab starts from a real-world north star:

```text
Find out if phone notification drains your energy.
```

It tests beliefs about notifications, 5-minute attention checks, rest, walking,
energy, productivity, and disturbance. ESSA can only see daily-style
observations; the hidden rules decide whether each action creates clarity,
partial information, or new data.

Run the ESSA Haiti education case for seven days with:

```bash
python3 -m examples.essa_haiti_education_case --days 7
```

After the final cycle, ESSA prints a compact run summary showing changes in
attendance, felt safety, uncertainty, and hunger pressure, plus the actions it
tested and how often its predictions matched the observed direction.

ESSA also stores salient episodes, recalls similar past situations before it
predicts, and consolidates repeated experiences into explainable semantic
lessons. Persist that cognitive memory between runs with:

```bash
python3 -m examples.essa_haiti_education_case --days 7 --memory-file essa-memory.json
```

## Neuromorphic hardware scaling

ESSA includes an experimental hardware substrate layer for distributing sparse,
event-driven cognitive workloads across multiple neuromorphic chips or nodes.
It separates the cognitive code from vendor SDKs through device adapters,
partitions work by neuron, synapse, and event capacity, routes events between
devices, and can reject allocations that exceed a declared power envelope.

Run the dependency-free capacity-planning simulation with:

```bash
python3 -m examples.neuromorphic_hardware_scale --devices 4 --power-budget 20
```

The included adapter is a simulator, so `20` watts is a planning assumption,
not measured electrical consumption. Real deployment requires an adapter for
the attached hardware SDK plus power telemetry from that system. The software
leaky-integrate-and-fire gate and cluster planner are designed so CPU simulation
can be replaced by a hardware backend without changing ESSA's SELF or case
logic.

## Substrate Intelligence Device SID-1

SID-1 is ESSA's first earth-native localization device architecture. Embedded
sensors detect a signal inside water or soil, and the local mesh estimates its
position from synchronized arrival times. Satellite, cellular, or radio links
are optional relays for an estimate that SID-1 has already calculated locally.

Run the crocodile-tag reference simulation with:

```bash
python3 -m examples.substrate_tracking_device
```

This is a software reference device, not manufactured tracking hardware. The
example uses four simulated riverbed hydrophones and an authorized acoustic tag.
See [`docs/SID_1_BLUEPRINT.md`](docs/SID_1_BLUEPRINT.md) for the physical
prototype path, scientific limits, and deployment safeguards.

Hasky Labs' Revision 0.1 design package adds a phased material list, electrical
and mechanical architecture, deployment configuration, sample sensor data, and
a field-controller CLI under [`hardware/sid1`](hardware/sid1). Run it with:

```bash
python3 -m examples.sid1_field_controller \
  --config hardware/sid1/config/water-array.json \
  --detections hardware/sid1/sample/detections.csv
```

The agreed route to the first physical unit is recorded in
[`hardware/sid1/SID1_A_BUILD_PLAN.md`](hardware/sid1/SID1_A_BUILD_PLAN.md).
SID1-A keeps the recorder, computer, storage, and power system dry; purchasing
expands from one verified signal channel to four only after each evidence gate
passes.

This case is grounded in a UN News article about children returning to school in
Haiti under gang violence and displacement:

```text
https://news.un.org/en/story/2026/09/1168337
```

ESSA's north star is:

```text
Prevent violence, prevent hunger, help children go to school,
and help children feel safe.
```

Each day, ESSA observes child-safety constraints such as gang pressure, group
violence, displacement, hunger, school condition, route risk, teacher access,
trauma signals, family cost pressure, attendance, felt safety, and uncertainty.
It then hypothesizes which action best serves the north star: securing the
route, creating a safe learning space, providing meals and supplies, supporting
teachers and trauma recovery, or repairing/enrolling when access is safe enough.

ESSA also observes a lightweight food-distribution topology model. It represents
food-system stress as barcode-like intervals across scales:

```text
local -> regional -> trade corridor -> global commodity market
```

Longer-lived intervals mean a hunger risk is not only local. For example, a
local market access gap that persists up to the global commodity-market scale is
treated as stronger evidence that hunger prevention needs distribution-network
stabilization, not only one-day meals. This is intentionally dependency-light:
it uses small Python dataclasses rather than heavy persistent-homology or graph
libraries.

## Landing page voice

The GitHub Pages landing page can play a generated ESSA introduction from
`docs/assets/essa-voice.mp3`. It does not use the computer's default browser
voice; generate the AI-agent voice locally with an OpenAI API key:

```bash
OPENAI_API_KEY=... python3 scripts/generate_essa_voice.py
ESSA_TTS_VOICE=onyx OPENAI_API_KEY=... python3 scripts/generate_essa_voice.py
```

Or place the key in a private `.env.local` file:

```bash
cp .env.example .env.local
python3 scripts/generate_essa_voice.py
```

Do not place an API key in `docs/index.html` or any browser-side file.

## Research status

**Experimental / hypothesis-driven.**

The project deliberately avoids assuming that a language model is the fundamental cognitive engine. A language model may eventually be used as an interface or component, but it is not the assumed primitive of ESSA.

See [`docs/ESSA_FOUNDATION.md`](docs/ESSA_FOUNDATION.md) and [`docs/SYMBOLIC_CORE.md`](docs/SYMBOLIC_CORE.md).
