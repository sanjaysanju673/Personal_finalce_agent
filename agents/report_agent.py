import os

from groq import Groq

from config.logging_config import get_logger
from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_BASE_URL
)

logger = get_logger(__name__)


class ReportAgent:

    def __init__(self):

        if GROQ_API_KEY:

            client_args = {
                "api_key": GROQ_API_KEY
            }

            if GROQ_BASE_URL:

                client_args[
                    "base_url"
                ] = GROQ_BASE_URL

            self.client = Groq(
                **client_args
            )

        else:

            logger.warning(
                "GROQ_API_KEY is not set."
            )

            self.client = Groq()

        self.model = GROQ_MODEL

    def generate_report(

        self,

        symbol,

        final_score,

        fundamentals,

        technicals,

        news,

        report_analysis,

        risk_analysis

    ):

        try:

            prompt = f"""
You are a Senior Equity Research Analyst.

Create a concise professional stock research report.

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

Report Analysis:
{report_analysis}

Risk Analysis:
{risk_analysis}

Instructions:

* Use plain text only.
* Keep report between 150 and 250 words.
* Professional investment style.
* Focus on actionable insights.

Format:

Executive Summary

Investment Rating
Recommendation:
Confidence:

Key Strengths

Key Risks

Fundamental Analysis

Technical Analysis

News Impact Analysis

Report Analysis

Risk Analysis

Short-Term Outlook

Long-Term Outlook

Final Verdict

Generate only the report.
"""

            response = (
                self.client
                .chat
                .completions
                .create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.model,
                    temperature=0.2,
                )
            )

            report = (
                response
                .choices[0]
                .message
                .content
            )

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

AI Report Generation Failed
"""