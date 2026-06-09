from datetime import datetime
from config.logging_config import get_logger

from collectors.stock_list import get_nifty500
from collectors.fundamentals import fetch_fundamentals
from collectors.technicals import calculate_indicators
from collectors.news import get_company_news

from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.news_agent import NewsAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from agents.report_agent import ReportAgent
from agents.company_report_agent import CompanyReportAgent

from tools.telegram_tool import send, send_file
from tools.pdf_tool import text_to_pdf

logger = get_logger(__name__)

PRELIMINARY_TOP_N = 50
FINAL_TOP_N = 20
REPORT_TOP_N = 5


def collect_stock_data(symbol, company_name):
    """Collect fundamentals and technicals for a stock."""
    logger.info(f"[COLLECT] Fetching fundamentals and technicals for {symbol}")
    try:
        logger.debug(f"  → Fetching fundamentals for {symbol}")
        fundamentals = fetch_fundamentals(symbol)
        if not fundamentals:
            logger.warning(f"  ✗ No fundamental data for {symbol}")
            return None

        logger.debug(f"  → Fetching technical indicators for {symbol}")
        technicals = calculate_indicators(symbol)
        if not technicals:
            logger.warning(f"  ✗ No technical data for {symbol}")
            return None

        return {
            "symbol": symbol,
            "company_name": company_name,
            "fundamentals": fundamentals,
            "technicals": technicals,
            "news_articles": []
        }

    except Exception as e:
        logger.error(f"  ✗ Error collecting data for {symbol}: {e}", exc_info=True)
        return None


def collect_fundamentals(symbol, company_name):
    """Collect fundamental data for one stock."""
    logger.info(f"[COLLECT] Fetching fundamentals for {symbol}")
    try:
        fundamentals = fetch_fundamentals(symbol)
        if not fundamentals:
            logger.warning(f"  ✗ No fundamental data for {symbol}")
            return None

        return {
            "symbol": symbol,
            "company_name": company_name,
            "fundamentals": fundamentals
        }
    except Exception as e:
        logger.error(f"  ✗ Error collecting fundamentals for {symbol}: {e}", exc_info=True)
        return None


def collect_technicals(stock):
    """Collect technical data for one stock after fundamentals are available."""
    symbol = stock["symbol"]
    logger.info(f"[COLLECT] Fetching technicals for {symbol}")
    try:
        technicals = calculate_indicators(symbol)
        if not technicals:
            logger.warning(f"  ✗ No technical data for {symbol}")
            return None

        stock["technicals"] = technicals
        stock["news_articles"] = []
        return stock
    except Exception as e:
        logger.error(f"  ✗ Error collecting technicals for {symbol}: {e}", exc_info=True)
        return None


def calculate_fast_scores(data):
    """Fast scoring: fundamentals + technicals for the preliminary ranking pass."""
    try:
        symbol = data["symbol"]

        fundamental_agent = FundamentalAgent()
        fundamental_result = fundamental_agent.analyze(data["fundamentals"])

        technical_agent = TechnicalAgent()
        technical_result = technical_agent.analyze(data["technicals"])

        scoring_agent = ScoringAgent()
        preliminary_score = scoring_agent.preliminary_score(
            fundamental_result["fundamental_score"],
            technical_result["technical_score"]
        )

        return {
            "symbol": symbol,
            "company_name": data["company_name"],
            "preliminary_score": preliminary_score,
            "final_score": preliminary_score,
            "fundamentals": data["fundamentals"],
            "technicals": data["technicals"],
            "news_articles": data["news_articles"],
            "news": None,
            "risk": None,
            "fundamental_reasons": fundamental_result["reasons"],
            "technical_reasons": technical_result["reasons"],
            "fundamental_score": fundamental_result["fundamental_score"],
            "technical_score": technical_result["technical_score"],
            "risk_score": 50,
            "report_reasons": []
        }

    except Exception as e:
        logger.error(f"  ✗ Error in fast scoring for {data['symbol']}: {e}", exc_info=True)
        return None


def calculate_news_and_final_score(stock, use_api: bool = False):
    """Add news and risk analysis, then recalculate the final score."""
    logger.info(f"[NEWS + RISK] Analyzing {stock['symbol']}")
    try:
        symbol = stock["symbol"]
        headlines = [item["title"] for item in stock.get("news_articles", [])]
        logger.debug(f"  → Running news analysis for {symbol} (use_api={use_api})")

        news_agent = NewsAgent()
        news_result = news_agent.analyze(headlines, use_api=use_api)
        logger.info(f"  ✓ News score: {news_result['news_score']} / Sentiment: {news_result['sentiment']}")

        risk_agent = RiskAgent()
        risk_input = risk_input = {
    "debt_equity": stock["fundamentals"].get(
        "debt_equity", 0
    ),

    "cash_flow": stock["fundamentals"].get(
        "cash_flow", "weak"
    ),

    "management_sentiment": stock[
        "fundamentals"
    ].get(
        "management_sentiment",
        "neutral"
    ),

    "negative_news": news_result.get(
        "sentiment", ""
    ).lower() in {
        "negative",
        "bearish"
    },

    "regulatory_risk": False
}
        risk_result = risk_agent.analyze(risk_input)
        logger.info(f"  ✓ Risk score: {risk_result['risk_score']}")
        company_report_agent = CompanyReportAgent()
        report_result = company_report_agent.analyze(stock["fundamentals"])
        stock["report_score"] = report_result["report_score"]
        stock["report_reasons"] = report_result["reasons"]
        scoring_agent = ScoringAgent()
        final_score = final_score = scoring_agent.calculate(
    stock["fundamental_score"],
    stock["technical_score"],
    news_result["news_score"],
    stock["report_score"],
    risk_result["risk_score"]
)
        logger.info(f"  ✓ Final score: {final_score}")

        stock["final_score"] = final_score
        stock["news"] = news_result
        stock["risk"] = risk_result
        stock["risk_score"] = risk_result["risk_score"]
        return stock

    except Exception as e:
        logger.error(f"  ✗ Error calculating news/risk score for {stock['symbol']}: {e}", exc_info=True)
        stock["news"] = {"sentiment": "Neutral", "news_score": 50}
        stock["risk"] = {"risk_score": 50, "reasons": []}
        stock["risk_score"] = 50
        stock["final_score"] = stock.get("preliminary_score", 0)
        return stock


def build_daily_report(top_stocks):
    """Step 6: Generate LLM analysis for top stocks"""
    logger.info(f"[LLM ANALYSIS] Building report for top {len(top_stocks)} stocks")

    report = []
    report.append(f"📈 Daily AI Stock Report")
    report.append(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    report.append(f"{'='*50}\n")

    rank = 1
    report_agent = ReportAgent()

    for stock in top_stocks:
        logger.debug(f"  → Generating LLM report for {stock['symbol']} (Rank #{rank})")
        try:
            llm_report = llm_report = report_agent.generate_report(
                            symbol=stock["symbol"],
                            final_score=stock["final_score"],
                            fundamentals=stock["fundamentals"],
                            technicals=stock["technicals"],
                            news=stock.get("news", {}),
                            report_analysis=stock.get(
                                "report_reasons", []
                            ),
                            risk_analysis=stock.get(
                                "risk", {}
                            )
)
            report.append(f"\n{'─'*50}")
            report.append(f"#{rank}. {stock['symbol']} | Score: {stock['final_score']}")
            report.append(f"{'─'*50}")
            report.append(llm_report)
            logger.debug(f"  ✓ LLM report generated for {stock['symbol']}")
            rank += 1
        except Exception as e:
            logger.error(f"  ✗ Error generating report for {stock['symbol']}: {e}", exc_info=True)
            continue

    report.append(f"\n{'='*50}")
    report.append(f"Report Generated By: AI Stock Analysis System")
    
    return "\n".join(report)


def run_workflow():
    """
    Main workflow orchestrator following the updated process flow:
    1. NIFTY500 - Fetch stock list
    2. Collect Fundamentals
    3. Collect Technicals
    4. Fundamental Agent
    5. Technical Agent
    6. Preliminary Score
    7. Top 50
    8. News Analysis
    9. Risk Analysis
    10. Final Score
    11. Top 20
    12. Top 5 LLM Reports
    13. Telegram PDF
    """
    logger.info("=" * 60)
    logger.info("[WORKFLOW START] Daily Stock Analysis Pipeline at 8 AM")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # STEP 1: NIFTY500 - Fetch stock list
        logger.info("\n[STEP 1/8] NIFTY500 - Fetching stock list")
        stock_df = get_nifty500()
        logger.info(f"✓ Fetched {len(stock_df)} stocks from NIFTY500")
        
        # Limit to first 100 for testing (can increase later)
        stock_df = stock_df.head(20)
        logger.info(f"✓ Processing first {len(stock_df)} stocks")
        
        # STEP 2: Collect Fundamentals
        logger.info("\n[STEP 2/8] COLLECT FUNDAMENTALS - Gathering fundamentals for each stock")
        fundamentals_list = []
        for idx, (_, row) in enumerate(stock_df.iterrows(), 1):
            symbol = row["Symbol"]
            company = row["Company Name"]
            fundamentals = collect_fundamentals(symbol, company)
            if fundamentals:
                fundamentals_list.append(fundamentals)

            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(stock_df)} fundamentals collected")

        logger.info(f"✓ Fundamentals collected for {len(fundamentals_list)} stocks")

        if not fundamentals_list:
            logger.warning("⚠ No fundamentals collected successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No fundamentals data")
            return

        # STEP 3: Collect Technicals
        logger.info("\n[STEP 3/8] COLLECT TECHNICALS - Gathering technical indicators for stocks")
        collected_data = []
        for idx, stock in enumerate(fundamentals_list, 1):
            result = collect_technicals(stock)
            if result:
                collected_data.append(result)

            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(fundamentals_list)} technicals collected")

        logger.info(f"✓ Technicals collected for {len(collected_data)} stocks")

        if not collected_data:
            logger.warning("⚠ No technicals collected successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No technical data")
            return

        # STEP 4: Score
        logger.info("\n[STEP 4/8] SCORE - Calculating scores from fundamentals and technicals")
        scored_stocks = []
        for idx, data in enumerate(collected_data, 1):
            score_result = calculate_fast_scores(data)
            if score_result:
                scored_stocks.append(score_result)
            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(collected_data)} stocks scored")

        logger.info(f"✓ Score calculation complete: {len(scored_stocks)} stocks scored")

        if not scored_stocks:
            logger.warning("⚠ No stocks scored successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No scores calculated")
            return

        # STEP 5: Preliminary Score
        logger.info("\n[STEP 5/13] PRELIMINARY SCORE - Ranking all scored stocks")
        preliminary_ranked = sorted(
            scored_stocks,
            key=lambda x: x["preliminary_score"],
            reverse=True
        )
        top_50 = preliminary_ranked[:PRELIMINARY_TOP_N]
        logger.info(f"✓ Selected top {len(top_50)} candidates for detailed analysis")
        for idx, stock in enumerate(top_50, 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Preliminary Score {stock['preliminary_score']:.2f}")

        # STEP 6: Top 50
        logger.info("\n[STEP 6/13] TOP 50 - Gathering news and risk data for shortlisted stocks")
        final_candidates = []
        for idx, stock in enumerate(top_50, 1):
            logger.info(f"  → Fetching news for {stock['symbol']}")
            stock["news_articles"] = get_company_news(stock["company_name"])
            logger.info(f"  ✓ Fetched {len(stock['news_articles'])} news articles for {stock['symbol']}")
            final_candidates.append(calculate_news_and_final_score(stock, use_api=False))

        # STEP 7: News Analysis + Risk Analysis
        logger.info("\n[STEP 7/13] NEWS ANALYSIS + RISK ANALYSIS - Refining the shortlist")
        final_ranked = sorted(
            final_candidates,
            key=lambda x: x["final_score"],
            reverse=True
        )
        top_20 = final_ranked[:FINAL_TOP_N]
        logger.info("✓ News and risk analysis complete, shortlist re-ranked")
        for idx, stock in enumerate(top_20, 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Final Score {stock['final_score']:.2f}")

        # STEP 8: Final Score
        logger.info("\n[STEP 8/13] FINAL SCORE - Confirming the top 20 final ranking")

        # STEP 9: Top 20
        logger.info(f"\n[STEP 9/13] TOP 20 - Keeping the best {len(top_20)} stocks for report generation")

        # STEP 10: Top 5 LLM Reports
        logger.info(f"\n[STEP 10/13] TOP 5 LLM REPORTS - Preparing the best {REPORT_TOP_N} names for deeper analysis")
        report_stocks = top_20[:REPORT_TOP_N]
        for idx, stock in enumerate(report_stocks, 1):
            logger.info(f"  {idx}. {stock['symbol']} - {stock['company_name']}")

        logger.info("\n[OPTIMIZE] Re-running API-based news analysis on the final report shortlist")
        for idx, stock in enumerate(report_stocks, 1):
            logger.info(f"  → API news analysis for {stock['symbol']}")
            if not stock.get("news_articles"):
                stock["news_articles"] = get_company_news(stock["company_name"])
            report_stocks[idx - 1] = calculate_news_and_final_score(stock, use_api=True)

        report_stocks = sorted(report_stocks, key=lambda x: x["final_score"], reverse=True)

        logger.info(f"\n[STEP 11/13] TELEGRAM PDF - Generating PDF report for top {REPORT_TOP_N} stocks")
        final_report = build_daily_report(report_stocks)
        
        # STEP 12: Telegram PDF
        logger.info("\n[STEP 12/13] TELEGRAM PDF - Sending report to Telegram")
        
        try:
            # Create reports directory
            reports_dir = "reports"
            import os
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)

            pdf_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(reports_dir, pdf_name)

            logger.info(f"Converting report to PDF: {pdf_path}")
            text_to_pdf(final_report, pdf_path, title="Daily AI Stock Report")

            caption = f"Daily AI Stock Report - {datetime.now().strftime('%d-%m-%Y')}"
            send_file(pdf_path, caption=caption)
            logger.info("✓ PDF report sent to Telegram successfully")
        except Exception as e:
            logger.error(f"✗ Failed to generate/send PDF report: {e}", exc_info=True)
            logger.warning("Report was generated but Telegram delivery failed")
        
        # Workflow completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 60)
        logger.info("[WORKFLOW COMPLETE] ✓ All steps executed successfully")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Stocks Analyzed: {len(collected_data)}")
        logger.info(f"Stocks Scored: {len(scored_stocks)}")
        logger.info(f"Preliminary Shortlist: {len(top_50)}")
        logger.info(f"Final Top 20: {len(top_20)}")
        logger.info(f"Report Stocks: {len(report_stocks)}")
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"✗ Workflow failed with critical error: {e}", exc_info=True)
        logger.info("[WORKFLOW FAILED] Critical error occurred")
        raise


if __name__ == "__main__":

    run_workflow()