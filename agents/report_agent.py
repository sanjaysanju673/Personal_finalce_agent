from langchain_ollama import ChatOllama

from config.settings import (
    OLLAMA_MODEL
)


class ReportAgent:

    def __init__(self):

        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            temperature=0
        )

    def generate_report(
        self,
        symbol,
        final_score,
        fundamentals,
        technicals,
        sentiment
    ):

        prompt = f"""
You are a stock analyst.

Stock: {symbol}

Final Score: {final_score}

Fundamentals:

{fundamentals}

Technicals:

{technicals}

News Sentiment:

{sentiment}

Generate:

1. Why selected

2. Risks

3. Technical Outlook

Maximum 150 words.
"""

        result = self.llm.invoke(
            prompt
        )

        return result.content