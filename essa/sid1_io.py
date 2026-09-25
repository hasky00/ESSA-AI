from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from essa.substrate_intelligence import (
    SubstrateDetection,
    SubstrateIntelligenceDevice,
    SubstrateSensorNode,
)


@dataclass(frozen=True)
class SID1LocalizationConfig:
    propagation_speed_mps: float
    bounds: tuple[float, float, float, float]
    grid_step_meters: float


def load_sid1_config(
    path: str | Path,
) -> tuple[SubstrateIntelligenceDevice, SID1LocalizationConfig]:
    value: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    sensors = tuple(
        SubstrateSensorNode(
            sensor_id=item["sensor_id"],
            x_meters=float(item["x_meters"]),
            y_meters=float(item["y_meters"]),
            medium=item["medium"],
            modality=item["modality"],
            clock_uncertainty_seconds=float(
                item.get("clock_uncertainty_seconds", 0.0001)
            ),
        )
        for item in value["sensors"]
    )
    bounds = value["localization"]["bounds"]
    if len(bounds) != 4:
        raise ValueError("Localization bounds require four numbers")
    device = SubstrateIntelligenceDevice(
        value["device_id"],
        sensors,
        relay_enabled=bool(value.get("relay_enabled", False)),
    )
    config = SID1LocalizationConfig(
        propagation_speed_mps=float(
            value["localization"]["propagation_speed_mps"]
        ),
        bounds=tuple(float(item) for item in bounds),
        grid_step_meters=float(value["localization"].get("grid_step_meters", 1.0)),
    )
    return device, config


def load_detections_csv(path: str | Path) -> tuple[SubstrateDetection, ...]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "sensor_id",
            "source_signature",
            "arrival_time_seconds",
            "amplitude",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"Detection CSV requires columns: {sorted(required)}")
        return tuple(
            SubstrateDetection(
                sensor_id=row["sensor_id"],
                source_signature=row["source_signature"],
                arrival_time_seconds=float(row["arrival_time_seconds"]),
                amplitude=float(row["amplitude"]),
            )
            for row in reader
        )
