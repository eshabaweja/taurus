import json
import typer
app = typer.Typer()

@app.command()
def generate(
    brand: str = typer.Option(..., "--brand"),
    sku: str = typer.Option(..., "--sku"),
    channel: str = typer.Option(..., "--channel"),
    output: str = typer.Option(None, "--output", "-o", help="Save response JSON to this path (e.g. runs/cold_run.json)"),
):
    from app.agent import run_agent
    typer.echo("Running agent (generating concepts, then scoring with LLM)...")
    result = run_agent(brand, sku, channel)
    typer.echo(f"Run ID: {result['run_id']}")
    for c in result["concepts"]:
        typer.echo(f"  - {c.get('hook', '')}")
    if output:
        payload = {"run_id": result["run_id"], "concepts": result["concepts"]}
        with open(output, "w") as f:
            json.dump(payload, f, indent=2)
        typer.echo(f"Saved to {output}")

@app.command()
def view_run(run_id: str = typer.Option(..., "--run-id")):
    from app.storage.db import get_artifacts_by_run_id
    artifacts = get_artifacts_by_run_id(run_id)
    typer.echo(f"Run {run_id}: {len(artifacts)} artifacts")
    for a in artifacts:
        atype = a.get("artifact_type", "")
        payload = a.get("payload") or {}
        if atype == "concepts":
            concepts = payload.get("concepts", [])
            typer.echo(f"  {atype}: {len(concepts)} concepts")
            for c in concepts:
                typer.echo(f"    - {c.get('hook', '')}")
        elif atype == "evaluation":
            scored = payload.get("scored", [])
            typer.echo(f"  {atype}: {len(scored)} scored")
            for s in scored:
                hook = (s.get("concept") or {}).get("hook", "")
                sc = s.get("score", 0)
                typer.echo(f"    - {sc:.2f}: {hook}")
        else:
            typer.echo(f"  {atype}: {list(payload.keys())}")

if __name__ == "__main__":
    app()