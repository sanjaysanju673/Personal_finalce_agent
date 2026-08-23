# Daily Trading Agent

A daily trading workflow built around market snapshot, stock screening, regime detection, strategy selection, candidate filtering, trade validation, and execution gating.

Updated workflow:
1. Live market snapshot
   - NIFTY / BANKNIFTY
   - VIX
   - sector strength
   - breadth
   - advance/decline
   - institutional flow
   - gap / volatility
2. Live stock universe
   - NIFTY500 universe
   - price / volume / relative volume / ATR / VWAP / RSI / EMA
   - breakout / breakdown / relative strength
3. Regime detector
   - trending / sideways / high-volatility / risk-off
4. Strategy selector
   - trend -> breakout / pullback
   - sideways -> mean reversion
   - high volatility -> momentum
   - risk-off -> defensive / no trade
5. Candidate engine
   - shortlist top 30, then top 10, then top 3 setups
6. Trade validation
   - entry / stop loss / target / R:R / liquidity / position size / invalidation
7. Execution gate
   - paper trade first
   - broker order API
   - position monitoring / exit
8. Trade memory
   - today's trades / yesterday's trades / losing setups / winning setups / sector exposure / cooldown

This project currently implements the stock-screening and ranking foundation behind that trading-agent workflow:
- NIFTY500 universe selection
- fundamentals + technical screening
- preliminary and final score ranking
- cached report reuse
- PDF generation
- Telegram delivery

Features:
- Market-wide NIFTY500 screening
- Fundamental and technical evaluation
- Regime-aware shortlist preparation
- Daily trading agent structure and execution flow
- Cached report reuse for faster runs
- Telegram PDF reporting

How it works:
- `run_workflow()` runs the daily trading-agent pipeline.
- It loads the stock universe, scores each stock, and picks the best candidates.
- It reuses cached report data when available to reduce repeated calculations.
- It generates a PDF summary and attempts to send it to Telegram when bot credentials are configured.

Environment:
- Create a `.env` file in the project root with values such as:
  - `GROQ_API_KEY=...`
  - `GROQ_MODEL=openai/gpt-oss-20b`
  - `TELEGRAM_BOT_TOKEN=...`
  - `TELEGRAM_CHAT_ID=...`
  - `DATABASE_PATH=database/stock.db`

Run:
- `python app.py`
- or `python run_daily_once.py`
