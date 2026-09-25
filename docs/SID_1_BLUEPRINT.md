# ESSA Substrate Intelligence Device SID-1

## Status

SID-1 is an experimental software reference device and hardware architecture.
No physical unit has been manufactured or attached to this repository.

## Principle

Localize in the target's native physical medium. Relay the locally computed
result through the sky only when long-distance communication is required.

## Device layers

1. Embedded sensor nodes: hydrophones in water, geophones in soil, or another
   medium-appropriate transducer.
2. Synchronized timing: each node timestamps the same event against a shared
   local clock.
3. Event mesh: nodes transmit sparse detections rather than continuous raw
   streams whenever possible.
4. ESSA edge controller: calculates position, confidence, residual error, and
   uncertainty locally.
5. Optional relay: cellular, radio, wired, or satellite transport sends the
   finished estimate; it does not produce the estimate.

## First reference mission

Four riverbed hydrophones detect an authorized acoustic wildlife tag. SID-1
uses local time-difference-of-arrival evidence to estimate a two-dimensional
position. The included example is deterministic simulation data, not a field
claim about crocodile tracking accuracy.

## Physical prototype requirements

- At least three synchronized medium-compatible sensors; four or more improve
  geometry and redundancy.
- Calibrated propagation speed for local water, soil, or rock conditions.
- Weatherproof or submersible enclosures and stable sensor coordinates.
- Local clock synchronization and measured clock uncertainty.
- Edge compute, storage, power management, and an emergency shutdown path.
- A neuromorphic adapter when physical neuromorphic hardware is available.
- Wildlife permits, ethical tagging practice, privacy controls, and deployment
  permission from the relevant land or water authority.

## Known limits

Multipath reflections, clock drift, sensor movement, temperature, salinity,
terrain, and incorrect propagation speed can degrade localization. Passive
detection without a known source signature may detect movement but may not
identify a particular animal. Field results must report calibration error and
must not describe a probability estimate as an exact fact.

## Hardware path

1. Validate the solver with recorded multi-sensor data.
2. Build four wired development nodes with synchronized clocks.
3. Perform tank or controlled-ground tests with known source positions.
4. Measure error, power, event rate, clock drift, and multipath failure modes.
5. Replace the Python solver or event gate with a supported neuromorphic
   hardware adapter while preserving the SID-1 contracts.
6. Attempt field research only with domain experts and required permissions.
