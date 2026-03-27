// Type definitions for MCP observer

export interface Insight {
  preferences?: {
    interests?: string[];
    dislikes?: string[];
    skills?: string[];
  };
  persona_cue?: 'solution_consultant' | 'account_executive' | null;
  skills_referenced?: string[];
  competitors_mentioned?: string[];
  product_focus?: 'enterprise saas' | 'conversational ai' | null;
  urgency?: 'low' | 'medium' | 'high';
  summary?: string;
  confidence?: number;
}

export interface Message {
  id: number;
  session_id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp: string;
  extracted_insight?: Insight;
}

export interface Session {
  id: string;
  persona: string;
  start_time: string;
  end_time?: string;
  messages: Message[];
  metadata?: Record<string, any>;
}

export interface ActivePersona {
  current_persona: string;
  last_switched: string;
  personas_available: string[];
}

export interface PatternData {
  communication_style?: string;
  interaction_patterns?: any[];
  [key: string]: any;
}

export interface Rule {
  id: string;
  pattern?: string;
  event?: string;
  source?: string;
  confidence?: number;
  action: string;
  condition?: string;
}

export interface RulesConfig {
  approval_mode: boolean;
  max_approvals_before_autonomous: number;
  triggers: Rule[];
  actions: Record<string, { description: string; exec: string }>;
  safety: {
    max_updates_per_minute: number;
    cooldown_after_error_seconds: number;
    allowed_paths: string[];
    forbidden_paths: string[];
  };
}

export interface ApprovalRequest {
  id: string;
  rule_id: string;
  description: string;
  action: string;
  data: Record<string, any>;
  timestamp: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface AuditLog {
  timestamp: string;
  action: string;
  file: string;
  change: Record<string, any>;
  backup_id?: string;
  approved_by?: string;
  rule_id?: string;
}