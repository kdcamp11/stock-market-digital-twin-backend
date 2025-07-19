"""
Schedules automatic updates for stock data ingestion.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from ingestion import main as ingestion_job

def start_scheduler(minutes=15):
    scheduler = BlockingScheduler()
    scheduler.add_job(ingestion_job, 'interval', minutes=minutes)
    scheduler.start()

if __name__ == '__main__':
    # Example: run every 15 minutes
    start_scheduler(minutes=15)
