import unittest

from essa.neuromorphic import NeuromorphicCompute


class NeuromorphicComputeTests(unittest.TestCase):
    def test_quiet_signals_do_not_activate_downstream_compute(self):
        compute = NeuromorphicCompute(("safety", "food", "learning"))

        pulse = compute.route({"safety": 0.1, "food": 0.1, "learning": 0.1})

        self.assertEqual(pulse.active_pathways, ())
        self.assertEqual(pulse.compute_units, 0)
        self.assertEqual(pulse.avoided_units, 3)

    def test_repeated_signal_accumulates_until_neuron_fires(self):
        compute = NeuromorphicCompute(
            ("safety",), threshold=0.7, leak=0.75, max_active=1
        )

        first = compute.route({"safety": 0.4})
        second = compute.route({"safety": 0.4})

        self.assertEqual(first.active_pathways, ())
        self.assertEqual(second.active_pathways, ("safety",))
        self.assertEqual(compute.neurons["safety"].spike_count, 1)

    def test_only_strongest_pathways_receive_compute(self):
        compute = NeuromorphicCompute(
            ("safety", "food", "learning"), threshold=0.5, max_active=2
        )

        pulse = compute.route({"safety": 1.0, "food": 0.8, "learning": 0.6})

        self.assertEqual(pulse.active_pathways, ("safety", "food"))
        self.assertEqual(pulse.inhibited_pathways, ("learning",))
        self.assertEqual(pulse.compute_units, 2)

    def test_statistics_compare_sparse_work_with_dense_baseline(self):
        compute = NeuromorphicCompute(("safety", "food", "learning"))
        compute.route(
            {"safety": 1.0, "food": 0.1, "learning": 0.1},
            minimum_active=1,
        )

        stats = compute.statistics()

        self.assertEqual(stats["compute_units"], 1)
        self.assertEqual(stats["dense_baseline_units"], 3)
        self.assertEqual(stats["avoided_units"], 2)


if __name__ == "__main__":
    unittest.main()
