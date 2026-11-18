"""Explicit LangGraph state schema for JangBot agentic orchestration."""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class JangBotState(TypedDict, total=False):
    """Typed conversation and orchestration state persisted across turns."""

    # Short-term checkpointed conversation history
    messages: Annotated[List[AnyMessage], add_messages]

    # Identifiers
    user_id: str
    session_id: str

    # Turn inputs and progressive resolution
    raw_query: str
    cleaned_query: str
    resolved_query: str

    # NLP & domain routing metadata
    intent: Optional[str]
    confidence: float
    entities: Dict[str, str]
    guardrail_status: str  # in_domain | social | followup | clarification | fallback | off_topic
    response_status: str   # answered | social | clarification | fallback | off_topic

    # Dialogue tracking persisted across checkpointed turns
    active_topic: Optional[str]
    last_fact_ids: List[str]
    last_entities: Dict[str, str]
    pending_offer: Optional[Dict[str, Any]]
    user_mood: Optional[str]
    conversation_turn: int
    used_variants: Dict[str, int]
    recent_replies: List[str]

    # Retrieved long-term Mem0 memories & verified DB tool outputs
    user_memories: List[Dict[str, Any]]
    retrieved_facts: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    baseline_reply: str

    # Final synthesized response
    reply: str
