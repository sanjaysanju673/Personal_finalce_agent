from config.logging_config import get_logger

logger = get_logger(__name__)


class CompanyReportAgent:

    def analyze(self, report_data):

        score = 0
        reasons = []

        revenue_growth = report_data.get(
            "revenue_growth", 0
        )

        profit_growth = report_data.get(
            "profit_growth", 0
        )

        debt_trend = report_data.get(
            "debt_trend", ""
        )

        cash_flow = report_data.get(
            "cash_flow", ""
        )

        management_sentiment = report_data.get(
            "management_sentiment", ""
        )

        if revenue_growth >= 10:
            score += 25
            reasons.append(
                f"Strong revenue growth ({revenue_growth}%)"
            )

        if profit_growth >= 10:
            score += 25
            reasons.append(
                f"Strong profit growth ({profit_growth}%)"
            )

        if debt_trend.lower() == "decreasing":
            score += 20
            reasons.append(
                "Debt reducing"
            )

        if cash_flow.lower() == "strong":
            score += 15
            reasons.append(
                "Strong cash flow"
            )

        if management_sentiment.lower() == "positive":
            score += 15
            reasons.append(
                "Positive management outlook"
            )

        return {
            "report_score": score,
            "reasons": reasons
        }