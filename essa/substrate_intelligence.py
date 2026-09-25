from __future__ import annotations

from dataclasses import dataclass
from math import exp, hypot, sqrt
from typing import Any


@dataclass(frozen=True)
class SubstrateSensorNode:
    sensor_id: str
    x_meters: float
    y_meters: float
    medium: str
    modality: str
    clock_uncertainty_seconds: float = 0.0001


@dataclass(frozen=True)
class SubstrateDetection:
    sensor_id: str
    source_signature: str
    arrival_time_seconds: float
    amplitude: float = 1.0


@dataclass(frozen=True)
class LocalizationEstimate:
    source_signature: str
    x_meters: float
    y_meters: float
    medium: str
    confidence: float
    timing_residual_seconds: float
    sensors_used: tuple[str, ...]
    method: str = "local_time_difference_of_arrival"


class SubstrateIntelligenceDevice:
    """SID-1 localizes signals inside their physical medium.

    This dependency-free reference implementation uses a bounded grid search.
    Physical devices can replace it with optimized solvers without changing the
    sensor and estimate contracts.
    """

    def __init__(
        self,
        device_id: str,
        sensors: tuple[SubstrateSensorNode, ...],
        *,
        relay_enabled: bool = False,
    ) -> None:
        if len(sensors) < 3:
            raise ValueError("SID-1 requires at least three sensor nodes")
        if len({sensor.sensor_id for sensor in sensors}) != len(sensors):
            raise ValueError("Sensor ids must be unique")
        self.device_id = device_id
        self.sensors = {sensor.sensor_id: sensor for sensor in sensors}
        self.relay_enabled = relay_enabled

    def localize(
        self,
        detections: tuple[SubstrateDetection, ...],
        *,
        propagation_speed_mps: float,
        bounds: tuple[float, float, float, float],
        grid_step_meters: float = 1.0,
    ) -> LocalizationEstimate:
        if propagation_speed_mps <= 0:
            raise ValueError("Propagation speed must be positive")
        if grid_step_meters <= 0:
            raise ValueError("Grid step must be positive")
        if len(detections) < 3:
            raise ValueError("At least three synchronized detections are required")
        if len({item.source_signature for item in detections}) != 1:
            raise ValueError("Detections must describe one source signature")
        if len({item.sensor_id for item in detections}) != len(detections):
            raise ValueError("Each sensor may contribute only one detection")

        try:
            sensors = [self.sensors[item.sensor_id] for item in detections]
        except KeyError as error:
            raise ValueError(f"Unknown sensor: {error.args[0]}") from error
        media = {sensor.medium for sensor in sensors}
        if len(media) != 1:
            raise ValueError("All detections must come through the same medium")

        min_x, max_x, min_y, max_y = bounds
        if min_x > max_x or min_y > max_y:
            raise ValueError("Localization bounds are invalid")

        best_x = min_x
        best_y = min_y
        best_residual = float("inf")
        x = min_x
        while x <= max_x + grid_step_meters * 0.001:
            y = min_y
            while y <= max_y + grid_step_meters * 0.001:
                residual = self._timing_residual(
                    x,
                    y,
                    sensors,
                    detections,
                    propagation_speed_mps,
                )
                if residual < best_residual:
                    best_x = x
                    best_y = y
                    best_residual = residual
                y += grid_step_meters
            x += grid_step_meters

        average_clock_uncertainty = sum(
            sensor.clock_uncertainty_seconds for sensor in sensors
        ) / len(sensors)
        spatial_time_resolution = grid_step_meters / propagation_speed_mps
        tolerance = max(1e-9, average_clock_uncertainty + spatial_time_resolution)
        geometry_factor = min(1.0, len(sensors) / 4.0)
        confidence = geometry_factor * exp(-best_residual / tolerance)
        return LocalizationEstimate(
            source_signature=detections[0].source_signature,
            x_meters=round(best_x, 3),
            y_meters=round(best_y, 3),
            medium=next(iter(media)),
            confidence=round(max(0.0, min(1.0, confidence)), 3),
            timing_residual_seconds=round(best_residual, 9),
            sensors_used=tuple(item.sensor_id for item in detections),
        )

    def relay_packet(self, estimate: LocalizationEstimate) -> dict[str, Any] | None:
        if not self.relay_enabled:
            return None
        return {
            "device_id": self.device_id,
            "source_signature": estimate.source_signature,
            "position": {
                "x_meters": estimate.x_meters,
                "y_meters": estimate.y_meters,
            },
            "medium": estimate.medium,
            "confidence": estimate.confidence,
            "localization_method": estimate.method,
            "localized_locally": True,
        }

    def blueprint(self) -> dict[str, Any]:
        return {
            "device": "ESSA Substrate Intelligence Device SID-1",
            "device_id": self.device_id,
            "principle": "localize_in_native_medium_relay_only_when_needed",
            "sensor_count": len(self.sensors),
            "media": sorted({sensor.medium for sensor in self.sensors.values()}),
            "modalities": sorted(
                {sensor.modality for sensor in self.sensors.values()}
            ),
            "relay_enabled": self.relay_enabled,
            "physical_hardware_attached": False,
        }

    def _timing_residual(
        self,
        x: float,
        y: float,
        sensors: list[SubstrateSensorNode],
        detections: tuple[SubstrateDetection, ...],
        propagation_speed_mps: float,
    ) -> float:
        travel_times = [
            hypot(x - sensor.x_meters, y - sensor.y_meters)
            / propagation_speed_mps
            for sensor in sensors
        ]
        emission_time = sum(
            detection.arrival_time_seconds - travel_time
            for detection, travel_time in zip(detections, travel_times)
        ) / len(detections)
        errors = [
            detection.arrival_time_seconds - (emission_time + travel_time)
            for detection, travel_time in zip(detections, travel_times)
        ]
        return sqrt(sum(error * error for error in errors) / len(errors))
