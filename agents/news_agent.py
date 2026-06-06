from langchain_ollama import ChatOllama

from config.settings import (
    OLLAMA_MODEL
)


class NewsAgent:

    def __init__(self):

        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            temperature=0
        )

    def analyze(self, headlines):

        if not headlines:

            return {
                "news_score": 50,
                "sentiment": "Neutral"
            }

        text = "\n".join(headlines)

        prompt = f"""
Analyze the news.

Headlines:

{text}

Return:

Positive
Neutral
Negative

and score from 0 to 100.

Format:

Sentiment:
Score:
"""

        result = self.llm.invoke(prompt)

        content = result.content

        score = 50

        sentiment = "Neutral"

        if "Positive" in content:
            sentiment = "Positive"
            score = 90

        elif "Negative" in content:
            sentiment = "Negative"
            score = 20

        return {
            "sentiment": sentiment,
            "news_score": score,
            "raw_response": content
        }