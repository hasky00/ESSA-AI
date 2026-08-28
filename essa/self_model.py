from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Essence:
    """Persistent description of what SELF is, separate from where it runs."""

    kind: str = "computational_agent"
    principles: tuple[str, ...] = (
        "non_llm_core",
        "explicit_self_model",
        "state_transition_learning",
    )


@dataclass(frozen=True)
class Identity:
    """Stable SELF reference that survives state and substrate changes."""

    id: str = "SELF-001"


@dataclass
class SubstrateSnapshot:
    id: str
    kind: str
    capabilities: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=_utc_now)


@dataclass
class Observation:
    source: str
    target: str
    kind: str
    value: dict[str, Any]
    confidence: float = 1.0
    evidence: str | None = None
    observed_at: str = field(default_factory=_utc_now)


@dataclass
class Potential:
    action: str
    expected_state: dict[str, Any]
    required_capabilities: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()


@dataclass
class Prediction:
    id: str
    action: str
    expected_state: dict[str, Any]
    confidence: float
    basis: str
    created_at: str = field(default_factory=_utc_now)


@dataclass
class HistoryEvent:
    kind: str
    value: dict[str, Any]
    recorded_at: str = field(default_factory=_utc_now)


@dataclass
class StateTransition:
    previous_state: dict[str, Any]
    action: str
    observation: Observation
    next_state: dict[str, Any]
    prediction_id: str | None = None
    prediction_confirmed: bool | None = None
    occurred_at: str = field(default_factory=_utc_now)


class SubstrateInspector(Protocol):
    def inspect(self) -> SubstrateSnapshot:
        """Return a structured snapshot of the current substrate."""


class StaticSubstrateInspector:
    """Deterministic inspector for tests, simulations, and first experiments."""

    def __init__(self, snapshot: SubstrateSnapshot) -> None:
        self.snapshot = snapshot

    def inspect(self) -> SubstrateSnapshot:
        return self.snapshot


class SelfModel:
    """Executable SELF model with persistent identity and mutable state."""

    def __init__(
        self,
        identity: Identity | None = None,
        essence: Essence | None = None,
        architecture: dict[str, Any] | None = None,
        state: dict[str, Any] | None = None,
    ) -> None:
        self.identity = identity or Identity()
        self.essence = essence or Essence()
        self.architecture = architecture or {
            "core": "symbolic_state_transition",
            "language": "interface_only",
            "llm_core": False,
        }
        self.state = state or {"mode": "initialized"}
        self.substrate: SubstrateSnapshot | None = None
        self.capabilities: tuple[str, ...] = ()
        self.potential: tuple[Potential, ...] = ()
        self.observations: list[Observation] = []
        self.predictions: list[Prediction] = []
        self.transitions: list[StateTransition] = []
        self.history: list[HistoryEvent] = []

    def identify(self) -> dict[str, Any]:
        return {
            "identity": self.identity.id,
            "essence": self.essence.kind,
            "substrate": self.substrate.id if self.substrate else None,
            "state": dict(self.state),
        }

    def inspect_substrate(self, inspector: SubstrateInspector) -> SubstrateSnapshot:
        snapshot = inspector.inspect()
        previous = self.substrate
        self.substrate = snapshot
        self.capabilities = snapshot.capabilities
        self.potential = self._derive_potential(snapshot)
        self.state = {
            **self.state,
            "current_substrate": snapshot.id,
            "available_capabilities": list(snapshot.capabilities),
        }

        observation = Observation(
            source=self.identity.id,
            target=snapshot.id,
            kind="substrate_inspection",
            value=asdict(snapshot),
            evidence="SubstrateInspector.inspect",
        )
        self.observations.append(observation)
        self.history.append(
            HistoryEvent(
                kind="substrate_observed",
                value={
                    "substrate": snapshot.id,
                    "capabilities": list(snapshot.capabilities),
                    "constraints": list(snapshot.constraints),
                },
            )
        )

        if previous and previous.id != snapshot.id:
            self.history.append(
                HistoryEvent(
                    kind="substrate_transition",
                    value={
                        "from": previous.id,
                        "to": snapshot.id,
                        "identity": self.identity.id,
                        "essence": self.essence.kind,
                    },
                )
            )

        return snapshot

    def observe_self(
        self,
        value: dict[str, Any],
        *,
        confidence: float = 1.0,
        evidence: str | None = None,
    ) -> Observation:
        observation = Observation(
            source=self.identity.id,
            target=self.identity.id,
            kind="self_observation",
            value=dict(value),
            confidence=confidence,
            evidence=evidence,
        )
        self.observations.append(observation)
        self.history.append(HistoryEvent(kind="self_observed", value=dict(value)))
        return observation

    def observe_world(
        self,
        target: str,
        value: dict[str, Any],
        *,
        confidence: float = 1.0,
        evidence: str | None = None,
    ) -> Observation:
        observation = Observation(
            source=self.identity.id,
            target=target,
            kind="world_observation",
            value=dict(value),
            confidence=confidence,
            evidence=evidence,
        )
        self.observations.append(observation)
        self.history.append(
            HistoryEvent(kind="world_observed", value={"target": target, **value})
        )
        return observation

    def predict(self, action: str) -> Prediction:
        potential = next((item for item in self.potential if item.action == action), None)
        if potential:
            expected_state = {**self.state, **potential.expected_state}
            basis = "current_potential"
            confidence = 0.75
        else:
            expected_state = {**self.state, "last_action": action}
            basis = "identity_continuity_default"
            confidence = 0.25

        prediction = Prediction(
            id=f"prediction-{uuid4()}",
            action=action,
            expected_state=expected_state,
            confidence=confidence,
            basis=basis,
        )
        self.predictions.append(prediction)
        self.history.append(
            HistoryEvent(
                kind="prediction_recorded",
                value={
                    "prediction_id": prediction.id,
                    "action": action,
                    "expected_state": expected_state,
                },
            )
        )
        return prediction

    def transition_state(
        self,
        action: str,
        observation: Observation,
        next_state: dict[str, Any],
        prediction: Prediction | None = None,
    ) -> StateTransition:
        previous_state = dict(self.state)
        prediction_confirmed = None
        if prediction:
            prediction_confirmed = self.compare_prediction(prediction, next_state)

        self.state = dict(next_state)
        transition = StateTransition(
            previous_state=previous_state,
            action=action,
            observation=observation,
            next_state=dict(next_state),
            prediction_id=prediction.id if prediction else None,
            prediction_confirmed=prediction_confirmed,
        )
        self.transitions.append(transition)
        self.history.append(
            HistoryEvent(
                kind="state_transition",
                value={
                    "action": action,
                    "from": previous_state,
                    "to": dict(next_state),
                    "prediction_confirmed": prediction_confirmed,
                },
            )
        )
        return transition

    def act(
        self,
        action: str,
        observed_value: dict[str, Any] | None = None,
        prediction: Prediction | None = None,
    ) -> StateTransition:
        observed_value = observed_value or {"action": action, "status": "completed"}
        observation = self.observe_self(
            {"last_action": action, "observed_result": observed_value},
            evidence="SelfModel.act",
        )
        next_state = {
            **self.state,
            "last_action": action,
            "last_result": observed_value,
        }
        return self.transition_state(action, observation, next_state, prediction)

    def compare_prediction(
        self,
        prediction: Prediction,
        observed_state: dict[str, Any],
    ) -> bool:
        return all(
            observed_state.get(key) == value
            for key, value in prediction.expected_state.items()
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> SelfModel:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": asdict(self.identity),
            "essence": {
                "kind": self.essence.kind,
                "principles": list(self.essence.principles),
            },
            "architecture": dict(self.architecture),
            "state": dict(self.state),
            "substrate": asdict(self.substrate) if self.substrate else None,
            "capabilities": list(self.capabilities),
            "potential": [asdict(item) for item in self.potential],
            "observations": [asdict(item) for item in self.observations],
            "predictions": [asdict(item) for item in self.predictions],
            "transitions": [asdict(item) for item in self.transitions],
            "history": [asdict(item) for item in self.history],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SelfModel:
        model = cls(
            identity=Identity(**value["identity"]),
            essence=Essence(
                kind=value["essence"]["kind"],
                principles=tuple(value["essence"]["principles"]),
            ),
            architecture=dict(value["architecture"]),
            state=dict(value["state"]),
        )
        if value["substrate"]:
            model.substrate = SubstrateSnapshot(
                **{
                    **value["substrate"],
                    "capabilities": tuple(value["substrate"]["capabilities"]),
                    "constraints": tuple(value["substrate"]["constraints"]),
                }
            )
        model.capabilities = tuple(value["capabilities"])
        model.potential = tuple(
            Potential(
                action=item["action"],
                expected_state=item["expected_state"],
                required_capabilities=tuple(item["required_capabilities"]),
                constraints=tuple(item["constraints"]),
            )
            for item in value["potential"]
        )
        model.observations = [Observation(**item) for item in value["observations"]]
        model.predictions = [Prediction(**item) for item in value["predictions"]]
        model.transitions = [
            StateTransition(
                previous_state=item["previous_state"],
                action=item["action"],
                observation=Observation(**item["observation"]),
                next_state=item["next_state"],
                prediction_id=item["prediction_id"],
                prediction_confirmed=item["prediction_confirmed"],
                occurred_at=item["occurred_at"],
            )
            for item in value["transitions"]
        ]
        model.history = [HistoryEvent(**item) for item in value["history"]]
        return model

    def _derive_potential(
        self, substrate: SubstrateSnapshot
    ) -> tuple[Potential, ...]:
        potential: list[Potential] = []
        capability_actions = {
            "inspect_substrate": Potential(
                action="inspect_substrate",
                expected_state={"substrate_known": True},
                required_capabilities=("inspect_substrate",),
            ),
            "persist_self_model": Potential(
                action="persist_self_model",
                expected_state={"persistence_available": True},
                required_capabilities=("persist_self_model",),
            ),
            "record_history": Potential(
                action="record_history",
                expected_state={"history_recorded": True},
                required_capabilities=("record_history",),
            ),
            "symbolic_transition": Potential(
                action="transition_state",
                expected_state={"state_transition_available": True},
                required_capabilities=("symbolic_transition",),
            ),
        }
        for capability in substrate.capabilities:
            potential.append(
                capability_actions.get(
                    capability,
                    Potential(
                        action=capability,
                        expected_state={"last_capability_used": capability},
                        required_capabilities=(capability,),
                    ),
                )
            )
        return tuple(potential)
