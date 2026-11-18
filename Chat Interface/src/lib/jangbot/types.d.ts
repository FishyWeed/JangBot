export type MascotState = 'idle' | 'thinking' | 'speaking';

export interface Profile {
  id: string;
  title: string;
  /** Last message text; empty shows "Empty conversation". */
  lastMessage?: string;
}

export interface Citation {
  /** Fact ID, e.g. "JG-014". */
  id: string;
  /** The fact or source detail shown in the row. */
  detail: string;
  publisher: string;
  /** Tier label, e.g. "Tier 1". */
  tier: string;
  /** 1 = top trust (outlined yellow tag); anything else = persimmon tag. */
  tierLevel?: number;
  url?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  /** Plain text; blank lines split paragraphs. */
  content: string;
  citations?: Citation[];
}
