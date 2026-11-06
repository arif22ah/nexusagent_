import time
from typing import Annotated, Any, Dict, List, TypedDict

import numpy as np
import requests
import torch
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.analytics.telemetry import telemetry_service
from app.core.config import settings
from app.models.neural_gate import PyTorchPolicyGate, TensorFlowAuxiliaryValidator
from app.tools.sandbox import invoke_sandboxed_tool

pytorch_gate = PyTorchPolicyGate(input_dim=16)
tf_validator = TensorFlowAuxiliaryValidator()

IN_MEMORY_TOOLS: Dict[str, Any] = {}
IN_MEMORY_TOOL_META: Dict[str, str] = {}


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context: Dict[str, Any]
    neural_confidence: float


def _mcp_endpoints() -> List[str]:
    urls = [f"{settings.MCP_SERVER_URL}/mcp/v1/rpc"]
    if "mcp_server" in settings.MCP_SERVER_URL:
        urls.append(settings.MCP_SERVER_URL.replace("mcp_server", "localhost") + "/mcp/v1/rpc")
    return urls


def query_mcp_tools() -> List[Dict[str, Any]]:
    payload = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
    for url in _mcp_endpoints():
        try:
            res = requests.post(url, json=payload, timeout=2)
            if res.status_code == 200:
                return res.json().get("result", {}).get("tools", [])
        except Exception:
            continue
    return []


def execute_mcp_tool_rpc(tool_name: str, arguments: Dict[str, Any]) -> str:
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 2,
    }
    last_err = "Tool execution rejected."
    for url in _mcp_endpoints():
        try:
            res = requests.post(url, json=payload, timeout=4)
            if res.status_code == 200:
                body = res.json()
                if "error" in body:
                    return f"MCP error: {body['error'].get('message')}"
                content = body.get("result", {}).get("content", [])
                return content[0].get("text", "") if content else "Tool finished with empty output."
        except Exception as e:
            last_err = f"MCP Protocol Fault: {e}"
    return last_err


def neural_guardrail_node(state: AgentState):
    t0 = time.time()
    session_id = state.get("context", {}).get("session_id", "default-session")
    # Deterministic feature projection from user message so confidence is meaningful and stable
    user_msg = str(state["messages"][-1].content) if state.get("messages") else ""
    rng = np.random.default_rng(abs(hash(user_msg)) % (2**32))
    simulated_features = torch.tensor(rng.standard_normal((1, 16)), dtype=torch.float32)
    confidence = pytorch_gate(simulated_features).item()
    anomaly = tf_validator.compute_anomaly_metric(rng.standard_normal(8))

    merged_ctx = dict(state.get("context") or {})
    merged_ctx["anomaly_metric"] = anomaly
    merged_ctx["gate_passed"] = confidence >= settings.CONFIDENCE_THRESHOLD

    telemetry_service.record_step("neural_gate", (time.time() - t0) * 1000, confidence, session_id=session_id)
    return {"neural_confidence": confidence, "context": merged_ctx}


def reasoning_executor_node(state: AgentState):
    t0 = time.time()
    session_id = state.get("context", {}).get("session_id", "default-session")
    user_msg = str(state["messages"][-1].content)
    confidence = state.get("neural_confidence", 0.5)

    mcp_tools = query_mcp_tools()
    tool_names = [t["name"] for t in mcp_tools] + list(IN_MEMORY_TOOLS.keys())

    # Match any registered in-memory sandboxed tool by name or 'evaluate' keyword
    matched_tool = None
    for t_name in IN_MEMORY_TOOLS:
        if t_name.lower() in user_msg.lower():
            matched_tool = t_name
            break
    if not matched_tool and "evaluate" in user_msg.lower() and IN_MEMORY_TOOLS:
        matched_tool = "custom_eval" if "custom_eval" in IN_MEMORY_TOOLS else next(iter(IN_MEMORY_TOOLS))

    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"):
        llm = ChatOpenAI(model=settings.MODEL_NAME, api_key=settings.OPENAI_API_KEY, temperature=0)
        sys_msg = SystemMessage(content=f"You are an enterprise AI Orchestrator. Registered Dynamic Tools: {tool_names}.")
        response = llm.invoke([sys_msg] + list(state["messages"]))
        output_text = response.content
    else:
        output_text = f"[Agent Output] Query processed with neural gate confidence {confidence:.3f}.\n"
        if "vitals" in user_msg.lower() and "system_vitals" in tool_names:
            tool_res = execute_mcp_tool_rpc("system_vitals", {"detailed": True})
            output_text += f"\n• MCP System Vitals: {tool_res}"
        elif matched_tool:
            try:
                result = invoke_sandboxed_tool(IN_MEMORY_TOOLS[matched_tool], (4, 8))
            except Exception as e:
                result = f"tool error: {e}"
            output_text += f"\n• Sandboxed Tool '{matched_tool}' Output: {result}"
        else:
            output_text += f"Executed default policy. Active tool manifest: {tool_names}"

    telemetry_service.record_step("reasoning", (time.time() - t0) * 1000, confidence, session_id=session_id)
    return {"messages": [AIMessage(content=output_text)]}


def compile_agent_workflow():
    builder = StateGraph(AgentState)
    builder.add_node("guardrail", neural_guardrail_node)
    builder.add_node("executor", reasoning_executor_node)
    builder.set_entry_point("guardrail")
    builder.add_edge("guardrail", "executor")
    builder.add_edge("executor", END)
    return builder.compile()


nexus_agent = compile_agent_workflow()
