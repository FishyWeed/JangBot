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
