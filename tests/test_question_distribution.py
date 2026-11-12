import unittest

from interview_app_backend.services.question_distribution import (
    get_weighted_distribution,
    get_question_type_for_index,
    QuestionType,
)


class TestQuestionDistribution(unittest.TestCase):

    def test_get_weighted_distribution_returns_dict(self):
        result = get_weighted_distribution()
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 5)

    def test_distribution_weights_sum_to_one(self):
        result = get_weighted_distribution()
        total = sum(result.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_get_question_type_for_index_returns_valid_type(self):
        qtype = get_question_type_for_index(1)
        self.assertIsInstance(qtype, QuestionType)

    def test_get_question_type_for_index_sequence_covers_types(self):
        types = set()
        for i in range(1, 21):
            types.add(get_question_type_for_index(i))
        self.assertGreaterEqual(len(types), 3)

    def test_get_question_type_for_index_with_gaps_increases_gap_weight(self):
        types = []
        for i in range(1, 11):
            types.append(get_question_type_for_index(i, has_gaps=True))
        has_gap_type = types.count(QuestionType.GAP_FOCUSED)
        self.assertGreater(has_gap_type, 0)

    def test_distribution_includes_all_types(self):
        result = get_weighted_distribution()
        expected_types = [
            QuestionType.TECHNICAL,
            QuestionType.BEHAVIOURAL,
            QuestionType.ROLE_SPECIFIC,
            QuestionType.GAP_FOCUSED,
            QuestionType.FOLLOW_UP,
        ]
        for qtype in expected_types:
            self.assertIn(qtype, result)


if __name__ == "__main__":
    unittest.main()