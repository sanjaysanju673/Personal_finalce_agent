from datetime import datetime
from config.logging_config import get_logger

from collectors.stock_list import get_nifty500
from collectors.fundamentals import fetch_fundamentals
from collectors.technicals import calculate_indicators
from collectors.news import get_company_news

from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.news_agent import NewsAgent
from agents.scoring_agent import ScoringAgent
from agents.report_agent import ReportAgent

from tools.telegram_tool import send, send_file
from tools.pdf_tool import text_to_pdf

logger = get_logger(__name__)

TOP_N = 20
FINAL_N = 5


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
    """Fast scoring: Fundamental + Technical only (no LLM, no news analysis)"""
    try:
        symbol = data["symbol"]
        
        fundamental_agent = FundamentalAgent()
        fundamental_result = fundamental_agent.analyze(data["fundamentals"])

        technical_agent = TechnicalAgent()
        technical_result = technical_agent.analyze(data["technicals"])

        scoring_agent = ScoringAgent()
        # Use 0 for news score initially (will be recalculated for top stocks)
        final_score = scoring_agent.calculate(
            fundamental_result["fundamental_score"],
            technical_result["technical_score"],
            0  # Placeholder news score
        )

        return {
            "symbol": symbol,
            "company_name": data["company_name"],
            "final_score": final_score,
            "fundamentals": data["fundamentals"],
            "technicals": data["technicals"],
            "news_articles": data["news_articles"],
            "news": None,
            "fundamental_reasons": fundamental_result["reasons"],
            "technical_reasons": technical_result["reasons"],
            "fundamental_score": fundamental_result["fundamental_score"],
            "technical_score": technical_result["technical_score"]
        }

    except Exception as e:
        logger.error(f"  ✗ Error in fast scoring for {data['symbol']}: {e}", exc_info=True)
        return None


def calculate_news_and_final_score(stock, use_api: bool = False):
    """Add news analysis for a stock and recalculate final score.

    If `use_api` is False, use the local heuristic to avoid API calls.
    """
    logger.info(f"[NEWS SCORE] Adding news analysis for {stock['symbol']}")
    try:
        symbol = stock["symbol"]
        headlines = [item["title"] for item in stock["news_articles"]]
        logger.debug(f"  → Running news analysis for {symbol} (use_api={use_api})")
        news_agent = NewsAgent()
        news_result = news_agent.analyze(headlines, use_api=use_api)
        logger.info(f"  ✓ News score: {news_result['news_score']}")

        logger.debug(f"  → Recalculating final score with news score")
        scoring_agent = ScoringAgent()
        final_score = scoring_agent.calculate(
            stock["fundamental_score"],
            stock["technical_score"],
            news_result["news_score"]
        )
        logger.info(f"  ✓ Final score with news: {final_score}")

        stock["final_score"] = final_score
        stock["news"] = news_result
        return stock

    except Exception as e:
        logger.error(f"  ✗ Error calculating news score for {stock['symbol']}: {e}", exc_info=True)
        stock["news"] = {"sentiment": "Neutral", "news_score": 50}
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
            llm_report = report_agent.generate_report(
                symbol=stock["symbol"],
                final_score=stock["final_score"],
                fundamentals=stock["fundamentals"],
                technicals=stock["technicals"],
                news=stock.get("news", {}).get("sentiment", "Neutral")
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
    Main workflow orchestrator following the new process flow:
    1. NIFTY500 - Fetch stock list
    2. Collect Fundamentals
    3. Collect Technicals
    4. Score
    5. Top 20
    6. News Analysis
    7. Top 5 LLM Report
    8. Telegram
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
        stock_df = stock_df.head(500)
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

        # STEP 5: Top 20
        logger.info("\n[STEP 5/8] TOP 20 - Selecting top stocks from score list")
        ranked_stocks = sorted(
            scored_stocks,
            key=lambda x: x["final_score"],
            reverse=True
        )
        top_stocks = ranked_stocks[:TOP_N]
        logger.info(f"✓ Selected top {len(top_stocks)} stocks for news analysis")
        for idx, stock in enumerate(top_stocks, 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Score {stock['final_score']:.2f}")

        # STEP 6: News Analysis
        logger.info("\n[STEP 6/8] NEWS ANALYSIS - Collecting news and scoring top stocks")
        for idx, stock in enumerate(top_stocks, 1):
            logger.info(f"  → Fetching news for {stock['symbol']}")
            stock["news_articles"] = get_company_news(stock["company_name"])
            logger.info(f"  ✓ Fetched {len(stock['news_articles'])} news articles for {stock['symbol']}")
            # Use heuristic analysis for the initial pass to avoid API calls
            top_stocks[idx-1] = calculate_news_and_final_score(stock, use_api=False)

        # Re-rank after news scoring
        top_stocks = sorted(
            top_stocks,
            key=lambda x: x["final_score"],
            reverse=True
        )
        logger.info("✓ News analysis complete and top stocks re-ranked")
        for idx, stock in enumerate(top_stocks[:FINAL_N], 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Score {stock['final_score']:.2f}")

        # STEP 7: Top 5 LLM Report
        logger.info(f"\n[STEP 7/8] TOP 5 - Selecting top {FINAL_N} stocks for LLM report")
        report_stocks = top_stocks[:FINAL_N]
        for idx, stock in enumerate(report_stocks, 1):
            logger.info(f"  {idx}. {stock['symbol']} - {stock['company_name']}")

        # Re-run news analysis using the API only for the final top-N to save calls
        logger.info("\n[OPTIMIZE] Re-running API-based news analysis for final top stocks")
        for idx, stock in enumerate(report_stocks, 1):
            logger.info(f"  → API news analysis for {stock['symbol']}")
            # fetch fresh articles if needed
            if not stock.get("news_articles"):
                stock["news_articles"] = get_company_news(stock["company_name"])

            # overwrite with API analysis
            report_stocks[idx-1] = calculate_news_and_final_score(stock, use_api=True)

        # Re-sort final report stocks by updated final_score
        report_stocks = sorted(report_stocks, key=lambda x: x["final_score"], reverse=True)

        logger.info(f"\n[STEP 8/8] LLM REPORT - Generating PDF report for top {FINAL_N} stocks")
        final_report = build_daily_report(report_stocks)
        
        # STEP 8: Telegram
        logger.info(f"\n[STEP 8/8] TELEGRAM - Sending report to Telegram")
        
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
        logger.info(f"Top Performers: {len(top_stocks)}")
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"✗ Workflow failed with critical error: {e}", exc_info=True)
        logger.info("[WORKFLOW FAILED] Critical error occurred")
        raise


if __name__ == "__main__":

    run_workflow()