export interface ToolCall {
  tool_name: string;
  tool_input: Record<string, unknown>;
  result: string | null;
  duration_ms: number | null;
}

export interface AgentTrace {
  agent_id: string;
  division: string | null;
  status: "running" | "complete" | "error";
  message: string;
  tools_called: ToolCall[];
  confidence_score: number | null;
  confidence_level: string | null;
  duration_ms: number | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  agent_traces: AgentTrace[];
  hitl_events: HitlRequest[];
  integration_events: IntegrationCall[];
  sublab: string | null;
}

export interface Chat {
  id: string;
  title: string;
  sublab: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface SublabInfo {
  name: string;
  description: string;
  agents: string[];
  divisions: string[];
  examples: string[];
}

export interface AgentInfo {
  id: string;
  division: string;
  status: string;
  sublabs: string[];
}

export interface ToolInfo {
  name: string;
  server: string;
  description: string;
}

export interface IntegrationInfo {
  name: string;
  status: string;
  description: string;
}

export interface HitlRequest {
  finding: string;
  agent_id: string;
  confidence_score: number;
  reason: string;
  status: "pending" | "approved" | "rejected";
}

export interface IntegrationCall {
  integration: string;
  action: string;
  status: "running" | "complete" | "error";
  detail: string;
}

// SSE event types from the streaming endpoint
export type StreamEvent =
  | { type: "trace_start"; message_id: string; trace: AgentTrace }
  | { type: "tool_call"; message_id: string; agent_id: string; tool: ToolCall }
  | { type: "trace_complete"; message_id: string; trace: AgentTrace }
  | { type: "hitl_flag"; message_id: string; hitl: HitlRequest }
  | { type: "hitl_resolved"; message_id: string; hitl: HitlRequest }
  | { type: "integration"; message_id: string; call: IntegrationCall }
  | { type: "text_delta"; message_id: string; delta: string }
  | { type: "done"; message_id: string };
