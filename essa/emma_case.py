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


EMMA_ACTIONS = (
    "secure_learning_route",
    "create_safe_learning_space",
    "provide_meals_and_supplies",
    "psychosocial_teacher_support",
    "repair_school_and_enroll",
)


@dataclass(frozen=True)
class EmmaCondition:
    turn: int
    gang_pressure: str
    displacement: str
    hunger: str
    school_condition: str
    route_risk: str
    teacher_access: str
    trauma_signs: str
    family_cost_pressure: str
    attendance: float
    felt_safety: float
    uncertainty: float


@dataclass(frozen=True)
class EmmaResult:
    action: str
    outcome: str
    cost: float
    previous_uncertainty: float
    next_uncertainty: float
    visible_effect: dict[str, Any]


class EmmaHaitiEducationEnvironment:
    """Hidden-rule case inspired by the UN News Haiti back-to-school article."""

    def __init__(
        self,
        *,
        attendance: float = 2.0,
        felt_safety: float = 2.0,
        hunger_pressure: float = 7.0,
        uncertainty: float = 8.0,
    ) -> None:
        self.turn = 0
        self.attendance = attendance
        self.felt_safety = felt_safety
        self.hunger_pressure = hunger_pressure
        self.uncertainty = uncertainty
        self.route_buffer = 0.0
        self.safe_space_buffer = 0.0

    def observe(self) -> EmmaCondition:
        gang_pattern = ("high", "high", "extreme", "high", "medium", "extreme")
        displacement_pattern = ("high", "high", "medium", "high", "medium", "high")
        hunger_pattern = ("high", "severe", "high", "medium", "severe", "high")
        school_pattern = ("damaged", "occupied", "open_fragile", "damaged", "open", "inaccessible")
        route_pattern = ("unsafe", "unsafe", "crossfire", "kidnap_risk", "unsafe", "crossfire")
        teacher_pattern = ("limited", "blocked", "limited", "limited", "available", "blocked")
        trauma_pattern = ("high", "high", "severe", "high", "medium", "severe")
        cost_pattern = ("high", "high", "medium", "severe", "high", "medium")

        i = self.turn % len(gang_pattern)
        route_risk = route_pattern[i]
        if self.route_buffer > 0 and route_risk != "crossfire":
            route_risk = "guarded"

        school_condition = school_pattern[i]
        if self.safe_space_buffer > 0 and school_condition in {"occupied", "inaccessible"}:
            school_condition = "temporary_safe_space"

        hunger = hunger_pattern[i]
        if self.hunger_pressure <= 4:
            hunger = "medium"
        if self.hunger_pressure <= 2:
            hunger = "low"

        return EmmaCondition(
            turn=self.turn,
            gang_pressure=gang_pattern[i],
            displacement=displacement_pattern[i],
            hunger=hunger,
            school_condition=school_condition,
            route_risk=route_risk,
            teacher_access=teacher_pattern[i],
            trauma_signs=trauma_pattern[i],
            family_cost_pressure=cost_pattern[i],
            attendance=round(self.attendance, 3),
            felt_safety=round(self.felt_safety, 3),
            uncertainty=round(self.uncertainty, 3),
        )

    def apply(self, action: str) -> EmmaResult:
        condition = self.observe()
        previous_uncertainty = self.uncertainty
        previous_attendance = self.attendance
        previous_safety = self.felt_safety
        previous_hunger = self.hunger_pressure
        effect = self._hidden_effect(action, condition)

        self.attendance = self._clamp(self.attendance + effect["attendance_delta"])
        self.felt_safety = self._clamp(self.felt_safety + effect["safety_delta"])
        self.hunger_pressure = self._clamp(
            self.hunger_pressure + effect["hunger_delta"]
        )
        self.uncertainty = self._clamp(self.uncertainty + effect["uncertainty_delta"])
        self.route_buffer = max(0.0, self.route_buffer - 1.0)
        self.safe_space_buffer = max(0.0, self.safe_space_buffer - 1.0)
        if action == "secure_learning_route":
            self.route_buffer = 2.0
        if action == "create_safe_learning_space":
            self.safe_space_buffer = 2.0
        self.turn += 1

        uncertainty_delta = self.uncertainty - previous_uncertainty
        if uncertainty_delta < -0.2:
            outcome = "protective_progress"
        elif abs(uncertainty_delta) <= 0.2:
            outcome = "partial_signal"
        else:
            outcome = "new_risk_signal"

        return EmmaResult(
            action=action,
            outcome=outcome,
            cost=self.action_cost(action),
            previous_uncertainty=round(previous_uncertainty, 3),
            next_uncertainty=round(self.uncertainty, 3),
            visible_effect={
                "attendance_delta": round(self.attendance - previous_attendance, 3),
                "felt_safety_delta": round(self.felt_safety - previous_safety, 3),
                "hunger_pressure_delta": round(
                    self.hunger_pressure - previous_hunger, 3
                ),
                "uncertainty_delta": round(uncertainty_delta, 3),
                "route_status": "buffered" if self.route_buffer else "exposed",
                "learning_space": "temporary_safe"
                if self.safe_space_buffer
                else "ordinary_or_damaged",
            },
        )

    def action_cost(self, action: str) -> float:
        costs = {
            "secure_learning_route": 0.7,
            "create_safe_learning_space": 0.55,
            "provide_meals_and_supplies": 0.45,
            "psychosocial_teacher_support": 0.35,
            "repair_school_and_enroll": 0.65,
        }
        return costs[action]

    def _hidden_effect(
        self, action: str, condition: EmmaCondition
    ) -> dict[str, float]:
        route_danger = condition.route_risk in {"unsafe", "crossfire", "kidnap_risk"}
        school_blocked = condition.school_condition in {"damaged", "occupied", "inaccessible"}
        hunger_high = condition.hunger in {"high", "severe"}
        trauma_high = condition.trauma_signs in {"high", "severe"}

        if action == "secure_learning_route":
            if route_danger:
                return self._effect(1.3, 2.2, -0.2, -1.9)
            return self._effect(0.4, 0.6, 0.0, -0.4)
        if action == "create_safe_learning_space":
            if school_blocked or condition.displacement == "high":
                return self._effect(1.6, 1.5, -0.1, -1.6)
            return self._effect(0.5, 0.7, 0.0, -0.5)
        if action == "provide_meals_and_supplies":
            if hunger_high or condition.family_cost_pressure in {"high", "severe"}:
                return self._effect(1.1, 0.7, -2.0, -1.4)
            return self._effect(0.4, 0.2, -0.5, -0.3)
        if action == "psychosocial_teacher_support":
            if trauma_high or condition.teacher_access == "limited":
                return self._effect(0.7, 1.2, -0.1, -1.2)
            return self._effect(0.2, 0.4, 0.0, -0.2)
        if action == "repair_school_and_enroll":
            if school_blocked and not route_danger:
                return self._effect(2.0, 0.8, -0.1, -1.7)
            if school_blocked and route_danger:
                return self._effect(0.3, -0.3, 0.0, 0.8)
            return self._effect(0.7, 0.2, -0.1, -0.4)
        raise ValueError(f"Unknown action: {action}")

    def _effect(
        self,
        attendance_delta: float,
        safety_delta: float,
        hunger_delta: float,
        uncertainty_delta: float,
    ) -> dict[str, float]:
        return {
            "attendance_delta": attendance_delta,
            "safety_delta": safety_delta,
            "hunger_delta": hunger_delta,
            "uncertainty_delta": uncertainty_delta,
        }

    def _clamp(self, value: float) -> float:
        return max(0.0, min(10.0, value))


class EmmaHaitiEducationLearner:
    """EMMA learns child-safety intervention rules from a Haiti education case."""

    def __init__(
        self,
        self_model: SelfModel | None = None,
        environment: EmmaHaitiEducationEnvironment | None = None,
    ) -> None:
        self.self_model = self_model or SelfModel()
        self.environment = environment or EmmaHaitiEducationEnvironment()
        self.north_star = (
            "Prevent violence, prevent hunger, help children go to school, "
            "and help children feel safe."
        )
        self.source_url = "https://news.un.org/en/story/2026/09/1168337"
        self.learned_rules: dict[tuple[str, str], LearnedRule] = {}
        self.world_model: list[Belief] = [
            Belief(
                id="B1",
                statement="Unsafe routes prevent children from reaching school.",
                confidence=0.55,
            ),
            Belief(
                id="B2",
                statement="Hunger and school costs reduce attendance and learning.",
                confidence=0.5,
            ),
            Belief(
                id="B3",
                statement="Safe learning spaces restore continuity when schools are damaged or occupied.",
                confidence=0.48,
            ),
            Belief(
                id="B4",
                statement="Trauma-aware teacher support helps children feel safe enough to learn.",
                confidence=0.45,
            ),
            Belief(
                id="B5",
                statement="Repair and enrollment help only after access is safe enough.",
                confidence=0.4,
            ),
        ]
        self.previous_condition: EmmaCondition | None = None
        self.cycle_number = 0
        self.self_model.inspect_substrate(
            StaticSubstrateInspector(
                SubstrateSnapshot(
                    id="emma-haiti-education-case",
                    kind="humanitarian_education_training_case",
                    capabilities=(
                        "observe_child_safety_signals",
                        "detect_hidden_access_constraints",
                        "hypothesize_intervention_rules",
                        "predict_attendance_safety_hunger",
                        "update_humanitarian_beliefs",
                    ),
                    constraints=(
                        "article_grounded_case",
                        "hidden_rules_not_real_world_advice",
                        "no_penalty_only_consequence",
                    ),
                    attributes={
                        "actions": list(EMMA_ACTIONS),
                        "source": self.source_url,
                    },
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
                "case": "emma_haiti_education",
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
            f"{item['belief']} -> {item['old_confidence']} -> {item['new_confidence']}"
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

    def _observe(self, condition: EmmaCondition) -> Observation:
        return self.self_model.observe_world(
            "emma_haiti_education_environment",
            {
                "turn": condition.turn,
                "gang_pressure": condition.gang_pressure,
                "displacement": condition.displacement,
                "hunger": condition.hunger,
                "school_condition": condition.school_condition,
                "route_risk": condition.route_risk,
                "teacher_access": condition.teacher_access,
                "trauma_signs": condition.trauma_signs,
                "family_cost_pressure": condition.family_cost_pressure,
                "attendance": condition.attendance,
                "felt_safety": condition.felt_safety,
                "uncertainty": condition.uncertainty,
            },
            evidence=self.source_url,
        )

    def _detect(self, condition: EmmaCondition) -> dict[str, Any]:
        features = {
            "violence_pressure": "high"
            if condition.gang_pressure in {"high", "extreme"}
            else "medium",
            "route_access": "danger"
            if condition.route_risk in {"unsafe", "crossfire", "kidnap_risk"}
            else "guarded",
            "hunger_pressure": "high"
            if condition.hunger in {"high", "severe"}
            else "lower",
            "school_access": "blocked"
            if condition.school_condition in {"damaged", "occupied", "inaccessible"}
            else "open",
            "trauma_pressure": "high"
            if condition.trauma_signs in {"high", "severe"}
            else "medium",
            "teacher_access": condition.teacher_access,
            "family_cost_pressure": condition.family_cost_pressure,
            "attendance_pressure": "low" if condition.attendance < 5 else "recovering",
            "felt_safety": "low" if condition.felt_safety < 5 else "recovering",
        }
        condition_key = "|".join(f"{key}:{value}" for key, value in features.items())
        changes: dict[str, Any] = {}
        if self.previous_condition:
            previous = self.previous_condition
            changes = {
                "attendance_delta": round(condition.attendance - previous.attendance, 3),
                "felt_safety_delta": round(
                    condition.felt_safety - previous.felt_safety, 3
                ),
                "uncertainty_delta": round(
                    condition.uncertainty - previous.uncertainty, 3
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
        recovery_action = (
            "psychosocial_teacher_support"
            if features["trauma_pressure"] == "high"
            else "repair_school_and_enroll"
        )
        return [
            {
                "id": "H1",
                "explanation": "Violence and unsafe routes are the main blocker.",
                "action": "secure_learning_route",
                "confidence": self._belief_confidence("B1"),
                "support": "route_access",
            },
            {
                "id": "H2",
                "explanation": "Hunger and cost pressure are blocking school continuity.",
                "action": "provide_meals_and_supplies",
                "confidence": self._belief_confidence("B2"),
                "support": "hunger_pressure",
            },
            {
                "id": "H3",
                "explanation": "Children need a safe learning space and trauma-aware support.",
                "action": "create_safe_learning_space"
                if features["school_access"] == "blocked"
                else recovery_action,
                "confidence": max(
                    self._belief_confidence("B3"), self._belief_confidence("B4")
                ),
                "support": "school_or_trauma_pressure",
            },
        ]

    def _predict(
        self,
        condition: EmmaCondition,
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
                f"If EMMA performs {chosen['action']}, child-safety uncertainty "
                f"should move by about {chosen['expected_delta']} because "
                f"{chosen['basis']}."
            ),
            "candidates": candidates,
            **chosen,
        }

    def _evaluate(
        self, prediction: dict[str, Any], result: EmmaResult
    ) -> dict[str, Any]:
        predicted_direction = "down" if prediction["expected_delta"] < 0 else "up"
        actual_delta = result.next_uncertainty - result.previous_uncertainty
        actual_direction = "down" if actual_delta < 0 else "up"
        confirmed = predicted_direction == actual_direction
        return {
            "outcome": result.outcome,
            "predicted_direction": predicted_direction,
            "actual_direction": actual_direction,
            "prediction_confirmed": confirmed,
            "actual_delta": round(actual_delta, 3),
            "surprise": None if confirmed else "prediction_direction_mismatch",
        }

    def _update(
        self,
        detected: dict[str, Any],
        prediction: dict[str, Any],
        result: EmmaResult,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        action = prediction["chosen_action"]
        key = (detected["condition_key"], action)
        rule = self.learned_rules.setdefault(
            key, LearnedRule(condition_key=detected["condition_key"], action=action)
        )
        rule.attempts += 1
        rule.successes += 1 if result.outcome == "protective_progress" else 0
        rule.total_uncertainty_delta += (
            result.next_uncertainty - result.previous_uncertainty
        )
        belief_updates = self._update_beliefs(detected, action, result, evaluation)
        self.world_model = [
            belief for belief in self.world_model if belief.confidence >= 0.2
        ]
        self.self_model.observe_self(
            {
                "case": "emma_haiti_education",
                "action": action,
                "outcome": result.outcome,
                "belief_updates": belief_updates,
            },
            evidence="EmmaHaitiEducationLearner._update",
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
        features = detected["features"]
        if features["route_access"] == "danger":
            return "reduce_violence_risk_on_route_to_school"
        if features["hunger_pressure"] == "high":
            return "reduce_hunger_and_cost_barrier"
        if features["school_access"] == "blocked":
            return "restore_safe_learning_continuity"
        if features["trauma_pressure"] == "high":
            return "increase_felt_safety_and_trauma_support"
        return "retest_old_beliefs_for_drift"

    def _surprises(
        self, condition: EmmaCondition, features: dict[str, str]
    ) -> list[str]:
        if self.previous_condition is None:
            return []
        surprises = []
        if (
            features["route_access"] == "guarded"
            and condition.felt_safety < self.previous_condition.felt_safety
        ):
            surprises.append("guarded_route_but_safety_dropped")
        if (
            features["hunger_pressure"] == "lower"
            and condition.attendance < self.previous_condition.attendance
        ):
            surprises.append("hunger_lower_but_attendance_dropped")
        if (
            features["school_access"] == "open"
            and features["felt_safety"] == "low"
        ):
            surprises.append("school_open_but_children_do_not_feel_safe")
        return surprises

    def _prior_delta(self, action: str, detected: dict[str, Any]) -> float:
        features = detected["features"]
        if action == "secure_learning_route":
            return -1.5 if features["route_access"] == "danger" else -0.4
        if action == "create_safe_learning_space":
            return -1.3 if features["school_access"] == "blocked" else -0.5
        if action == "provide_meals_and_supplies":
            return -1.2 if features["hunger_pressure"] == "high" else -0.3
        if action == "psychosocial_teacher_support":
            return -1.0 if features["trauma_pressure"] == "high" else -0.2
        if action == "repair_school_and_enroll":
            if features["route_access"] == "danger":
                return 0.5
            return -1.1 if features["school_access"] == "blocked" else -0.3
        raise ValueError(f"Unknown action: {action}")

    def _information_gain(
        self, detected: dict[str, Any], action: str, known_rule: bool
    ) -> float:
        gain = 0.4 if known_rule else 0.8
        if detected["low_confidence_beliefs"]:
            gain += 0.2
        if action == "repair_school_and_enroll" and detected["features"]["route_access"] == "danger":
            gain += 0.3
        return gain

    def _north_star_progress(self, detected: dict[str, Any], action: str) -> float:
        features = detected["features"]
        if action == "secure_learning_route" and features["route_access"] == "danger":
            return 1.2
        if action == "provide_meals_and_supplies" and features["hunger_pressure"] == "high":
            return 1.0
        if action == "create_safe_learning_space" and features["school_access"] == "blocked":
            return 0.95
        if action == "psychosocial_teacher_support" and features["trauma_pressure"] == "high":
            return 0.85
        if action == "repair_school_and_enroll" and features["route_access"] == "guarded":
            return 0.8
        return 0.35

    def _update_beliefs(
        self,
        detected: dict[str, Any],
        action: str,
        result: EmmaResult,
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        touched = self._beliefs_for(action, result)
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

    def _beliefs_for(self, action: str, result: EmmaResult) -> list[Belief]:
        ids = []
        if action == "secure_learning_route":
            ids.append("B1")
        if action == "provide_meals_and_supplies":
            ids.append("B2")
        if action == "create_safe_learning_space":
            ids.append("B3")
        if action == "psychosocial_teacher_support":
            ids.append("B4")
        if action == "repair_school_and_enroll":
            ids.append("B5")
        if result.visible_effect["felt_safety_delta"] > 0:
            ids.append("B4")
        return [belief for belief in self.world_model if belief.id in set(ids)]

    def _belief_confidence(self, belief_id: str) -> float:
        for belief in self.world_model:
            if belief.id == belief_id:
                return round(belief.confidence, 3)
        return 0.2
