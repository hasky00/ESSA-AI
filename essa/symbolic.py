from dataclasses import dataclass, field
from typing import Any


@dataclass
class Relation:
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class Entity:
    id: str
    essence: str
    substrate: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class Observation:
    source: str
    target: str
    value: Any
    confidence: float = 1.0
    evidence: str | None = None


@dataclass
class StateTransition:
    previous_state: dict[str, Any]
    action: str
    observation: Observation
    next_state: dict[str, Any]


class ESSAWorld:
    """Minimal symbolic world model for ESSA v0.1."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.observations: list[Observation] = []
        self.transitions: list[StateTransition] = []

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def observe(self, observation: Observation) -> None:
        self.observations.append(observation)

    def transition(
        self,
        entity_id: str,
        action: str,
        observation: Observation,
        next_state: dict[str, Any],
    ) -> StateTransition:
        entity = self.entities[entity_id]
        transition = StateTransition(
            previous_state=dict(entity.state),
            action=action,
            observation=observation,
            next_state=next_state,
        )
        entity.state = dict(next_state)
        self.observations.append(observation)
        self.transitions.append(transition)
        return transition
