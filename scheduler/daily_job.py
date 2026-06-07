from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config.logging_config import get_logger
from workflows.stock_workflow import run_workflow
import time

logger = get_logger(__name__)

scheduler = None


def schedule_daily_job():
    """
    Schedule the stock analysis workflow to run daily at 8:00 AM
    """
    global scheduler
    
    logger.info("Initializing Daily Job Scheduler")
    logger.info("Scheduling stock analysis workflow for 8:00 AM daily")
    
    scheduler = BackgroundScheduler()
    
    # Schedule to run at 8:00 AM every day
    scheduler.add_job(
        func=run_workflow,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_stock_analysis',
        name='Daily Stock Analysis Workflow',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✓ Scheduler started successfully")
    logger.info("✓ Workflow scheduled for 08:00 AM daily")
    
    return scheduler


def stop_scheduler():
    """Stop the scheduler gracefully"""
    global scheduler
    if scheduler:
        logger.info("Stopping scheduler...")
        scheduler.shutdown(wait=False)
        logger.info("✓ Scheduler stopped")


def run_manually():
    """Run the workflow immediately (for testing)"""
    logger.info("Running workflow manually (triggered by user)")
    try:
        run_workflow()
    except Exception as e:
        logger.error(f"Manual run failed: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Stock Analysis Scheduler Started")
    logger.info("=" * 60)
    
    try:
        # Initialize scheduler
        schedule_daily_job()
        
        logger.info("Scheduler is running. Press Ctrl+C to exit.")
        
        # Keep the scheduler running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nReceived shutdown signal")
        stop_scheduler()
        logger.info("Scheduler shut down gracefully")
    
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        stop_scheduler()
        raise