from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import Config
from src.logger import app_logger

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False) # crowdworks, lancers etc...
    job_url = Column(String(1000), nullable=False, unique=True, index=True)
    external_job_id = Column(String(255))
    title = Column(String(500))
    description = Column(Text)
    reward = Column(String(200))
    deadline = Column(String(100))
    client_name = Column(String(255))
    source_file = Column(String(255))
    
    first_seen_at = Column(String(100), nullable=False, default=lambda: datetime.utcnow().isoformat())
    last_seen_at = Column(String(100), nullable=False, default=lambda: datetime.utcnow().isoformat())
    
    status = Column(String(50), nullable=False, default='new') # new, fetching, fetched, judged, ignored, notified, etc.
    
    ai_match_score = Column(Integer)
    ai_judge_result = Column(String(50)) # matched, unmatached 等
    ai_judge_reason = Column(Text)
    proposal_text = Column(Text)
    
    is_applied = Column(Boolean, nullable=False, default=False)
    application_error = Column(Text)
    
    notified = Column(Integer, nullable=False, default=0) # 0: 未通知, 1: 通知済
    
    created_at = Column(String(100), nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(100), nullable=False, default=lambda: datetime.utcnow().isoformat())

# SQLiteデータベースのエンジン作成
# Config.DB_PATH は pathlib.Path オブジェクト
engine = create_engine(f"sqlite:///{Config.DB_PATH}")

# テーブルの作成
Base.metadata.create_all(engine)

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
