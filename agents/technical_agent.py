from config.logging_config import get_logger

logger = get_logger(__name__)

class TechnicalAgent:
    
    def analyze(self, data):
        logger.debug(f"Analyzing technical data: {data}")

        score = 0

        reasons = []

        rsi = data.get("rsi") or 0

        close = data.get("close") or 0

        sma50 = data.get("sma50") or 0

        sma200 = data.get("sma200") or 0

        if rsi > 50:
            score += 25
            reasons.append(
                f"RSI bullish ({round(rsi, 2)})"
            )
            logger.info(f"RSI check passed: {round(rsi, 2)} > 50")

        if close > sma200:
            score += 25
            reasons.append(
                "Price above 200 SMA"
            )
            logger.info(f"Price above 200 SMA check passed: {close} > {sma200}")

        if sma50 > sma200:
            score += 25
            reasons.append(
                "Golden trend structure"
            )
            logger.info(f"Golden cross check passed: SMA50 {sma50} > SMA200 {sma200}")

        if close > sma50:
            score += 25
            reasons.append(
                "Price above 50 SMA"
            )
            logger.info(f"Price above 50 SMA check passed: {close} > {sma50}")

        logger.info(f"Technical analysis complete - Score: {score}, Reasons: {reasons}")
        return {
            "technical_score": score,
            "reasons": reasons
        }