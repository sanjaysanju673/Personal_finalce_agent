from config.logging_config import get_logger
from workflows.stock_workflow import run_workflow

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("DAILY TRADING AGENT - RUNNING NOW")
    logger.info("=" * 70 + "\n")

    try:
        result = run_workflow(top_n=20)
        logger.info("\nSUMMARY: %s", result.get("summary", "No summary available"))
        workflow_steps = result.get("workflow_steps", [])
        if workflow_steps:
            logger.info("WORKFLOW STEPS:")
            for idx, step in enumerate(workflow_steps, start=1):
                logger.info("%s. %s", idx, step)

        if result.get("top_candidates"):
            logger.info("TOP CANDIDATES:")
            for idx, item in enumerate(result["top_candidates"], start=1):
                symbol = item.get("symbol", "N/A")
                score = item.get("trade_score", item.get("final_score", item.get("preliminary_score", 0)))
                company_name = item.get("company_name", "")
                logger.info("%s. %s | %s | trade_score=%.2f", idx, symbol, company_name, float(score))
        else:
            logger.info("NO TOP CANDIDATES FOUND")

        actionable = result.get("actionable_setups") or []
        if actionable:
            logger.info("ACTIONABLE SETUPS:")
            for setup in actionable:
                symbol = setup.get("symbol", "N/A")
                logger.info("%s | %s | RR=%.1f | Status=%s", symbol, setup.get("direction", "NO TRADE"), float(setup.get("rr", 0.0)), setup.get("status", "WAIT"))

        if result.get("report_path"):
            logger.info("REPORT PDF GENERATED: %s", result["report_path"])
        if result.get("telegram_sent") is True:
            logger.info("TELEGRAM PDF REPORT SENT SUCCESSFULLY")
        elif result.get("telegram_sent") is False:
            logger.info("TELEGRAM PDF REPORT NOT SENT - credentials missing or API failed")

        logger.info("\n" + "=" * 70)
        logger.info("✓ DAILY TRADING AGENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"✗ Application error: {e}", exc_info=True)
        logger.info("=" * 70)
        logger.info("✗ DAILY TRADING AGENT FAILED")
        logger.info("=" * 70)
        raise