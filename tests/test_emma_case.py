import unittest

from essa.emma_case import (
    EmmaHaitiEducationEnvironment,
    EmmaHaitiEducationLearner,
    FoodNetworkTopology,
)


class EmmaHaitiEducationCaseTests(unittest.TestCase):
    def test_north_star_matches_child_safety_goal(self):
        learner = EmmaHaitiEducationLearner()

        self.assertIn("Prevent violence", learner.north_star)
        self.assertIn("prevent hunger", learner.north_star)
        self.assertIn("go to school", learner.north_star)
        self.assertIn("feel safe", learner.north_star)

    def test_cycle_observes_article_grounded_constraints(self):
        learner = EmmaHaitiEducationLearner()

        report = learner.run_cycle()

        self.assertIn("gang_pressure", report.observe)
        self.assertIn("hunger", report.observe)
        self.assertIn("route_risk", report.observe)
        self.assertIn("trauma_signs", report.observe)
        self.assertIn("food_network_barcode", report.observe)
        self.assertIn("food_topology_risk", report.observe)
        self.assertEqual(len(report.hypothesize), 3)
        self.assertIn("chosen_action", report.predict)
        self.assertIn("belief_updates", report.update)
        self.assertTrue(report.next_task)

    def test_food_network_topology_creates_lightweight_barcode(self):
        topology = FoodNetworkTopology()

        barcode = topology.barcode(turn=1, stabilization_buffer=0)

        self.assertTrue(barcode)
        self.assertTrue(any(item.birth_scale == "local" for item in barcode))
        self.assertTrue(
            any(item.death_scale == "global_commodity_market" for item in barcode)
        )
        self.assertGreater(topology.risk_score(barcode), 0)

    def test_high_food_topology_risk_can_select_distribution_action(self):
        learner = EmmaHaitiEducationLearner()

        learner.run_cycle()
        report = learner.run_cycle()

        self.assertEqual(
            report.predict["chosen_action"],
            "stabilize_food_distribution_network",
        )
        self.assertEqual(
            report.predict["candidates"][1]["action"],
            "stabilize_food_distribution_network",
        )

    def test_seven_day_loop_updates_world_model(self):
        learner = EmmaHaitiEducationLearner()

        reports = [learner.run_cycle() for _ in range(7)]

        self.assertEqual(len(reports), 7)
        self.assertTrue(learner.output_forward_rules())
        self.assertTrue(any(belief.evidence_count for belief in learner.world_model))

    def test_safe_learning_space_can_buffer_blocked_school(self):
        environment = EmmaHaitiEducationEnvironment()

        result = environment.apply("create_safe_learning_space")

        self.assertEqual(result.visible_effect["learning_space"], "temporary_safe")

    def test_cycle_text_uses_requested_loop_format(self):
        learner = EmmaHaitiEducationLearner()

        text = learner.cycle_text(learner.run_cycle())

        self.assertIn("OBSERVED:", text)
        self.assertIn("SURPRISES:", text)
        self.assertIn("HYPOTHESES:", text)
        self.assertIn("CHOSEN ACTION + PREDICTION:", text)
        self.assertIn("RESULT:", text)
        self.assertIn("MODEL UPDATE:", text)
        self.assertIn("NEXT TASK:", text)


if __name__ == "__main__":
    unittest.main()
