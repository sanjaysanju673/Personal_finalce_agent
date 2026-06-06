class TechnicalAgent:
    
    def analyze(self, data):

        score = 0

        reasons = []

        rsi = data.get("rsi", 0)

        close = data.get("close", 0)

        sma50 = data.get("sma50", 0)

        sma200 = data.get("sma200", 0)

        if rsi > 50:
            score += 25
            reasons.append(
                f"RSI bullish ({round(rsi,2)})"
            )

        if close > sma200:
            score += 25
            reasons.append(
                "Price above 200 SMA"
            )

        if sma50 > sma200:
            score += 25
            reasons.append(
                "Golden trend structure"
            )

        if close > sma50:
            score += 25
            reasons.append(
                "Price above 50 SMA"
            )

        return {
            "technical_score": score,
            "reasons": reasons
        }