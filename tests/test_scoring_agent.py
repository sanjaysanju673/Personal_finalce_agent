import unittest

from agents.scoring_agent import ScoringAgent


class ScoringAgentTests(unittest.TestCase):
    def test_preliminary_score_uses_fundamental_and_technical_inputs(self):
        agent = ScoringAgent()

        score = agent.preliminary_score(80, 70)

        self.assertEqual(score, 77.0)

    def test_calculate_accepts_report_and_risk_inputs(self):
        agent = ScoringAgent()

        score = agent.calculate(80, 70, 10, 20, 30)

        self.assertEqual(score, 42.5)


if __name__ == "__main__":
    unittest.main()
