import unittest

from essa.haiti_education_case import (
    ESSAHaitiEducationEnvironment,
    ESSAHaitiEducationLearner,
    FoodNetworkTopology,
)


class ESSAHaitiEducationCaseTests(unittest.TestCase):
    def test_north_star_matches_child_safety_goal(self):
        learner = ESSAHaitiEducationLearner()

        self.assertIn("Prevent violence", learner.north_star)
        self.assertIn("prevent hunger", learner.north_star)
        self.assertIn("go to school", learner.north_star)
        self.assertIn("feel safe", learner.north_star)

    def test_cycle_observes_article_grounded_constraints(self):
        learner = ESSAHaitiEducationLearner()

        report = learner.run_cycle()

        self.assertIn("gang_pressure", report.observe)
        self.assertIn("group_violence", report.observe)
        self.assertIn("hunger", report.observe)
        self.assertIn("route_risk", report.observe)
        self.assertIn("trauma_signs", report.observe)
        self.assertIn("food_network_barcode", report.observe)
        self.assertIn("food_topology_risk", report.observe)
        self.assertIn("group_violence", report.detect["features"])
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
        learner = ESSAHaitiEducationLearner()

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
        learner = ESSAHaitiEducationLearner()

        reports = [learner.run_cycle() for _ in range(7)]

        self.assertEqual(len(reports), 7)
        self.assertTrue(learner.output_forward_rules())
        self.assertTrue(any(belief.evidence_count for belief in learner.world_model))

    def test_seven_day_summary_reports_measurable_change(self):
        learner = ESSAHaitiEducationLearner()
        reports = [learner.run_cycle() for _ in range(7)]

        summary = learner.summarize_run(reports)

        self.assertEqual(summary["cycles"], 7)
        self.assertGreater(summary["change"]["attendance"], 0)
        self.assertGreater(summary["change"]["felt_safety"], 0)
        self.assertLess(summary["change"]["uncertainty"], 0)
        self.assertLess(summary["hunger_pressure_change"], 0)
        self.assertEqual(sum(summary["actions"].values()), 7)
        self.assertGreaterEqual(summary["prediction_accuracy"], 0)
        self.assertLessEqual(summary["prediction_accuracy"], 1)
        self.assertTrue(summary["next_task"])

    def test_summary_requires_at_least_one_cycle(self):
        learner = ESSAHaitiEducationLearner()

        with self.assertRaises(ValueError):
            learner.summarize_run([])

    def test_haiti_case_records_and_recalls_cognitive_memory(self):
        learner = ESSAHaitiEducationLearner()

        reports = [learner.run_cycle() for _ in range(7)]

        self.assertEqual(len(learner.cognitive_memory.episodes), 7)
        self.assertTrue(learner.cognitive_memory.semantic_memories)
        self.assertTrue(
            any(
                candidate["basis"] == "episodic_memory"
                for report in reports
                for candidate in report.predict["candidates"]
            )
        )
        self.assertIn("memory_episode", reports[-1].update)
        self.assertEqual(
            learner.self_model.state["episodic_memory_count"],
            7,
        )

    def test_safe_learning_space_can_buffer_blocked_school(self):
        environment = ESSAHaitiEducationEnvironment()

        result = environment.apply("create_safe_learning_space")

        self.assertEqual(result.visible_effect["learning_space"], "temporary_safe")

    def test_cycle_text_uses_requested_loop_format(self):
        learner = ESSAHaitiEducationLearner()

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
