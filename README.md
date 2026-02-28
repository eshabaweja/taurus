# Taurus Engineering Assignment

## Instructions
Make a venv, then `source venv/bin/activate`. Setup: `pip install -r requirements.txt`, rename `.env.example` to `.env`, set `OPENAI_API_KEY` (and optional `DATABASE_URL`). Run everything from project root.

Run API: `uvicorn app.main:app --reload`

- **Generate concepts:** `python cli.py generate --brand <brand> --sku <sku> --channel <channel>`  
  Example: `python cli.py generate --brand aniwell --sku itch-relief --channel tiktok`
- **View a run (by ID):** `python cli.py view-run --run-id <uuid>`

Optional: `python cli.py generate --brand aniwell --sku itch-relief --channel tiktok --output runs/my_run.json` to **save the response** to a file.

## Design decisions
SQLite (default `taurus.db`) stores runs, artifacts, and key-value memory (e.g. last-run learnings). ChromaDB (`.chromadb`) is used for vector search: indexing top creatives per run, indexing distilled memory learnings, and computing a novelty penalty so concepts too similar to past winners get a lower score.

Evaluation is heuristic and LLM critic. The heuristic scores hook length, question-style hooks, and novelty; the LLM critic scores 0–10 for hook strength, brand compliance, channel fit. Final score is the average of the two. We take the top N, generate improved variants via LLM, re-score, and pick the best per slot.

The generator is an LLM call with context: brand guidelines, past creatives (from data/tools), key-value memory, and (when available) vector-retrieved top creatives and vector-retrieved memory learnings. After each run we distill short learnings and write them to both SQLite (key-value) and ChromaDB (vector) so future runs can use them. Improvement and memory content are real (not stubs): variants are generated and scored, and learnings are persisted and queried.

## Example run outputs
Create a `runs/` directory if it doesn’t exist.

Cold run: `runs/run_0.json`.  
First run with memory: `runs/run_1.json`.

## Future work
- finding trending patterns on Meta and TikTok to seed the generator or tune scoring
- more vector DB use: e.g. semantic search over past creatives by theme, or clustering to find winning angles
- unit tests for the evaluator heuristic, CLI, and API
- rate limiting and retries for the OpenAI client
- API to list runs (e.g. by brand/sku) instead of only fetch by run ID
- clearer errors when the LLM fails or returns invalid JSON