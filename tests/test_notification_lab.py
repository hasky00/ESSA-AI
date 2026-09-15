import unittest

from essa.notification_lab import (
    NotificationEnergyEnvironment,
    NotificationEnergyLearner,
)


class NotificationEnergyLabTests(unittest.TestCase):
    def test_seed_beliefs_match_notification_energy_case(self):
        learner = NotificationEnergyLearner()

        beliefs = {belief["id"]: belief for belief in learner.output_world_model()}

        self.assertEqual(
            learner.north_star,
            "Find out if phone notification drains your energy.",
        )
        self.assertIn("Too many phone notifications", beliefs["B1"]["belief"])
        self.assertIn("5 minutes", beliefs["B2"]["belief"])
        self.assertIn("Walking", beliefs["B3"]["belief"])
        self.assertIn("No notification", beliefs["B4"]["belief"])

    def test_cycle_uses_notification_observations_and_updates_beliefs(self):
        learner = NotificationEnergyLearner()
        before = {belief.id: belief.confidence for belief in learner.world_model}

        report = learner.run_cycle()

        self.assertIn("sleep_hours", report.observe)
        self.assertIn("phone_notifications", report.observe)
        self.assertIn("attention_minutes", report.observe)
        self.assertEqual(len(report.hypothesize), 3)
        self.assertIn("chosen_action", report.predict)
        self.assertIn("belief_updates", report.update)
        self.assertTrue(report.next_task)
        after = {belief.id: belief.confidence for belief in learner.world_model}
        self.assertNotEqual(before, after)

    def test_switching_off_notifications_can_create_no_disturbance(self):
        environment = NotificationEnergyEnvironment()

        result = environment.apply("switch_off_notifications")

        self.assertEqual(result.visible_effect["notification_mode"], "off")
        self.assertEqual(result.visible_effect["disturbance"], "none")

    def test_cycle_text_uses_requested_output_format(self):
        learner = NotificationEnergyLearner()

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
