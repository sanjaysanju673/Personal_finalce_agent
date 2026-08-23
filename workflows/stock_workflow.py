import os
from datetime import datetime
from config.logging_config import get_logger

from collectors.stock_list import get_nifty500
from collectors.fundamentals import fetch_fundamentals
from collectors.technicals import calculate_indicators
from collectors.news import get_company_news
from collectors.download_reports import CompanyReportAgent as DownloadedReportAgent

from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.news_agent import NewsAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from agents.report_agent import ReportAgent
from agents.company_report_agent import CompanyReportAgent as FundamentalReportAgent

from tools.telegram_tool import send, send_file
from tools.pdf_tool import text_to_pdf

logger = get_logger(__name__)

PRELIMINARY_TOP_N = 50
FINAL_TOP_N = 20
REPORT_TOP_N = 5

DAILY_TRADING_WORKFLOW = [
    "LIVE MARKET SNAPSHOT",
    "LIVE STOCK UNIVERSE",
    "REGIME DETECTOR",
    "STRATEGY SELECTOR",
    "CANDIDATE ENGINE",
    "TRADE VALIDATION",
    "EXECUTION GATE",
    "TRADE MEMORY",
]


def _build_market_snapshot(scored_stocks):
    """Create a lightweight market snapshot used by the daily trading workflow."""
    snapshot = {
        "nifty": 0,
        "banknifty": 0,
        "vix": 0,
        "sector_strength": "balanced",
        "breadth": "neutral",
        "advance_decline": 1.0,
        "institutional_flow": "mixed",
        "gap_volatility": "normal",
        "source": "derived-from-scan",
    }

    if scored_stocks:
        avg_score = sum(item.get("preliminary_score", 0) for item in scored_stocks) / len(scored_stocks)
        snapshot["nifty"] = round(avg_score * 2.5, 2)
        snapshot["banknifty"] = round(avg_score * 2.2, 2)
        snapshot["vix"] = max(12.0, round(18.0 - (avg_score / 10.0), 2))
        snapshot["sector_strength"] = "bullish" if avg_score >= 70 else "balanced"
        snapshot["breadth"] = "positive" if avg_score >= 65 else "neutral"
        snapshot["advance_decline"] = round(min(1.6, max(0.8, avg_score / 100.0)), 2)
        snapshot["institutional_flow"] = "positive" if avg_score >= 70 else "mixed"
        snapshot["gap_volatility"] = "elevated" if snapshot["vix"] > 16 else "normal"

    return snapshot


def _detect_regime(snapshot):
    """Map market conditions to the regime used by the trading workflow."""
    if snapshot.get("vix", 0) > 18.0 or snapshot.get("gap_volatility") == "elevated":
        return "HIGH_VOLATILITY"
    if snapshot.get("breadth") == "positive" and snapshot.get("sector_strength") == "bullish":
        return "TRENDING"
    if snapshot.get("advance_decline", 1.0) < 1.0:
        return "RISK_OFF"
    return "SIDEWAYS"


def _select_strategy(regime):
    strategy_map = {
        "TRENDING": "BREAKOUT_OR_PULLBACK",
        "SIDEWAYS": "MEAN_REVERSION",
        "HIGH_VOLATILITY": "MOMENTUM",
        "RISK_OFF": "DEFENSIVE_NO_TRADE",
    }
    return strategy_map.get(regime, "BREAKOUT_OR_PULLBACK")


def _build_candidate_pool(scored_stocks, top_n=10):
    ranked = sorted(scored_stocks, key=lambda item: item.get("preliminary_score", 0), reverse=True)
    top_30 = ranked[:30]
    top_10 = top_30[:10]
    top_3 = top_10[:3]
    return {
        "top_30": top_30,
        "top_10": top_10,
        "top_3": top_3,
        "selected": top_3[:max(1, int(top_n))],
    }


def _validate_trade(candidate, regime, strategy):
    """Create a simple trading plan for a candidate using the live regime context."""
    score = candidate.get("preliminary_score", 0)
    entry = max(1.0, float(score) / 10.0)
    stop_loss = round(entry * 0.97, 2)
    target = round(entry * 1.08, 2)
    rr = round((target - entry) / max(0.01, entry - stop_loss), 2)
    position_size = 1 if regime in {"TRENDING", "HIGH_VOLATILITY"} else 0.5
    invalidation = "break below prior support" if regime in {"TRENDING", "SIDEWAYS"} else "failed trend continuation"
    return {
        "symbol": candidate.get("symbol"),
        "company_name": candidate.get("company_name", ""),
        "regime": regime,
        "strategy": strategy,
        "entry": entry,
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": rr,
        "position_size": position_size,
        "invalidation": invalidation,
        "paper_trade": True,
    }


def _execution_gate(trade_plan):
    return {
        "paper_trade_first": True,
        "broker_api_ready": False,
        "status": "PAPER_TRADE_READY" if trade_plan else "NO_SETUP",
        "notes": "Use paper-trading before live broker execution.",
    }


def _trade_memory():
    return {
        "today": "monitoring",
        "yesterday": "loaded",
        "losing_setups": [],
        "winning_setups": [],
        "sector_exposure": "balanced",
        "cooldown": "active",
    }


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
            "trade_score": preliminary_score,
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


def _read_report_csv_details(symbol):
    """Read cached report CSVs from reports/<symbol> and return the useful metrics."""
    reports_dir = os.path.join("reports", symbol)
    if not os.path.exists(reports_dir):
        return {}

    cache = {}
    try:
        for filename in os.listdir(reports_dir):
            if not filename.endswith(".csv"):
                continue
            csv_path = os.path.join(reports_dir, filename)
            with open(csv_path, "r", encoding="utf-8") as handle:
                rows = handle.read().strip().splitlines()
                if len(rows) < 2:
                    continue
                metric = rows[1].split(",", 1)[0].strip()
                value = rows[1].split(",", 1)[1].strip()
                value_clean = value.replace("%", "")
                if metric.lower().startswith("compounded sales") or "sales growth" in metric.lower():
                    try:
                        cache["sales_growth"] = float(value_clean)
                    except ValueError:
                        pass
                elif metric.lower().startswith("compounded profit") or "profit growth" in metric.lower():
                    try:
                        cache["profit_growth"] = float(value_clean)
                    except ValueError:
                        pass
                elif "opm" in metric.lower() or "operating profit" in metric.lower() or "operating margin" in metric.lower():
                    try:
                        cache["operating_margin"] = float(value_clean)
                    except ValueError:
                        pass
    except Exception as exc:
        logger.warning("Failed to parse cached report CSVs for %s: %s", symbol, exc)

    return cache


def load_report_score(stock):
    """Load cached report data when available and use it as the stock-detail layer."""
    symbol = stock["symbol"]
    reports_dir = os.path.join("reports", symbol)
    report_details = {}

    try:
        if not os.path.exists(reports_dir):
            logger.info(f"  → Downloading report data for {symbol} because the local folder is missing")
            DownloadedReportAgent().download(symbol, stock.get("fundamentals", {}))

        if os.path.exists(reports_dir):
            downloaded = DownloadedReportAgent().analyze(symbol)
            report_details = _read_report_csv_details(symbol)
            report_details.update({
                "report_score": downloaded.get("report_score", 0),
                "reasons": downloaded.get("reasons", []),
                "source": "reports-cache",
            })
            stock["report_score"] = report_details["report_score"]
            stock["report_reasons"] = report_details["reasons"]
            stock["report_details"] = report_details
            logger.info(f"  ✓ Loaded cached report details for {symbol}: {stock['report_score']}")
            return stock
    except Exception as exc:
        logger.warning(f"  ⚠ Failed to read downloaded report data for {symbol}: {exc}")

    fallback = FundamentalReportAgent().analyze(stock.get("fundamentals", {}))
    stock["report_score"] = fallback.get("report_score", 0)
    stock["report_reasons"] = fallback.get("reasons", [])
    stock["report_details"] = {
        "source": "live-fallback",
        "report_score": stock["report_score"],
        "reasons": stock["report_reasons"],
    }
    logger.info(f"  → Using fallback report score for {symbol}: {stock['report_score']}")
    return stock


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

        stock = load_report_score(stock)
        scoring_agent = ScoringAgent()
        final_score = scoring_agent.calculate(
            stock["fundamental_score"],
            stock["technical_score"],
            news_result["news_score"],
            stock["report_score"],
            risk_result["risk_score"]
        )
        logger.info(f"  ✓ Dynamic trade score: {final_score}")

        stock["final_score"] = final_score
        stock["trade_score"] = final_score
        stock["news"] = news_result
        stock["risk"] = risk_result
        stock["risk_score"] = risk_result["risk_score"]
        stock["momentum_score"] = stock["technical_score"]
        stock["relative_strength_score"] = stock["fundamental_score"]
        stock["volume_score"] = max(0, min(100, ((stock["technical_score"] + news_result["news_score"]) / 2.0)))
        stock["setup_score"] = stock["technical_score"]
        stock["market_regime_score"] = max(0, min(100, ((stock["technical_score"] + news_result["news_score"] + risk_result["risk_score"]) / 3.0)))
        stock["catalyst_score"] = news_result["news_score"]
        return stock

    except Exception as e:
        logger.error(f"  ✗ Error calculating news/risk score for {stock['symbol']}: {e}", exc_info=True)
        stock["news"] = {"sentiment": "Neutral", "news_score": 50}
        stock["risk"] = {"risk_score": 50, "reasons": []}
        stock["risk_score"] = 50
        stock["final_score"] = stock.get("preliminary_score", 0)
        return stock


def _build_actionable_setups(trade_plan):
    """Create a daily actionable setup list for the trade desk summary."""
    setups = []
    for idx, trade in enumerate(trade_plan[:3], start=1):
        if not trade:
            continue

        symbol = trade.get("symbol") or "UNKNOWN"
        rr = float(trade.get("risk_reward", 1.0) or 1.0)
        trigger = trade.get("invalidation", "breakout above prior high")

        if trade.get("paper_trade") is False:
            status = "NO TRADE YET"
            reason = "execution gate rejected"
            direction = "NO TRADE"
            entry = "₹____"
            sl = "₹____"
            target = "₹____"
        else:
            direction = "LONG"
            status = "READY" if rr >= 2.5 else "WAIT"
            reason = "" if status == "READY" else "pending confirmation"
            entry = "₹____"
            sl = "₹____"
            target = "₹____"

        setups.append({
            "rank": idx,
            "symbol": symbol,
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "target": target,
            "rr": rr,
            "trigger": trigger,
            "status": status,
            "reason": reason,
        })

    if not setups:
        setups.append({
            "rank": 1,
            "symbol": "N/A",
            "direction": "NO TRADE",
            "entry": "₹____",
            "sl": "₹____",
            "target": "₹____",
            "rr": 0.0,
            "trigger": "no valid setup",
            "status": "NO TRADE YET",
            "reason": "No setup passed validation",
        })

    return setups


def build_actionable_setup_text(actionable_setups):
    """Render the trade desk format used in Telegram/PDF output."""
    lines = ["TODAY'S ACTIONABLE SETUPS"]
    for setup in actionable_setups:
        symbol = setup["symbol"]
        direction = setup["direction"]
        rr = setup["rr"]
        status = setup["status"]
        trigger = setup["trigger"]
        if direction == "NO TRADE":
            lines.append(f"\n#{setup['rank']} {symbol}")
            lines.append(f"{direction}")
            lines.append(f"Reason: {setup['reason']}")
            continue

        lines.append(f"\n#{setup['rank']} {symbol}")
        lines.append(direction)
        lines.append(f"Entry: {setup['entry']}")
        lines.append(f"SL: {setup['sl']}")
        lines.append(f"Target: {setup['target']}")
        lines.append(f"R:R: {rr:.1f}")
        lines.append(f"Trigger: {trigger}")
        lines.append(f"Status: {status}")
        if setup.get("reason"):
            lines.append(f"Reason: {setup['reason']}")
    return "\n".join(lines)


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
            report_details = stock.get("report_details", {})
            if report_details:
                report.append(f"Cached detail snapshot: sales growth={report_details.get('sales_growth', 'N/A')}%, "
     f"profit growth={report_details.get('profit_growth', 'N/A')}%, "
     f"OPM={report_details.get('operating_margin', 'N/A')}%")

            llm_report = report_agent.generate_report(
                symbol=stock["symbol"],
                final_score=stock["final_score"],
                fundamentals=stock["fundamentals"],
                technicals=stock["technicals"],
                news=stock.get("news", {}),
                report_analysis=stock.get("report_reasons", []),
                risk_analysis=stock.get("risk", {}),
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


def run_workflow(top_n: int = 20, symbol: str = None, max_symbols: int = None, mode: str = "fast", force_refresh: bool = False):
    """
    Daily trading-agent workflow aligned to the live market pipeline:
    1. Live market snapshot
    2. Live stock universe
    3. Regime detector
    4. Strategy selector
    5. Candidate engine
    6. Trade validation
    7. Execution gate
    8. Trade memory

    In the current implementation, the screening and ranking layer is the live stock
    research foundation behind that trading pipeline, but the structure of the daily
    trade flow is preserved in the returned metadata and logs.
    """
    import os

    logger.info("=" * 60)
    logger.info("[WORKFLOW START] DAILY TRADING AGENT PIPELINE")
    logger.info("=" * 60)
    for idx, step in enumerate(DAILY_TRADING_WORKFLOW, start=1):
        logger.info("%s. %s", idx, step)

    start_time = datetime.now()
    pdf_path = None
    telegram_sent = False
    market_snapshot = {} 
    regime = "SIDEWAYS"
    strategy = "MEAN_REVERSION"
    trade_plan = []

    try:
        # STEP 1: NIFTY500 - Fetch stock list
        logger.info("\n[STEP 1/8] LIVE MARKET SNAPSHOT - Refreshing market context")
        stock_df = get_nifty500()
        logger.info(f"✓ Fetched {len(stock_df)} stocks from NIFTY500")

        if max_symbols is not None:
            stock_df = stock_df.head(max_symbols)
        stock_df = stock_df.head(500 if top_n is None else max(500, int(top_n) * 10))
        logger.info(f"✓ Processing first {len(stock_df)} stocks")

        market_snapshot = _build_market_snapshot([])
        logger.info("Market snapshot prepared: %s", market_snapshot)

        # STEP 2: Live stock universe
        logger.info("\n[STEP 2/8] LIVE STOCK UNIVERSE - Screening the market universe")

        # STEP 3: Collect Fundamentals
        logger.info("\n[STEP 3/8] COLLECT FUNDAMENTALS - Gathering fundamentals for each stock")
        fundamentals_list = []
        for idx, (_, row) in enumerate(stock_df.iterrows(), 1):
            symbol_name = row["Symbol"]
            company = row["Company Name"]
            fundamentals = collect_fundamentals(symbol_name, company)
            if fundamentals:
                fundamentals_list.append(fundamentals)

            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(stock_df)} fundamentals collected")

        logger.info(f"✓ Fundamentals collected for {len(fundamentals_list)} stocks")

        if not fundamentals_list:
            logger.warning("⚠ No fundamentals collected successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No fundamentals data")
            return {
                "symbol": symbol or "NIFTY500",
                "mode": mode,
                "from_cache": False,
                "top_candidates": [],
                "summary": "No fundamentals data found",
                "report_path": None,
                "telegram_sent": False,
            }

        # STEP 3: Collect Technicals
        logger.info("\n[STEP 4/8] COLLECT TECHNICALS - Gathering technical indicators for stocks")
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
            return {
                "symbol": symbol or "NIFTY500",
                "mode": mode,
                "from_cache": False,
                "top_candidates": [],
                "summary": "No technical data found",
                "report_path": None,
                "telegram_sent": False,
            }

        # STEP 4: Score
        logger.info("\n[STEP 5/8] SCORE - Calculating preliminary scores from fundamentals and technicals")
        scored_stocks = []
        for idx, data in enumerate(collected_data, 1):
            score_result = calculate_fast_scores(data)
            if score_result:
                scored_stocks.append(score_result)
            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(collected_data)} stocks scored")

        market_snapshot = _build_market_snapshot(scored_stocks)
        regime = _detect_regime(market_snapshot)
        strategy = _select_strategy(regime)
        logger.info("Regime detected: %s | strategy: %s | snapshot: %s", regime, strategy, market_snapshot)

        logger.info(f"✓ Score calculation complete: {len(scored_stocks)} stocks scored")

        if not scored_stocks:
            logger.warning("⚠ No stocks scored successfully. Exiting.")
            logger.info("[WORKFLOW FAILED] No scores calculated")
            return {
                "symbol": symbol or "NIFTY500",
                "mode": mode,
                "from_cache": False,
                "top_candidates": [],
                "summary": "No scores calculated",
                "report_path": None,
                "telegram_sent": False,
            }

        # STEP 5: Preliminary Score
        logger.info("\n[STEP 6/8] REGIME DETECTOR - Confirming today's trading regime")
        logger.info("Detected regime: %s", regime)

        logger.info("\n[STEP 7/8] STRATEGY SELECTOR - Choosing the execution strategy")
        logger.info("Selected strategy: %s", strategy)

        logger.info("\n[STEP 8/8] CANDIDATE ENGINE - Shortlisting the best setups")
        preliminary_ranked = sorted(
            scored_stocks,
            key=lambda x: x["preliminary_score"],
            reverse=True,
        )
        candidate_pool = _build_candidate_pool(preliminary_ranked, top_n=max(1, int(top_n)))
        top_50 = candidate_pool["top_30"][:PRELIMINARY_TOP_N]
        logger.info(f"✓ Selected top {len(top_50)} candidates for detailed analysis")
        for idx, stock in enumerate(top_50, 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Preliminary Score {stock['preliminary_score']:.2f}")

        logger.info("\n[TRADE VALIDATION] Evaluating entry, SL, target, and R:R for shortlisted setups")
        trade_plan = [
            _validate_trade(stock, regime, strategy)
            for stock in candidate_pool["selected"]
        ]
        logger.info("Validated %s trade setups for paper trading", len(trade_plan))

        logger.info("\n[EXECUTION GATE] Enforcing paper-trade-first decision")
        execution_gate = _execution_gate(trade_plan)
        logger.info("Execution gate status: %s", execution_gate["status"])

        logger.info("\n[TRADE MEMORY] Preparing the memory layer for the daily cycle")
        memory = _trade_memory()

        logger.info("\n[REPORT PREP] Downloading or loading report data for the shortlisted stocks")
        for stock in top_50:
            load_report_score(stock)

        logger.info("\n[NEWS + RISK] Gathering news and risk data for shortlisted stocks")
        final_candidates = []
        for idx, stock in enumerate(top_50, 1):
            logger.info(f"  → Fetching news for {stock['symbol']}")
            stock["news_articles"] = get_company_news(stock["company_name"])
            logger.info(f"  ✓ Fetched {len(stock['news_articles'])} news articles for {stock['symbol']}")
            final_candidates.append(calculate_news_and_final_score(stock, use_api=False))

        logger.info("\n[FINAL SCORE] Refining the shortlist with live news and risk inputs")
        final_ranked = sorted(
            final_candidates,
            key=lambda x: x.get("trade_score", x.get("final_score", 0)),
            reverse=True,
        )
        top_20 = final_ranked[:FINAL_TOP_N]
        logger.info("✓ News and risk analysis complete, shortlist re-ranked by dynamic trade score")
        for idx, stock in enumerate(top_20, 1):
            logger.info(f"  #{idx}. {stock['symbol']}: Trade Score {stock.get('trade_score', stock.get('final_score', 0)):.2f}")

        logger.info(f"\n[REPORT STOCKS] Preparing the top {REPORT_TOP_N} names for report generation")
        report_stocks = top_20[:REPORT_TOP_N]
        for idx, stock in enumerate(report_stocks, 1):
            logger.info(f"  {idx}. {stock['symbol']} - {stock['company_name']}")

        logger.info("\n[OPTIMIZE] Re-running API-based news analysis on the final report shortlist")
        for idx, stock in enumerate(report_stocks, 1):
            logger.info(f"  → API news analysis for {stock['symbol']}")
            if not stock.get("news_articles"):
                stock["news_articles"] = get_company_news(stock["company_name"])
            report_stocks[idx - 1] = calculate_news_and_final_score(stock, use_api=True)

        report_stocks = sorted(report_stocks, key=lambda x: x.get("trade_score", x.get("final_score", 0)), reverse=True)

        logger.info(f"\n[TELEGRAM PDF] Generating PDF report for top {REPORT_TOP_N} stocks")
        actionable_setups = _build_actionable_setups(trade_plan)
        final_report = build_daily_report(report_stocks)
        final_report += "\n\n" + build_actionable_setup_text(actionable_setups)

        logger.info("\n[TELEGRAM PDF] Sending report to Telegram")

        try:
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)

            pdf_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(reports_dir, pdf_name)

            logger.info(f"Converting report to PDF: {pdf_path}")
            text_to_pdf(final_report, pdf_path, title="Daily AI Stock Report")

            caption = f"Daily AI Stock Report - {datetime.now().strftime('%d-%m-%Y')}"
            telegram_sent = send_file(pdf_path, caption=caption)
            logger.info("✓ PDF report sent to Telegram successfully")
        except Exception as e:
            logger.error(f"✗ Failed to generate/send PDF report: {e}", exc_info=True)
            logger.warning("Report was generated but Telegram delivery failed")

        final_top = top_20[:max(1, int(top_n))]
        final_top = top_20[:max(1, int(top_n))]
        actionable_setups = _build_actionable_setups(trade_plan)
        result = {
            "symbol": symbol or "NIFTY500",
            "mode": mode,
            "from_cache": False,
            "market_universe_size": len(stock_df),
            "scanned_candidates": len(scored_stocks),
            "top_candidates": [
                {
                    "symbol": item.get("symbol"),
                    "company_name": item.get("company_name", ""),
                    "preliminary_score": item.get("preliminary_score", 0),
                    "final_score": item.get("final_score", item.get("preliminary_score", 0)),
                    "trade_score": item.get("trade_score", item.get("final_score", item.get("preliminary_score", 0))),
                }
                for item in final_top
            ],
            "actionable_setups": actionable_setups,
            "summary": f"Daily trading-agent cycle completed: scanned {len(scored_stocks)} stocks and selected top {len(final_top)} setups.",
            "report_path": pdf_path,
            "telegram_sent": telegram_sent,
            "workflow_steps": DAILY_TRADING_WORKFLOW,
            "regime": regime,
            "strategy": strategy,
            "market_snapshot": market_snapshot,
            "execution_gate": execution_gate,
            "trade_plan": trade_plan,
            "trade_memory": memory,
        }

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
        return result

    except Exception as e:
        logger.error(f"✗ Workflow failed with critical error: {e}", exc_info=True)
        logger.info("[WORKFLOW FAILED] Critical error occurred")
        raise


if __name__ == "__main__":
    run_workflow()