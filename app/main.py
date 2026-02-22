from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.storage.db import init_db, get_artifacts_by_run_id, update_run_status
from app.agent import run_agent
from models import GenerateRequest, GenerateResponse, RunResponse, CreativeConcept

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
    result = run_agent(body.brand_id, body.sku_id, body.channel)
    concepts = [CreativeConcept.model_validate(c) for c in result["concepts"]]
    return GenerateResponse(run_id=result["run_id"], concepts=concepts)


@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run_artifacts(run_id: str):
    """Return artifacts stored for this run."""
    artifacts = get_artifacts_by_run_id(run_id)
    return RunResponse(run_id=run_id, artifacts=artifacts)


@app.get("/health")
def health_check():
    return {"status": "ok"}