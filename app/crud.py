from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from sqlalchemy.dialects.postgresql import insert
from app import database as models, schemas
from datetime import date, timedelta
from typing import List

def get_stale_keywords(db: Session, days_stale: int = 7) -> List[str]:
    """
    Gets a list of distinct keywords where the most recent data point
    is older than the specified number of days.
    """
    seven_days_ago = date.today() - timedelta(days=days_stale)
    
    stale_keywords_query = (
        db.query(models.TrendData.keyword)
        .group_by(models.TrendData.keyword)
        .having(func.max(models.TrendData.date) < seven_days_ago)
    )
    
    results = stale_keywords_query.all()
    return [keyword for (keyword,) in results]

def get_latest_data_date(db: Session, keyword: str) -> date | None:
    """
    Gets the date of the most recent data point stored for a given keyword.
    """
    latest_entry = db.query(models.TrendData.date).filter(models.TrendData.keyword == keyword).order_by(desc(models.TrendData.date)).first()
    if latest_entry:
        return latest_entry[0]
    return None

def get_trend_data_by_keyword(db: Session, keyword: str, start_date: date, end_date: date):
    """Retrieves trend data for a keyword within a specific date range."""
    return db.query(models.TrendData).filter(
        models.TrendData.keyword == keyword,
        models.TrendData.date >= start_date,
        models.TrendData.date <= end_date
    ).order_by(models.TrendData.date.asc()).all()

def bulk_upsert_trend_data(db: Session, data: List[schemas.TrendDataCreate]):
    """
    Performs a bulk 'upsert' (insert on conflict update).
    This is efficient and handles updates to existing daily scores, including the isPartial case.
    """
    if not data:
        return

    insert_data = [item.model_dump() for item in data]

    insert_stmt = insert(models.TrendData).values(insert_data)
    
    # Define what to do on conflict (update the score, isPartial flag, and date_queried)
    on_conflict_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['date', 'keyword'],
        set_={
            'score': insert_stmt.excluded.score,
            'isPartial': insert_stmt.excluded.isPartial, 
            'date_queried': insert_stmt.excluded.date_queried
        }
    )
    
    db.execute(on_conflict_stmt)
    db.commit()
