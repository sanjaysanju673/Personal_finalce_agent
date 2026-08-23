from config.logging_config import get_logger

logger = get_logger(__name__)


class RiskAgent:

    def analyze(self, data):

        score = 100
        reasons = []

        debt_equity = data.get(
            "debt_equity", 0
        )

        if debt_equity > 2:
            score -= 25
            reasons.append(
                "High debt"
            )

        if data.get(
            "negative_news", False
        ):
            score -= 25
            reasons.append(
                "Negative news risk"
            )

        if data.get(
            "cash_flow"
        ) == "weak":

            score -= 15

            reasons.append(
                "Weak cash flow"
            )

        if data.get(
            "management_sentiment"
        ) == "negative":

            score -= 15

            reasons.append(
                "Negative management outlook"
            )

        if data.get(
            "regulatory_risk", False
        ):
            score -= 20

            reasons.append(
                "Regulatory concerns"
            )

        score = max(
            score,
            0
        )

        return {
            "risk_score": score,
            "reasons": reasons
        }