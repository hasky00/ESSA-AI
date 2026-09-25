# ESSA-SID1 Sensor Pods

**Status:** product concept and requirements input; not manufactured or validated

## W1-W4: water array

Four identical hydrophones share one acquisition clock. Their first job is to
detect the same authorized acoustic event and provide arrival times for local
water-domain localization.

The useful bandwidth must be selected from measured source signatures and site
noise, not from a promise to detect "any movement." A 2 Hz to 30 kHz reference
class covers low-frequency pressure events through common underwater acoustic
signals. Wider-band sensing up to 200 kHz may be evaluated later when a measured
use case justifies its power, sample-rate, storage, and processing cost.

## G1: ground pod

G1 is a separate three-axis vibration sensor. It requires physical coupling to
the measured substrate:

- use the removable spike in suitable soil;
- use a bolted, bonded, or magnetic flat foot on compatible rock or structures;
- record orientation, mounting method, substrate, and coupling quality with each
  observation.

A 4.5 Hz low-frequency geophone is the initial reference class. Final bandwidth,
sensitivity, axis matching, preamplifier, and ADC requirements depend on measured
targets and background vibration.

## Internal inertial reference

The base-station IMU is a reference channel, not a replacement for G1. It marks
handling, impact, tilt, and enclosure motion that could otherwise be mistaken for
an environmental event.

## Fusion rule

ESSA preserves water, ground, and device-motion observations as separate evidence.
It may increase confidence when independently calibrated channels agree in time,
but it must retain disagreement and missing detections rather than forcing a
single result. All localization remains experimental until tested against known
positions under controlled conditions.

## Reference classes

- HTI-96-Min hydrophone, 2 Hz to 30 kHz:
  https://www.hightechincusa.com/products/hydrophones/hti96min.html
- Ocean Sonics icListen HF, 10 Hz to 200 kHz:
  https://oceansonics.com/iclisten-hf-hydrophone/
- Geospace GS-ONE LF geophone, 4.5 Hz or 5 Hz:
  https://www.geospace.com/products/sensors-and-geophones/gs-one-lf/

These are engineering references, not purchasing endorsements or selected
production parts.
