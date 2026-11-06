# NexusAgent Platform (Enterprise Edition)

Full-stack agentic AI platform:
- FastAPI + LangGraph (stateful agent workflow, runtime tool loader)
- MCP server (JSON-RPC 2.0 tool discovery)
- PyTorch & TensorFlow (local neural policy gate / validator)
- NumPy, Pandas, Matplotlib (telemetry charts)
- Django Admin (audit logs and tool governance)
- PostgreSQL + pgvector
- Next.js 14 (chat UI + tool hot-deploy console)
- Docker Compose

## Run

    docker compose up --build

First build takes 10-20 min (PyTorch + TensorFlow are large). Then open:

| Service        | URL                            |
|----------------|--------------------------------|
| Web UI         | http://localhost:3000          |
| Backend docs   | http://localhost:8000/docs     |
| MCP server     | http://localhost:8080/health   |
| Django admin   | http://localhost:8001/admin/ (admin / admin12345) |

Edit `.env` to set a real `OPENAI_API_KEY` (default `mock-key` = offline demo mode).

## Try it
1. In the UI type `show system vitals` (calls the MCP tool).
2. Click "Validate & Mount to Agent", then type `evaluate` (runs your sandboxed tool).
3. Click "Render Plot" for telemetry.

Reset the database: `docker compose down -v`
