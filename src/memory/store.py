"""SQLite persistence for per-device multi-profile chat sessions."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SESSIONS_DB = BASE_DIR / "logs" / "sessions.db"


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    """Persist chat profiles, UI message history, and isolated user_id/session_id pairs per device."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_SESSIONS_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL DEFAULT 'default',
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    ui_messages TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cols = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(chat_sessions)").fetchall()
            }
            if "user_id" not in cols:
                conn.execute(
                    "ALTER TABLE chat_sessions ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default_user'"
                )
            if "device_id" not in cols:
                conn.execute(
                    "ALTER TABLE chat_sessions ADD COLUMN device_id TEXT NOT NULL DEFAULT 'default'"
                )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_device ON chat_sessions(device_id, updated_at DESC)"
            )
            conn.commit()

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "session_id": row["session_id"],
            "device_id": row["device_id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "messages": json.loads(row["ui_messages"] or "[]"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_profiles(self, device_id: str = "default") -> List[Dict[str, Any]]:
        """List saved chat profiles for a specific device ordered by most recently updated."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, device_id, user_id, title, ui_messages, created_at, updated_at
                FROM chat_sessions
                WHERE device_id = ?
                ORDER BY updated_at DESC
                """,
                (device_id,),
            ).fetchall()

        profiles = []
        for row in rows:
            messages = json.loads(row["ui_messages"] or "[]")
            last_preview = messages[-1]["content"][:80] if messages else ""
            profiles.append(
                {
                    "session_id": row["session_id"],
                    "device_id": row["device_id"],
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "message_count": len(messages),
                    "last_preview": last_preview,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
        return profiles

    def create_profile(
        self,
        session_id: str,
        user_id: str,
        title: str,
        greeting: str,
        device_id: str = "default",
    ) -> Dict[str, Any]:
        """Create and persist a new chat profile for a device seeded with the bot greeting."""
        now = _utc_now()
        initial_messages = [
            {
                "id": f"{session_id}-init",
                "role": "assistant",
                "content": greeting,
                "status": "social",
                "confidence": 1.0,
                "fact_ids": [],
                "memories_used": [],
                "citations": [],
                "created_at": now,
            }
        ]
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (
                    session_id, device_id, user_id, title, ui_messages, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, device_id, user_id, title, json.dumps(initial_messages), now, now),
            )
            conn.commit()
        return self.get_profile(session_id, device_id=device_id)  # type: ignore[return-value]

    def get_profile(
        self,
        session_id: str,
        device_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a full chat profile scoped to device_id when provided."""
        with self._connect() as conn:
            if device_id is not None:
                row = conn.execute(
                    "SELECT * FROM chat_sessions WHERE session_id = ? AND device_id = ?",
                    (session_id, device_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM chat_sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
        return self._row_to_profile(row) if row else None

    def save_messages(
        self,
        session_id: str,
        ui_messages: List[Dict[str, Any]],
        title: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> None:
        """Persist updated UI messages and optional title for a profile."""
        now = _utc_now()
        where_clause = "WHERE session_id = ? AND device_id = ?" if device_id is not None else "WHERE session_id = ?"
        where_params = (session_id, device_id) if device_id is not None else (session_id,)
        with self._connect() as conn:
            if title is not None:
                conn.execute(
                    f"""
                    UPDATE chat_sessions
                    SET ui_messages = ?, title = ?, updated_at = ?
                    {where_clause}
                    """,
                    (json.dumps(ui_messages), title, now, *where_params),
                )
            else:
                conn.execute(
                    f"""
                    UPDATE chat_sessions
                    SET ui_messages = ?, updated_at = ?
                    {where_clause}
                    """,
                    (json.dumps(ui_messages), now, *where_params),
                )
            conn.commit()

    def rename_profile(
        self,
        session_id: str,
        title: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """Rename an existing chat profile."""
        where_clause = "WHERE session_id = ? AND device_id = ?" if device_id is not None else "WHERE session_id = ?"
        where_params = (session_id, device_id) if device_id is not None else (session_id,)
        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE chat_sessions SET title = ?, updated_at = ? {where_clause}",
                (title.strip() or "Untitled Chat", _utc_now(), *where_params),
            )
            conn.commit()
            return cur.rowcount > 0

    def reset_profile(
        self,
        session_id: str,
        new_session_id: str,
        new_user_id: str,
        greeting: str,
        device_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Reset a chat profile with a fresh session_id/user_id so memory starts clean."""
        now = _utc_now()
        initial_messages = [
            {
                "id": f"{new_session_id}-init",
                "role": "assistant",
                "content": greeting,
                "status": "social",
                "confidence": 1.0,
                "fact_ids": [],
                "memories_used": [],
                "citations": [],
                "created_at": now,
            }
        ]
        where_clause = "WHERE session_id = ? AND device_id = ?" if device_id is not None else "WHERE session_id = ?"
        where_params = (session_id, device_id) if device_id is not None else (session_id,)
        with self._connect() as conn:
            cur = conn.execute(
                f"""
                UPDATE chat_sessions
                SET session_id = ?,
                    user_id = ?,
                    ui_messages = ?,
                    updated_at = ?
                {where_clause}
                """,
                (new_session_id, new_user_id, json.dumps(initial_messages), now, *where_params),
            )
            conn.commit()
            if cur.rowcount == 0:
                return None
        return self.get_profile(new_session_id, device_id=device_id)

    def delete_profile(
        self,
        session_id: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """Delete a chat profile."""
        where_clause = "WHERE session_id = ? AND device_id = ?" if device_id is not None else "WHERE session_id = ?"
        where_params = (session_id, device_id) if device_id is not None else (session_id,)
        with self._connect() as conn:
            cur = conn.execute(
                f"DELETE FROM chat_sessions {where_clause}",
                where_params,
            )
            conn.commit()
            return cur.rowcount > 0
