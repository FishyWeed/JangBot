"""Working memory and session state management."""

from typing import Any, Dict, List, Optional


class SessionMemory:
    """Track working memory and pending dialogue offers for a conversation session."""

    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.user_name: Optional[str] = None
        self.user_mood: Optional[str] = None
        self.active_topic: Optional[str] = None
        self.last_fact_ids: List[str] = []
        self.conversation_turn: int = 0
        self.history: List[Dict[str, str]] = []
        self.pending_offer: Optional[Dict[str, Any]] = None
        self.used_variants: Dict[str, int] = {}
        self.recent_replies: List[str] = []

    def record_turn(self, role: str, content: str) -> None:
        """Add a message turn to conversation history."""
        self.history.append({"role": role, "content": content})
        if role == "assistant" and content:
            self.recent_replies.append(content)
        self.conversation_turn += 1

    def set_topic(self, topic: str, fact_ids: List[str]) -> None:
        """Update active topic and related facts."""
        self.active_topic = topic
        self.last_fact_ids = fact_ids

    def set_pending_offer(self, offer: Optional[Dict[str, Any]]) -> None:
        """Store pending question or choice offered to the user."""
        self.pending_offer = offer

    def clear_pending_offer(self) -> None:
        """Clear pending offer when answered or superseded."""
        self.pending_offer = None

    def reset(self) -> None:
        """Reset session working memory."""
        self.user_name = None
        self.user_mood = None
        self.active_topic = None
        self.last_fact_ids = []
        self.conversation_turn = 0
        self.history = []
        self.pending_offer = None
        self.used_variants = {}
        self.recent_replies = []
