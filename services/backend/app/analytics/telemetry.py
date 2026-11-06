import base64
import io
import threading
from collections import deque

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from app.core.db import log_telemetry_step


class TelemetryEngine:
    def __init__(self):
        self.records = deque(maxlen=500)
        self._lock = threading.Lock()

    def record_step(self, step_name: str, latency_ms: float, confidence: float, session_id: str = "default-session"):
        with self._lock:
            self.records.append({"step": step_name, "latency_ms": latency_ms, "confidence": confidence})
        log_telemetry_step(session_id=session_id, step_name=step_name, latency_ms=latency_ms, confidence=confidence)

    def render_analytics_chart(self) -> str:
        with self._lock:
            recent = list(self.records)[-10:]

        if not recent:
            df = pd.DataFrame({
                "step": [f"Step {i}" for i in range(1, 6)],
                "latency_ms": np.random.uniform(80, 150, 5),
                "confidence": np.random.uniform(0.75, 0.98, 5),
            })
        else:
            df = pd.DataFrame(recent)
            df["step"] = [f"{i + 1}:{s}" for i, s in enumerate(df["step"])]

        fig = Figure(figsize=(7, 3.2), dpi=100)
        fig.patch.set_facecolor("#0f172a")
        ax1 = fig.add_subplot(111)
        ax1.set_facecolor("#1e293b")
        ax2 = ax1.twinx()

        ax1.bar(df["step"], df["latency_ms"], color="#38bdf8", alpha=0.7, width=0.4)
        ax2.plot(df["step"], df["confidence"], color="#10b981", marker="o", linewidth=2.5)

        ax1.set_ylabel("Latency (ms)", color="#38bdf8", fontsize=9)
        ax2.set_ylabel("Confidence Score", color="#10b981", fontsize=9)
        ax1.tick_params(colors="#94a3b8", labelsize=7)
        ax2.tick_params(colors="#94a3b8", labelsize=8)
        ax1.tick_params(axis="x", rotation=30)
        ax1.grid(color="#334155", linestyle="--", alpha=0.5)
        ax1.set_title("System Operational Telemetry", color="#f8fafc", fontsize=11, pad=12)
        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode('utf-8')}"


telemetry_service = TelemetryEngine()
