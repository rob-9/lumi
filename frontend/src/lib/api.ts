import type { Chat, SublabInfo, AgentInfo, ToolInfo, IntegrationInfo, StreamEvent } from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
  return res.json();
}

export const api = {
  listSublabs: () => get<Record<string, SublabInfo>>("/sublabs"),
  getSublabAgents: (id: string) => get<AgentInfo[]>(`/sublabs/${id}/agents`),
  listAgents: () => get<AgentInfo[]>("/sublabs/meta/agents"),
  listTools: () => get<ToolInfo[]>("/sublabs/meta/tools"),
  listIntegrations: () => get<IntegrationInfo[]>("/sublabs/meta/integrations"),

  listChats: () => get<Chat[]>("/chats"),
  getChat: (id: string) => get<Chat>(`/chats/${id}`),
  createChat: (sublab: string, message: string) => post<Chat>("/chats", { sublab, message }),

  sendMessage: async function* (chatId: string, content: string): AsyncGenerator<StreamEvent> {
    const res = await fetch(`${BASE}/chats/${chatId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) throw new Error(`POST /chats/${chatId}/messages: ${res.status}`);
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          yield JSON.parse(line.slice(6)) as StreamEvent;
        }
      }
    }
  },
};
