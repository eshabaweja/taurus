import os
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import json

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine)

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


class MemoryEntry(Base):
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

def get_session():
    return SessionLocal()
    
# helper functions
def create_run(run_id, brand_id, sku_id, status="running"):

    session = get_session()
    try:
        run = Run(
            run_id=run_id,
            brand_id=brand_id,
            sku_id=sku_id,
            status=status,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run
    finally:
        session.close()

def update_run_status(run_id, status):
    try:
        session = get_session()
        run = session.query(Run).filter_by(run_id=run_id).first()
        if run is None:
            return
        run.status = status
        session.commit()
    finally:
        session.close()

def create_artifact(run_id, artifact_type, payload_dict):
    try:
        session =  get_session()
        artifact = Artifact(
            run_id=run_id,
            artifact_type=artifact_type,
            payload = json.dumps(payload_dict)
        )
        session.add(artifact)
        session.commit()
        session.refresh(artifact)
        return artifact
    finally:
        session.close()

def get_artifacts_by_run_id(run_id):
    session = get_session()
    try:
        artifacts = session.query(Artifact).filter_by(run_id=run_id).all()
        return [
            {
                "id": a.id,
                "run_id": a.run_id,
                "artifact_type": a.artifact_type,
                "payload": json.loads(a.payload), 
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in artifacts
        ]
    finally:
        session.close()

def create_memory_entry(brand_id, sku_id, key, value):
    session = get_session()
    try:
        memory_entry = MemoryEntry(
            brand_id=brand_id,
            sku_id=sku_id,
            key=key,
            value=value
        )
        session.add(memory_entry)
        session.commit()
        session.refresh(memory_entry)
        return memory_entry
    finally:
        session.close()
        
def get_memory_entries(brand_id, sku_id, key=None):
    session = get_session()
    try:
        query = session.query(MemoryEntry).filter_by(brand_id=brand_id, sku_id=sku_id)
        if key is not None:
            query = query.filter_by(key=key)
        memory_entries = query.all()
        return [
            {
                "id": m.id,
                "brand_id": m.brand_id,
                "sku_id": m.sku_id,
                "key": m.key,
                "value": m.value,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memory_entries
        ]
    finally:
        session.close()