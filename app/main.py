from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from . import crud, schemas, services
from .database import get_db, init_db

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing database and scheduler...")
    init_db()
    
    scheduler.add_job(
        services.update_stale_keywords_service,
        'interval',
        hours=24,
        id="update_stale_keywords_job"
    )
    scheduler.start()
    print("Database and scheduler initialization complete.")
    
    yield
    
    print("Application shutdown: Shutting down scheduler.")
    scheduler.shutdown()
    print("Scheduler shutdown complete.")

app = FastAPI(
    title="Google Trends API",
    description="An API to fetch and store Google Trends keyword popularity data with periodic updates.",
    lifespan=lifespan
)

@app.get("/trends/{keyword}", response_model=List[schemas.TrendDataResponse])
def get_keyword_trends(
    keyword: str,
    start_date: date = Query(None, description="Start date for filtering results (YYYY-MM-DD). Defaults to 90 days ago."),
    end_date: date = Query(None, description="End date for filtering results (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db)
):
    """
    Fetches interest-over-time data for a given keyword.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=90)
    
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date.")

    normalized_keyword = keyword.strip().lower()
    services.fetch_and_store_trends(db, keyword=normalized_keyword)
    db_data = crud.get_trend_data_by_keyword(db, keyword=normalized_keyword, start_date=start_date, end_date=end_date)
    
    if not db_data:
        raise HTTPException(status_code=404, detail=f"No data found for keyword '{keyword}' in the specified range. The keyword may have no search interest.")
        
    return db_data
