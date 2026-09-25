# Hasky Labs ESSA-SID1-A Build Plan

## Decision record

Hasky Labs will pursue SID1-A as the first physical laboratory prototype of the
ESSA Substrate Intelligent Device.

SID1-A tests one proposition:

> Can four sensors inside water give ESSA a repeatable local position without
> using a satellite to perform localization?

All acquisition electronics, edge compute, storage, battery equipment, and
operators remain dry and above water. Only hydrophones, field-rated cables,
anchors, and approved calibration sources enter the water.

## Scope

SID1-A includes:

- Four identical cabled hydrophones.
- One recorder or ADC with at least four truly simultaneous input channels and
  one shared sample clock.
- One dry edge computer running the ESSA-SID1 controller.
- One authorized laboratory acoustic source with a documented waveform or tag
  identifier.
- A measured sensor geometry in a tank or controlled pond.
- Local storage and optional result relay, disabled during baseline tests.

SID1-A excludes:

- Animal deployment.
- Autonomous drilling or physical intervention.
- Underwater radio.
- A custom production PCB.
- A submerged edge computer.
- Claims of field accuracy, waterproof certification, 20 W operation, or
  commercial readiness.

## Procurement order

Do not purchase the full array in one step. Each gate protects the next spend.

### Gate P0: source and bandwidth

1. Select a legal laboratory acoustic pinger or playback source.
2. Record its center frequency, bandwidth, pulse duration, source level, and
   repetition interval.
3. Confirm the intended hydrophone, cable length, preamplifier, recorder input,
   and recorder sample rate preserve that signal.
4. Obtain written confirmation from component vendors when published frequency
   or cable-loading specifications are insufficient.

**Exit evidence:** one signed compatibility sheet listing every signal-path
component and its relevant frequency range.

### Gate P1: one-channel proof

Purchase or borrow:

- One hydrophone and its field cable.
- The proposed synchronized recorder.
- The approved calibration source.
- Required dry-side power, storage, and adapters.

Capture the source through one channel at short, medium, and longest intended
test distance. Check clipping, noise floor, missed pulses, connectors, phantom
power compatibility, and cable handling noise.

**Exit evidence:** raw recordings, recorder settings, source coordinates,
temperature, test distance, and a reproducible pulse-detection report.

### Gate P2: four-channel array

Only after P1 succeeds, obtain three additional matching hydrophones, cables,
mounts, glands, and anchors. Confirm all recorder channels use one conversion
clock and preserve their relative timing.

**Exit evidence:** the same test pulse appears on all four channels with stable,
measured arrival-time differences.

### Gate P3: edge controller

Install the repository on the dry edge computer. Store the measured sensor
coordinates in a versioned SID1 JSON configuration. Convert synchronized pulse
detections to the SID1 CSV contract and run the local controller.

```bash
python3 -m examples.sid1_field_controller \
  --config hardware/sid1/config/water-array.json \
  --detections hardware/sid1/sample/detections.csv
```

**Exit evidence:** local estimate, confidence, timing residual, sensor IDs,
configuration revision, and no satellite localization dependency.

## Assembly boundary

```text
WATER                                  DRY / ABOVE WATER

Hydrophone NW -----------------------> recorder input 1
Hydrophone NE -----------------------> recorder input 2
Hydrophone SW -----------------------> recorder input 3
Hydrophone SE -----------------------> recorder input 4
                                          |
                                   shared sample clock
                                          |
                                      edge computer
                                          |
                                  ESSA-SID1 local result
```

Every submerged cable receives strain relief before its electrical termination.
No battery, mains connection, non-rated connector, or open electronics enters
the water.

## Controlled-water test

1. Mark a local coordinate system and survey all four hydrophone positions.
2. Measure water temperature and other variables needed for propagation-speed
   calibration.
3. Place the source at a series of known coordinates covering the center, edges,
   corners, and positions close to individual sensors.
4. Capture repeated pulses at every coordinate.
5. Keep the raw synchronized data and derive detections without changing sensor
   coordinates between attempts.
6. Compare ESSA's local estimates against measured source coordinates.
7. Repeat after moving one sensor slightly to test configuration-error handling.

## Evidence to record

For every run, preserve:

- UTC start time and experiment identifier.
- Operator and equipment serial numbers.
- Hardware and software revision.
- Sensor coordinates and coordinate-measurement method.
- Source identifier, waveform, and known position.
- Sample rate, channel gain, filters, and clock configuration.
- Water temperature and propagation-speed assumption.
- Raw data location and checksum.
- Per-channel detection status and arrival timestamp.
- Estimated position, confidence, timing residual, and actual error.
- Battery voltage, average power, peak power, and run duration when measured.
- Environmental, multipath, clipping, dropout, or safety notes.

## Acceptance report

SID1-A does not pass because one ideal point is correct. The report must include:

- Number and percentage of pulses detected by all four channels.
- Missed and false detections per channel.
- Median localization error.
- 95th-percentile localization error.
- Worst-case localization error and its geometry.
- Timing residual distribution.
- Repeatability at unchanged coordinates.
- Sensitivity to propagation-speed and sensor-coordinate error.
- Measured idle, acquisition, and localization power.

Numerical field claims will be set from measured evidence. A provisional target
may guide testing, but it must not be presented as achieved performance before
the report exists.

## Stop conditions

Stop the test and return to the previous gate when:

- The source frequency is outside any component's verified signal path.
- Channels are not sampled simultaneously or relative timing is unstable.
- Any submerged cable, connector, or enclosure is damaged or not depth-rated.
- Electrical protection, strain relief, recovery lines, or site permission are
  missing.
- Detections mix source signatures or cannot distinguish the calibration source.
- Results require hidden manual corrections that are absent from configuration.
- Wildlife, people, or the environment could be disturbed.

## Transition to SID1-B

SID1-B begins only after SID1-A produces a reproducible controlled-water report.
That evidence will determine ADC bandwidth, analog gain, filter design, timing
requirements, compute load, battery capacity, enclosure design, sensor spacing,
and whether a neuromorphic accelerator provides a measurable benefit.
