from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Model Context Protocol (MCP) Server", version="1.0.0")


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


MCP_TOOLS: Dict[str, Dict[str, Any]] = {
    "system_vitals": {
        "definition": {
            "name": "system_vitals",
            "description": "Reads hardware status and cluster availability metrics.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "detailed": {"type": "boolean", "description": "Return full subsystem stats"}
                },
                "required": [],
            },
        },
        "handler": lambda args: {"cluster_status": "healthy", "gpu_utilization": 0.28, "active_nodes": 4},
    }
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp_server"}


@app.get("/mcp/v1/tools")
def list_tools() -> List[Dict[str, Any]]:
    return [tool["definition"] for tool in MCP_TOOLS.values()]


@app.post("/mcp/v1/rpc")
def handle_json_rpc(req: JSONRPCRequest):
    if req.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": [tool["definition"] for tool in MCP_TOOLS.values()]},
        }

    if req.method == "tools/call":
        params = req.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in MCP_TOOLS:
            return {"jsonrpc": "2.0", "id": req.id,
                    "error": {"code": -32601, "message": f"Tool '{name}' not found."}}
        try:
            output = MCP_TOOLS[name]["handler"](arguments)
            return {"jsonrpc": "2.0", "id": req.id,
                    "result": {"content": [{"type": "text", "text": str(output)}]}}
        except Exception as err:
            return {"jsonrpc": "2.0", "id": req.id,
                    "error": {"code": -32000, "message": f"Execution error: {err}"}}

    return {"jsonrpc": "2.0", "id": req.id,
            "error": {"code": -32601, "message": f"Method '{req.method}' not implemented."}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
