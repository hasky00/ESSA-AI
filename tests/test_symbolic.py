from essa.symbolic import Entity, ESSAWorld, Observation, Relation


def test_world_can_represent_self():
    world = ESSAWorld()
    self_entity = Entity(
        id="SELF",
        essence="computational_agent",
        substrate="test_runtime",
        state={"task": "idle"},
        architecture={"core": "symbolic"},
    )
    world.add_entity(self_entity)

    assert world.entities["SELF"].essence == "computational_agent"
    assert world.entities["SELF"].substrate == "test_runtime"


def test_relation_can_link_self_to_substrate():
    relation = Relation("SELF", "instantiated_on", "H100")
    assert relation.predicate == "instantiated_on"


def test_observation_updates_state_through_transition():
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

    assert transition.previous_state == {"load": 0}
    assert world.entities["SELF"].state == {"load": 75}
    assert len(world.transitions) == 1
