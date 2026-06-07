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
            prompt = prompt = f"""
You are a Senior Equity Research Analyst.

Create a concise professional stock research report.

Stock Symbol: {symbol}

Overall Score: {final_score}/100

Fundamental Metrics:
{fundamentals}

Technical Indicators:
{technicals}

News Analysis:
{news}

Instructions:

* Use plain text only.
* Do not use boxes, separators, lines, stars, markdown, emojis or ASCII art.
* Use the exact section titles below.
* Keep the report between 150 and 250 words.
* Write in professional investment research style.
* Focus on actionable insights.

Format:

Executive Summary

Investment Rating
Recommendation:
Confidence:

Key Strengths

* Point 1
* Point 2
* Point 3

Key Risks

* Point 1
* Point 2
* Point 3

Fundamental Analysis

Technical Analysis

News Impact Analysis

Short-Term Outlook

Long-Term Outlook

Final Verdict

Generate only the report.
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