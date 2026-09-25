from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from essa.sid1_io import load_detections_csv, load_sid1_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--detections", required=True)
    args = parser.parse_args()

    device, config = load_sid1_config(args.config)
    detections = load_detections_csv(args.detections)
    estimate = device.localize(
        detections,
        propagation_speed_mps=config.propagation_speed_mps,
        bounds=config.bounds,
        grid_step_meters=config.grid_step_meters,
    )
    print(
        json.dumps(
            {
                "brand": "Hasky Labs",
                "device": "ESSA-SID1",
                "blueprint": device.blueprint(),
                "estimate": asdict(estimate),
                "relay_packet": device.relay_packet(estimate),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
