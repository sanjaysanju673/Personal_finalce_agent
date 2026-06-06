from datetime import datetime

from collectors.stock_list import get_nifty500
from collectors.fundamentals import fetch_fundamentals
from collectors.technicals import calculate_indicators
from collectors.news import get_company_news

from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.news_agent import NewsAgent
from agents.scoring_agent import ScoringAgent
from agents.report_agent import ReportAgent

from tools.telegram_tool import send

TOP_N = 10


def process_stock(symbol, company_name):

    print(f"Processing {symbol}")

    try:

        fundamentals = fetch_fundamentals(symbol)

        if not fundamentals:
            return None

        technicals = calculate_indicators(symbol)

        if not technicals:
            return None

        news_articles = get_company_news(company_name)

        headlines = [
            item["title"]
            for item in news_articles
        ]

        fundamental_agent = FundamentalAgent()

        technical_agent = TechnicalAgent()

        news_agent = NewsAgent()

        scoring_agent = ScoringAgent()

        fundamental_result = (
            fundamental_agent.analyze(
                fundamentals
            )
        )

        technical_result = (
            technical_agent.analyze(
                technicals
            )
        )

        news_result = (
            news_agent.analyze(
                headlines
            )
        )

        final_score = (
            scoring_agent.calculate(
                fundamental_result[
                    "fundamental_score"
                ],
                technical_result[
                    "technical_score"
                ],
                news_result[
                    "news_score"
                ]
            )
        )

        return {

            "symbol": symbol,

            "company_name": company_name,

            "final_score": final_score,

            "fundamentals": fundamentals,

            "technicals": technicals,

            "news": news_result,

            "fundamental_reasons":
                fundamental_result[
                    "reasons"
                ],

            "technical_reasons":
                technical_result[
                    "reasons"
                ]
        }

    except Exception as e:

        print(
            f"Error for {symbol}: {e}"
        )

        return None


def build_daily_report(top_stocks):

    report_agent = ReportAgent()

    report = []

    report.append(
        f"📈 Daily AI Stock Report\n"
        f"{datetime.now().strftime('%d-%m-%Y')}\n"
    )

    rank = 1

    for stock in top_stocks:

        llm_report = (
            report_agent.generate_report(
                symbol=stock["symbol"],
                final_score=stock["final_score"],
                fundamentals=stock["fundamentals"],
                technicals=stock["technicals"],
                sentiment=stock["news"][
                    "sentiment"
                ]
            )
        )

        report.append(
            f"\n{'='*40}\n"
        )

        report.append(
            f"{rank}. "
            f"{stock['symbol']}\n"
        )

        report.append(
            f"Score: "
            f"{stock['final_score']}\n"
        )

        report.append(
            llm_report
        )

        rank += 1

    return "\n".join(report)


def run_workflow():

    print(
        "Starting Stock Analysis..."
    )

    stock_df = get_nifty500()

    results = []

    # Start with first 50 stocks
    # Increase later

    stock_df = stock_df.head(50)

    for _, row in stock_df.iterrows():

        symbol = row["Symbol"]

        company = row["Company Name"]

        result = process_stock(
            symbol,
            company
        )

        if result:

            results.append(result)

    if not results:

        print(
            "No stocks processed"
        )

        return

    ranked = sorted(
        results,
        key=lambda x:
        x["final_score"],
        reverse=True
    )

    top_stocks = ranked[:TOP_N]

    report = build_daily_report(
        top_stocks
    )

    print(report)

    send(report)

    print(
        "Telegram report sent."
    )


if __name__ == "__main__":

    run_workflow()