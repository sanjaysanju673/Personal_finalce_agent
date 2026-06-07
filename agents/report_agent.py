import os

from groq import Groq

from config.logging_config import get_logger
from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL

logger = get_logger(__name__)


class ReportAgent:

    def __init__(self):

        if GROQ_API_KEY:
            client_args = {"api_key": GROQ_API_KEY}
            if GROQ_BASE_URL:
                client_args["base_url"] = GROQ_BASE_URL
            self.client = Groq(**client_args)
        else:
            logger.warning(
                "GROQ_API_KEY is not set. ReportAgent will not be able to call Groq."
            )
            self.client = Groq()

        self.model = GROQ_MODEL

    def generate_report(

        self,

        symbol,

        final_score,

        fundamentals,

        technicals,

        news

    ):

        try:

            prompt = f"""
You are a professional stock market analyst.

Analyze the following stock. and generate a concise report covering the following aspects:

Stock: {symbol}

Final Score:
{final_score}
Fundamentals:
{fundamentals}

Technicals:
{technicals}

News Sentiment:
{news}

Generate:

1. Investment Summary
2. Key Strengths
3. Key Risks
4. Short-Term Outlook
5. Long-Term Outlook

Keep response under 300 words.
"""

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.2,
            )

            report = response.choices[0].message.content

            logger.info(
                f"Report generated for {symbol}"
            )

            return report

        except Exception as e:

            logger.exception(
                f"Report generation failed for {symbol}: {e}"
            )

            return f"""
                                    Stock: {symbol}

                                    Final Score: {final_score}

                                    News Sentiment: {news}

                                    AI Report Generation Failed
                   """