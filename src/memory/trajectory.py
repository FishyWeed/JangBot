"""Non-blocking JSONL trajectory and user-correction feedback logger for LangGraph + Mem0."""

import json
import queue
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.settings import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

_CORRECTION_PATTERNS = (
    r"\bno[,\s]+(?:actually|that'?s|it'?s|you)\b",
    r"\bthat'?s\s+(?:wrong|incorrect|not right|inaccurate)\b",
    r"\byou\s+(?:got\s+that\s+wrong|misunderstood|missed|forgot)\b",
    r"\bnot\s+what\s+i\s+asked\b",
    r"\bactually[,\s]+(?:it|the|that|no)\b",
    r"\bwrong\s+answer\b",
    r"\bincorrect\b",
)

_POSITIVE_PATTERNS = (
    r"\b(?:spot\s+on|exactly\s+right|that'?s\s+right|perfect|great\s+explanation|makes\s+sense)\b",
)


def detect_feedback_signal(user_text: str) -> Optional[float]:
    """Infer an optional scalar feedback score (-1.0 correction, +1.0 confirmation) from the next user turn."""
    low = (user_text or "").strip().lower()
    if not low:
        return None
    for pat in _CORRECTION_PATTERNS:
        if re.search(pat, low):
            return -1.0
    for pat in _POSITIVE_PATTERNS:
        if re.search(pat, low):
            return 1.0
    return None


class TrajectoryLogger:
    """Asynchronous writer persisting structured conversation trajectories to data/trajectories.jsonl."""

    def __init__(self, log_path: Optional[Path] = None, enabled: Optional[bool] = None) -> None:
        train_cfg = config.get("training", {})
        default_rel = train_cfg.get("trajectory_log", "data/trajectories.jsonl")
        self.log_path: Path = Path(log_path) if log_path is not None else BASE_DIR / default_rel
        self.enabled: bool = bool(train_cfg.get("log_trajectories", True)) if enabled is None else bool(enabled)
        self._queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()
        self._file_lock = threading.Lock()
        self._worker: Optional[threading.Thread] = None
        if self.enabled:
            self._start_worker()

    def _start_worker(self) -> None:
        self._worker = threading.Thread(target=self._run_loop, name="trajectory-logger", daemon=True)
        self._worker.start()

    def _run_loop(self) -> None:
        while True:
            op, payload = self._queue.get()
            try:
                if op == "append":
                    self._append_record(payload)
                elif op == "feedback":
                    self._update_feedback_score(payload["trajectory_id"], payload["feedback_score"], payload.get("correction_text"))
            except Exception:
                pass
            finally:
                self._queue.task_done()

    def _append_record(self, record: Dict[str, Any]) -> None:
        with self._file_lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _update_feedback_score(
        self,
        trajectory_id: str,
        feedback_score: float,
        correction_text: Optional[str] = None,
    ) -> None:
        with self._file_lock:
            if not self.log_path.exists():
                return
            lines = self.log_path.read_text(encoding="utf-8").splitlines()
            updated = False
            out_lines: List[str] = []
            for ln in lines:
                if not ln.strip():
                    continue
                try:
                    rec = json.loads(ln)
                except Exception:
                    out_lines.append(ln)
                    continue
                if rec.get("trajectory_id") == trajectory_id:
                    rec["feedback_score"] = float(feedback_score)
                    if correction_text:
                        rec["feedback_note"] = correction_text
                    updated = True
                out_lines.append(json.dumps(rec, ensure_ascii=False))
            if updated:
                self.log_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    def log_turn(
        self,
        *,
        session_id: str,
        user_id: str,
        turn: int,
        system_prompt: str,
        mem0_retrieved_context: List[str],
        user_query: str,
        assistant_response: str,
        tool_calls: List[Dict[str, Any]],
        resolved_query: str = "",
        intent: Optional[str] = None,
        response_status: str = "answered",
        fact_ids: Optional[List[str]] = None,
        feedback_score: Optional[float] = None,
    ) -> str:
        """Enqueue a trajectory record without blocking the response turn; returns trajectory_id."""
        tid = uuid.uuid4().hex
        if not self.enabled:
            return tid
        record: Dict[str, Any] = {
            "trajectory_id": tid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "user_id": user_id,
            "turn": int(turn),
            "system_prompt": system_prompt,
            "mem0_retrieved_context": list(mem0_retrieved_context),
            "user_query": user_query,
            "resolved_query": resolved_query or user_query,
            "intent": intent,
            "response_status": response_status,
            "fact_ids": list(fact_ids or []),
            "tool_calls": list(tool_calls),
            "assistant_response": assistant_response,
            "feedback_score": feedback_score,
        }
        self._queue.put(("append", record))
        return tid

    def record_feedback(
        self,
        trajectory_id: str,
        feedback_score: float,
        correction_text: Optional[str] = None,
    ) -> None:
        """Asynchronously back-patch feedback_score on a previously logged trajectory."""
        if not self.enabled or not trajectory_id:
            return
        self._queue.put(
            (
                "feedback",
                {
                    "trajectory_id": trajectory_id,
                    "feedback_score": float(feedback_score),
                    "correction_text": correction_text,
                },
            )
        )

    def flush(self, timeout: float = 5.0) -> None:
        """Wait until all queued trajectory writes complete (used in tests and graceful shutdown)."""
        if not self.enabled:
            return
        done = threading.Event()

        def _join() -> None:
            self._queue.join()
            done.set()

        t = threading.Thread(target=_join, daemon=True)
        t.start()
        done.wait(timeout=timeout)
