import json
import logging
from typing import Any, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_db_connection():
    # Fall back gracefully between 'postgres' (Docker) and 'localhost' (local CMD)
    try:
        return psycopg2.connect(settings.DATABASE_URL, connect_timeout=2)
    except Exception:
        if "@postgres:" in settings.DATABASE_URL:
            fallback_url = settings.DATABASE_URL.replace("@postgres:", "@localhost:")
            return psycopg2.connect(fallback_url, connect_timeout=2)
        raise


def log_execution_audit(session_id: str, query_text: str, response_text: str, confidence: float) -> None:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Insert into Django's audit_registry_executionauditrecord if migrated
                cur.execute(
                    """
                    INSERT INTO audit_registry_executionauditrecord
                        (session_id, query_text, response_text, neural_confidence, timestamp)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """,
                    (session_id, query_text, response_text, float(confidence)),
                )
    except Exception as e:
        logger.debug(f"Django audit table insert skipped: {e}")


def log_telemetry_step(session_id: str, step_name: str, latency_ms: float, confidence: float) -> None:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_execution_telemetry
                        (session_id, step_name, latency_ms, neural_confidence)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, step_name, float(latency_ms), float(confidence)),
                )
    except Exception as e:
        logger.debug(f"Telemetry DB insert skipped: {e}")


def persist_sandboxed_tool(name: str, description: str, source_code: str, is_sandboxed: bool = True) -> None:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO registry_tools (name, description, parameters, source_code, is_sandboxed)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        source_code = EXCLUDED.source_code,
                        is_sandboxed = EXCLUDED.is_sandboxed
                    """,
                    (name, description, json.dumps({}), source_code, is_sandboxed),
                )
    except Exception as e:
        logger.debug(f"registry_tools insert skipped: {e}")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_registry_managedagenttool
                        (name, description, source_code, is_sandboxed, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        source_code = EXCLUDED.source_code,
                        is_sandboxed = EXCLUDED.is_sandboxed
                    """,
                    (name, description, source_code, is_sandboxed),
                )
    except Exception as e:
        logger.debug(f"Django ManagedAgentTool insert skipped: {e}")


def load_persisted_tools() -> List[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT name, description, source_code FROM registry_tools WHERE is_sandboxed = TRUE")
                return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
