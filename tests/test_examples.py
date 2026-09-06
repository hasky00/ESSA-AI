import json
import subprocess
import sys
import unittest


class ExampleTests(unittest.TestCase):
    def test_simple_self_aware_agent_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "examples.simple_self_aware_agent"],
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(result.stdout)

        self.assertEqual(output["identity"], "SELF-001")
        self.assertEqual(output["essence"], "computational_agent")
        self.assertEqual(output["substrate"], "example-python-runtime")
        self.assertTrue(output["prediction"]["confirmed"])
        self.assertIn("self_observed", output["history_events"])
        self.assertIn("world_observed", output["history_events"])
        self.assertEqual(
            output["self_world_boundary"]["world_observations"][0]["target"],
            "calibration_lab",
        )


if __name__ == "__main__":
    unittest.main()
