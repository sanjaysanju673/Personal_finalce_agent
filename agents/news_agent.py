import json

from ollama import chat

from config.logging_config import get_logger
from config.settings import LOCAL_OLLAMA_MODEL

logger = get_logger(__name__)


class NewsAgent:

    def __init__(self):

        self.model = LOCAL_OLLAMA_MODEL

    def analyze(
        self,
        articles,
        use_api: bool = True
    ):

        try:

            if not articles:

                return {
                    "sentiment": "Neutral",
                    "news_score": 50
                }

            headlines = "\n".join(
                [article.get("title", "") for article in articles[:10]]
                if isinstance(articles[0], dict)
                else [str(article) for article in articles[:10]]
            )

            if not use_api:
                pos_words = ["gain", "rise", "up", "beat", "positive", "upgrade", "surge", "record"]
                neg_words = ["fall", "drop", "down", "miss", "negative", "downgrade", "decline", "loss"]
                text = headlines.lower()
                pos_count = sum(text.count(w) for w in pos_words)
                neg_count = sum(text.count(w) for w in neg_words)
                diff = pos_count - neg_count
                score = max(0, min(100, 50 + diff * 10))
                sentiment = (
                    "Positive" if score >= 66 else
                    "Negative" if score <= 34 else
                    "Neutral"
                )
                logger.info(f"News sentiment (heuristic): {sentiment}, score: {score}")
                return {"sentiment": sentiment, "news_score": score}

            prompt =prompt = f"""
You must respond ONLY with JSON.

Example:

{{
  "sentiment":"Positive",
  "score":80
}}

News Headlines:

{headlines}
"""
            response = chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response["message"]["content"]

            try:
                result = json.loads(content)
                sentiment = result.get("sentiment", "Neutral")
                score = result.get("score", 50)
                logger.info(f"News sentiment (local Ollama): {sentiment}, score: {score}")
                return {"sentiment": sentiment, "news_score": score}
            except Exception:
                logger.warning("JSON parse failed; falling back to heuristic")
                return self.analyze(articles, use_api=False)

        except Exception as e:

            logger.exception(
                f"News analysis failed: {e}"
            )

            return {

                "sentiment": "Neutral",

                "news_score": 50

            }