from __future__ import annotations

import argparse
import json

from essa.neuromorphic_hardware import (
    NeuromorphicCluster,
    NeuromorphicDevice,
    NeuromorphicWorkload,
    SimulatedNeuromorphicAdapter,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--devices", type=int, default=4)
    parser.add_argument("--power-budget", type=float, default=20.0)
    args = parser.parse_args()
    if args.devices < 1:
        parser.error("--devices must be at least 1")

    devices = tuple(
        NeuromorphicDevice(
            device_id=f"neuromorphic-node-{index + 1}",
            backend="simulated_hardware_adapter",
            chip_count=1,
            neuron_capacity=1_000,
            synapse_capacity=8_000,
            event_capacity_per_step=1_000,
            power_envelope_watts=5.0,
            hardware_accelerated=False,
        )
        for index in range(args.devices)
    )
    workloads = (
        NeuromorphicWorkload("safety", "safety", 700, 4_000, 500, priority=4),
        NeuromorphicWorkload("food", "food", 650, 3_500, 450, priority=3),
        NeuromorphicWorkload("learning", "learning", 700, 4_200, 500, priority=3),
        NeuromorphicWorkload(
            "memory",
            "cognitive_memory",
            600,
            3_800,
            350,
            priority=2,
            depends_on=("safety", "food", "learning"),
        ),
    )
    adapter = SimulatedNeuromorphicAdapter(devices)
    cluster = NeuromorphicCluster((adapter,))
    plan = cluster.plan(workloads, power_budget_watts=args.power_budget)
    deployments = cluster.deploy(plan)
    print(
        json.dumps(
            {
                "mode": "capacity_planning_simulation",
                "hardware_attached": False,
                "devices_discovered": len(devices),
                "power_budget_watts": args.power_budget,
                "planned_power_envelope_watts": plan.planned_power_envelope_watts,
                "complete": plan.complete,
                "allocations": [item.__dict__ for item in plan.allocations],
                "unallocated_shards": list(plan.unallocated_shards),
                "interconnect_routes": [
                    item.__dict__ for item in plan.interconnect_routes
                ],
                "device_utilization": plan.device_utilization,
                "deployments": deployments,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
