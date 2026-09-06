from __future__ import annotations

import json
from typing import Any

from essa import SelfModel, StaticSubstrateInspector, SubstrateSnapshot


class SimpleSelfAwareAgent:
    """Small deterministic agent that exercises the ESSA SELF loop."""

    def __init__(self) -> None:
        self.self_model = SelfModel()
        self.environment = {
            "name": "calibration_lab",
            "signal": "needs_calibration",
        }

    def run_cycle(self) -> dict[str, Any]:
        self.self_model.inspect_substrate(
            StaticSubstrateInspector(
                SubstrateSnapshot(
                    id="example-python-runtime",
                    kind="python_runtime",
                    capabilities=(
                        "inspect_substrate",
                        "record_history",
                        "symbolic_transition",
                        "persist_self_model",
                    ),
                    constraints=("no_llm_core", "deterministic_example"),
                    attributes={"example": True},
                )
            )
        )
        self.self_model.observe_self(
            {
                "goal": "preserve_identity_while_updating_state",
                "current_mode": self.self_model.state["mode"],
            },
            evidence="SimpleSelfAwareAgent.run_cycle",
        )
        self.self_model.observe_world(
            self.environment["name"],
            {"signal": self.environment["signal"]},
            evidence="SimpleSelfAwareAgent.environment",
        )

        prediction = self.self_model.predict("transition_state")
        transition = self.self_model.act(
            "transition_state",
            {
                "status": "completed",
                "environment_signal": self.environment["signal"],
            },
            prediction=prediction,
        )

        return {
            "identity": self.self_model.identity.id,
            "essence": self.self_model.essence.kind,
            "substrate": self.self_model.substrate.id,
            "self_world_boundary": {
                "self_observations": [
                    item.value
                    for item in self.self_model.observations
                    if item.kind == "self_observation"
                ],
                "world_observations": [
                    {"target": item.target, "value": item.value}
                    for item in self.self_model.observations
                    if item.kind == "world_observation"
                ],
            },
            "prediction": {
                "action": prediction.action,
                "basis": prediction.basis,
                "confirmed": transition.prediction_confirmed,
            },
            "state": self.self_model.identify()["state"],
            "history_events": [event.kind for event in self.self_model.history],
        }


def main() -> None:
    agent = SimpleSelfAwareAgent()
    print(json.dumps(agent.run_cycle(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
