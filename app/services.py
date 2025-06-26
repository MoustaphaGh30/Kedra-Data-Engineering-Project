from sqlalchemy.orm import Session
from pytrends.request import TrendReq
from . import crud, schemas
from .database import SessionLocal
from datetime import date, datetime
import time


def update_stale_keywords_service():
    """
    Service function designed to be run by the background scheduler.
    It gets all stale keywords and triggers an update for each.
    """
    print(f"[{datetime.now()}] Running scheduled job: Checking for stale keywords...")
    db = SessionLocal()
    try:
        stale_keywords = crud.get_stale_keywords(db)
        if not stale_keywords:
            print("No stale keywords found. Job finished.")
            return

        print(f"Found {len(stale_keywords)} stale keywords to update: {stale_keywords}")
        for keyword in stale_keywords:
            fetch_and_store_trends(db, keyword)
            time.sleep(5)
        
        print("Scheduled job: All stale keywords updated successfully.")

    finally:
        db.close()

def fetch_and_store_trends(db: Session, keyword: str):
    """
    Main service function to orchestrate fetching, validation, and storing of trend data.
    It handles the initial 90-day fetch and subsequent dynamic updates.
    """
    normalized_keyword = keyword.strip().lower()
    pytrends = TrendReq(hl='en-US', tz=360)
    
    latest_date_in_db = crud.get_latest_data_date(db, keyword=normalized_keyword)
    
    # Case where the keyword has been queried before
    if latest_date_in_db:
        start_date_str = latest_date_in_db.strftime('%Y-%m-%d')
        end_date_str = date.today().strftime('%Y-%m-%d')
        timeframe = f'{start_date_str} {end_date_str}'
        print(f"'{normalized_keyword}' found. Fetching from {start_date_str} to today.")

    # Case where the keyword has never been queried before
    else:
        timeframe = 'today 3-m'
        print(f"First time fetching '{normalized_keyword}'. Fetching last 90 days.")
        
    pytrends.build_payload(kw_list=[normalized_keyword], cat=0, timeframe=timeframe, geo='', gprop='')
    df = pytrends.interest_over_time()
    
    if df.empty:
        print(f"No new trend data found for '{normalized_keyword}' in timeframe '{timeframe}'.")
        return True

    validated_data = []
    for index, row in df.iterrows():

        is_partial_value = row.get('isPartial', False)
        
        validated_data.append(schemas.TrendDataCreate(
            date=index.date(),
            keyword=normalized_keyword,
            score=row[normalized_keyword],
            isPartial=is_partial_value
        ))
    
    crud.bulk_upsert_trend_data(db, data=validated_data)
    
    return True
