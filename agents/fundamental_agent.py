from config.constants import (
    MIN_ROE,
    MIN_PROFIT_GROWTH,
    MIN_SALES_GROWTH,
    MAX_DEBT_EQUITY
)
from config.logging_config import get_logger

logger = get_logger(__name__)

class FundamentalAgent:

    def analyze(self, data):
        logger.debug(f"Analyzing fundamental data: {data}")

        score = 0

        reasons = []

        roe = data.get("roe") or 0
        profit_growth = data.get("profit_growth") or 0
        sales_growth = data.get("sales_growth") or 0
        debt = data.get("debt_equity") or 999

        if isinstance(roe, (int, float)) and roe >= MIN_ROE:
            score += 25
            reasons.append(
                f"ROE is healthy ({roe}%)"
            )
            logger.info(f"ROE check passed: {roe}% >= {MIN_ROE}%")

        if isinstance(profit_growth, (int, float)) and profit_growth >= MIN_PROFIT_GROWTH:
            score += 25
            reasons.append(
                f"Profit growth strong ({profit_growth}%)"
            )
            logger.info(f"Profit growth check passed: {profit_growth}% >= {MIN_PROFIT_GROWTH}%")

        if isinstance(sales_growth, (int, float)) and sales_growth >= MIN_SALES_GROWTH:
            score += 25
            reasons.append(
                f"Sales growth healthy ({sales_growth}%)"
            )
            logger.info(f"Sales growth check passed: {sales_growth}% >= {MIN_SALES_GROWTH}%")

        if isinstance(debt, (int, float)) and debt <= MAX_DEBT_EQUITY:
            score += 25
            reasons.append(
                f"Low debt ({debt})"
            )
            logger.info(f"Debt check passed: {debt} <= {MAX_DEBT_EQUITY}")

        logger.info(f"Fundamental analysis complete - Score: {score}, Reasons: {reasons}")
        return {
            "fundamental_score": score,
            "reasons": reasons
        }