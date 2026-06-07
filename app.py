from config.logging_config import get_logger
from workflows.stock_workflow import run_workflow

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("STOCK ANALYSIS SYSTEM - RUNNING NOW")
    logger.info("=" * 70 + "\n")
    
    try:
        run_workflow()
        logger.info("\n" + "=" * 70)
        logger.info("✓ APPLICATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"✗ Application error: {e}", exc_info=True)
        logger.info("=" * 70)
        logger.info("✗ APPLICATION FAILED")
        logger.info("=" * 70)
        raise