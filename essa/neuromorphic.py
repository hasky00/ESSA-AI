from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PathwayNeuron:
    name: str
    threshold: float = 0.7
    leak: float = 0.5
    membrane_potential: float = 0.0
    spike_count: int = 0

    def integrate(self, stimulus: float) -> float:
        bounded = max(0.0, min(1.0, stimulus))
        self.membrane_potential = min(
            1.5,
            self.membrane_potential * self.leak + bounded,
        )
        return self.membrane_potential

    def fire(self) -> None:
        self.spike_count += 1
        self.membrane_potential = 0.0


@dataclass(frozen=True)
class ComputePulse:
    cycle: int
    active_pathways: tuple[str, ...]
    inhibited_pathways: tuple[str, ...]
    stimuli: dict[str, float]
    membrane_potentials: dict[str, float]
    compute_units: int
    dense_baseline_units: int
    avoided_units: int
    reason: str


class NeuromorphicCompute:
    """Small leaky-integrate-and-fire gate for sparse cognitive processing.

    Compute units count activated cognitive pathways. They are an operation proxy,
    not a measurement of electrical power.
    """

    def __init__(
        self,
        pathways: tuple[str, ...],
        *,
        threshold: float = 0.7,
        leak: float = 0.5,
        max_active: int = 2,
    ) -> None:
        if not pathways:
            raise ValueError("At least one pathway is required")
        if max_active < 1:
            raise ValueError("max_active must be positive")
        self.pathway_order = pathways
        self.max_active = min(max_active, len(pathways))
        self.neurons = {
            name: PathwayNeuron(name=name, threshold=threshold, leak=leak)
            for name in pathways
        }
        self.cycle = 0
        self.total_compute_units = 0
        self.total_dense_baseline_units = 0

    def route(
        self,
        stimuli: dict[str, float],
        *,
        minimum_active: int = 0,
    ) -> ComputePulse:
        unknown = set(stimuli) - set(self.neurons)
        if unknown:
            raise ValueError(f"Unknown cognitive pathways: {sorted(unknown)}")
        self.cycle += 1
        potentials = {
            name: round(self.neurons[name].integrate(stimuli.get(name, 0.0)), 3)
            for name in self.pathway_order
        }
        firing = [
            name
            for name in self.pathway_order
            if potentials[name] >= self.neurons[name].threshold
        ]
        firing.sort(key=lambda name: potentials[name], reverse=True)
        active = firing[: self.max_active]
        reason = "spike_triggered"

        required = min(max(0, minimum_active), self.max_active)
        if len(active) < required:
            remaining = [name for name in self.pathway_order if name not in active]
            remaining.sort(key=lambda name: potentials[name], reverse=True)
            active.extend(remaining[: required - len(active)])
            reason = "minimum_competing_hypotheses"

        for name in active:
            self.neurons[name].fire()

        inhibited = tuple(name for name in self.pathway_order if name not in active)
        compute_units = len(active)
        dense_units = len(self.pathway_order)
        self.total_compute_units += compute_units
        self.total_dense_baseline_units += dense_units
        return ComputePulse(
            cycle=self.cycle,
            active_pathways=tuple(active),
            inhibited_pathways=inhibited,
            stimuli={
                name: round(max(0.0, min(1.0, stimuli.get(name, 0.0))), 3)
                for name in self.pathway_order
            },
            membrane_potentials=potentials,
            compute_units=compute_units,
            dense_baseline_units=dense_units,
            avoided_units=dense_units - compute_units,
            reason=reason,
        )

    def statistics(self) -> dict[str, float | int]:
        baseline = self.total_dense_baseline_units
        avoided = baseline - self.total_compute_units
        return {
            "cycles": self.cycle,
            "compute_units": self.total_compute_units,
            "dense_baseline_units": baseline,
            "avoided_units": avoided,
            "avoided_fraction": round(avoided / baseline, 3) if baseline else 0.0,
        }
