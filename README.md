# Multi-Agent Orchestrator (LangGraph)

Async multi-agent workflow using LangGraph with Redis checkpoints: router → search / math / petrol agents, plus responder.

## Features
- Router decides SEARCH / MATH / PETROL / FINISH via prompts + heuristics.
- Async tools: Tavily web search, safe math eval, petrol price API (mock FastAPI).
- Redis Stack checkpoints (RediSearch indexes).
- REPL driver in `main.py`.

## Environment
Set in `.env`:
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `REDIS_URL` — `redis://localhost:6379` (local) or `redis://redis_db:6379` (compose)
- `PETROL_API_BASE_URL` — `http://127.0.0.1:8000` (local) or `http://petrol_api:8000` (compose)

## Local Run
```bash
pip install -r requirements.txt
# optional mock petrol API
uvicorn tools.mock_petrol_api:app --reload --port 8000
# Redis Stack (needs RediSearch)
docker compose up -d redis_db redis_insight
python main.py
```

## Docker Compose (full stack)
```bash
docker compose build
docker compose up -d
docker compose logs -f app
```
REPL inside container:
```bash
docker compose run --rm app
# or attach: docker attach multi_agent_app   # detach: Ctrl+P Ctrl+Q
```

## Services
- `redis_db`: Redis Stack for checkpoints.
- `redis_insight`: UI on `5540`.
- `petrol_api`: mock petrol FastAPI on `8000`.
- `app`: multi-agent REPL (uses OpenAI + Tavily + Redis + petrol API).

## Code Map
- `main.py`: graph build, REPL.
- `agents/`: router, search, math, petrol, responder, shared LLM.
- `tools/`: search (Tavily), math, petrol client.
- `prompts.py`: router/responder prompts.
- `state.py`: state schema (messages as dict for Redis serialization).
- `tools/mock_petrol_api.py`: mock petrol prices.

## Notes
- Requires Redis Stack (not plain Redis). Keep secrets out of VCS. Docker warns `version` obsolete; safe to remove line if desired.
