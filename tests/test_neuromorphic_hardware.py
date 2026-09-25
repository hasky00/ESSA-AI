import unittest

from essa.neuromorphic_hardware import (
    NeuromorphicCluster,
    NeuromorphicDevice,
    NeuromorphicWorkload,
    SimulatedNeuromorphicAdapter,
)


def device(device_id: str) -> NeuromorphicDevice:
    return NeuromorphicDevice(
        device_id=device_id,
        backend="test",
        chip_count=1,
        neuron_capacity=1_000,
        synapse_capacity=5_000,
        event_capacity_per_step=1_000,
        power_envelope_watts=5.0,
        hardware_accelerated=False,
    )


class NeuromorphicHardwareTests(unittest.TestCase):
    def test_adding_devices_scales_allocatable_workload(self):
        workloads = tuple(
            NeuromorphicWorkload(f"shard-{index}", "memory", 700, 3_000, 400)
            for index in range(3)
        )
        one = NeuromorphicCluster((SimulatedNeuromorphicAdapter((device("n1"),)),))
        three = NeuromorphicCluster(
            (
                SimulatedNeuromorphicAdapter(
                    (device("n1"), device("n2"), device("n3"))
                ),
            )
        )

        one_plan = one.plan(workloads)
        three_plan = three.plan(workloads)

        self.assertEqual(len(one_plan.allocations), 1)
        self.assertFalse(one_plan.complete)
        self.assertEqual(len(three_plan.allocations), 3)
        self.assertTrue(three_plan.complete)

    def test_power_budget_limits_used_hardware(self):
        cluster = NeuromorphicCluster(
            (SimulatedNeuromorphicAdapter((device("n1"), device("n2"))),)
        )
        workloads = (
            NeuromorphicWorkload("safety", "safety", 700, 3_000, 400),
            NeuromorphicWorkload("memory", "memory", 700, 3_000, 400),
        )

        plan = cluster.plan(workloads, power_budget_watts=5.0)

        self.assertEqual(len(plan.allocations), 1)
        self.assertEqual(plan.planned_power_envelope_watts, 5.0)
        self.assertEqual(len(plan.unallocated_shards), 1)

    def test_dependencies_across_devices_create_event_routes(self):
        cluster = NeuromorphicCluster(
            (SimulatedNeuromorphicAdapter((device("n1"), device("n2"))),)
        )
        workloads = (
            NeuromorphicWorkload("safety", "safety", 700, 3_000, 400),
            NeuromorphicWorkload(
                "memory",
                "memory",
                700,
                3_000,
                400,
                depends_on=("safety",),
            ),
        )

        plan = cluster.plan(workloads)

        self.assertEqual(len(plan.interconnect_routes), 1)
        self.assertTrue(plan.interconnect_routes[0].event_driven)

    def test_strict_power_budget_rejects_unknown_power_device(self):
        unknown_power = NeuromorphicDevice(
            device_id="unknown",
            backend="test",
            chip_count=1,
            neuron_capacity=1_000,
            synapse_capacity=5_000,
            event_capacity_per_step=1_000,
            power_envelope_watts=None,
        )
        cluster = NeuromorphicCluster(
            (SimulatedNeuromorphicAdapter((unknown_power,)),)
        )

        plan = cluster.plan(
            (NeuromorphicWorkload("safety", "safety", 100, 500, 100),),
            power_budget_watts=20.0,
        )

        self.assertFalse(plan.complete)
        self.assertEqual(plan.unallocated_shards, ("safety",))

    def test_cluster_deploys_through_owning_adapter(self):
        adapter = SimulatedNeuromorphicAdapter((device("n1"),))
        cluster = NeuromorphicCluster((adapter,))
        plan = cluster.plan(
            (NeuromorphicWorkload("safety", "safety", 100, 500, 100),)
        )

        results = cluster.deploy(plan)

        self.assertEqual(results[0]["status"], "deployed")
        self.assertEqual(adapter.deployments[0].shard_id, "safety")


if __name__ == "__main__":
    unittest.main()
