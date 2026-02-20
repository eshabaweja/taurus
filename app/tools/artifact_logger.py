from app.storage.db import create_artifact


def log_artifact(run_id, artifact_type, payload):
    create_artifact(run_id, artifact_type, payload)
    return {"ok": True, "run_id": run_id, "artifact_type": artifact_type}
