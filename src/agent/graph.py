"""Compiled LangGraph state machine with SQLite checkpointing for JangBot."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from src.settings import config
from src.knowledge.repository import KnowledgeRepository
from src.nlp.preprocessor import NLPPreprocessor
from src.nlp.classifier import IntentClassifier
from src.memory.long_term import LongTermMemoryManager
from src.agent.tools import JangguToolchain
from src.agent.nodes import JangBotNodes
from src.agent.state import JangBotState

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class JangBotGraphAgent:
    """LangGraph + Mem0 conversational agent orchestrating verified Janggu tools."""

    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        memory_manager: Optional[LongTermMemoryManager] = None,
        checkpoints_db_path: Optional[Path] = None,
        nlp: Optional[NLPPreprocessor] = None,
        classifier: Optional[IntentClassifier] = None,
    ) -> None:
        self.repository = repository or KnowledgeRepository()
        self.nlp = nlp or NLPPreprocessor()
        self.classifier = classifier or IntentClassifier()

        self.memory_manager = memory_manager or LongTermMemoryManager(
            encoder=self.classifier.encoder,
        )
        self.toolchain = JangguToolchain(self.repository)
        self.nodes = JangBotNodes(
            toolchain=self.toolchain,
            memory_manager=self.memory_manager,
            nlp=self.nlp,
            classifier=self.classifier,
        )

        agent_cfg = config.get("agent", {})
        ckpt_path = Path(checkpoints_db_path) if checkpoints_db_path else BASE_DIR / agent_cfg.get("checkpoints_db", "data/checkpoints.db")
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(ckpt_path), check_same_thread=False)
        self.checkpointer = SqliteSaver(self._conn)
        self.checkpointer.setup()

        self.graph = self._compile_graph()

    @staticmethod
    def _route_after_guardrail(state: JangBotState) -> str:
        """Route in-domain queries to verified tools and non-tool outcomes directly to synthesis."""
        if state.get("guardrail_status") == "in_domain":
            return "execute_tools"
        return "synthesize_response"

    def _compile_graph(self):
        """Construct and compile the LangGraph StateGraph with SQLite checkpointing."""
        builder = StateGraph(JangBotState)

        builder.add_node("retrieve_memory", self.nodes.retrieve_memory)
        builder.add_node("rewrite_context", self.nodes.rewrite_context)
        builder.add_node("classify_and_guard", self.nodes.classify_and_guard)
        builder.add_node("execute_tools", self.nodes.execute_tools)
        builder.add_node("synthesize_response", self.nodes.synthesize_response)
        builder.add_node("update_memory", self.nodes.update_memory)

        builder.add_edge(START, "retrieve_memory")
        builder.add_edge("retrieve_memory", "rewrite_context")
        builder.add_edge("rewrite_context", "classify_and_guard")
        builder.add_conditional_edges(
            "classify_and_guard",
            self._route_after_guardrail,
            {
                "execute_tools": "execute_tools",
                "synthesize_response": "synthesize_response",
            },
        )
        builder.add_edge("execute_tools", "synthesize_response")
        builder.add_edge("synthesize_response", "update_memory")
        builder.add_edge("update_memory", END)

        return builder.compile(checkpointer=self.checkpointer)

    def invoke_turn(
        self,
        session_id: str,
        raw_text: str,
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
        """Run one conversational turn through LangGraph for the given user and session thread."""
        graph_config = {"configurable": {"thread_id": session_id}}
        payload = {
            "messages": [HumanMessage(content=raw_text)],
            "raw_query": raw_text,
            "user_id": user_id,
            "session_id": session_id,
        }
        final_state = self.graph.invoke(payload, config=graph_config)

        response_status = final_state.get("response_status", "answered")
        turn_fact_ids = (
            list(final_state.get("last_fact_ids") or [])
            if response_status == "answered"
            else []
        )

        return {
            "reply": final_state.get("reply", ""),
            "confidence": float(final_state.get("confidence", 0.0)),
            "status": response_status,
            "fact_ids": turn_fact_ids,
            "resolved_query": final_state.get("resolved_query", raw_text),
            "memories_used": [m.get("memory") for m in (final_state.get("user_memories") or []) if m.get("memory")],
            "intent": final_state.get("intent"),
        }

    def get_thread_state(self, session_id: str) -> Dict[str, Any]:
        """Inspect persisted checkpoint values for a session thread."""
        snapshot = self.graph.get_state({"configurable": {"thread_id": session_id}})
        return dict(snapshot.values) if snapshot and snapshot.values else {}

    def close(self) -> None:
        """Close underlying SQLite checkpointer connection cleanly."""
        if getattr(self, "_conn", None) is not None:
            self._conn.close()
            self._conn = None
