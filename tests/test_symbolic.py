import unittest

from essa.symbolic import Entity, ESSAWorld, Observation, Relation


class SymbolicCoreTests(unittest.TestCase):
    def test_world_can_represent_self(self):
        world = ESSAWorld()
        self_entity = Entity(
            id="SELF",
            essence="computational_agent",
            substrate="test_runtime",
            state={"task": "idle"},
            architecture={"core": "symbolic"},
        )
        world.add_entity(self_entity)

        self.assertEqual(world.entities["SELF"].essence, "computational_agent")
        self.assertEqual(world.entities["SELF"].substrate, "test_runtime")


    def test_relation_can_link_self_to_substrate(self):
        relation = Relation("SELF", "instantiated_on", "H100")
        self.assertEqual(relation.predicate, "instantiated_on")


    def test_observation_updates_state_through_transition(self):
        world = ESSAWorld()
        world.add_entity(Entity(id="SELF", essence="agent", state={"load": 0}))

        observation = Observation(
            source="SELF",
            target="GPU",
            value={"load": 75},
            evidence="benchmark",
        )
        transition = world.transition(
            entity_id="SELF",
            action="run_kernel",
            observation=observation,
            next_state={"load": 75},
        )

        self.assertEqual(transition.previous_state, {"load": 0})
        self.assertEqual(world.entities["SELF"].state, {"load": 75})
        self.assertEqual(len(world.transitions), 1)


if __name__ == "__main__":
    unittest.main()
