import unittest

from agents.scoring_agent import ScoringAgent


class ScoringAgentTests(unittest.TestCase):
    def test_preliminary_score_uses_fundamental_and_technical_inputs(self):
        agent = ScoringAgent()

        score = agent.preliminary_score(80, 70)

        self.assertEqual(score, 75.0)

    def test_calculate_accepts_three_arguments_for_preliminary_pass(self):
        agent = ScoringAgent()

        score = agent.calculate(80, 70, 0)

        self.assertEqual(score, 46.0)


if __name__ == "__main__":
    unittest.main()
