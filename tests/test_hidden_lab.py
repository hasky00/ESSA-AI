import unittest

from essa.hidden_lab import ESSAHiddenRuleLearner, HiddenConstraintEnvironment


class HiddenLabTests(unittest.TestCase):
    def test_cycle_contains_full_essa_loop(self):
        learner = ESSAHiddenRuleLearner()

        report = learner.run_cycle()

        self.assertEqual(report.cycle, 1)
        self.assertIn("signal", report.observe)
        self.assertIn("condition_key", report.detect)
        self.assertEqual(len(report.hypothesize), 3)
        self.assertIn("chosen_action", report.predict)
        self.assertIn("written_prediction", report.predict)
        self.assertIn("expected_information_gain", report.predict)
        self.assertIn("cost_risk", report.predict)
        self.assertIn("north_star_progress", report.predict)
        self.assertIn("visible_effect", report.act)
        self.assertIn("prediction_confirmed", report.evaluate)
        self.assertIn("belief_updates", report.update)
        self.assertTrue(report.next_task)
        self.assertTrue(report.north_star)
        self.assertGreaterEqual(len(report.output_forward_rules), 1)

    def test_hidden_rules_are_not_exposed_in_observation(self):
        learner = ESSAHiddenRuleLearner()

        report = learner.run_cycle()

        self.assertNotIn("hidden", report.observe)
        self.assertNotIn("rule", report.observe)
        self.assertIn("rule", report.update)

    def test_repeated_cycles_update_rules_and_self_model_history(self):
        learner = ESSAHiddenRuleLearner()

        reports = [learner.run_cycle() for _ in range(8)]

        self.assertEqual(reports[-1].cycle, 8)
        self.assertGreaterEqual(len(learner.learned_rules), 4)
        self.assertTrue(learner.output_forward_rules())
        self.assertIn("learned_rule_count", learner.self_model.state)
        self.assertIn("belief_count", learner.self_model.state)
        self.assertTrue(
            any(event.kind == "state_transition" for event in learner.self_model.history)
        )

    def test_environment_changes_one_cycle_at_a_time(self):
        environment = HiddenConstraintEnvironment(uncertainty=8.0, energy=7)
        learner = ESSAHiddenRuleLearner(environment=environment)

        first = learner.run_cycle()
        second = learner.run_cycle()

        self.assertEqual(first.observe["turn"], 0)
        self.assertEqual(second.observe["turn"], 1)
        self.assertNotEqual(first.observe["signal"], second.observe["signal"])

    def test_world_model_confidence_changes_after_cycle(self):
        learner = ESSAHiddenRuleLearner()
        before = {belief.id: belief.confidence for belief in learner.world_model}

        learner.run_cycle()

        after = {belief.id: belief.confidence for belief in learner.world_model}
        self.assertNotEqual(before, after)

    def test_cycle_text_uses_requested_output_format(self):
        learner = ESSAHiddenRuleLearner()

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
