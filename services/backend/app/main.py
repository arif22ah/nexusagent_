from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.agent.orchestrator import IN_MEMORY_TOOL_META, IN_MEMORY_TOOLS, nexus_agent
from app.analytics.telemetry import telemetry_service
from app.core.config import settings
from app.core.db import load_persisted_tools, log_execution_audit, persist_sandboxed_tool
from app.tools.sandbox import build_sandboxed_callable


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reload previously registered sandboxed tools from PostgreSQL on startup
    for row in load_persisted_tools():
        try:
            IN_MEMORY_TOOLS[row["name"]] = build_sandboxed_callable(row["name"], row["source_code"])
            IN_MEMORY_TOOL_META[row["name"]] = row.get("description", "")
        except Exception:
            pass
    yield


app = FastAPI(title="NexusAgent Enterprise Gateway", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryPayload(BaseModel):
    query: str
    session_id: str = "default-session"


class DynamicToolRegistration(BaseModel):
    name: str
    description: str
    source_code: str


@app.get("/health")
def health():
    return {
        "status": "online",
        "subsystems": ["pytorch", "tensorflow", "langgraph", "mcp"],
        "mounted_tools": list(IN_MEMORY_TOOLS.keys()),
    }


@app.post("/api/v1/agent/run")
def execute_agent(payload: QueryPayload):
    try:
        initial_state = {
            "messages": [HumanMessage(content=payload.query)],
            "context": {"session_id": payload.session_id},
            "neural_confidence": 0.0,
        }
        res = nexus_agent.invoke(initial_state)
        response_text = res["messages"][-1].content
        confidence = float(res.get("neural_confidence", 0.0))

        log_execution_audit(
            session_id=payload.session_id,
            query_text=payload.query,
            response_text=response_text,
            confidence=confidence,
        )

        return {
            "response": response_text,
            "confidence": confidence,
            "session_id": payload.session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tools/register")
def register_sandboxed_tool(payload: DynamicToolRegistration):
    try:
        fn = build_sandboxed_callable(payload.name, payload.source_code)
        IN_MEMORY_TOOLS[payload.name] = fn
        IN_MEMORY_TOOL_META[payload.name] = payload.description
        persist_sandboxed_tool(payload.name, payload.description, payload.source_code, is_sandboxed=True)
        return {
            "status": "success",
            "message": f"Tool '{payload.name}' sandboxed, persisted, and mounted successfully.",
            "tool_registry_size": len(IN_MEMORY_TOOLS),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Safety check failed: {e}")


@app.get("/api/v1/telemetry/plot")
def get_telemetry_plot():
    return {"image_data": telemetry_service.render_analytics_chart()}
