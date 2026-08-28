import tempfile
import unittest
from pathlib import Path

from essa.self_model import SelfModel, StaticSubstrateInspector, SubstrateSnapshot


class SelfModelTests(unittest.TestCase):
    def test_identity_and_essence_survive_substrate_change(self):
        model = SelfModel()
        substrate_a = SubstrateSnapshot(
            id="H100",
            kind="gpu",
            capabilities=("inspect_substrate", "record_history"),
        )
        substrate_b = SubstrateSnapshot(
            id="RTX_5090",
            kind="gpu",
            capabilities=("inspect_substrate", "symbolic_transition"),
        )

        model.inspect_substrate(StaticSubstrateInspector(substrate_a))
        model.inspect_substrate(StaticSubstrateInspector(substrate_b))

        self.assertEqual(model.identity.id, "SELF-001")
        self.assertEqual(model.essence.kind, "computational_agent")
        self.assertEqual(model.substrate.id, "RTX_5090")
        self.assertIn("symbolic_transition", model.capabilities)
        self.assertTrue(
            any(event.kind == "substrate_transition" for event in model.history)
        )

    def test_self_and_world_observations_are_distinct(self):
        model = SelfModel()

        self_observation = model.observe_self({"uncertainty": 0.2})
        world_observation = model.observe_world("ENVIRONMENT", {"temperature": 19})

        self.assertEqual(self_observation.target, "SELF-001")
        self.assertEqual(self_observation.kind, "self_observation")
        self.assertEqual(world_observation.target, "ENVIRONMENT")
        self.assertEqual(world_observation.kind, "world_observation")

    def test_prediction_action_and_transition_record_history(self):
        model = SelfModel()
        model.inspect_substrate(
            StaticSubstrateInspector(
                SubstrateSnapshot(
                    id="symbolic-runtime",
                    kind="runtime",
                    capabilities=("symbolic_transition",),
                )
            )
        )

        prediction = model.predict("transition_state")
        transition = model.act(
            "transition_state",
            {"status": "completed"},
            prediction=prediction,
        )

        self.assertEqual(transition.previous_state["current_substrate"], "symbolic-runtime")
        self.assertEqual(model.state["last_action"], "transition_state")
        self.assertIsNotNone(transition.prediction_id)
        self.assertEqual(model.transitions[-1], transition)
        self.assertTrue(any(event.kind == "state_transition" for event in model.history))

    def test_self_model_persists_to_json_and_loads_back(self):
        model = SelfModel()
        model.inspect_substrate(
            StaticSubstrateInspector(
                SubstrateSnapshot(
                    id="portable-runtime",
                    kind="runtime",
                    capabilities=("persist_self_model", "record_history"),
                )
            )
        )
        model.observe_self({"mode": "testing"})

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "self.json"
            model.save(path)
            loaded = SelfModel.load(path)

        self.assertEqual(loaded.identity.id, model.identity.id)
        self.assertEqual(loaded.essence.kind, model.essence.kind)
        self.assertEqual(loaded.substrate.id, "portable-runtime")
        self.assertEqual(len(loaded.history), len(model.history))


if __name__ == "__main__":
    unittest.main()
