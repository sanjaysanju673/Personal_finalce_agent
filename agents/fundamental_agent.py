from config.constants import (
    MIN_ROE,
    MIN_PROFIT_GROWTH,
    MIN_SALES_GROWTH,
    MAX_DEBT_EQUITY
)


class FundamentalAgent:

    def analyze(self, data):

        score = 0

        reasons = []

        roe = data.get("roe", 0)
        profit_growth = data.get("profit_growth", 0)
        sales_growth = data.get("sales_growth", 0)
        debt = data.get("debt_equity", 999)

        if roe >= MIN_ROE:
            score += 25
            reasons.append(
                f"ROE is healthy ({roe}%)"
            )

        if profit_growth >= MIN_PROFIT_GROWTH:
            score += 25
            reasons.append(
                f"Profit growth strong ({profit_growth}%)"
            )

        if sales_growth >= MIN_SALES_GROWTH:
            score += 25
            reasons.append(
                f"Sales growth healthy ({sales_growth}%)"
            )

        if debt <= MAX_DEBT_EQUITY:
            score += 25
            reasons.append(
                f"Low debt ({debt})"
            )

        return {
            "fundamental_score": score,
            "reasons": reasons
        }