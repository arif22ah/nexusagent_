"use client";

import React, { useState } from 'react';

interface ChatMessage {
  sender: 'User' | 'Nexus' | 'System';
  text: string;
  confidence?: number;
}

export default function ConsoleDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [plotUrl, setPlotUrl] = useState<string | null>(null);

  const [toolName, setToolName] = useState('custom_eval');
  const [toolDescription, setToolDescription] = useState('Multiplies two numbers in isolated scope');
  const [toolCode, setToolCode] = useState('def custom_eval(a, b):\n    return a * b + 10');
  const [toolFeedback, setToolFeedback] = useState<string | null>(null);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const sendQuery = async () => {
    if (!inputQuery.trim() || isLoading) return;
    const current = inputQuery;
    setInputQuery('');
    setMessages(prev => [...prev, { sender: 'User', text: current }]);
    setIsLoading(true);

    try {
      const res = await fetch(`${backendUrl}/api/v1/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: current, session_id: 'enterprise-client-1' }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessages(prev => [...prev, { sender: 'System', text: `Error: ${data.detail ?? res.statusText}` }]);
      } else {
        setMessages(prev => [...prev, { sender: 'Nexus', text: data.response, confidence: data.confidence }]);
      }
    } catch {
      setMessages(prev => [...prev, { sender: 'System', text: 'Backend communication error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const registerSandboxedTool = async () => {
    setToolFeedback('Compiling AST and verifying safety...');
    try {
      const res = await fetch(`${backendUrl}/api/v1/tools/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: toolName,
          description: toolDescription,
          source_code: toolCode,
        }),
      });
      const data = await res.json();
      setToolFeedback(res.ok ? `Deployed: ${data.message}` : `Blocked: ${data.detail}`);
    } catch (e: any) {
      setToolFeedback(`Failed: ${e.message}`);
    }
  };

  const refreshTelemetry = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/v1/telemetry/plot`);
      const data = await res.json();
      setPlotUrl(data.image_data);
    } catch {
      alert('Failed to retrieve telemetry visualizations.');
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <div className="flex-1 flex flex-col border-r border-border">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-surface/50">
          <div>
            <h1 className="font-semibold text-lg text-sky-400">NexusAgent Orchestrator</h1>
            <p className="text-xs text-slate-400">LangGraph + MCP + Neural Gate</p>
          </div>
          <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded border border-emerald-500/20">
            System Online
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg max-w-2xl text-sm ${
                m.sender === 'User' ? 'ml-auto bg-sky-600 text-white' : 'bg-surface border border-border'
              }`}
            >
              <div className="flex justify-between items-center mb-1 text-xs opacity-70">
                <span className="font-bold">{m.sender}</span>
                {m.confidence !== undefined && (
                  <span>Confidence: {(m.confidence * 100).toFixed(1)}%</span>
                )}
              </div>
              <div className="whitespace-pre-wrap">{m.text}</div>
            </div>
          ))}
          {isLoading && (
            <div className="text-xs text-slate-500 animate-pulse">
              NexusAgent evaluating state machine and neural policies...
            </div>
          )}
        </div>

        <div className="p-4 border-t border-border bg-surface/30">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-surface border border-border rounded-md px-4 py-2 text-sm focus:outline-none focus:border-sky-500"
              placeholder="Ask a question or try 'show system vitals'..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendQuery()}
            />
            <button
              onClick={sendQuery}
              disabled={isLoading}
              className="bg-sky-500 hover:bg-sky-600 px-5 py-2 text-sm font-semibold rounded-md transition disabled:opacity-50"
            >
              Run Step
            </button>
          </div>
        </div>
      </div>

      <div className="w-[440px] bg-surface flex flex-col p-6 space-y-6 overflow-y-auto">
        <div>
          <h2 className="text-xs font-bold tracking-wider uppercase text-slate-400 mb-3">
            Hot-Deploy Sandboxed Tool
          </h2>
          <div className="space-y-3">
            <input
              className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-white"
              placeholder="Function Name"
              value={toolName}
              onChange={(e) => setToolName(e.target.value)}
            />
            <input
              className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-white"
              placeholder="Description"
              value={toolDescription}
              onChange={(e) => setToolDescription(e.target.value)}
            />
            <textarea
              className="w-full bg-background border border-border rounded p-3 text-xs font-mono text-emerald-400"
              rows={4}
              value={toolCode}
              onChange={(e) => setToolCode(e.target.value)}
            />
            <button
              onClick={registerSandboxedTool}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs py-2 rounded font-medium transition"
            >
              Validate & Mount to Agent
            </button>
            {toolFeedback && (
              <p className="text-xs text-slate-400 mt-1 font-mono break-words">{toolFeedback}</p>
            )}
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-xs font-bold tracking-wider uppercase text-slate-400">
              Operational Telemetry
            </h2>
            <button onClick={refreshTelemetry} className="text-xs text-sky-400 hover:underline">
              Render Plot
            </button>
          </div>
          {plotUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={plotUrl} alt="Telemetry" className="w-full rounded border border-border" />
          ) : (
            <div className="h-32 bg-background flex items-center justify-center text-xs text-slate-500 rounded border border-dashed border-border">
              Click 'Render Plot' to compute NumPy/Pandas stream
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
