import type {
	BotConfig,
	ChatMessage,
	ChatProfile,
	ChatProfileSummary,
	ConceptNodeDetails,
	SemanticGraphOverview,
	SemanticPathResult
} from './types';

const DEVICE_STORAGE_KEY = 'jangbot_device_id';

function getDeviceId(): string {
	if (typeof window === 'undefined') return 'default';
	let id = window.localStorage.getItem(DEVICE_STORAGE_KEY);
	if (!id) {
		id =
			typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
				? crypto.randomUUID()
				: `dev_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
		window.localStorage.setItem(DEVICE_STORAGE_KEY, id);
	}
	return id;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
	const res = await fetch(url, {
		headers: {
			'Content-Type': 'application/json',
			'X-Device-Id': getDeviceId(),
			...(options?.headers ?? {})
		},
		...options
	});

	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || `Request failed (${res.status})`);
	}

	return res.json() as Promise<T>;
}

export const api = {
	getConfig(): Promise<BotConfig> {
		return request<BotConfig>('/api/config');
	},

	async listSessions(): Promise<ChatProfileSummary[]> {
		const data = await request<{ sessions: ChatProfileSummary[] }>('/api/sessions');
		return data.sessions;
	},

	createSession(title = 'New Chat'): Promise<ChatProfile> {
		return request<ChatProfile>('/api/sessions', {
			method: 'POST',
			body: JSON.stringify({ title })
		});
	},

	getSession(sessionId: string): Promise<ChatProfile> {
		return request<ChatProfile>(`/api/sessions/${encodeURIComponent(sessionId)}`);
	},

	renameSession(sessionId: string, title: string): Promise<ChatProfile> {
		return request<ChatProfile>(`/api/sessions/${encodeURIComponent(sessionId)}`, {
			method: 'PATCH',
			body: JSON.stringify({ title })
		});
	},

	resetSession(sessionId: string): Promise<ChatProfile> {
		return request<ChatProfile>(`/api/sessions/${encodeURIComponent(sessionId)}/reset`, {
			method: 'POST'
		});
	},

	deleteSession(sessionId: string): Promise<{ deleted: boolean }> {
		return request<{ deleted: boolean }>(`/api/sessions/${encodeURIComponent(sessionId)}`, {
			method: 'DELETE'
		});
	},

	sendMessage(
		sessionId: string,
		message: string
	): Promise<{
		session_id: string;
		user_id: string;
		title: string;
		user_message: ChatMessage;
		assistant_message: ChatMessage;
	}> {
		return request('/api/chat', {
			method: 'POST',
			body: JSON.stringify({ session_id: sessionId, message })
		});
	},

	async getMemories(userId: string): Promise<Array<Record<string, unknown>>> {
		const data = await request<{ user_id: string; memories: Array<Record<string, unknown>> }>(
			`/api/memories/${encodeURIComponent(userId)}`
		);
		return data.memories;
	},

	getGraph(params?: {
		node_type?: string;
		predicate?: string;
		category?: string;
	}): Promise<SemanticGraphOverview> {
		const qs = new URLSearchParams();
		if (params?.node_type) qs.set('node_type', params.node_type);
		if (params?.predicate) qs.set('predicate', params.predicate);
		if (params?.category) qs.set('category', params.category);
		const suffix = qs.toString() ? `?${qs.toString()}` : '';
		return request<SemanticGraphOverview>(`/api/graph${suffix}`);
	},

	getGraphNode(concept: string): Promise<ConceptNodeDetails> {
		return request<ConceptNodeDetails>(`/api/graph/node/${encodeURIComponent(concept)}`);
	},

	getGraphPath(fromConcept: string, toConcept: string, maxHops = 5): Promise<SemanticPathResult> {
		const qs = new URLSearchParams({
			from: fromConcept,
			to: toConcept,
			max_hops: String(maxHops)
		});
		return request<SemanticPathResult>(`/api/graph/path?${qs.toString()}`);
	}
};
