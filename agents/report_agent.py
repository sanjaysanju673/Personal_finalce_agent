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
You are a Senior Equity Research Analyst.

Create a professional stock research report suitable for a PDF investment report.

STOCK INFORMATION

Stock Symbol:
{symbol}

Overall Score:
{final_score}/100

Fundamental Metrics:
{fundamentals}

Technical Indicators:
{technicals}

News Analysis:
{news}

REPORT REQUIREMENTS:

* Use clear section headings.
* Use bullet points where appropriate.
* Keep language professional and concise.
* Do not exceed 250 words.
* Do not use markdown code blocks.
* Avoid repeating raw data values unnecessarily.
* Focus on investment insights.

OUTPUT FORMAT:

==================================================
STOCK RESEARCH REPORT
=====================

EXECUTIVE SUMMARY

* Provide a 2-3 sentence summary.

INVESTMENT RATING

* BUY / WATCH / AVOID
* Confidence Level: LOW / MEDIUM / HIGH

KEY STRENGTHS
• Strength 1
• Strength 2
• Strength 3

KEY RISKS
• Risk 1
• Risk 2
• Risk 3

FUNDAMENTAL ANALYSIS
• Revenue Growth Assessment
• Profitability Assessment
• Financial Health Assessment

TECHNICAL ANALYSIS
• Trend Direction
• Momentum Analysis
• Support / Resistance Outlook

NEWS IMPACT ANALYSIS
• Sentiment Assessment
• Major Positive Factors
• Major Negative Factors

SHORT-TERM OUTLOOK (1-3 Months)
• Expected stock behavior
• Key catalysts

LONG-TERM OUTLOOK (1-3 Years)
• Growth potential
• Business outlook

FINAL VERDICT
• One clear recommendation.
• One sentence justification.

Generate the report now.
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