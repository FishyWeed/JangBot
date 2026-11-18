"""Entry point for JangBot execution and validation."""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_system_check() -> bool:
    """Validate database, sources and configuration integrity."""
    from src.settings import config
    from src.knowledge.repository import KnowledgeRepository

    print("Running JangBot integrity checks...")
    db_path = Path(config["paths"]["database"])

    if not db_path.exists():
        print(f"[FAIL] Database file missing: {db_path}")
        return False
    print(f"[OK] Database exists: {db_path}")

    repo = KnowledgeRepository()
    facts = repo.get_verified_facts()
    if not facts:
        print("[FAIL] No verified facts found in database.")
        return False
    print(f"[OK] Verified facts count: {len(facts)}")

    missing_citations = 0
    for fact in facts:
        citations = repo.get_citations_for_fact(fact["id"])
        if not citations:
            missing_citations += 1

    if missing_citations > 0:
        print(f"[FAIL] {missing_citations} facts have no citations.")
        return False
    print("[OK] All verified facts contain source citations.")

    print("All system checks passed successfully.")
    return True


def main():
    """Parse arguments and start selected mode."""
    parser = argparse.ArgumentParser(description="JangBot Expert System Chatbot")
    parser.add_argument(
        "--mode",
        choices=["cli", "server"],
        default="cli",
        help="Execution mode (default: cli)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run system integrity validation",
    )
    parser.add_argument(
        "--user-id",
        default="default_user",
        help="Persistent Mem0 user identifier across sessions",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional LangGraph checkpoint thread ID to resume",
    )

    args = parser.parse_args()

    if args.check:
        success = run_system_check()
        sys.exit(0 if success else 1)

    if args.mode == "cli":
        from src.interface.cli import run_cli
        run_cli(user_id=args.user_id, session_id=args.session_id)
    elif args.mode == "server":
        import os
        import uvicorn
        host = os.getenv("HOST", "127.0.0.1")
        port = int(os.getenv("PORT", "8000"))
        uvicorn.run("src.interface.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
