export interface Citation {
	fact_id: string;
	source_id: string;
	title: string;
	detail: string;
	publisher: string;
	tier: number;
	url?: string | null;
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	status?: string;
	confidence?: number;
	fact_ids?: string[];
	memories_used?: string[];
	citations?: Citation[];
	created_at: string;
}

export interface ChatProfileSummary {
	session_id: string;
	user_id: string;
	title: string;
	message_count: number;
	last_preview: string;
	created_at: string;
	updated_at: string;
}

export interface ChatProfile {
	session_id: string;
	user_id: string;
	title: string;
	messages: ChatMessage[];
	created_at: string;
	updated_at: string;
}

export interface PacingConfig {
	enabled: boolean;
	min_delay_ms: number;
	max_delay_ms: number;
	words_per_minute: number;
}

export interface BotConfig {
	bot_name: string;
	greeting: string;
	pacing: PacingConfig;
	memory_backend: string;
	llm_available: boolean;
}

export interface ConceptNode {
	id: string;
	label: string;
	korean_name?: string | null;
	node_type: string;
	category?: string | null;
	summary: string;
	aliases: string[];
}

export interface SemanticEdge {
	id: number;
	subject: string;
	predicate: string;
	object: string;
	fact_id: string;
	qualifier?: string | null;
}

export interface SemanticGraphOverview {
	nodes: ConceptNode[];
	edges: SemanticEdge[];
	stats: {
		node_count: number;
		edge_count: number;
		total_nodes: number;
		total_edges: number;
		node_types: string[];
		predicates: string[];
	};
}

export interface SemanticRelationDetail {
	direction: 'outgoing' | 'incoming';
	predicate: string;
	neighbor_id: string;
	neighbor_label: string;
	neighbor_korean_name?: string | null;
	neighbor_type: string;
	fact_id: string;
	qualifier?: string | null;
	fact_statement: string;
	citations: Citation[];
}

export interface SemanticFollowup {
	id: string;
	label: string;
	korean_name?: string | null;
	node_type: string;
	predicate: string;
	fact_id: string;
	prompt: string;
}

export interface ConceptNodeDetails {
	node: ConceptNode;
	outgoing: SemanticRelationDetail[];
	incoming: SemanticRelationDetail[];
	fact_ids: string[];
	citations: Citation[];
	suggested_followups: SemanticFollowup[];
}

export interface SemanticPathHop {
	from_id: string;
	from_label: string;
	predicate: string;
	direction: 'outgoing' | 'incoming';
	to_id: string;
	to_label: string;
	fact_id: string;
	qualifier?: string | null;
	fact_statement: string;
	citations: Citation[];
}

export interface SemanticPathResult {
	found: boolean;
	source?: ConceptNode;
	target?: ConceptNode;
	hop_count: number;
	hops: SemanticPathHop[];
	fact_ids: string[];
	citations: Citation[];
	narrative?: string;
}
