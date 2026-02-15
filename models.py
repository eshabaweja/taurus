from pydantic import BaseModel

class CreativeConcept(BaseModel):
    creative_id: str
    sku_id: str
    channel: str
    hook: str
    angle: str
    script: str
    shot_list: str
    cta: str

class PastCreative(CreativeConcept):
    ctr: float
    cvr: float
    cpa: float

class ScoredConcept(BaseModel):
    concept: CreativeConcept
    heuristic_score: float
    llm_critic_score: float

class RunArtifact(BaseModel):
    run_id: str
    artifact_type: str
    payload: dict

class MemoryEntry(BaseModel):
    brand_id: str
    sku_id: str
    key: str
    value: str
    timestamp: int|None = None
