"""Terminal interface for JangBot development mode."""

import sys
import time
import uuid
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from src.settings import config
from src.knowledge.repository import KnowledgeRepository
from src.dialogue.manager import DialogueManager
from src.dialogue.variations import pick_greeting


def run_cli(user_id: str = "default_user", session_id: Optional[str] = None) -> None:
    """Run interactive terminal chat session with persistent LangGraph + Mem0 memory."""
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    console = Console()
    repository = KnowledgeRepository()
    dialogue_manager = DialogueManager(repository)
    active_session_id = session_id or f"cli_{uuid.uuid4().hex[:8]}"

    bot_name = config["bot"]["name"]
    initial_greeting = pick_greeting(bot_name)
    mem_mode = dialogue_manager.memory_manager.backend_mode
    llm_mode = dialogue_manager.agent.nodes.llm.provider if dialogue_manager.agent.nodes.llm.is_available else "offline_fallback"

    console.print(
        Panel.fit(
            f"[bold cyan]{bot_name}[/bold cyan] - Korean Janggu Expert Agent\n"
            f"[dim]User: {user_id} | Session: {active_session_id} | Memory: {mem_mode} | LLM: {llm_mode}[/dim]\n"
            "[dim]Type '/memories' to inspect saved profile facts, or 'exit' to quit.[/dim]",
            border_style="cyan",
        )
    )

    console.print(f"\n[bold cyan]{bot_name}:[/bold cyan] {initial_greeting}")
    pacing_enabled = config.get("pacing", {}).get("enabled", True)

    try:
        while True:
            try:
                user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Session closed.[/dim]")
                break

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit"}:
                console.print("[dim]Goodbye.[/dim]")
                break

            if user_input.lower() == "/memories":
                saved = dialogue_manager.get_user_memories(user_id)
                if not saved:
                    console.print("[dim]No long-term memories recorded for this user yet.[/dim]")
                else:
                    for item in saved:
                        console.print(f"[dim]- {item.get('memory')}[/dim]")
                continue

            if pacing_enabled:
                time.sleep(0.4)

            result = dialogue_manager.process_message(active_session_id, user_input, user_id=user_id)
            console.print(f"[bold cyan]{bot_name}:[/bold cyan] {result['reply']}")
    finally:
        dialogue_manager.close()


if __name__ == "__main__":
    run_cli()
