from workflows.stock_workflow import run_workflow

if __name__ == "__main__":
    # Run workflow once and exit (good for scheduling via Task Scheduler)
    run_workflow()
