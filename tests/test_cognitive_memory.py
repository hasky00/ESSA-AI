import tempfile
import unittest
from pathlib import Path

from essa.cognitive_memory import CognitiveMemory


class CognitiveMemoryTests(unittest.TestCase):
    def test_surprise_creates_more_salient_memory(self):
        memory = CognitiveMemory()
        ordinary = memory.remember(
            context={"route": "safe"},
            action="observe",
            predicted_delta=-0.2,
            actual_delta=-0.2,
            outcome="partial_signal",
            prediction_confirmed=True,
        )
        surprising = memory.remember(
            context={"route": "unsafe"},
            action="secure_route",
            predicted_delta=-1.0,
            actual_delta=0.5,
            outcome="new_risk_signal",
            prediction_confirmed=False,
            surprises=["violence_increased"],
        )

        self.assertGreater(surprising.salience, ordinary.salience)

    def test_recall_prefers_similar_context(self):
        memory = CognitiveMemory()
        memory.remember(
            context={"route": "danger", "violence": "active"},
            action="secure_route",
            predicted_delta=-1.0,
            actual_delta=-1.4,
            outcome="protective_progress",
            prediction_confirmed=True,
        )
        memory.remember(
            context={"route": "guarded", "violence": "present"},
            action="secure_route",
            predicted_delta=-0.5,
            actual_delta=-0.3,
            outcome="partial_signal",
            prediction_confirmed=True,
        )

        recalled = memory.recall(
            {"route": "danger", "violence": "active"},
            action="secure_route",
            limit=1,
        )

        self.assertEqual(recalled[0].episode_id, "episode-1")
        self.assertEqual(recalled[0].similarity, 1.0)

    def test_recalled_episodes_create_an_estimate(self):
        memory = CognitiveMemory()
        for actual_delta in (-1.0, -1.4):
            memory.remember(
                context={"route": "danger", "violence": "active"},
                action="secure_route",
                predicted_delta=-1.2,
                actual_delta=actual_delta,
                outcome="protective_progress",
                prediction_confirmed=True,
            )

        estimate = memory.estimate(
            {"route": "danger", "violence": "active"}, "secure_route"
        )

        self.assertIsNotNone(estimate)
        self.assertAlmostEqual(estimate["expected_delta"], -1.2, places=1)
        self.assertEqual(len(estimate["episode_ids"]), 2)

    def test_repeated_experience_consolidates_into_semantic_memory(self):
        memory = CognitiveMemory()
        for _ in range(2):
            memory.remember(
                context={"route": "danger", "violence": "active"},
                action="secure_route",
                predicted_delta=-1.0,
                actual_delta=-1.5,
                outcome="protective_progress",
                prediction_confirmed=True,
            )

        lesson = memory.semantic_memories[0]

        self.assertEqual(lesson.action, "secure_route")
        self.assertIn("route:danger", lesson.conditions)
        self.assertEqual(lesson.evidence_count, 2)

    def test_memory_persists_to_json(self):
        memory = CognitiveMemory()
        memory.remember(
            context={"hunger": "high"},
            action="provide_meals",
            predicted_delta=-1.0,
            actual_delta=-1.2,
            outcome="protective_progress",
            prediction_confirmed=True,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            memory.save(path)
            loaded = CognitiveMemory.load(path)

        self.assertEqual(loaded.episodes[0].action, "provide_meals")
        self.assertEqual(loaded.episodes[0].context, {"hunger": "high"})


if __name__ == "__main__":
    unittest.main()
