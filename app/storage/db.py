import os
from sqlalchemy.orm.session import Session
from dotenv import load_dotenv
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    brand_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    artifacts: Mapped[list["Artifact"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    run: Mapped["Run"] = relationship(back_populates="artifacts")


class Memory_Entry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session()->Session:
    return Session()
    
# helper functions
def create_run(run_id, brand_id, sku_id, status="running"):
    pass
def update_run_status(run_id, status):
    pass
def insert_artifact(run_id, artifact_type, payload_dict):
    pass
def get_artifacts_by_run_id(run_id):
    pass
def write_memory_entry(brand_id, sku_id, key, value):
    pass
def get_memory_entries(brand_id, sku_id, key=None):
    pass