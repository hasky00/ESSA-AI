from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass
class MemoryEpisode:
    id: str
    sequence: int
    context: dict[str, str]
    action: str
    predicted_delta: float
    actual_delta: float
    outcome: str
    prediction_confirmed: bool
    surprises: tuple[str, ...]
    salience: float
    strength: float
    recall_count: int = 0


@dataclass(frozen=True)
class MemoryRecall:
    episode_id: str
    action: str
    actual_delta: float
    outcome: str
    similarity: float
    score: float


@dataclass(frozen=True)
class SemanticMemory:
    id: str
    action: str
    conditions: tuple[str, ...]
    expected_delta: float
    confidence: float
    evidence_count: int


class CognitiveMemory:
    """Dependency-free episodic recall and semantic consolidation for ESSA."""

    def __init__(self, *, max_episodes: int = 200, min_similarity: float = 0.35) -> None:
        if max_episodes < 1:
            raise ValueError("max_episodes must be positive")
        self.max_episodes = max_episodes
        self.min_similarity = min_similarity
        self.episodes: list[MemoryEpisode] = []
        self.semantic_memories: list[SemanticMemory] = []
        self._sequence = 0

    def remember(
        self,
        *,
        context: dict[str, str],
        action: str,
        predicted_delta: float,
        actual_delta: float,
        outcome: str,
        prediction_confirmed: bool,
        surprises: list[str] | tuple[str, ...] = (),
    ) -> MemoryEpisode:
        self._sequence += 1
        normalized_surprises = tuple(item for item in surprises if item)
        prediction_error = abs(actual_delta - predicted_delta)
        salience = min(
            1.0,
            0.2
            + min(0.3, prediction_error * 0.15)
            + (0.25 if not prediction_confirmed else 0.0)
            + min(0.15, len(normalized_surprises) * 0.075)
            + (0.1 if abs(actual_delta) >= 1.0 else 0.0),
        )
        episode = MemoryEpisode(
            id=f"episode-{self._sequence}",
            sequence=self._sequence,
            context=dict(context),
            action=action,
            predicted_delta=round(predicted_delta, 3),
            actual_delta=round(actual_delta, 3),
            outcome=outcome,
            prediction_confirmed=prediction_confirmed,
            surprises=normalized_surprises,
            salience=round(salience, 3),
            strength=round(0.5 + salience * 0.5, 3),
        )
        self.episodes.append(episode)
        self._trim()
        self.consolidate()
        return episode

    def recall(
        self,
        context: dict[str, str],
        *,
        action: str | None = None,
        limit: int = 3,
    ) -> list[MemoryRecall]:
        if limit < 1:
            return []
        candidates: list[tuple[float, MemoryEpisode, float]] = []
        newest = max((episode.sequence for episode in self.episodes), default=1)
        for episode in self.episodes:
            if action is not None and episode.action != action:
                continue
            similarity = self._similarity(context, episode.context)
            if similarity < self.min_similarity:
                continue
            recency = episode.sequence / newest
            score = (
                similarity * 0.65
                + episode.salience * 0.2
                + episode.strength * 0.1
                + recency * 0.05
            )
            candidates.append((score, episode, similarity))

        candidates.sort(key=lambda item: (item[0], item[1].sequence), reverse=True)
        recalls = []
        for score, episode, similarity in candidates[:limit]:
            episode.recall_count += 1
            recalls.append(
                MemoryRecall(
                    episode_id=episode.id,
                    action=episode.action,
                    actual_delta=episode.actual_delta,
                    outcome=episode.outcome,
                    similarity=round(similarity, 3),
                    score=round(score, 3),
                )
            )
        return recalls

    def estimate(self, context: dict[str, str], action: str) -> dict[str, Any] | None:
        recalls = self.recall(context, action=action)
        if not recalls:
            return None
        total_weight = sum(item.score for item in recalls)
        expected_delta = sum(
            item.actual_delta * item.score for item in recalls
        ) / total_weight
        confidence = min(
            0.9,
            0.3
            + sum(item.similarity for item in recalls) / len(recalls) * 0.4
            + len(recalls) * 0.06,
        )
        return {
            "expected_delta": round(expected_delta, 3),
            "confidence": round(confidence, 3),
            "episode_ids": [item.episode_id for item in recalls],
            "similarities": [item.similarity for item in recalls],
        }

    def consolidate(self, *, min_evidence: int = 2) -> list[SemanticMemory]:
        by_action: dict[str, list[MemoryEpisode]] = {}
        for episode in self.episodes:
            by_action.setdefault(episode.action, []).append(episode)

        memories = []
        for action, episodes in sorted(by_action.items()):
            if len(episodes) < min_evidence:
                continue
            conditions = []
            keys = sorted(set().union(*(episode.context for episode in episodes)))
            for key in keys:
                values = [episode.context.get(key) for episode in episodes]
                value = max(set(values), key=values.count)
                if value is not None and values.count(value) / len(values) >= 0.67:
                    conditions.append(f"{key}:{value}")
            expected_delta = sum(item.actual_delta for item in episodes) / len(episodes)
            confirmed_rate = sum(item.prediction_confirmed for item in episodes) / len(
                episodes
            )
            memories.append(
                SemanticMemory(
                    id=f"lesson-{action}",
                    action=action,
                    conditions=tuple(conditions),
                    expected_delta=round(expected_delta, 3),
                    confidence=round(
                        min(0.95, 0.35 + len(episodes) * 0.08 + confirmed_rate * 0.3),
                        3,
                    ),
                    evidence_count=len(episodes),
                )
            )
        self.semantic_memories = memories
        return list(memories)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_episodes": self.max_episodes,
            "min_similarity": self.min_similarity,
            "sequence": self._sequence,
            "episodes": [
                {**asdict(episode), "surprises": list(episode.surprises)}
                for episode in self.episodes
            ],
            "semantic_memories": [
                {**asdict(memory), "conditions": list(memory.conditions)}
                for memory in self.semantic_memories
            ],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CognitiveMemory:
        memory = cls(
            max_episodes=value.get("max_episodes", 200),
            min_similarity=value.get("min_similarity", 0.35),
        )
        memory._sequence = value.get("sequence", 0)
        memory.episodes = [
            MemoryEpisode(
                **{**item, "surprises": tuple(item.get("surprises", ()))},
            )
            for item in value.get("episodes", [])
        ]
        memory.semantic_memories = [
            SemanticMemory(
                **{**item, "conditions": tuple(item.get("conditions", ()))},
            )
            for item in value.get("semantic_memories", [])
        ]
        return memory

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> CognitiveMemory:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def _trim(self) -> None:
        while len(self.episodes) > self.max_episodes:
            weakest = min(
                self.episodes,
                key=lambda episode: (
                    episode.salience * episode.strength,
                    episode.sequence,
                ),
            )
            self.episodes.remove(weakest)

    def _similarity(self, left: dict[str, str], right: dict[str, str]) -> float:
        keys = set(left) | set(right)
        if not keys:
            return 1.0
        matches = sum(left.get(key) == right.get(key) for key in keys)
        return matches / len(keys)
