"""Run the 100+ golden benchmark suite against JangBot (Danbi) offline agent."""

import sys
import tempfile
import time
from pathlib import Path
import yaml

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.settings import config
from src.knowledge.repository import KnowledgeRepository
from src.memory.long_term import LongTermMemoryManager
from src.dialogue.manager import DialogueManager

GOLDEN_PATH = BASE_DIR / "tools" / "eval" / "golden_questions.yaml"


def run_benchmark():
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Isolate agent storage & deterministic mode during benchmark
    tmp_dir = Path(tempfile.mkdtemp())
    config["agent"]["checkpoints_db"] = str(tmp_dir / "checkpoints.db")
    config["agent"]["use_llm_when_available"] = False
    config["memory"]["local_fallback_db"] = str(tmp_dir / "memories.db")
    config["memory"]["qdrant_path"] = str(tmp_dir / "qdrant")
    config["memory"]["history_db"] = str(tmp_dir / "history.db")

    repo = KnowledgeRepository()
    mem = LongTermMemoryManager(
        local_db_path=tmp_dir / "memories.db",
        qdrant_path=tmp_dir / "qdrant",
        history_db_path=tmp_dir / "history.db",
    )
    dm = DialogueManager(repo, memory_manager=mem, checkpoints_db_path=tmp_dir / "checkpoints.db")

    total = 0
    passed = 0
    failures = []
    t0 = time.time()

    try:
        # 1. Single-turn categories (each gets fresh isolated session & user)
        for cat_name, items in data.get("categories", {}).items():
            for idx, item in enumerate(items):
                total += 1
                q = item["query"]
                expected_status = item["expected_status"]
                must_any = [k.lower() for k in item.get("must_contain_any", [])]
                sess = f"bench_{cat_name}_{idx}"
                res = dm.process_message(sess, q, user_id=f"u_{cat_name}_{idx}")

                reply_low = res["reply"].lower()
                ok_status = res["status"] == expected_status
                ok_kw = (not must_any) or any(k in reply_low for k in must_any)
                if ok_status and ok_kw:
                    passed += 1
                else:
                    failures.append({
                        "section": cat_name,
                        "query": q,
                        "expected_status": expected_status,
                        "actual_status": res["status"],
                        "intent": res.get("intent"),
                        "conf": round(res.get("confidence", 0.0), 3),
                        "must_contain_any": must_any,
                        "reply_preview": res["reply"][:180].replace("\n", " "),
                    })

        # 2. Multi-turn conversations
        for conv_name, turns in data.get("conversations", {}).items():
            sess = f"conv_{conv_name}"
            uid = f"u_{conv_name}"
            for t_idx, turn in enumerate(turns):
                total += 1
                q = turn["query"]
                expected_status = turn["expected_status"]
                must_any = [k.lower() for k in turn.get("must_contain_any", [])]
                res = dm.process_message(sess, q, user_id=uid)

                reply_low = res["reply"].lower()
                ok_status = res["status"] == expected_status
                ok_kw = (not must_any) or any(k in reply_low for k in must_any)
                if ok_status and ok_kw:
                    passed += 1
                else:
                    failures.append({
                        "section": f"{conv_name} (turn {t_idx + 1})",
                        "query": q,
                        "expected_status": expected_status,
                        "actual_status": res["status"],
                        "intent": res.get("intent"),
                        "conf": round(res.get("confidence", 0.0), 3),
                        "must_contain_any": must_any,
                        "reply_preview": res["reply"][:180].replace("\n", " "),
                    })
    finally:
        dm.close()

    elapsed = round(time.time() - t0, 2)
    print(f"BENCHMARK COMPLETE: {passed}/{total} passed ({len(failures)} failed) in {elapsed}s")
    for fail in failures:
        print("---")
        for k, v in fail.items():
            print(f"  {k}: {v}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(run_benchmark())
