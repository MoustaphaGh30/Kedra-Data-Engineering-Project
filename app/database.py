from sqlalchemy import create_engine, Column, String, Integer, Date, DateTime, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import datetime

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TrendData(Base):
    __tablename__ = "trend_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    keyword = Column(String, index=True, nullable=False)
    score = Column(Integer, nullable=False)
    isPartial = Column(Boolean, nullable=False, default=False)
    date_queried = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    __table_args__ = (UniqueConstraint('date', 'keyword', name='_date_keyword_uc'),)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()