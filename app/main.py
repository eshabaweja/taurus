from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.storage.db import init_db, get_artifacts_by_run_id, create_run, update_run_status
from app.tools import run_tool
from models import GenerateRequest, GenerateResponse, RunResponse
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB."""
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/generate", response_model=GenerateResponse)
def create_generate(body: GenerateRequest):
    run_id = str(uuid.uuid4())
    create_run(run_id, body.brand_id, body.sku_id, status="running")
    # Stub: return empty concepts. Later: run_agent(body.brand_id, body.sku_id, body.channel)
    update_run_status(run_id, "completed")
    return GenerateResponse(run_id=run_id, concepts=[])


@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run_artifacts(run_id: str):
    """Return artifacts stored for this run."""
    artifacts = get_artifacts_by_run_id(run_id)
    return RunResponse(run_id=run_id, artifacts=artifacts)


@app.get("/health")
def health_check():
    return {"status": "ok"}