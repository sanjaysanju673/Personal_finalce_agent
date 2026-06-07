from config.logging_config import get_logger

logger = get_logger(__name__)


class FundamentalAgent:

    def analyze(self, data):

        logger.debug(
            f"Analyzing fundamental data: {data}"
        )

        score = 0

        reasons = []

        roe = data.get("roe") or 0

        profit_margin = data.get(
            "profit_growth"
        ) or 0

        debt = data.get(
            "debt_equity"
        ) or 999

        market_cap = data.get(
            "market_cap"
        ) or 0

        # ROE
        if roe >= 15:

            score += 35

            reasons.append(
                f"Strong ROE ({roe:.2f}%)"
            )

            logger.info(
                f"ROE check passed: {roe}%"
            )

        # Profit Margin
        if profit_margin >= 10:

            score += 25

            reasons.append(
                f"Healthy Profit Margin ({profit_margin:.2f}%)"
            )

            logger.info(
                f"Profit Margin check passed: {profit_margin}%"
            )

        # Debt
        if debt <= 1:

            score += 25

            reasons.append(
                f"Low Debt ({debt})"
            )

            logger.info(
                f"Debt check passed: {debt}"
            )

        # Market Cap
        if market_cap >= 100_000_000_000:

            score += 15

            reasons.append(
                "Large Cap Company"
            )

            logger.info(
                f"Market Cap check passed: {market_cap}"
            )

        logger.info(
            f"Fundamental analysis complete - "
            f"Score: {score}, "
            f"Reasons: {reasons}"
        )

        return {

            "fundamental_score": score,

            "reasons": reasons

        }