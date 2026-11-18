"""Pytest fixtures ensuring tests run against isolated temporary agent stores."""

import pytest


@pytest.fixture(autouse=True)
def isolated_agent_storage(tmp_path, monkeypatch):
    """Isolate checkpoints and user memories per test without altering production data/."""
    from src.settings import config

    agent_cfg = dict(config.get("agent", {}))
    agent_cfg["checkpoints_db"] = str(tmp_path / "checkpoints.db")
    agent_cfg["use_llm_when_available"] = False
    monkeypatch.setitem(config, "agent", agent_cfg)

    mem_cfg = dict(config.get("memory", {}))
    mem_cfg["local_fallback_db"] = str(tmp_path / "local_memories.db")
    mem_cfg["qdrant_path"] = str(tmp_path / "mem0_qdrant")
    mem_cfg["history_db"] = str(tmp_path / "mem0_history.db")
    monkeypatch.setitem(config, "memory", mem_cfg)
