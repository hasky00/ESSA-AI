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


@dataclass(frozen=True)
class CycleReport:
    cycle: int
    observe: dict[str, Any]
    detect: dict[str, Any]
    hypothesize: dict[str, Any]
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
        self.uncertainty = max(0.0, min(10.0, self.uncertainty + effect))
        self.energy = max(0, min(10, self.energy + self._energy_delta(action, effect)))
        self.turn += 1

        return ActionResult(
            action=action,
            success=self.uncertainty < previous,
            previous_uncertainty=round(previous, 3),
            next_uncertainty=round(self.uncertainty, 3),
            energy=self.energy,
            visible_effect={
                "uncertainty_delta": round(self.uncertainty - previous, 3),
                "signal_after_action": "clearer" if effect < 0 else "more_ambiguous",
            },
        )

    def _hidden_effect(self, action: str, condition: EnvironmentCondition) -> float:
        if action == "calibrate":
            if condition.noise == "high":
                return 1.3
            if abs(condition.signal) >= 3 and condition.energy >= 2:
                return -3.0
            return 0.8
        if action == "stabilize":
            if abs(condition.drift) >= 2:
                return -2.2
            return 0.7
        if action == "probe":
            if condition.noise == "high":
                return -1.4
            return -0.4
        if action == "conserve":
            if condition.energy <= 3:
                return -1.8
            return 0.2
        raise ValueError(f"Unknown action: {action}")

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
    ) -> None:
        self.self_model = self_model or SelfModel()
        self.environment = environment or HiddenConstraintEnvironment()
        self.learned_rules: dict[tuple[str, str], LearnedRule] = {}
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
        hypothesis = self._hypothesize(detected)
        prediction = self._predict(condition, detected, hypothesis)
        result = self.environment.apply(hypothesis["action"])
        evaluation = self._evaluate(prediction, result)
        update = self._update(detected, hypothesis, prediction, result, evaluation)
        next_task = self._next_task()
        rules = self.output_forward_rules()

        next_state = {
            **self.self_model.state,
            "cycle": self.cycle_number,
            "last_condition_key": detected["condition_key"],
            "last_action": result.action,
            "last_success": result.success,
            "uncertainty": result.next_uncertainty,
            "next_task": next_task,
            "learned_rule_count": len(self.learned_rules),
        }
        self.self_model.transition_state(
            result.action,
            observation,
            next_state,
            prediction=None,
        )

        return CycleReport(
            cycle=self.cycle_number,
            observe=observation.value,
            detect=detected,
            hypothesize=hypothesis,
            predict=prediction,
            act={
                "action": result.action,
                "success": result.success,
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
        return {"features": features, "condition_key": condition_key}

    def _hypothesize(self, detected: dict[str, Any]) -> dict[str, Any]:
        condition_key = detected["condition_key"]
        known = [
            rule for (key, _), rule in self.learned_rules.items() if key == condition_key
        ]
        if known:
            best = max(known, key=lambda rule: rule.score())
            reason = "best_learned_rule_for_detected_condition"
            confidence = best.confidence
            action = best.action
        else:
            features = detected["features"]
            action = self._cold_start_action(features)
            reason = "cold_start_structural_hypothesis"
            confidence = 0.2
        return {"action": action, "reason": reason, "confidence": round(confidence, 3)}

    def _predict(
        self,
        condition: EnvironmentCondition,
        detected: dict[str, Any],
        hypothesis: dict[str, Any],
    ) -> dict[str, Any]:
        rule = self.learned_rules.get((detected["condition_key"], hypothesis["action"]))
        if rule and rule.attempts:
            expected_delta = rule.average_uncertainty_delta
            basis = "learned_rule"
            confidence = rule.confidence
        else:
            expected_delta = self._cold_start_expected_delta(hypothesis["action"])
            basis = "cold_start_prior"
            confidence = hypothesis["confidence"]
        return {
            "action": hypothesis["action"],
            "basis": basis,
            "expected_uncertainty": round(
                max(0.0, min(10.0, condition.uncertainty + expected_delta)), 3
            ),
            "expected_delta": round(expected_delta, 3),
            "confidence": round(confidence, 3),
        }

    def _evaluate(
        self, prediction: dict[str, Any], result: ActionResult
    ) -> dict[str, Any]:
        predicted_direction = "down" if prediction["expected_delta"] < 0 else "up"
        actual_delta = result.next_uncertainty - result.previous_uncertainty
        actual_direction = "down" if actual_delta < 0 else "up"
        return {
            "success": result.success,
            "predicted_direction": predicted_direction,
            "actual_direction": actual_direction,
            "prediction_confirmed": predicted_direction == actual_direction,
            "actual_delta": round(actual_delta, 3),
        }

    def _update(
        self,
        detected: dict[str, Any],
        hypothesis: dict[str, Any],
        prediction: dict[str, Any],
        result: ActionResult,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        key = (detected["condition_key"], hypothesis["action"])
        rule = self.learned_rules.setdefault(
            key,
            LearnedRule(
                condition_key=detected["condition_key"],
                action=hypothesis["action"],
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
        return {
            "rule": rule.condition_key,
            "action": rule.action,
            "attempts": rule.attempts,
            "success_rate": round(rule.success_rate, 3),
            "average_uncertainty_delta": round(rule.average_uncertainty_delta, 3),
            "previous_prediction_basis": prediction["basis"],
        }

    def _next_task(self) -> str:
        if self.environment.uncertainty <= 2:
            return "maintain_low_uncertainty"
        if self.environment.energy <= 2:
            return "restore_energy_before_high_cost_actions"
        return "continue_mapping_hidden_constraints"

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
