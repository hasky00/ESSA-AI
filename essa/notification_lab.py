from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from essa.hidden_lab import Belief, CycleReport, LearnedRule
from essa.self_model import (
    Observation,
    SelfModel,
    StaticSubstrateInspector,
    SubstrateSnapshot,
)


NOTIFICATION_ACTIONS = (
    "switch_off_notifications",
    "check_notifications_5_minutes",
    "suggest_rest",
    "suggest_walking",
)


@dataclass(frozen=True)
class EnergyCondition:
    turn: int
    sleep_hours: float
    mood: str
    coffee: int
    walked: bool
    phone_notifications: int
    attention_minutes: int
    energy: float
    productivity: float
    uncertainty: float


@dataclass(frozen=True)
class EnergyResult:
    action: str
    outcome: str
    cost: float
    previous_uncertainty: float
    next_uncertainty: float
    visible_effect: dict[str, Any]


class NotificationEnergyEnvironment:
    """A personal-energy simulation with hidden notification and recovery rules."""

    def __init__(
        self,
        *,
        energy: float = 6.0,
        productivity: float = 5.0,
        uncertainty: float = 7.0,
    ) -> None:
        self.turn = 0
        self.energy = energy
        self.productivity = productivity
        self.uncertainty = uncertainty
        self.notification_mode = "normal"
        self.walked_recently = False

    def observe(self) -> EnergyCondition:
        sleep_pattern = (6.0, 7.5, 5.5, 8.0, 6.5, 4.8, 7.0)
        coffee_pattern = (1, 2, 1, 0, 3, 2, 1)
        notification_pattern = (34, 8, 55, 13, 42, 4, 27)
        sleep_hours = sleep_pattern[self.turn % len(sleep_pattern)]
        coffee = coffee_pattern[self.turn % len(coffee_pattern)]
        base_notifications = notification_pattern[self.turn % len(notification_pattern)]
        phone_notifications = (
            0 if self.notification_mode == "off" else base_notifications
        )
        mood = self._mood(sleep_hours, phone_notifications)
        attention_minutes = min(30, phone_notifications // 4)

        return EnergyCondition(
            turn=self.turn,
            sleep_hours=sleep_hours,
            mood=mood,
            coffee=coffee,
            walked=self.walked_recently,
            phone_notifications=phone_notifications,
            attention_minutes=attention_minutes,
            energy=round(self.energy, 3),
            productivity=round(self.productivity, 3),
            uncertainty=round(self.uncertainty, 3),
        )

    def apply(self, action: str) -> EnergyResult:
        condition = self.observe()
        previous_uncertainty = self.uncertainty
        previous_energy = self.energy
        previous_productivity = self.productivity
        cost = self.action_cost(action)
        effect = self._hidden_effect(action, condition)

        if action == "switch_off_notifications":
            self.notification_mode = "off"
        elif action == "check_notifications_5_minutes":
            self.notification_mode = "normal"

        self.energy = max(0.0, min(10.0, self.energy + effect["energy_delta"]))
        self.productivity = max(
            0.0, min(10.0, self.productivity + effect["productivity_delta"])
        )
        self.uncertainty = max(
            0.0, min(10.0, self.uncertainty + effect["uncertainty_delta"])
        )
        self.walked_recently = action == "suggest_walking"
        self.turn += 1

        uncertainty_delta = self.uncertainty - previous_uncertainty
        if uncertainty_delta < -0.1:
            outcome = "clarity"
        elif abs(uncertainty_delta) <= 0.1:
            outcome = "partial"
        else:
            outcome = "new_data"

        return EnergyResult(
            action=action,
            outcome=outcome,
            cost=cost,
            previous_uncertainty=round(previous_uncertainty, 3),
            next_uncertainty=round(self.uncertainty, 3),
            visible_effect={
                "energy_delta": round(self.energy - previous_energy, 3),
                "productivity_delta": round(
                    self.productivity - previous_productivity, 3
                ),
                "uncertainty_delta": round(uncertainty_delta, 3),
                "notification_mode": self.notification_mode,
                "disturbance": "none"
                if self.notification_mode == "off"
                else "present",
            },
        )

    def action_cost(self, action: str) -> float:
        costs = {
            "switch_off_notifications": 0.35,
            "check_notifications_5_minutes": 0.25,
            "suggest_rest": 0.15,
            "suggest_walking": 0.2,
        }
        return costs[action]

    def _hidden_effect(
        self, action: str, condition: EnergyCondition
    ) -> dict[str, float]:
        sleep_low = condition.sleep_hours < 6
        notifications_high = condition.phone_notifications >= 30
        attention_drain = condition.attention_minutes >= 5

        if action == "switch_off_notifications":
            if notifications_high or attention_drain:
                return {
                    "energy_delta": 1.1,
                    "productivity_delta": 1.2,
                    "uncertainty_delta": -1.8,
                }
            return {
                "energy_delta": 0.2,
                "productivity_delta": 0.1,
                "uncertainty_delta": -0.2,
            }
        if action == "check_notifications_5_minutes":
            if sleep_low:
                return {
                    "energy_delta": -1.0,
                    "productivity_delta": -1.1,
                    "uncertainty_delta": 0.9,
                }
            return {
                "energy_delta": -0.4,
                "productivity_delta": -0.5,
                "uncertainty_delta": -0.3,
            }
        if action == "suggest_rest":
            if sleep_low:
                return {
                    "energy_delta": 1.4,
                    "productivity_delta": 0.3,
                    "uncertainty_delta": -1.0,
                }
            return {
                "energy_delta": 0.4,
                "productivity_delta": -0.1,
                "uncertainty_delta": 0.1,
            }
        if action == "suggest_walking":
            if condition.mood in {"heavy", "scattered"}:
                return {
                    "energy_delta": 0.8,
                    "productivity_delta": 0.9,
                    "uncertainty_delta": -1.2,
                }
            return {
                "energy_delta": 0.4,
                "productivity_delta": 0.4,
                "uncertainty_delta": -0.5,
            }
        raise ValueError(f"Unknown action: {action}")

    def _mood(self, sleep_hours: float, notifications: int) -> str:
        if sleep_hours < 6 and notifications >= 30:
            return "scattered"
        if sleep_hours < 6:
            return "heavy"
        if notifications >= 30:
            return "alert"
        return "clear"


class NotificationEnergyLearner:
    """ESSA lab seeded from the user's notification-energy core beliefs."""

    def __init__(
        self,
        self_model: SelfModel | None = None,
        environment: NotificationEnergyEnvironment | None = None,
    ) -> None:
        self.self_model = self_model or SelfModel()
        self.environment = environment or NotificationEnergyEnvironment()
        self.north_star = "Find out if phone notification drains your energy."
        self.learned_rules: dict[tuple[str, str], LearnedRule] = {}
        self.world_model: list[Belief] = [
            Belief(
                id="B1",
                statement="Too many phone notifications drain your energy.",
                confidence=0.5,
            ),
            Belief(
                id="B2",
                statement=(
                    "Paying attention to notifications for 5 minutes a day "
                    "reduces productivity."
                ),
                confidence=0.45,
            ),
            Belief(
                id="B3",
                statement="Walking makes your mind clearer.",
                confidence=0.5,
            ),
            Belief(
                id="B4",
                statement="No notification means no disturbance.",
                confidence=0.35,
            ),
        ]
        self.previous_condition: EnergyCondition | None = None
        self.cycle_number = 0
        self.self_model.inspect_substrate(
            StaticSubstrateInspector(
                SubstrateSnapshot(
                    id="notification-energy-lab",
                    kind="personal_energy_simulation",
                    capabilities=(
                        "observe_daily_energy",
                        "detect_notification_pressure",
                        "hypothesize_core_belief",
                        "predict_energy_productivity",
                        "update_belief_confidence",
                    ),
                    constraints=("hidden_daily_rules", "no_penalty_only_consequence"),
                    attributes={"actions": list(NOTIFICATION_ACTIONS)},
                )
            )
        )

    def run_cycle(self) -> CycleReport:
        self.cycle_number += 1
        condition = self.environment.observe()
        observation = self._observe(condition)
        detected = self._detect(condition)
        hypotheses = self._hypothesize(detected)
        prediction = self._predict(condition, detected, hypotheses)
        result = self.environment.apply(prediction["chosen_action"])
        evaluation = self._evaluate(prediction, result)
        update = self._update(detected, prediction, result, evaluation)
        next_task = self._next_task(detected)
        self.previous_condition = condition

        self.self_model.transition_state(
            result.action,
            observation,
            {
                **self.self_model.state,
                "north_star": self.north_star,
                "cycle": self.cycle_number,
                "last_action": result.action,
                "last_outcome": result.outcome,
                "uncertainty": result.next_uncertainty,
                "next_task": next_task,
                "belief_count": len(self.world_model),
            },
        )

        return CycleReport(
            cycle=self.cycle_number,
            north_star=self.north_star,
            observe=observation.value,
            detect=detected,
            hypothesize=hypotheses,
            predict=prediction,
            act={
                "action": result.action,
                "outcome": result.outcome,
                "cost": result.cost,
                "visible_effect": result.visible_effect,
            },
            evaluate=evaluation,
            update=update,
            next_task=next_task,
            output_forward_rules=self.output_forward_rules(),
        )

    def output_world_model(self) -> list[dict[str, Any]]:
        return [
            {
                "id": belief.id,
                "belief": belief.statement,
                "confidence": round(belief.confidence, 3),
                "evidence_count": belief.evidence_count,
                "drift_notes": belief.drift_notes,
            }
            for belief in self.world_model
        ]

    def output_forward_rules(self) -> list[dict[str, Any]]:
        ranked = sorted(
            self.learned_rules.values(),
            key=lambda rule: (rule.score(), rule.attempts),
            reverse=True,
        )
        return [
            {
                "when": rule.condition_key,
                "prefer": rule.action,
                "confidence": round(rule.confidence, 3),
                "attempts": rule.attempts,
                "success_rate": round(rule.success_rate, 3),
                "average_uncertainty_delta": round(rule.average_uncertainty_delta, 3),
            }
            for rule in ranked[:8]
        ]

    def cycle_text(self, report: CycleReport) -> str:
        hypotheses = " / ".join(
            f"{item['id']} {item['explanation']} -> {item['action']}"
            for item in report.hypothesize
        )
        updates = report.update.get("belief_updates", [])
        model_update = "; ".join(
            (
                f"{item['belief']} -> {item['old_confidence']} "
                f"-> {item['new_confidence']}"
            )
            for item in updates
        )
        return "\n".join(
            [
                f"OBSERVED:     {report.observe}",
                f"SURPRISES:    {report.detect.get('surprises') or report.evaluate.get('surprise') or 'none'}",
                f"HYPOTHESES:   {hypotheses}",
                "CHOSEN ACTION + PREDICTION: "
                f"{report.predict['chosen_action']} | "
                f"{report.predict['written_prediction']}",
                f"RESULT:       {report.act}",
                f"MODEL UPDATE: {model_update or 'no confidence change'}",
                f"NEXT TASK:    {report.next_task}",
            ]
        )

    def _observe(self, condition: EnergyCondition) -> Observation:
        return self.self_model.observe_world(
            "notification_energy_environment",
            {
                "turn": condition.turn,
                "sleep_hours": condition.sleep_hours,
                "mood": condition.mood,
                "coffee": condition.coffee,
                "walking": condition.walked,
                "phone_notifications": condition.phone_notifications,
                "attention_minutes": condition.attention_minutes,
                "energy": condition.energy,
                "productivity": condition.productivity,
                "uncertainty": condition.uncertainty,
            },
            evidence="NotificationEnergyEnvironment.observe",
        )

    def _detect(self, condition: EnergyCondition) -> dict[str, Any]:
        features = {
            "sleep": "low" if condition.sleep_hours < 6 else "enough",
            "mood": condition.mood,
            "coffee": "high" if condition.coffee >= 3 else "normal",
            "walking": "yes" if condition.walked else "no",
            "notification_pressure": "high"
            if condition.phone_notifications >= 30
            else "low",
            "attention_pressure": "high"
            if condition.attention_minutes >= 5
            else "low",
            "energy_pressure": "low" if condition.energy < 5 else "ready",
            "productivity_pressure": "low"
            if condition.productivity < 5
            else "ready",
        }
        condition_key = "|".join(f"{key}:{value}" for key, value in features.items())
        changes: dict[str, Any] = {}
        if self.previous_condition:
            previous = self.previous_condition
            changes = {
                "sleep_delta": round(condition.sleep_hours - previous.sleep_hours, 2),
                "notifications_delta": (
                    condition.phone_notifications - previous.phone_notifications
                ),
                "attention_delta": (
                    condition.attention_minutes - previous.attention_minutes
                ),
                "energy_delta": round(condition.energy - previous.energy, 3),
                "productivity_delta": round(
                    condition.productivity - previous.productivity, 3
                ),
            }
        return {
            "features": features,
            "condition_key": condition_key,
            "changes_since_last_cycle": changes,
            "surprises": self._surprises(condition, features),
            "low_confidence_beliefs": [
                belief.id for belief in self.world_model if belief.confidence < 0.5
            ],
        }

    def _hypothesize(self, detected: dict[str, Any]) -> list[dict[str, Any]]:
        features = detected["features"]
        hypotheses = [
            {
                "id": "H1",
                "explanation": "Notifications are the main hidden drain.",
                "action": "switch_off_notifications",
                "confidence": self._belief_confidence("B1"),
                "support": "notification_pressure"
                if features["notification_pressure"] == "high"
                else "retest_no_notification_case",
            },
            {
                "id": "H2",
                "explanation": "Attention checking itself may reduce productivity.",
                "action": "check_notifications_5_minutes",
                "confidence": self._belief_confidence("B2"),
                "support": "attention_pressure",
            },
            {
                "id": "H3",
                "explanation": "Walking or rest may restore clarity better than changing notifications.",
                "action": "suggest_rest"
                if features["sleep"] == "low"
                else "suggest_walking",
                "confidence": self._belief_confidence("B3"),
                "support": "recovery_alternative",
            },
        ]
        return hypotheses

    def _predict(
        self,
        condition: EnergyCondition,
        detected: dict[str, Any],
        hypotheses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        candidates = []
        for hypothesis in hypotheses:
            action = hypothesis["action"]
            rule = self.learned_rules.get((detected["condition_key"], action))
            if rule and rule.attempts:
                expected_delta = rule.average_uncertainty_delta
                basis = "learned_rule"
                confidence = rule.confidence
            else:
                expected_delta = self._prior_delta(action, detected)
                basis = "core_belief_prior"
                confidence = hypothesis["confidence"]
            information_gain = self._information_gain(detected, action, rule is not None)
            cost_risk = self.environment.action_cost(action)
            north_star_progress = self._north_star_progress(detected, action)
            score = information_gain + north_star_progress - cost_risk
            candidates.append(
                {
                    "action": action,
                    "basis": basis,
                    "expected_uncertainty": round(
                        max(0.0, min(10.0, condition.uncertainty + expected_delta)), 3
                    ),
                    "expected_delta": round(expected_delta, 3),
                    "confidence": round(confidence, 3),
                    "expected_information_gain": round(information_gain, 3),
                    "cost_risk": round(cost_risk, 3),
                    "north_star_progress": round(north_star_progress, 3),
                    "score": round(score, 3),
                }
            )
        chosen = max(candidates, key=lambda item: item["score"])
        return {
            "chosen_action": chosen["action"],
            "written_prediction": (
                f"If ESSA performs {chosen['action']}, uncertainty should move "
                f"by about {chosen['expected_delta']} because {chosen['basis']}."
            ),
            "candidates": candidates,
            **chosen,
        }

    def _evaluate(
        self, prediction: dict[str, Any], result: EnergyResult
    ) -> dict[str, Any]:
        predicted_direction = "down" if prediction["expected_delta"] < 0 else "up"
        actual_delta = result.next_uncertainty - result.previous_uncertainty
        actual_direction = "down" if actual_delta < 0 else "up"
        return {
            "outcome": result.outcome,
            "predicted_direction": predicted_direction,
            "actual_direction": actual_direction,
            "prediction_confirmed": predicted_direction == actual_direction,
            "actual_delta": round(actual_delta, 3),
            "surprise": None
            if predicted_direction == actual_direction
            else "prediction_direction_mismatch",
        }

    def _update(
        self,
        detected: dict[str, Any],
        prediction: dict[str, Any],
        result: EnergyResult,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        action = prediction["chosen_action"]
        key = (detected["condition_key"], action)
        rule = self.learned_rules.setdefault(
            key, LearnedRule(condition_key=detected["condition_key"], action=action)
        )
        rule.attempts += 1
        rule.successes += 1 if result.outcome == "clarity" else 0
        rule.total_uncertainty_delta += (
            result.next_uncertainty - result.previous_uncertainty
        )
        belief_updates = self._update_beliefs(detected, action, result, evaluation)
        self.world_model = [
            belief for belief in self.world_model if belief.confidence >= 0.2
        ]
        self.self_model.observe_self(
            {
                "case": "notification_energy",
                "action": action,
                "outcome": result.outcome,
                "belief_updates": belief_updates,
            },
            evidence="NotificationEnergyLearner._update",
        )
        return {
            "rule": rule.condition_key,
            "action": rule.action,
            "attempts": rule.attempts,
            "success_rate": round(rule.success_rate, 3),
            "average_uncertainty_delta": round(rule.average_uncertainty_delta, 3),
            "previous_prediction_basis": prediction["basis"],
            "belief_updates": belief_updates,
            "active_beliefs": self.output_world_model(),
        }

    def _next_task(self, detected: dict[str, Any]) -> str:
        if detected["low_confidence_beliefs"]:
            return f"test_core_belief:{detected['low_confidence_beliefs'][0]}"
        if detected["features"]["notification_pressure"] == "low":
            return "retest_no_notification_no_disturbance"
        return "hunt_notification_energy_uncertainty"

    def _surprises(
        self, condition: EnergyCondition, features: dict[str, str]
    ) -> list[str]:
        surprises = []
        if self.previous_condition is None:
            return surprises
        if (
            condition.phone_notifications == 0
            and condition.energy < self.previous_condition.energy
        ):
            surprises.append("no_notifications_but_energy_dropped")
        if (
            features["notification_pressure"] == "high"
            and condition.mood == "clear"
        ):
            surprises.append("many_notifications_but_mood_clear")
        return surprises

    def _prior_delta(self, action: str, detected: dict[str, Any]) -> float:
        features = detected["features"]
        if action == "switch_off_notifications":
            return -1.2 if features["notification_pressure"] == "high" else -0.2
        if action == "check_notifications_5_minutes":
            return 0.6 if features["attention_pressure"] == "high" else -0.1
        if action == "suggest_rest":
            return -0.9 if features["sleep"] == "low" else 0.0
        if action == "suggest_walking":
            return -0.8
        raise ValueError(f"Unknown action: {action}")

    def _information_gain(
        self, detected: dict[str, Any], action: str, known_rule: bool
    ) -> float:
        gain = 0.4 if known_rule else 0.8
        if action == "check_notifications_5_minutes":
            gain += 0.25
        if detected["low_confidence_beliefs"]:
            gain += 0.2
        return gain

    def _north_star_progress(self, detected: dict[str, Any], action: str) -> float:
        features = detected["features"]
        if action == "switch_off_notifications":
            return 1.0
        if action == "check_notifications_5_minutes":
            return 0.75
        if action == "suggest_walking" and features["mood"] in {"heavy", "scattered"}:
            return 0.65
        if action == "suggest_rest" and features["sleep"] == "low":
            return 0.65
        return 0.35

    def _update_beliefs(
        self,
        detected: dict[str, Any],
        action: str,
        result: EnergyResult,
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        touched = self._beliefs_for(action, detected, result)
        delta = 0.08 if evaluation["prediction_confirmed"] else -0.12
        updates = []
        for belief in touched:
            if evaluation["surprise"]:
                belief.drift_notes.append(f"cycle_{self.cycle_number}: surprise")
            old, new = belief.adjust(delta)
            updates.append(
                {
                    "belief": belief.id,
                    "old_confidence": round(old, 3),
                    "new_confidence": round(new, 3),
                    "reason": "prediction_confirmed"
                    if delta > 0
                    else "prediction_surprise",
                }
            )
        return updates

    def _beliefs_for(
        self,
        action: str,
        detected: dict[str, Any],
        result: EnergyResult,
    ) -> list[Belief]:
        ids = []
        if action == "switch_off_notifications":
            ids.extend(["B1", "B4"])
        if action == "check_notifications_5_minutes":
            ids.append("B2")
        if action == "suggest_walking":
            ids.append("B3")
        if result.visible_effect["disturbance"] == "none":
            ids.append("B4")
        return [belief for belief in self.world_model if belief.id in set(ids)]

    def _belief_confidence(self, belief_id: str) -> float:
        for belief in self.world_model:
            if belief.id == belief_id:
                return round(belief.confidence, 3)
        return 0.2
