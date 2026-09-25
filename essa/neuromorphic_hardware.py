from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class NeuromorphicDevice:
    device_id: str
    backend: str
    chip_count: int
    neuron_capacity: int
    synapse_capacity: int
    event_capacity_per_step: int
    power_envelope_watts: float | None = None
    hardware_accelerated: bool = True


@dataclass(frozen=True)
class NeuromorphicWorkload:
    shard_id: str
    pathway: str
    neurons: int
    synapses: int
    events_per_step: int
    priority: int = 1
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class HardwareAllocation:
    shard_id: str
    pathway: str
    device_id: str
    neurons: int
    synapses: int
    events_per_step: int


@dataclass(frozen=True)
class InterconnectRoute:
    source_shard: str
    target_shard: str
    source_device: str
    target_device: str
    event_driven: bool = True


@dataclass(frozen=True)
class NeuromorphicScalePlan:
    allocations: tuple[HardwareAllocation, ...]
    unallocated_shards: tuple[str, ...]
    interconnect_routes: tuple[InterconnectRoute, ...]
    device_utilization: dict[str, dict[str, float | int]]
    planned_power_envelope_watts: float | None

    @property
    def complete(self) -> bool:
        return not self.unallocated_shards


class NeuromorphicHardwareAdapter(Protocol):
    def discover(self) -> tuple[NeuromorphicDevice, ...]:
        """Return devices currently available to ESSA."""

    def deploy(self, allocation: HardwareAllocation) -> dict[str, Any]:
        """Deploy one planned workload shard to a device."""


class SimulatedNeuromorphicAdapter:
    """Development adapter with the same contract as a future hardware SDK."""

    def __init__(self, devices: tuple[NeuromorphicDevice, ...]) -> None:
        self.devices = devices
        self.deployments: list[HardwareAllocation] = []

    def discover(self) -> tuple[NeuromorphicDevice, ...]:
        return self.devices

    def deploy(self, allocation: HardwareAllocation) -> dict[str, Any]:
        if allocation.device_id not in {device.device_id for device in self.devices}:
            raise ValueError(f"Device is not managed by this adapter: {allocation.device_id}")
        self.deployments.append(allocation)
        return {
            "device_id": allocation.device_id,
            "shard_id": allocation.shard_id,
            "status": "deployed",
            "simulated": True,
        }


class NeuromorphicCluster:
    """Capacity-aware planner for scaling ESSA across neuromorphic devices."""

    def __init__(self, adapters: tuple[NeuromorphicHardwareAdapter, ...]) -> None:
        self.adapters = adapters

    def discover(self) -> tuple[NeuromorphicDevice, ...]:
        devices = []
        seen = set()
        for adapter in self.adapters:
            for device in adapter.discover():
                if device.device_id in seen:
                    raise ValueError(f"Duplicate device id: {device.device_id}")
                seen.add(device.device_id)
                devices.append(device)
        return tuple(devices)

    def plan(
        self,
        workloads: tuple[NeuromorphicWorkload, ...],
        *,
        power_budget_watts: float | None = None,
    ) -> NeuromorphicScalePlan:
        devices = self.discover()
        remaining = {
            device.device_id: {
                "neurons": device.neuron_capacity,
                "synapses": device.synapse_capacity,
                "events": device.event_capacity_per_step,
            }
            for device in devices
        }
        used_devices: set[str] = set()
        allocations = []
        unallocated = []
        ordered_workloads = sorted(
            workloads,
            key=lambda item: (
                item.priority,
                item.neurons,
                item.synapses,
                item.events_per_step,
            ),
            reverse=True,
        )

        for workload in ordered_workloads:
            candidates = []
            for device in devices:
                capacity = remaining[device.device_id]
                if not self._fits(workload, capacity):
                    continue
                added_power = (
                    device.power_envelope_watts
                    if device.device_id not in used_devices
                    else 0.0
                )
                current_power = self._power_envelope(devices, used_devices)
                if power_budget_watts is not None and added_power is None:
                    continue
                if (
                    power_budget_watts is not None
                    and current_power is not None
                    and current_power + added_power > power_budget_watts
                ):
                    continue
                utilization = max(
                    workload.neurons / device.neuron_capacity,
                    workload.synapses / device.synapse_capacity,
                    workload.events_per_step / device.event_capacity_per_step,
                )
                candidates.append((utilization, device))

            if not candidates:
                unallocated.append(workload.shard_id)
                continue

            _, chosen = min(candidates, key=lambda item: (item[0], item[1].device_id))
            capacity = remaining[chosen.device_id]
            capacity["neurons"] -= workload.neurons
            capacity["synapses"] -= workload.synapses
            capacity["events"] -= workload.events_per_step
            used_devices.add(chosen.device_id)
            allocations.append(
                HardwareAllocation(
                    shard_id=workload.shard_id,
                    pathway=workload.pathway,
                    device_id=chosen.device_id,
                    neurons=workload.neurons,
                    synapses=workload.synapses,
                    events_per_step=workload.events_per_step,
                )
            )

        allocation_by_shard = {item.shard_id: item for item in allocations}
        routes = []
        for workload in workloads:
            target = allocation_by_shard.get(workload.shard_id)
            if target is None:
                continue
            for source_id in workload.depends_on:
                source = allocation_by_shard.get(source_id)
                if source and source.device_id != target.device_id:
                    routes.append(
                        InterconnectRoute(
                            source_shard=source.shard_id,
                            target_shard=target.shard_id,
                            source_device=source.device_id,
                            target_device=target.device_id,
                        )
                    )

        utilization = {}
        for device in devices:
            free = remaining[device.device_id]
            utilization[device.device_id] = {
                "neuron_fraction": round(
                    1 - free["neurons"] / device.neuron_capacity, 3
                ),
                "synapse_fraction": round(
                    1 - free["synapses"] / device.synapse_capacity, 3
                ),
                "event_fraction": round(
                    1 - free["events"] / device.event_capacity_per_step, 3
                ),
                "chip_count": device.chip_count,
            }
        return NeuromorphicScalePlan(
            allocations=tuple(allocations),
            unallocated_shards=tuple(unallocated),
            interconnect_routes=tuple(routes),
            device_utilization=utilization,
            planned_power_envelope_watts=self._power_envelope(devices, used_devices),
        )

    def deploy(self, plan: NeuromorphicScalePlan) -> list[dict[str, Any]]:
        adapter_by_device = {
            device.device_id: adapter
            for adapter in self.adapters
            for device in adapter.discover()
        }
        return [
            adapter_by_device[allocation.device_id].deploy(allocation)
            for allocation in plan.allocations
        ]

    def _fits(
        self,
        workload: NeuromorphicWorkload,
        capacity: dict[str, int],
    ) -> bool:
        return (
            workload.neurons <= capacity["neurons"]
            and workload.synapses <= capacity["synapses"]
            and workload.events_per_step <= capacity["events"]
        )

    def _power_envelope(
        self,
        devices: tuple[NeuromorphicDevice, ...],
        used_devices: set[str],
    ) -> float | None:
        selected = [device for device in devices if device.device_id in used_devices]
        if any(device.power_envelope_watts is None for device in selected):
            return None
        return round(sum(device.power_envelope_watts or 0.0 for device in selected), 3)
