from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from .db import SessionLocal
from .services.snmp import SnmpClient
from .services.discovery import DiscoveryService
from .services.fast_discovery import FastDiscoveryService
from .services.polling import PollingService
from .models import Device
from .config import settings

_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        # Re-enable discovery job with fast discovery (no SNMP)
        snmp_client = SnmpClient(config=settings.snmp_config)
        fast_discovery = FastDiscoveryService(config=settings.snmp_config)
        discovery = DiscoveryService(snmp_client, fast_discovery)

        async def job():
            db: Session = SessionLocal()
            try:
                await discovery.run_discovery(db)
            finally:
                db.close()

        # Run discovery every 30 seconds to catch network changes quickly
        _scheduler.add_job(job, "interval", seconds=30, id="discovery_job")
        print("🚀 Scheduler started with fast discovery every 30 seconds")
        _scheduler.start()


