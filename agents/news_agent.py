import json

from ollama import chat

from config.logging_config import get_logger
from config.settings import LOCAL_OLLAMA_MODEL

logger = get_logger(__name__)


class NewsAgent:

    def __init__(
        self,
        model: str = LOCAL_OLLAMA_MODEL
    ):
        self.model = model

    def analyze(
        self,
        articles,
        use_api: bool = True
    ):
        try:
            if not articles:
                return {
                    "sentiment": "Neutral",
                    "news_score": 50,
                    "confidence": 50,
                    "recommendation": "WATCH",
                    "risk_level": "MEDIUM",
                    "reason": "No news available"
                }

            headlines = "\n".join(
                [article.get("title", "") for article in articles[:10]]
                if isinstance(articles[0], dict)
                else [str(article) for article in articles[:10]]
            )

            if not use_api:
                pos_words = [
                    "gain", "rise", "up", "beat",
                    "positive", "upgrade",
                    "surge", "record",
                    "contract", "order"
                ]

                neg_words = [
                    "fall", "drop", "down",
                    "miss", "negative",
                    "downgrade", "decline",
                    "loss", "penalty"
                ]

                text = headlines.lower()

                pos_count = sum(
                    text.count(word)
                    for word in pos_words
                )

                neg_count = sum(
                    text.count(word)
                    for word in neg_words
                )

                diff = pos_count - neg_count

                score = max(
                    0,
                    min(
                        100,
                        50 + diff * 10
                    )
                )

                sentiment = (
                    "Positive"
                    if score >= 66
                    else "Negative"
                    if score <= 34
                    else "Neutral"
                )

                recommendation = (
                    "BUY"
                    if score >= 75
                    else "WATCH"
                    if score >= 50
                    else "AVOID"
                )

                return {
                    "sentiment": sentiment,
                    "news_score": score,
                    "confidence": 60,
                    "recommendation": recommendation,
                    "risk_level": "MEDIUM",
                    "reason": "Heuristic news analysis"
                }

            prompt = f"""
You are a professional equity research analyst.

Analyze the following company news headlines and estimate their likely impact on the stock price over the next 1 to 3 months.

Consider:

* Revenue growth
* Profitability
* New orders/contracts
* Business expansion
* Regulatory risks
* Debt concerns
* Management quality
* Industry outlook
* Competitive advantage
* Long-term growth potential

Scoring:

0-20   = Extremely Bearish
21-40  = Bearish
41-60  = Neutral
61-80  = Bullish
81-100 = Very Bullish

Recommendations:

BUY
WATCH
AVOID

IMPORTANT:

Return ONLY valid JSON.

Format:

{{
"sentiment": "Positive",
"score": 80,
"confidence": 90,
"recommendation": "BUY",
"risk_level": "LOW",
"reason": "Strong order wins and positive growth outlook"
}}

News Headlines:

{headlines}
"""
            response = chat(
                model=self.model,
                format="json",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response["message"]["content"]

            result = json.loads(content)

            return {
                "sentiment": result.get(
                    "sentiment",
                    "Neutral"
                ),
                "news_score": int(
                    result.get(
                        "score",
                        50
                    )
                ),
                "confidence": int(
                    result.get(
                        "confidence",
                        50
                    )
                ),
                "recommendation": result.get(
                    "recommendation",
                    "WATCH"
                ),
                "risk_level": result.get(
                    "risk_level",
                    "MEDIUM"
                ),
                "reason": result.get(
                    "reason",
                    ""
                )
            }
        except Exception as e:
            logger.exception(
                f"News analysis failed: {e}"
            )

            return {
                "sentiment": "Neutral",
                "news_score": 50,
                "confidence": 50,
                "recommendation": "WATCH",
                "risk_level": "MEDIUM",
                "reason": "Fallback due to error"
            }
