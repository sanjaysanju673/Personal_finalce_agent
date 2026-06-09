from config.logging_config import get_logger

logger = get_logger(__name__)


class FundamentalAgent:

    def analyze(self, data):

        logger.debug(
            f"Analyzing fundamental data: {data}"
        )

        score = 0
        reasons = []

        roe = data.get(
            "roe", 0
        )

        revenue_growth = data.get(
            "revenue_growth", 0
        )

        profit_growth = data.get(
            "profit_growth", 0
        )

        debt_equity = data.get(
            "debt_equity", 999
        )

        eps_growth = data.get(
            "eps_growth", 0
        )

        current_ratio = data.get(
            "current_ratio", 0
        )

        # ROE (20)

        if roe >= 20:
            score += 20
            reasons.append(
                f"Excellent ROE ({roe:.2f}%)"
            )

        elif roe >= 15:
            score += 15
            reasons.append(
                f"Good ROE ({roe:.2f}%)"
            )

        # Revenue Growth (20)

        if revenue_growth >= 15:
            score += 20
            reasons.append(
                f"Strong Revenue Growth ({revenue_growth:.2f}%)"
            )

        elif revenue_growth >= 8:
            score += 10
            reasons.append(
                f"Moderate Revenue Growth ({revenue_growth:.2f}%)"
            )

        # Profit Growth (20)

        if profit_growth >= 15:
            score += 20
            reasons.append(
                f"Strong Profit Growth ({profit_growth:.2f}%)"
            )

        elif profit_growth >= 8:
            score += 10
            reasons.append(
                f"Moderate Profit Growth ({profit_growth:.2f}%)"
            )

        # Debt Equity (15)

        if debt_equity <= 0.5:
            score += 15
            reasons.append(
                f"Very Low Debt ({debt_equity})"
            )

        elif debt_equity <= 1:
            score += 10
            reasons.append(
                f"Manageable Debt ({debt_equity})"
            )

        # EPS Growth (15)

        if eps_growth >= 15:
            score += 15
            reasons.append(
                f"Strong EPS Growth ({eps_growth:.2f}%)"
            )

        elif eps_growth >= 5:
            score += 8
            reasons.append(
                f"Positive EPS Growth ({eps_growth:.2f}%)"
            )

        # Current Ratio (10)

        if current_ratio >= 2:
            score += 10
            reasons.append(
                f"Strong Liquidity ({current_ratio:.2f})"
            )

        elif current_ratio >= 1:
            score += 5
            reasons.append(
                f"Adequate Liquidity ({current_ratio:.2f})"
            )

        logger.info(
            f"Fundamental analysis complete - "
            f"Score: {score}"
        )

        return {
            "fundamental_score": score,
            "reasons": reasons
        }