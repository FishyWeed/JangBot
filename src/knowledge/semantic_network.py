"""Verifiable Semantic Network traversal and relational reasoning engine."""

from collections import deque
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from src.knowledge.repository import KnowledgeRepository
from src.dialogue.variations import pick_variation

PREDICATE_FORWARD_PHRASE: Dict[str, str] = {
    "has_part": "includes",
    "made_of": "is crafted from",
    "tuned_by": "is tuned through",
    "finished_with": "is treated and finished with",
    "classified_as": "is classified as",
    "produces": "generates",
    "acts_as": "functions as",
    "prevents": "prevents",
    "measured_or_modeled_by": "is measured or modeled using",
    "played_with": "is played with",
    "strikes": "strikes",
    "uses_rhythm": "uses",
    "used_in": "is featured in",
    "excluded_from": "was historically excluded from",
    "leads_or_directs": "leads and directs",
    "evolved_into": "evolved into",
    "standardized_by": "was standardized by",
    "documented_in": "is documented in",
    "created_by": "was created by",
    "preserved_at": "is preserved at",
    "distinguished_from": "is formally distinguished from",
    "depicted_in": "is depicted in",
    "digitized_by": "is digitized through",
}

PREDICATE_REVERSE_PHRASE: Dict[str, str] = {
    "has_part": "is part of",
    "made_of": "forms the material of",
    "tuned_by": "tunes",
    "finished_with": "finishes",
    "classified_as": "classifies",
    "produces": "is produced by",
    "acts_as": "is created by",
    "prevents": "is prevented by",
    "measured_or_modeled_by": "models or analyzes",
    "played_with": "is used to play",
    "strikes": "is struck by",
    "uses_rhythm": "is performed in",
    "used_in": "features",
    "excluded_from": "historically excluded",
    "leads_or_directs": "is led by",
    "evolved_into": "evolved from",
    "standardized_by": "standardized",
    "documented_in": "documents",
    "created_by": "created",
    "preserved_at": "preserves",
    "distinguished_from": "is distinguished from",
    "depicted_in": "depicts",
    "digitized_by": "digitizes",
}


class SemanticNetwork:
    """In-memory graph index backed strictly by verified SQLite triples and citations."""

    def __init__(self, repository: Optional[KnowledgeRepository] = None) -> None:
        self.repository = repository or KnowledgeRepository()
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.outgoing: Dict[str, List[Dict[str, Any]]] = {}
        self.incoming: Dict[str, List[Dict[str, Any]]] = {}
        self._alias_to_id: Dict[str, str] = {}
        self._sorted_aliases: List[Tuple[str, str]] = []
        self.reload()

    def reload(self) -> None:
        """Load verified concept nodes and semantic edges from SQLite."""
        self.nodes = {}
        self.edges = []
        self.outgoing = {}
        self.incoming = {}
        self._alias_to_id = {}

        if not self.repository.has_semantic_network():
            self._sorted_aliases = []
            return

        for node in self.repository.get_all_concept_nodes():
            nid = node["id"]
            self.nodes[nid] = node
            self.outgoing[nid] = []
            self.incoming[nid] = []

            keys = [nid, nid.replace("_", " "), node["label"]]
            if node.get("korean_name"):
                keys.append(node["korean_name"])
            keys.extend(node.get("aliases") or [])

            for raw_alias in keys:
                norm = self._norm(raw_alias)
                if norm and norm not in self._alias_to_id:
                    self._alias_to_id[norm] = nid

        self._sorted_aliases = sorted(
            self._alias_to_id.items(),
            key=lambda item: (-len(item[0]), item[0]),
        )

        for edge in self.repository.get_semantic_relations():
            subj = edge["subject_id"]
            obj = edge["object_id"]
            if subj not in self.nodes or obj not in self.nodes:
                continue
            self.edges.append(edge)
            self.outgoing[subj].append(edge)
            self.incoming[obj].append(edge)

    @staticmethod
    def _norm(text: str) -> str:
        cleaned = re.sub(r"[?!.,;:\"'()\[\]{}]+", " ", (text or "").lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    @property
    def available(self) -> bool:
        return bool(self.nodes and self.edges)

    def resolve_concept(self, text_or_alias: str) -> Optional[str]:
        """Resolve a canonical concept ID, label, Korean name or alias."""
        if not self.available or not text_or_alias:
            return None
        norm = self._norm(text_or_alias)
        if not norm:
            return None
        if norm in self._alias_to_id:
            return self._alias_to_id[norm]
        underscored = norm.replace(" ", "_")
        if underscored in self.nodes:
            return underscored
        if norm.endswith("s") and norm[:-1] in self._alias_to_id:
            return self._alias_to_id[norm[:-1]]
        return None

    def extract_concepts_from_text(self, text: str) -> List[str]:
        """Extract distinct verified concepts referenced in free text (longest non-overlapping match)."""
        if not self.available or not text:
            return []
        norm = self._norm(text)
        if not norm:
            return []

        occupied: List[Tuple[int, int]] = []
        found: List[Tuple[int, str]] = []
        generic_skip = {"body", "shell", "wood", "gut", "met", "peg", "cfl", "gak"}

        for alias, nid in self._sorted_aliases:
            if len(alias) <= 2:
                continue
            pattern = rf"(?<![a-z0-9\uAC00-\uD7A3]){re.escape(alias)}(?:s)?(?![a-z0-9\uAC00-\uD7A3])"
            for m in re.finditer(pattern, norm):
                start, end = m.span()
                if any(not (end <= s or start >= e) for s, e in occupied):
                    continue
                if alias in generic_skip and nid == "ullimtong" and re.search(r"\b(?:what|which)\s+body\b", norm):
                    continue
                occupied.append((start, end))
                found.append((start, nid))

        found.sort(key=lambda pair: pair[0])
        ordered: List[str] = []
        for _, nid in found:
            if nid not in ordered:
                ordered.append(nid)
        return ordered

    def _collect_citations(self, fact_ids: Sequence[str]) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        seen = set()
        for fid in dict.fromkeys(fact_ids):
            for c in self.repository.get_citations_for_fact(fid):
                key = (fid, c.get("source_id"), c.get("citation_detail"))
                if key in seen:
                    continue
                seen.add(key)
                rec = dict(c)
                rec["fact_id"] = fid
                citations.append(rec)
        return citations

    def get_graph_overview(
        self,
        node_type: Optional[str] = None,
        predicate: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return filtered or full semantic network nodes, edges and summary counts."""
        selected_nodes = [
            n
            for n in self.nodes.values()
            if (not node_type or n["node_type"] == node_type)
            and (not category or n.get("category") == category)
        ]
        selected_node_ids = {n["id"] for n in selected_nodes}

        selected_edges = [
            e
            for e in self.edges
            if (not predicate or e["predicate"] == predicate)
            and (
                (not node_type and not category)
                or (e["subject_id"] in selected_node_ids and e["object_id"] in selected_node_ids)
            )
        ]
        if predicate and not node_type and not category:
            edge_node_ids = {e["subject_id"] for e in selected_edges} | {e["object_id"] for e in selected_edges}
            selected_nodes = [self.nodes[nid] for nid in sorted(edge_node_ids) if nid in self.nodes]

        return {
            "nodes": selected_nodes,
            "edges": [
                {
                    "id": e["id"],
                    "subject": e["subject_id"],
                    "predicate": e["predicate"],
                    "object": e["object_id"],
                    "fact_id": e["fact_id"],
                    "qualifier": e.get("qualifier"),
                }
                for e in selected_edges
            ],
            "stats": {
                "node_count": len(selected_nodes),
                "edge_count": len(selected_edges),
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": sorted({n["node_type"] for n in self.nodes.values()}),
                "predicates": sorted({e["predicate"] for e in self.edges}),
            },
        }

    def get_neighbors(
        self,
        concept_or_alias: str,
        direction: str = "both",
        predicate: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List verified incoming/outgoing relations and neighbor nodes for a concept."""
        cid = self.resolve_concept(concept_or_alias)
        if not cid:
            return []

        results: List[Dict[str, Any]] = []
        if direction in {"out", "outgoing", "both"}:
            for e in self.outgoing.get(cid, []):
                if predicate and e["predicate"] != predicate:
                    continue
                target = self.nodes[e["object_id"]]
                results.append(
                    {
                        "direction": "outgoing",
                        "predicate": e["predicate"],
                        "neighbor_id": target["id"],
                        "neighbor_label": target["label"],
                        "neighbor_korean_name": target.get("korean_name"),
                        "neighbor_type": target["node_type"],
                        "fact_id": e["fact_id"],
                        "qualifier": e.get("qualifier"),
                        "fact_statement": e["fact_statement"],
                        "citations": self._collect_citations([e["fact_id"]]),
                    }
                )
        if direction in {"in", "incoming", "both"}:
            for e in self.incoming.get(cid, []):
                if predicate and e["predicate"] != predicate:
                    continue
                source = self.nodes[e["subject_id"]]
                results.append(
                    {
                        "direction": "incoming",
                        "predicate": e["predicate"],
                        "neighbor_id": source["id"],
                        "neighbor_label": source["label"],
                        "neighbor_korean_name": source.get("korean_name"),
                        "neighbor_type": source["node_type"],
                        "fact_id": e["fact_id"],
                        "qualifier": e.get("qualifier"),
                        "fact_statement": e["fact_statement"],
                        "citations": self._collect_citations([e["fact_id"]]),
                    }
                )
        return results

    def get_node_details(self, concept_or_alias: str) -> Optional[Dict[str, Any]]:
        """Return full node profile, incoming/outgoing verified triples and follow-up suggestions."""
        cid = self.resolve_concept(concept_or_alias)
        if not cid:
            return None
        node = self.nodes[cid]
        outgoing = self.get_neighbors(cid, direction="outgoing")
        incoming = self.get_neighbors(cid, direction="incoming")
        fact_ids = list(dict.fromkeys([e["fact_id"] for e in outgoing + incoming]))
        return {
            "node": node,
            "outgoing": outgoing,
            "incoming": incoming,
            "fact_ids": fact_ids,
            "citations": self._collect_citations(fact_ids),
            "suggested_followups": self.suggest_followup_concepts([cid], exclude_ids={cid}, limit=4),
        }

    def _adjacent_steps(self, node_id: str, directed: bool = False) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Return (next_node_id, direction, edge) ordered so specific non-hub neighbors come before 'janggu'."""
        steps: List[Tuple[str, str, Dict[str, Any]]] = []
        for e in self.outgoing.get(node_id, []):
            steps.append((e["object_id"], "outgoing", e))
        if not directed:
            for e in self.incoming.get(node_id, []):
                steps.append((e["subject_id"], "incoming", e))
        steps.sort(key=lambda item: (item[0] == "janggu", item[2]["id"]))
        return steps

    def _build_path_payload(
        self,
        source_id: str,
        target_id: str,
        raw_hops: List[Tuple[str, str, str, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        hops: List[Dict[str, Any]] = []
        fact_ids: List[str] = []
        for frm, to, direction, edge in raw_hops:
            fid = edge["fact_id"]
            if fid not in fact_ids:
                fact_ids.append(fid)
            hops.append(
                {
                    "from_id": frm,
                    "from_label": self.nodes[frm]["label"],
                    "predicate": edge["predicate"],
                    "direction": direction,
                    "to_id": to,
                    "to_label": self.nodes[to]["label"],
                    "fact_id": fid,
                    "qualifier": edge.get("qualifier"),
                    "fact_statement": edge["fact_statement"],
                    "citations": self._collect_citations([fid]),
                }
            )
        facts = self.repository.get_facts_by_ids(fact_ids)
        citations = self._collect_citations(fact_ids)
        payload: Dict[str, Any] = {
            "found": True,
            "source": self.nodes[source_id],
            "target": self.nodes[target_id],
            "hop_count": len(hops),
            "hops": hops,
            "fact_ids": fact_ids,
            "facts": facts,
            "citations": citations,
        }
        payload["narrative"] = self.render_path_story(payload)
        return payload

    def find_shortest_path(
        self,
        source: str,
        target: str,
        max_hops: int = 4,
        directed: bool = False,
    ) -> Dict[str, Any]:
        """Run BFS to find the shortest verified path between two concepts."""
        src_id = self.resolve_concept(source)
        tgt_id = self.resolve_concept(target)
        if not src_id or not tgt_id:
            return {"found": False, "reason": "unknown_concept", "source": src_id, "target": tgt_id, "hops": [], "fact_ids": [], "facts": [], "citations": []}
        if src_id == tgt_id:
            return {
                "found": True,
                "source": self.nodes[src_id],
                "target": self.nodes[tgt_id],
                "hop_count": 0,
                "hops": [],
                "fact_ids": [],
                "facts": [],
                "citations": [],
                "narrative": self.nodes[src_id]["summary"],
            }

        # Prefer specific non-hub shortest path first if one exists within max_hops; fallback to full graph
        def _bfs(avoid_hub: bool) -> Optional[List[Tuple[str, str, str, Dict[str, Any]]]]:
            queue: deque[Tuple[str, List[Tuple[str, str, str, Dict[str, Any]]]]] = deque([(src_id, [])])
            visited: Set[str] = {src_id}
            while queue:
                curr, path = queue.popleft()
                if len(path) >= max_hops:
                    continue
                for nxt, direction, edge in self._adjacent_steps(curr, directed=directed):
                    if avoid_hub and nxt == "janggu" and nxt != tgt_id:
                        continue
                    if nxt in visited:
                        continue
                    next_path = path + [(curr, nxt, direction, edge)]
                    if nxt == tgt_id:
                        return next_path
                    visited.add(nxt)
                    queue.append((nxt, next_path))
            return None

        best_no_hub = _bfs(avoid_hub=True)
        best_any = _bfs(avoid_hub=False)
        chosen = best_no_hub if (best_no_hub is not None and (best_any is None or len(best_no_hub) <= len(best_any) + 1)) else best_any

        if not chosen:
            return {
                "found": False,
                "reason": "no_path_within_max_hops",
                "source": self.nodes[src_id],
                "target": self.nodes[tgt_id],
                "hop_count": 0,
                "hops": [],
                "fact_ids": [],
                "facts": [],
                "citations": [],
            }
        return self._build_path_payload(src_id, tgt_id, chosen)

    def find_path_to_node_type(
        self,
        source: str,
        target_type: str,
        target_hint_words: Optional[Set[str]] = None,
        max_hops: int = 4,
        via_concepts: Optional[Sequence[str]] = None,
        preferred_final_predicates: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """BFS from source concept to nearest verified node matching target_type (and optional hints)."""
        src_id = self.resolve_concept(source)
        if not src_id:
            return {"found": False, "hops": [], "fact_ids": [], "facts": [], "citations": []}

        via_set = set(via_concepts or [])
        hint_words = {w.lower() for w in (target_hint_words or set()) if w}
        pref_preds = set(preferred_final_predicates or set())

        def _match_rank(nid: str) -> Optional[int]:
            node = self.nodes[nid]
            if node["node_type"] != target_type:
                return None
            if not hint_words:
                return 0
            title_hay = " ".join([nid, node["label"], " ".join(node.get("aliases") or [])]).lower()
            if any(h in title_hay for h in hint_words):
                return 0
            if any(h in node.get("summary", "").lower() for h in hint_words):
                return 1
            return None

        queue: deque[Tuple[str, List[Tuple[str, str, str, Dict[str, Any]]]]] = deque([(src_id, [])])
        visited: Set[str] = {src_id}
        candidates: List[Tuple[int, int, int, int, str, List[Tuple[str, str, str, Dict[str, Any]]]]] = []

        while queue:
            curr, path = queue.popleft()
            if len(path) >= max_hops:
                continue
            for nxt, direction, edge in self._adjacent_steps(curr, directed=False):
                if nxt in visited:
                    continue
                next_path = path + [(curr, nxt, direction, edge)]
                hint_rank = _match_rank(nxt)
                if hint_rank is not None:
                    path_nodes = {p[0] for p in next_path} | {p[1] for p in next_path}
                    via_bonus = 0 if (not via_set or bool(path_nodes & via_set)) else 1
                    pred_bonus = 0 if (not pref_preds or edge["predicate"] in pref_preds) else 1
                    hub_penalty = 1 if ("janggu" in path_nodes and nxt != "janggu") else 0
                    candidates.append((hint_rank, pred_bonus, via_bonus, len(next_path) + hub_penalty, nxt, next_path))
                visited.add(nxt)
                queue.append((nxt, next_path))

        if not candidates:
            return {"found": False, "hops": [], "fact_ids": [], "facts": [], "citations": []}

        candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4]))
        _, _, _, _, target_id, best_path = candidates[0]
        return self._build_path_payload(src_id, target_id, best_path)

    def answer_relational_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Answer multi-hop relational questions strictly from verified semantic triples."""
        if not self.available or not query:
            return None

        low = self._norm(query)
        concepts = self.extract_concepts_from_text(query)
        if not concepts:
            return None

        # 1. Explicit target-type chained questions ("What wood makes up the body that creates the acoustic choke?")
        type_rules: List[Tuple[str, str, Set[str], Set[str]]] = [
            (r"\b(?:what|which)\s+(?:type of\s+)?wood\b", "material", {"wood", "paulownia"}, {"made_of"}),
            (r"\b(?:what|which)\s+(?:animal\s+)?(?:hide|hides|skin|skins|leather)\b", "material", {"hide", "skin", "leather"}, {"made_of"}),
            (r"\b(?:what|which)\s+(?:kind of\s+)?material\b", "material", set(), {"made_of"}),
            (r"\b(?:what|which)\s+museum\b", "person_institution_tech", {"museum"}, {"preserved_at"}),
            (r"\b(?:who|which\s+(?:king|monarch|scholar|master|dancer|researcher))\b", "person_institution_tech", set(), {"created_by", "standardized_by"}),
            (r"\b(?:what|which)\s+(?:stick|mallet|implement)\b", "implement", set(), {"played_with", "strikes"}),
            (r"\b(?:what|which)\s+(?:rhythm|jangdan|beat|cycle)\b", "rhythm", set(), {"uses_rhythm"}),
            (r"\b(?:what|which)\s+(?:book|treatise|chronicle|record|notation)\b", "historical_record", set(), {"documented_in", "depicted_in"}),
        ]
        is_chained_clause = any(w in low for w in ("that creates", "that produces", "that acts", "that strikes", "that leads", "that plays", "that prevents", "fired in", "makes up", "connected to", "connect to", "connects to", "link between", "links", "relate to", "relates to"))

        if is_chained_clause:
            for pattern, target_type, hint_words, pref_preds in type_rules:
                if re.search(pattern, low):
                    anchors = [c for c in reversed(concepts) if c != "janggu" and self.nodes[c]["node_type"] != target_type]
                    if not anchors:
                        anchors = [c for c in reversed(concepts) if c != "janggu"]
                    if anchors:
                        via = [c for c in concepts if c != anchors[0] and c != "janggu"]
                        path_res = self.find_path_to_node_type(
                            anchors[0],
                            target_type=target_type,
                            target_hint_words=hint_words,
                            max_hops=4,
                            via_concepts=via,
                            preferred_final_predicates=pref_preds,
                        )
                        if path_res.get("found") and path_res.get("hop_count", 0) >= 1:
                            return path_res

        # 2. Explicit two-concept connection / path questions ("How does X connect to Y?", "What links X and Y?")
        asks_connection = any(
            p in low
            for p in (
                "connect", "connected", "connection", "link", "linked", "links",
                "relate", "related", "relationship", "path between", "bridge between",
                "how did", "how does", "lead to", "leads to", "tie into",
            )
        )
        specific_concepts = [c for c in concepts if c != "janggu"]
        if asks_connection and len(specific_concepts) >= 2:
            src, tgt = specific_concepts[0], specific_concepts[-1]
            path_res = self.find_shortest_path(src, tgt, max_hops=5, directed=False)
            if path_res.get("found") and path_res.get("hop_count", 0) >= 1:
                return path_res

        return None

    def suggest_followup_concepts(
        self,
        concept_ids: Sequence[str],
        exclude_ids: Optional[Set[str]] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Suggest relevant neighboring verified concepts based on active graph nodes."""
        if not self.available:
            return []

        excluded = set(exclude_ids or set()) | set(concept_ids) | {"janggu"}
        suggestions: List[Dict[str, Any]] = []
        seen_neighbors: Set[str] = set()

        for cid in concept_ids:
            resolved = self.resolve_concept(cid)
            if not resolved:
                continue
            for rel in self.get_neighbors(resolved, direction="both"):
                nid = rel["neighbor_id"]
                if nid in excluded or nid in seen_neighbors:
                    continue
                seen_neighbors.add(nid)
                node = self.nodes[nid]
                suggestions.append(
                    {
                        "id": nid,
                        "label": node["label"],
                        "korean_name": node.get("korean_name"),
                        "node_type": node["node_type"],
                        "via_concept": resolved,
                        "predicate": rel["predicate"],
                        "direction": rel["direction"],
                        "fact_id": rel["fact_id"],
                        "prompt": f"Tell me about {node['label']} on the janggu.",
                    }
                )
                if len(suggestions) >= limit:
                    return suggestions
        return suggestions

    def render_path_story(self, path_result: Dict[str, Any], session: Any = None) -> str:
        """Render a verified multi-hop graph path into cohesive storyteller prose with zero bullet dumps."""
        hops = path_result.get("hops") or []
        if not hops:
            src = path_result.get("source")
            return src["summary"] if isinstance(src, dict) and src.get("summary") else ""

        src_label = path_result["source"]["label"]
        tgt_label = path_result["target"]["label"]

        clauses: List[str] = []
        for idx, hop in enumerate(hops):
            phrase = (
                PREDICATE_FORWARD_PHRASE.get(hop["predicate"], hop["predicate"].replace("_", " "))
                if hop["direction"] == "outgoing"
                else PREDICATE_REVERSE_PHRASE.get(hop["predicate"], hop["predicate"].replace("_", " "))
            )
            qual = f" ({hop['qualifier']})" if hop.get("qualifier") else ""
            if idx == 0:
                clauses.append(f"{hop['from_label']} {phrase} {hop['to_label']}{qual}")
            else:
                clauses.append(f"which in turn {phrase} {hop['to_label']}{qual}")

        chain_sentence = ", ".join(clauses) + "."
        lead = pick_variation(
            "semnet::path_lead",
            (
                f"Follow the verified thread from {src_label} to {tgt_label} and every link clicks cleanly into place: ",
                f"Tracing how {src_label} connects to {tgt_label} across the verified records, ",
                f"Step along the chain linking {src_label} and {tgt_label}: ",
                f"Pull on {src_label} inside the janggu's history and craft, and it leads straight to {tgt_label}: ",
                f"Connect {src_label} to {tgt_label} step by step through verified sources, and the story unfolds cleanly: ",
                f"From {src_label} all the way to {tgt_label}, each verified link bridges the next: ",
            ),
            session=session,
        )

        # Weave the final target's summary & a graph-neighbor follow-up question
        tgt_summary = path_result["target"].get("summary") or ""
        followups = self.suggest_followup_concepts(
            [path_result["target"]["id"], path_result["source"]["id"]],
            exclude_ids={h["from_id"] for h in hops} | {h["to_id"] for h in hops},
            limit=2,
        )
        if len(followups) >= 2:
            closing = f"Want to follow the next thread from here—{followups[0]['label']} or {followups[1]['label']}?"
        elif len(followups) == 1:
            closing = f"Curious to explore how {followups[0]['label']} connects to this story next?"
        else:
            closing = "Where in this chain would you like to zoom in closer next?"

        body = f"{lead}{chain_sentence}"
        if tgt_summary and tgt_summary.lower() not in body.lower():
            body = f"{body}\n\n{tgt_summary}"
        return f"{body}\n\n{closing}"
