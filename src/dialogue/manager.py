"""Dialogue manager delegating conversational orchestration to LangGraph + Mem0."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from src.knowledge.repository import KnowledgeRepository
from src.memory.session import SessionMemory
from src.memory.long_term import LongTermMemoryManager
from src.agent.graph import JangBotGraphAgent


class DialogueManager:
    """Manage dialogue flow, LangGraph checkpointing and Mem0 user memory."""

    def __init__(
        self,
        repository: KnowledgeRepository,
        memory_manager: Optional[LongTermMemoryManager] = None,
        checkpoints_db_path: Optional[Path] = None,
    ):
        self.repository = repository
        self.agent = JangBotGraphAgent(
            repository=repository,
            memory_manager=memory_manager,
            checkpoints_db_path=checkpoints_db_path,
        )
        # Preserve component attributes for backward-compatible inspection/testing
        self.nlp = self.agent.nlp
        self.classifier = self.agent.classifier
        self.engine = self.agent.toolchain.engine
        self.memory_manager = self.agent.memory_manager
        self.sessions: Dict[str, SessionMemory] = {}

    def get_or_create_session(self, session_id: str) -> SessionMemory:
        """Retrieve existing session mirror or initialize a new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(session_id)
        return self.sessions[session_id]

    def process_message(
        self,
        session_id: str,
        raw_text: str,
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
        """Process a user message through LangGraph + Mem0 and return the response."""
        session = self.get_or_create_session(session_id)
        session.record_turn("user", raw_text)

        result = self.agent.invoke_turn(
            session_id=session_id,
            raw_text=raw_text,
            user_id=user_id,
        )

        # Mirror checkpointed state back into SessionMemory for legacy inspectors
        thread_state = self.agent.get_thread_state(session_id)
        session.active_topic = thread_state.get("active_topic")
        session.last_fact_ids = list(thread_state.get("last_fact_ids") or [])
        session.pending_offer = thread_state.get("pending_offer")
        session.user_mood = thread_state.get("user_mood")
        session.record_turn("assistant", result["reply"])

        return result

    def get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all persistent long-term memories stored for user_id."""
        return self.memory_manager.get_all(user_id=user_id)

    def close(self) -> None:
        """Release underlying graph checkpointer resources."""
        self.agent.close()
