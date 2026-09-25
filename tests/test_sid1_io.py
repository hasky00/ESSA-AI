import tempfile
import unittest
from pathlib import Path

from essa.sid1_io import load_detections_csv, load_sid1_config


ROOT = Path(__file__).resolve().parents[1]


class SID1IOTests(unittest.TestCase):
    def test_reference_hardware_config_and_detections_localize(self):
        device, config = load_sid1_config(
            ROOT / "hardware/sid1/config/water-array.json"
        )
        detections = load_detections_csv(
            ROOT / "hardware/sid1/sample/detections.csv"
        )

        estimate = device.localize(
            detections,
            propagation_speed_mps=config.propagation_speed_mps,
            bounds=config.bounds,
            grid_step_meters=config.grid_step_meters,
        )

        self.assertEqual(device.device_id, "HASKY-LABS-ESSA-SID1-001")
        self.assertEqual((estimate.x_meters, estimate.y_meters), (37.0, 64.0))
        self.assertIsNone(device.relay_packet(estimate))

    def test_detection_csv_requires_all_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.csv"
            path.write_text("sensor_id,arrival_time_seconds\na,1.0\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_detections_csv(path)


if __name__ == "__main__":
    unittest.main()
