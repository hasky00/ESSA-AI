import unittest
from math import hypot

from essa.substrate_intelligence import (
    SubstrateDetection,
    SubstrateIntelligenceDevice,
    SubstrateSensorNode,
)


def water_sensors():
    return (
        SubstrateSensorNode("nw", 0, 100, "water", "hydrophone"),
        SubstrateSensorNode("ne", 100, 100, "water", "hydrophone"),
        SubstrateSensorNode("sw", 0, 0, "water", "hydrophone"),
        SubstrateSensorNode("se", 100, 0, "water", "hydrophone"),
    )


def detections_for(sensors, x, y, *, signature="tag-1"):
    return tuple(
        SubstrateDetection(
            sensor.sensor_id,
            signature,
            10.0 + hypot(x - sensor.x_meters, y - sensor.y_meters) / 1_500.0,
        )
        for sensor in sensors
    )


class SubstrateIntelligenceTests(unittest.TestCase):
    def test_local_mesh_estimates_position_without_relay(self):
        sensors = water_sensors()
        device = SubstrateIntelligenceDevice("sid-test", sensors)

        estimate = device.localize(
            detections_for(sensors, 37, 64),
            propagation_speed_mps=1_500,
            bounds=(0, 100, 0, 100),
        )

        self.assertEqual((estimate.x_meters, estimate.y_meters), (37.0, 64.0))
        self.assertGreater(estimate.confidence, 0.99)
        self.assertIsNone(device.relay_packet(estimate))

    def test_relay_contains_local_result_but_does_not_localize(self):
        sensors = water_sensors()
        device = SubstrateIntelligenceDevice(
            "sid-relay", sensors, relay_enabled=True
        )
        estimate = device.localize(
            detections_for(sensors, 20, 80),
            propagation_speed_mps=1_500,
            bounds=(0, 100, 0, 100),
        )

        packet = device.relay_packet(estimate)

        self.assertTrue(packet["localized_locally"])
        self.assertEqual(packet["position"], {"x_meters": 20.0, "y_meters": 80.0})

    def test_at_least_three_detections_are_required(self):
        sensors = water_sensors()
        device = SubstrateIntelligenceDevice("sid-test", sensors)

        with self.assertRaises(ValueError):
            device.localize(
                detections_for(sensors, 37, 64)[:2],
                propagation_speed_mps=1_500,
                bounds=(0, 100, 0, 100),
            )

    def test_detections_from_different_media_are_rejected(self):
        sensors = (
            *water_sensors()[:3],
            SubstrateSensorNode("ground", 50, 50, "soil", "geophone"),
        )
        device = SubstrateIntelligenceDevice("sid-test", sensors)

        with self.assertRaises(ValueError):
            device.localize(
                detections_for(sensors, 37, 64),
                propagation_speed_mps=1_500,
                bounds=(0, 100, 0, 100),
            )


if __name__ == "__main__":
    unittest.main()
