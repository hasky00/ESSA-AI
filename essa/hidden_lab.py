from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from essa.self_model import (
    Observation,
    SelfModel,
    StaticSubstrateInspector,
    SubstrateSnapshot,
)


ACTIONS = ("calibrate", "stabilize", "probe", "conserve")


@dataclass(frozen=True)
class EnvironmentCondition:
    turn: int
    signal: int
    drift: int
    noise: str
    energy: int
    uncertainty: float


@dataclass(frozen=True)
class ActionResult:
    action: str
    success: bool
    outcome: str
    cost: float
    previous_uncertainty: float
    next_uncertainty: float
    energy: int
    visible_effect: dict[str, Any]


@dataclass
class LearnedRule:
    condition_key: str
    action: str
    attempts: int = 0
    successes: int = 0
    total_uncertainty_delta: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.successes / self.attempts

    @property
    def average_uncertainty_delta(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.total_uncertainty_delta / self.attempts

    @property
    def confidence(self) -> float:
        return min(0.95, 0.25 + self.attempts * 0.12 + self.success_rate * 0.25)

    def score(self) -> float:
        return (self.success_rate * 2.0) - self.average_uncertainty_delta


@dataclass
class Belief:
    id: str
    statement: str
    confidence: float
    evidence_count: int = 0
    drift_notes: list[str] = field(default_factory=list)

    def adjust(self, delta: float) -> tuple[float, float]:
        old = self.confidence
        self.confidence = max(0.0, min(1.0, self.confidence + delta))
        if delta != 0:
            self.evidence_count += 1
        return old, self.confidence


@dataclass(frozen=True)
class CycleReport:
    cycle: int
    north_star: str
    observe: dict[str, Any]
    detect: dict[str, Any]
    hypothesize: list[dict[str, Any]]
    predict: dict[str, Any]
    act: dict[str, Any]
    evaluate: dict[str, Any]
    update: dict[str, Any]
    next_task: str
    output_forward_rules: list[dict[str, Any]]


class HiddenConstraintEnvironment:
    """Small changing environment whose true rules are not exposed to ESSA."""

    def __init__(self, *, uncertainty: float = 8.0, energy: int = 7) -> None:
        self.turn = 0
        self.uncertainty = uncertainty
        self.energy = energy

    def observe(self) -> EnvironmentCondition:
        signal = ((self.turn * 7 + 3) % 11) - 5
        drift = ((self.turn * 5 + 1) % 9) - 4
        noise = "high" if self.turn % 4 == 2 else "low"
        return EnvironmentCondition(
            turn=self.turn,
            signal=signal,
            drift=drift,
            noise=noise,
            energy=self.energy,
            uncertainty=round(self.uncertainty, 3),
        )

    def apply(self, action: str) -> ActionResult:
        condition = self.observe()
        previous = self.uncertainty
        effect = self._hidden_effect(action, condition)
        cost = self.action_cost(action)
        self.uncertainty = max(0.0, min(10.0, self.uncertainty + effect))
        self.energy = max(0, min(10, self.energy + self._energy_delta(action, effect)))
        self.turn += 1
        actual_delta = self.uncertainty - previous
        if actual_delta < -0.1:
            outcome = "success"
        elif abs(actual_delta) <= 0.1:
            outcome = "partial"
        else:
            outcome = "new_data"

        return ActionResult(
            action=action,
            success=self.uncertainty < previous,
            outcome=outcome,
            cost=cost,
            previous_uncertainty=round(previous, 3),
            next_uncertainty=round(self.uncertainty, 3),
            energy=self.energy,
            visible_effect={
                "uncertainty_delta": round(self.uncertainty - previous, 3),
                "signal_after_action": "clearer" if effect < 0 else "more_ambiguous",
            },
        )

    def _hidden_effect(self, action: str, condition: EnvironmentCondition) -> float:
        phase = (condition.turn // 12) % 3
        if action == "calibrate":
            if condition.noise == "high":
                return -0.6 if phase == 1 else 1.3
            if abs(condition.signal) >= 3 and condition.energy >= 2:
                return -3.0
            return 0.8
        if action == "stabilize":
            if phase == 2 and condition.noise == "high":
                return -1.6
            if abs(condition.drift) >= 2:
                return -2.2
            return 0.7
        if action == "probe":
            if phase == 1 and condition.noise == "high":
                return 0.5
            if condition.noise == "high":
                return -1.4
            return -0.4
        if action == "conserve":
            if condition.energy <= 3:
                return -1.8
            return 0.2
        raise ValueError(f"Unknown action: {action}")

    def action_cost(self, action: str) -> float:
        costs = {
            "calibrate": 0.7,
            "stabilize": 0.6,
            "probe": 0.2,
            "conserve": 0.1,
        }
        return costs[action]

    def _energy_delta(self, action: str, effect: float) -> int:
        if action == "conserve":
            return 2
        if action == "probe":
            return 0
        if effect < 0:
            return -1
        return -2


class ESSAHiddenRuleLearner:
    """Runs one observe-detect-hypothesize-predict-act-evaluate-update cycle."""

    def __init__(
        self,
        self_model: SelfModel | None = None,
        environment: HiddenConstraintEnvironment | None = None,
        north_star: str | None = None,
    ) -> None:
        self.self_model = self_model or SelfModel()
        self.environment = environment or HiddenConstraintEnvironment()
        self.north_star = north_star or (
            "Reduce meaningful uncertainty by discovering stable rules in a changing "
            "environment while conserving enough energy to keep learning."
        )
        self.learned_rules: dict[tuple[str, str], LearnedRule] = {}
        self.world_model: list[Belief] = [
            Belief(
                id="B1",
                statement="High signal pressure responds to calibrate when energy is ready.",
                confidence=0.45,
            ),
            Belief(
                id="B2",
                statement="High drift pressure responds to stabilize.",
                confidence=0.45,
            ),
            Belief(
                id="B3",
                statement="High noise is best explored by probe.",
                confidence=0.4,
            ),
            Belief(
                id="B4",
                statement="Low energy makes conserve useful for future learning.",
                confidence=0.4,
            ),
        ]
        self.previous_condition: EnvironmentCondition | None = None
        self.cycle_number = 0
        self.self_model.inspect_substrate(
            StaticSubstrateInspector(
                SubstrateSnapshot(
                    id="hidden-rule-lab",
                    kind="simulated_environment",
                    capabilities=(
                        "observe_condition",
                        "detect_pattern",
                        "hypothesize_action",
                        "predict_uncertainty",
                        "evaluate_result",
                        "update_rules",
                    ),
                    constraints=("hidden_rules", "one_cycle_per_turn", "no_llm_core"),
                    attributes={"actions": list(ACTIONS)},
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
        rules = self.output_forward_rules()
        self.previous_condition = condition

        next_state = {
            **self.self_model.state,
            "north_star": self.north_star,
            "cycle": self.cycle_number,
            "last_condition_key": detected["condition_key"],
            "last_action": result.action,
            "last_outcome": result.outcome,
            "uncertainty": result.next_uncertainty,
            "next_task": next_task,
            "learned_rule_count": len(self.learned_rules),
            "belief_count": len(self.world_model),
        }
        self.self_model.transition_state(
            result.action,
            observation,
            next_state,
            prediction=None,
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
            output_forward_rules=rules,
        )

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

    def _observe(self, condition: EnvironmentCondition) -> Observation:
        return self.self_model.observe_world(
            "hidden_constraint_environment",
            {
                "turn": condition.turn,
                "signal": condition.signal,
                "drift": condition.drift,
                "noise": condition.noise,
                "energy": condition.energy,
                "uncertainty": condition.uncertainty,
            },
            evidence="HiddenConstraintEnvironment.observe",
        )

    def _detect(self, condition: EnvironmentCondition) -> dict[str, Any]:
        features = {
            "signal_pressure": "high" if abs(condition.signal) >= 3 else "low",
            "drift_pressure": "high" if abs(condition.drift) >= 2 else "low",
            "noise_pressure": condition.noise,
            "energy_pressure": "low" if condition.energy <= 3 else "ready",
            "uncertainty_pressure": "high" if condition.uncertainty >= 5 else "low",
        }
        condition_key = "|".join(f"{key}:{value}" for key, value in features.items())
        changes: dict[str, Any] = {}
        if self.previous_condition:
            previous = self.previous_condition
            changes = {
                "signal_delta": condition.signal - previous.signal,
                "drift_delta": condition.drift - previous.drift,
                "noise_changed": condition.noise != previous.noise,
                "energy_delta": condition.energy - previous.energy,
                "uncertainty_delta": round(
                    condition.uncertainty - previous.uncertainty, 3
                ),
            }
        surprises = self._surprises(features, condition)
        return {
            "features": features,
            "condition_key": condition_key,
            "changes_since_last_cycle": changes,
            "surprises": surprises,
            "low_confidence_beliefs": [
                belief.id for belief in self.world_model if belief.confidence < 0.5
            ],
        }

    def _hypothesize(self, detected: dict[str, Any]) -> list[dict[str, Any]]:
        condition_key = detected["condition_key"]
        known = [
            rule for (key, _), rule in self.learned_rules.items() if key == condition_key
        ]
        hypotheses: list[dict[str, Any]] = []
        if known:
            best = max(known, key=lambda rule: rule.score())
            hypotheses.append(
                {
                    "id": "H1",
                    "explanation": "A learned condition-action rule applies here.",
                    "action": best.action,
                    "confidence": round(best.confidence, 3),
                    "support": "best_learned_rule_for_detected_condition",
                }
            )
        else:
            features = detected["features"]
            hypotheses.append(
                {
                    "id": "H1",
                    "explanation": "The strongest visible pressure points to a cold-start action.",
                    "action": self._cold_start_action(features),
                    "confidence": 0.2,
                    "support": "cold_start_structural_hypothesis",
                }
            )

        features = detected["features"]
        hypotheses.append(
            {
                "id": "H2",
                "explanation": "Cheap probing may reveal more than acting on the first pattern.",
                "action": "probe",
                "confidence": self._belief_confidence("B3"),
                "support": "information_gain",
            }
        )
        hypotheses.append(
            {
                "id": "H3",
                "explanation": "Energy may be the hidden constraint limiting future learning.",
                "action": "conserve" if features["energy_pressure"] == "low" else "stabilize",
                "confidence": self._belief_confidence("B4"),
                "support": "constraint_check",
            }
        )
        return hypotheses[:3]

    def _predict(
        self,
        condition: EnvironmentCondition,
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
                expected_delta = self._cold_start_expected_delta(action)
                basis = "cold_start_prior"
                confidence = hypothesis["confidence"]
            information_gain = self._expected_information_gain(
                detected, action, known_rule=rule is not None
            )
            cost_risk = self.environment.action_cost(action)
            north_star_progress = self._north_star_progress(action, detected)
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
        self, prediction: dict[str, Any], result: ActionResult
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
        result: ActionResult,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        action = prediction["chosen_action"]
        key = (detected["condition_key"], action)
        rule = self.learned_rules.setdefault(
            key,
            LearnedRule(
                condition_key=detected["condition_key"],
                action=action,
            ),
        )
        rule.attempts += 1
        rule.successes += 1 if result.success else 0
        rule.total_uncertainty_delta += (
            result.next_uncertainty - result.previous_uncertainty
        )
        self.self_model.observe_self(
            {
                "learned_rule": rule.condition_key,
                "action": rule.action,
                "attempts": rule.attempts,
                "success_rate": round(rule.success_rate, 3),
                "average_uncertainty_delta": round(rule.average_uncertainty_delta, 3),
                "prediction_confirmed": evaluation["prediction_confirmed"],
            },
            evidence="ESSAHiddenRuleLearner._update",
        )
        belief_updates = self._update_beliefs(detected, action, evaluation)
        self.world_model = [
            belief for belief in self.world_model if belief.confidence >= 0.2
        ]
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
            return (
                "test_low_confidence_belief:"
                f"{detected['low_confidence_beliefs'][0]}"
            )
        if self.environment.uncertainty <= 2:
            return "retest_high_confidence_beliefs_for_drift"
        if self.environment.energy <= 2:
            return "restore_energy_before_high_cost_actions"
        return "hunt_largest_uncertainty_that_serves_north_star"

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
        if not model_update:
            model_update = "no confidence change"
        surprises = report.detect.get("surprises") or report.evaluate.get("surprise")
        return "\n".join(
            [
                f"OBSERVED:     {report.observe}",
                f"SURPRISES:    {surprises or 'none'}",
                f"HYPOTHESES:   {hypotheses}",
                "CHOSEN ACTION + PREDICTION: "
                f"{report.predict['chosen_action']} | "
                f"{report.predict['written_prediction']}",
                f"RESULT:       {report.act}",
                f"MODEL UPDATE: {model_update}",
                f"NEXT TASK:    {report.next_task}",
            ]
        )

    def _cold_start_action(self, features: dict[str, str]) -> str:
        if features["energy_pressure"] == "low":
            return "conserve"
        if features["noise_pressure"] == "high":
            return "probe"
        if features["signal_pressure"] == "high":
            return "calibrate"
        if features["drift_pressure"] == "high":
            return "stabilize"
        return "probe"

    def _cold_start_expected_delta(self, action: str) -> float:
        priors = {
            "calibrate": -1.0,
            "stabilize": -0.8,
            "probe": -0.3,
            "conserve": -0.2,
        }
        return priors[action]

    def _belief_confidence(self, belief_id: str) -> float:
        for belief in self.world_model:
            if belief.id == belief_id:
                return round(belief.confidence, 3)
        return 0.2

    def _surprises(
        self, features: dict[str, str], condition: EnvironmentCondition
    ) -> list[str]:
        surprises: list[str] = []
        if self.previous_condition is None:
            return surprises
        previous = self.previous_condition
        if features["energy_pressure"] == "low" and previous.energy > 3:
            surprises.append("energy_constraint_crossed_low_threshold")
        if condition.noise != previous.noise:
            surprises.append("noise_pressure_changed")
        if abs(condition.drift - previous.drift) >= 5:
            surprises.append("drift_constraint_moved_sharply")
        return surprises

    def _expected_information_gain(
        self,
        detected: dict[str, Any],
        action: str,
        *,
        known_rule: bool,
    ) -> float:
        gain = 0.8 if not known_rule else 0.25
        if detected["low_confidence_beliefs"]:
            gain += 0.25
        if action == "probe":
            gain += 0.25
        return gain

    def _north_star_progress(
        self, action: str, detected: dict[str, Any]
    ) -> float:
        features = detected["features"]
        if features["energy_pressure"] == "low" and action == "conserve":
            return 1.0
        if features["uncertainty_pressure"] == "high" and action != "conserve":
            return 0.75
        if action == "probe":
            return 0.55
        return 0.45

    def _update_beliefs(
        self,
        detected: dict[str, Any],
        action: str,
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        touched = self._beliefs_for(action, detected)
        if evaluation["prediction_confirmed"]:
            delta = 0.08
        else:
            delta = -0.12
            if touched:
                touched[0].drift_notes.append(
                    f"cycle_{self.cycle_number}: {evaluation['surprise']}"
                )

        updates = []
        for belief in touched:
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
        if not updates and evaluation["surprise"]:
            new_belief = Belief(
                id=f"B{len(self.world_model) + 1}",
                statement=(
                    f"Unexpected result for {action} under "
                    f"{detected['condition_key']} suggests a hidden drifting constraint."
                ),
                confidence=0.35,
                evidence_count=1,
                drift_notes=[f"cycle_{self.cycle_number}: first surprise"],
            )
            self.world_model.append(new_belief)
            updates.append(
                {
                    "belief": new_belief.id,
                    "old_confidence": 0.0,
                    "new_confidence": new_belief.confidence,
                    "reason": "new_surprise_explanation",
                }
            )
        return updates

    def _beliefs_for(
        self, action: str, detected: dict[str, Any]
    ) -> list[Belief]:
        belief_ids = {
            "calibrate": ["B1"],
            "stabilize": ["B2"],
            "probe": ["B3"],
            "conserve": ["B4"],
        }.get(action, [])
        if detected["features"]["noise_pressure"] == "high" and "B3" not in belief_ids:
            belief_ids.append("B3")
        return [
            belief for belief in self.world_model if belief.id in set(belief_ids)
        ]
