# ESSA-SID1 Hardware Package

This directory contains Hasky Labs' Revision 0.1 design inputs for the ESSA
Substrate Intelligent Device 1.

- `DESIGN.md`: system, electrical, mechanical, power, software, and validation design.
- `MATERIALS.csv`: phased bill of materials with minimum specifications and selection status.
- `config/water-array.json`: reference sensor geometry and solver configuration.
- `sample/detections.csv`: synchronized acceptance-test detections.

Run the reference controller from the repository root:

```bash
python3 -m examples.sid1_field_controller \
  --config hardware/sid1/config/water-array.json \
  --detections hardware/sid1/sample/detections.csv
```

No PCB, waterproof enclosure, field accuracy, or 20 W electrical result has yet
been validated. Do not purchase all materials or deploy around wildlife until a
qualified electrical engineer and relevant field specialists review Revision A.
