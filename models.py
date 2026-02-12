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