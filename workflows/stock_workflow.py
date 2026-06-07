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
from database.repository import (
    save_stock_data
)

from tools.telegram_tool import send, send_file
from tools.pdf_tool import text_to_pdf

logger = get_logger(__name__)

TOP_N = 10


def collect_stock_data(symbol, company_name):
    """Step 1 & 2: Collect fundamentals, technicals, and news data"""
    logger.info(f"[COLLECT] Fetching data for {symbol}")
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

        logger.debug(f"  → Fetching news for {symbol}")
        news_articles = get_company_news(company_name)
        logger.debug(f"  ✓ Got {len(news_articles)} news articles for {symbol}")

        return {
            "symbol": symbol,
            "company_name": company_name,
            "fundamentals": fundamentals,
            "technicals": technicals,
            "news_articles": news_articles
        }

    except Exception as e:
        logger.error(f"  ✗ Error collecting data for {symbol}: {e}", exc_info=True)
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


def calculate_news_and_final_score(stock):
    """Add LLM-based news analysis and recalculate final score"""
    logger.info(f"[LLM SCORE] Adding news analysis for {stock['symbol']}")
    try:
        symbol = stock["symbol"]
        
        headlines = [item["title"] for item in stock["news_articles"]]
        logger.debug(f"  → Running LLM news analysis for {symbol}")
        news_agent = NewsAgent()
        news_result = news_agent.analyze(headlines)
        logger.info(f"  ✓ News score: {news_result['news_score']}")

        logger.debug(f"  → Recalculating final score with LLM news")
        scoring_agent = ScoringAgent()
        final_score = scoring_agent.calculate(
            stock["fundamental_score"],
            stock["technical_score"],
            news_result["news_score"]
        )
        logger.info(f"  ✓ Final score with LLM: {final_score}")

        stock["final_score"] = final_score
        stock["news"] = news_result
        return stock

    except Exception as e:
        logger.error(f"  ✗ Error calculating LLM score for {stock['symbol']}: {e}", exc_info=True)
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
                sentiment=stock["news"]["sentiment"]
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
    Main workflow orchestrator following the exact process flow:
    1. NIFTY500 - Fetch stock list
    2. Collect Data - Gather fundamentals, technicals, news
    3. Store SQLite - Save data to database
    4. Calculate Scores - Analyze and score each stock
    5. Rank Stocks - Sort by final score
    6. Top 10 - Select top performers
    7. LLM Analysis - Generate comprehensive reports
    8. Telegram - Send results to telegram
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
        
        # Limit to first 2200 for testing (can increase later)
        stock_df = stock_df.head(2200)
        logger.info(f"✓ Processing first {len(stock_df)} stocks")
        
        # STEP 2 & 3: Collect Data and Store SQLite
        logger.info("\n[STEP 2/8] COLLECT DATA - Gathering fundamentals, technicals, news")
        logger.info("[STEP 3/8] STORE SQLITE - Saving collected data to database")
        
        collected_data = []
        stored_count = 0
        
        for idx, (_, row) in enumerate(stock_df.iterrows(), 1):
            symbol = row["Symbol"]
            company = row["Company Name"]
            
            # Collect data for each stock
            data = collect_stock_data(symbol, company)
            if data:
                collected_data.append(data)
                
                # Store immediately to database
                logger.debug(f"  → Storing {symbol} in SQLite")
                try:
                    save_stock_data({
                        "symbol": symbol,
                        "company_name": company,
                        "fundamentals": data["fundamentals"],
                        "technicals": data["technicals"],
                        "news": {"sentiment": "neutral"},
                        "final_score": 0,
                        "fundamental_reasons": [],
                        "technical_reasons": []
                    })
                    stored_count += 1
                except Exception as e:
                    logger.error(f"  ✗ Failed to store {symbol}: {e}")
            
            # Progress update
            if idx % 5 == 0:
                logger.info(f"  Progress: {idx}/{len(stock_df)} stocks processed")
        
        logger.info(f"✓ Data collection complete: {len(collected_data)} stocks collected, {stored_count} stored in SQLite")
        
        if not collected_data:
            logger.warning("⚠ No stocks processed successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No data collected")
            return
        
        # STEP 4: Calculate Scores (FAST - No LLM)
        logger.info("\n[STEP 4/8] CALCULATE SCORES - Computing fundamental + technical scores (fast)")
        
        scored_stocks = []
        for idx, data in enumerate(collected_data, 1):
            score_result = calculate_fast_scores(data)
            if score_result:
                scored_stocks.append(score_result)
            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(collected_data)} stocks fast-scored")
        
        logger.info(f"✓ Fast score calculation complete: {len(scored_stocks)} stocks scored")
        
        if not scored_stocks:
            logger.warning("⚠ No stocks scored successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No scores calculated")
            return
        
        # STEP 5: Rank Stocks
        logger.info("\n[STEP 5/8] RANK STOCKS - Sorting by fundamental + technical score")
        
        ranked_stocks = sorted(
            scored_stocks,
            key=lambda x: x["final_score"],
            reverse=True
        )
        
        logger.info(f"✓ Ranking complete. Top 5 stocks (before LLM):")
        for idx, stock in enumerate(ranked_stocks[:5], 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Score {stock['final_score']:.2f}")
        
        # STEP 6: Top 10
        logger.info(f"\n[STEP 6/8] TOP 10 - Selecting top {TOP_N} performers for LLM analysis")
        
        top_stocks = ranked_stocks[:TOP_N]
        logger.info(f"✓ Selected top {len(top_stocks)} stocks for LLM-based news analysis")
        
        for idx, stock in enumerate(top_stocks, 1):
            logger.info(f"  {idx}. {stock['symbol']} - {stock['company_name']}")
        
        # STEP 6B: LLM News Analysis for Top Stocks Only
        logger.info(f"\n[STEP 6B/8] LLM NEWS ANALYSIS - Adding LLM analysis to top {len(top_stocks)} stocks")
        
        for idx, stock in enumerate(top_stocks, 1):
            top_stocks[idx-1] = calculate_news_and_final_score(stock)
        
        # Re-rank after adding LLM scores
        top_stocks = sorted(
            top_stocks,
            key=lambda x: x["final_score"],
            reverse=True
        )
        
        logger.info(f"✓ LLM analysis complete. Updated top {len(top_stocks)} stocks with LLM scores:")
        for idx, stock in enumerate(top_stocks, 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Final Score {stock['final_score']:.2f}")
        
        # STEP 7: LLM Analysis (Report Generation)
        logger.info(f"\n[STEP 7/8] LLM ANALYSIS - Generating detailed reports")
        
        final_report = build_daily_report(top_stocks)
        
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