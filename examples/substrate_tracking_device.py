from __future__ import annotations

from dataclasses import asdict
import json
from math import hypot

from essa.substrate_intelligence import (
    SubstrateDetection,
    SubstrateIntelligenceDevice,
    SubstrateSensorNode,
)


def main() -> None:
    sensors = (
        SubstrateSensorNode("riverbed-nw", 0, 100, "water", "hydrophone"),
        SubstrateSensorNode("riverbed-ne", 100, 100, "water", "hydrophone"),
        SubstrateSensorNode("riverbed-sw", 0, 0, "water", "hydrophone"),
        SubstrateSensorNode("riverbed-se", 100, 0, "water", "hydrophone"),
    )
    device = SubstrateIntelligenceDevice(
        "SID-1-crocodile-localizer",
        sensors,
        relay_enabled=False,
    )
    actual_x, actual_y = 37.0, 64.0
    emission_time = 100.0
    sound_speed_mps = 1_500.0
    detections = tuple(
        SubstrateDetection(
            sensor_id=sensor.sensor_id,
            source_signature="authorized-acoustic-tag-crocodile-01",
            arrival_time_seconds=emission_time
            + hypot(actual_x - sensor.x_meters, actual_y - sensor.y_meters)
            / sound_speed_mps,
        )
        for sensor in sensors
    )
    estimate = device.localize(
        detections,
        propagation_speed_mps=sound_speed_mps,
        bounds=(0, 100, 0, 100),
        grid_step_meters=1.0,
    )
    error_meters = hypot(
        estimate.x_meters - actual_x,
        estimate.y_meters - actual_y,
    )
    print(
        json.dumps(
            {
                "status": "software_reference_device",
                "blueprint": device.blueprint(),
                "actual_position_for_simulation_only": {
                    "x_meters": actual_x,
                    "y_meters": actual_y,
                },
                "local_estimate": asdict(estimate),
                "localization_error_meters": round(error_meters, 3),
                "satellite_used_for_localization": False,
                "relay_packet": device.relay_packet(estimate),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
