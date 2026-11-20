"""FastAPI HTTP server exposing JangBot LangGraph + Mem0 dialogue endpoints."""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.dialogue.manager import DialogueManager
from src.dialogue.variations import pick_greeting
from src.knowledge.repository import KnowledgeRepository
from src.memory.store import SessionStore
from src.settings import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_BUILD_DIR = BASE_DIR / "Chat Interface" / "build"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatRequest(BaseModel):
    """Inbound chat payload scoped by user_id and session_id."""

    message: str = Field(..., min_length=1)
    user_id: str = Field(default="default_user", min_length=1)
    session_id: str = Field(default="web_session_1", min_length=1)


class ChatResponse(BaseModel):
    """Structured response payload returned by Danbi."""

    reply: str
    status: str
    confidence: float
    fact_ids: List[str] = []
    memories_used: List[str] = []


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default="New Chat", max_length=80)


class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)


class ProfileChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


_manager: DialogueManager | None = None
_session_store: SessionStore | None = None


def get_dialogue_manager() -> DialogueManager:
    """Lazy-initialize singleton DialogueManager for FastAPI handlers."""
    global _manager
    if _manager is None:
        _manager = DialogueManager(KnowledgeRepository())
    return _manager


def get_session_store() -> SessionStore:
    """Lazy-initialize singleton SessionStore for multi-profile chat persistence."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store


def _collect_citations(
    repository: KnowledgeRepository,
    fact_ids: List[str],
) -> List[Dict[str, Any]]:
    """Collect deduplicated source citations for a list of fact IDs."""
    citations: List[Dict[str, Any]] = []
    seen = set()
    for fact_id in fact_ids:
        for item in repository.get_citations_for_fact(fact_id):
            key = (fact_id, item.get("source_id"), item.get("citation_detail"))
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                {
                    "fact_id": fact_id,
                    "source_id": item.get("source_id"),
                    "title": item.get("title"),
                    "detail": item.get("citation_detail") or item.get("title"),
                    "publisher": item.get("publisher", "Unknown Publisher"),
                    "tier": item.get("tier", 1),
                    "url": item.get("url"),
                }
            )
    return citations


def _auto_title(message: str) -> str:
    """Create a concise sidebar title from the user's first message."""
    cleaned = " ".join(message.strip().split())
    if len(cleaned) <= 38:
        return cleaned
    return cleaned[:35].rstrip() + "..."


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize and cleanly tear down agent resources."""
    get_dialogue_manager()
    get_session_store()
    yield
    if _manager is not None:
        _manager.close()


app = FastAPI(title="JangBot (Danbi) API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
def health() -> Dict[str, Any]:
    """Return service and memory backend health status."""
    dm = get_dialogue_manager()
    return {
        "status": "ok",
        "memory_backend": dm.memory_manager.backend_mode,
        "llm_available": dm.agent.nodes.llm.is_available,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Process one conversational turn via LangGraph + Mem0."""
    dm = get_dialogue_manager()
    res = dm.process_message(
        session_id=req.session_id,
        raw_text=req.message,
        user_id=req.user_id,
    )
    return ChatResponse(
        reply=res["reply"],
        status=res["status"],
        confidence=res["confidence"],
        fact_ids=res.get("fact_ids", []),
        memories_used=res.get("memories_used", []),
    )


@app.get("/memories/{user_id}")
@app.get("/api/memories/{user_id}")
def list_memories(user_id: str) -> Dict[str, Any]:
    """Return stored Mem0 / local long-term memories for user_id."""
    dm = get_dialogue_manager()
    return {"user_id": user_id, "memories": dm.get_user_memories(user_id)}


@app.get("/api/config")
def get_bot_config() -> Dict[str, Any]:
    """Return bot identity, initial greeting, pacing, and runtime capabilities."""
    dm = get_dialogue_manager()
    return {
        "bot_name": config["bot"]["name"],
        "greeting": pick_greeting(config["bot"]["name"]),
        "pacing": config.get(
            "pacing",
            {
                "enabled": True,
                "min_delay_ms": 300,
                "max_delay_ms": 1200,
                "words_per_minute": 250,
            },
        ),
        "memory_backend": dm.memory_manager.backend_mode,
        "llm_available": dm.agent.nodes.llm.is_available,
    }


def _resolve_device_id(x_device_id: Optional[str]) -> str:
    """Normalize the X-Device-Id header for per-device profile isolation."""
    cleaned = (x_device_id or "").strip()
    return cleaned[:128] if cleaned else "default"


@app.get("/api/sessions")
def list_sessions(
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, Any]:
    """List all saved chat profiles for the requesting device."""
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)
    return {"sessions": store.list_profiles(device_id=device_id)}


@app.post("/api/sessions")
def create_session(
    payload: CreateSessionRequest,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, Any]:
    """Create a new isolated chat profile for the requesting device."""
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)
    session_id = uuid.uuid4().hex
    user_id = f"profile_{session_id[:12]}"
    title = (payload.title or "New Chat").strip() or "New Chat"
    greeting = pick_greeting(config["bot"]["name"])
    return store.create_profile(
        session_id=session_id,
        user_id=user_id,
        title=title,
        greeting=greeting,
        device_id=device_id,
    )


@app.get("/api/sessions/{session_id}")
def get_session(
    session_id: str,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, Any]:
    """Retrieve a single chat profile and its UI message history for this device."""
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)
    profile = store.get_profile(session_id, device_id=device_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Chat profile not found.")
    return profile


@app.patch("/api/sessions/{session_id}")
def rename_session(
    session_id: str,
    payload: RenameSessionRequest,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, Any]:
    """Rename a chat profile belonging to this device."""
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)
    if not store.rename_profile(session_id, payload.title, device_id=device_id):
        raise HTTPException(status_code=404, detail="Chat profile not found.")
    return store.get_profile(session_id, device_id=device_id)  # type: ignore[return-value]


@app.post("/api/sessions/{session_id}/reset")
def reset_session(
    session_id: str,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, Any]:
    """Reset a chat profile with a fresh session_id and user_id."""
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)
    new_session_id = uuid.uuid4().hex
    new_user_id = f"profile_{new_session_id[:12]}"
    profile = store.reset_profile(
        session_id=session_id,
        new_session_id=new_session_id,
        new_user_id=new_user_id,
        greeting=pick_greeting(config["bot"]["name"]),
        device_id=device_id,
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Chat profile not found.")
    return profile


@app.delete("/api/sessions/{session_id}")
def delete_session(
    session_id: str,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, bool]:
    """Delete a chat profile belonging to this device."""
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)
    if not store.delete_profile(session_id, device_id=device_id):
        raise HTTPException(status_code=404, detail="Chat profile not found.")
    return {"deleted": True}


@app.post("/api/chat")
def profile_chat(
    payload: ProfileChatRequest,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
) -> Dict[str, Any]:
    """Process one turn for a specific chat profile, persisting UI messages."""
    raw_text = payload.message.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    dm = get_dialogue_manager()
    store = get_session_store()
    device_id = _resolve_device_id(x_device_id)

    profile = store.get_profile(payload.session_id, device_id=device_id)
    if profile is None:
        profile = store.create_profile(
            session_id=payload.session_id,
            user_id=f"profile_{payload.session_id[:12]}",
            title="New Chat",
            greeting=pick_greeting(config["bot"]["name"]),
            device_id=device_id,
        )

    ui_messages: List[Dict[str, Any]] = list(profile.get("messages", []))
    user_msg = {
        "id": uuid.uuid4().hex,
        "role": "user",
        "content": raw_text,
        "created_at": _utc_now(),
    }
    ui_messages.append(user_msg)

    res = dm.process_message(
        session_id=profile["session_id"],
        raw_text=raw_text,
        user_id=profile["user_id"],
    )
    fact_ids: List[str] = res.get("fact_ids", []) or []
    citations = _collect_citations(dm.repository, fact_ids)

    assistant_msg = {
        "id": uuid.uuid4().hex,
        "role": "assistant",
        "content": res["reply"],
        "status": res.get("status", "answered"),
        "confidence": res.get("confidence", 1.0),
        "fact_ids": fact_ids,
        "memories_used": res.get("memories_used", []),
        "citations": citations,
        "created_at": _utc_now(),
    }
    ui_messages.append(assistant_msg)

    current_title = profile.get("title", "New Chat")
    next_title = _auto_title(raw_text) if current_title == "New Chat" else current_title
    store.save_messages(profile["session_id"], ui_messages, title=next_title, device_id=device_id)

    return {
        "session_id": profile["session_id"],
        "user_id": profile["user_id"],
        "title": next_title,
        "user_message": user_msg,
        "assistant_message": assistant_msg,
    }


@app.get("/api/citations")
def get_citations(
    fact_ids: str = Query(..., description="Comma-separated fact IDs, e.g. F04,F05"),
) -> Dict[str, Any]:
    """Return verified source citations for the requested fact IDs."""
    dm = get_dialogue_manager()
    ids = [fid.strip() for fid in fact_ids.split(",") if fid.strip()]
    return {"citations": _collect_citations(dm.repository, ids)}


@app.get("/api/graph")
def get_semantic_graph(
    node_type: Optional[str] = Query(default=None, description="Optional node_type filter"),
    predicate: Optional[str] = Query(default=None, description="Optional predicate filter"),
    category: Optional[str] = Query(default=None, description="Optional category filter"),
) -> Dict[str, Any]:
    """Return the verified semantic network nodes, directed edges and summary counts."""
    dm = get_dialogue_manager()
    return dm.agent.toolchain.semantic_network.get_graph_overview(
        node_type=node_type,
        predicate=predicate,
        category=category,
    )


@app.get("/api/graph/node/{concept}")
def get_semantic_graph_node(concept: str) -> Dict[str, Any]:
    """Return a verified concept node, its incoming/outgoing cited relations and neighbor follow-ups."""
    dm = get_dialogue_manager()
    details = dm.agent.toolchain.semantic_network.get_node_details(concept)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Concept '{concept}' not found in semantic network.")
    return details


@app.get("/api/graph/path")
def get_semantic_graph_path(
    from_concept: str = Query(..., alias="from", min_length=1, description="Source concept ID or alias"),
    to_concept: str = Query(..., alias="to", min_length=1, description="Target concept ID or alias"),
    max_hops: int = Query(default=4, ge=1, le=8),
    directed: bool = Query(default=False),
) -> Dict[str, Any]:
    """Find the shortest verified multi-hop path and supporting citations between two concepts."""
    dm = get_dialogue_manager()
    sn = dm.agent.toolchain.semantic_network
    if sn.resolve_concept(from_concept) is None:
        raise HTTPException(status_code=404, detail=f"Source concept '{from_concept}' not found.")
    if sn.resolve_concept(to_concept) is None:
        raise HTTPException(status_code=404, detail=f"Target concept '{to_concept}' not found.")
    return sn.find_shortest_path(from_concept, to_concept, max_hops=max_hops, directed=directed)


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    """Serve the built SvelteKit static app when available."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found.")

    if not FRONTEND_BUILD_DIR.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Frontend build not found. Run 'npm run build' inside 'Chat Interface' "
                "or run the SvelteKit dev server on port 5173."
            ),
        )

    target = (FRONTEND_BUILD_DIR / full_path).resolve()
    if (
        full_path
        and target.is_file()
        and str(target).startswith(str(FRONTEND_BUILD_DIR.resolve()))
    ):
        return FileResponse(target)

    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend index.html not found.")
