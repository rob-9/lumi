"use client";

import { useEffect, useState, useRef, useCallback, use } from "react";
import { api } from "@/lib/api";
import type { Chat, Message, AgentTrace, HitlRequest, IntegrationCall } from "@/lib/types";
import { ChatList } from "@/components/chat/chat-list";
import { ChatMessage } from "@/components/chat/message";
import { AgentActivityGroup } from "@/components/chat/agent-activity-group";
import { HitlCard } from "@/components/chat/hitl-card";
import { IntegrationCard } from "@/components/chat/integration-card";
import { AgentsPanel } from "@/components/panels/agents-panel";
import { PlanPanel } from "@/components/panels/plan-panel";
import { ToolsPanel } from "@/components/panels/tools-panel";
import { Send, PanelRightOpen, PanelRightClose, FlaskConical } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

type RightTab = "plan" | "agents" | "tools";

type LiveEvent =
  | { kind: "trace"; trace: AgentTrace }
  | { kind: "hitl_flag"; hitl: HitlRequest }
  | { kind: "hitl_resolved"; hitl: HitlRequest }
  | { kind: "integration"; call: IntegrationCall };

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: chatId } = use(params);
  const [chat, setChat] = useState<Chat | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [liveTraces, setLiveTraces] = useState<AgentTrace[]>([]);
  const [rightTab, setRightTab] = useState<RightTab>("plan");
  const [rightOpen, setRightOpen] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getChat(chatId).then(setChat).catch(() => {
      window.location.href = "/";
    });
    api.listChats().then(setChats);
  }, [chatId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [chat?.messages, streamText, liveEvents]);

  useEffect(() => {
    if (chat && chat.messages.length === 1 && chat.messages[0].role === "user") {
      runStream(chat.messages[0].content);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chat?.id]);

  const runStream = useCallback(async (content: string) => {
    setStreaming(true);
    setStreamText("");
    setLiveEvents([]);
    setLiveTraces([]);

    try {
    for await (const event of api.sendMessage(chatId, content)) {
      console.log("[SSE]", event.type, event);
      switch (event.type) {
        case "trace_start":
          setLiveTraces((prev) => [...prev, event.trace]);
          setLiveEvents((prev) => [...prev, { kind: "trace", trace: event.trace }]);
          break;
        case "tool_call":
          setLiveTraces((prev) =>
            prev.map((t) =>
              t.agent_id === event.agent_id
                ? { ...t, tools_called: [...t.tools_called, event.tool] }
                : t
            )
          );
          setLiveEvents((prev) =>
            prev.map((e) =>
              e.kind === "trace" && e.trace.agent_id === event.agent_id
                ? { kind: "trace", trace: { ...e.trace, tools_called: [...e.trace.tools_called, event.tool] } }
                : e
            )
          );
          break;
        case "trace_complete":
          setLiveTraces((prev) =>
            prev.map((t) => (t.agent_id === event.trace.agent_id ? event.trace : t))
          );
          setLiveEvents((prev) =>
            prev.map((e) =>
              e.kind === "trace" && e.trace.agent_id === event.trace.agent_id
                ? { kind: "trace", trace: event.trace }
                : e
            )
          );
          break;
        case "hitl_flag":
          setLiveEvents((prev) => [...prev, { kind: "hitl_flag", hitl: event.hitl }]);
          break;
        case "hitl_resolved":
          setLiveEvents((prev) =>
            prev.map((e) =>
              e.kind === "hitl_flag" && e.hitl.agent_id === event.hitl.agent_id
                ? { kind: "hitl_resolved", hitl: event.hitl }
                : e
            )
          );
          break;
        case "integration":
          setLiveEvents((prev) => [...prev, { kind: "integration", call: event.call }]);
          break;
        case "text_delta":
          setStreamText((prev) => prev + event.delta);
          break;
        case "done": {
          const updated = await api.getChat(chatId);
          setChat(updated);
          setStreamText("");
          setStreaming(false);
          api.listChats().then(setChats);
          break;
        }
      }
    }
    } catch (err) {
      console.error("[SSE] Stream error:", err);
      setStreaming(false);
    }
  }, [chatId]);

  async function handleSend() {
    if (!input.trim() || streaming) return;
    const text = input.trim();
    setInput("");

    const userMsg: Message = {
      id: crypto.randomUUID().slice(0, 8),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
      agent_traces: [],
      hitl_events: [],
      integration_events: [],
      sublab: null,
    };
    setChat((prev) => prev ? { ...prev, messages: [...prev.messages, userMsg] } : prev);
    await runStream(text);
  }

  // Separate live events by kind for rendering
  const liveTracesFromEvents = liveEvents
    .filter((e): e is Extract<LiveEvent, { kind: "trace" }> => e.kind === "trace")
    .map((e) => e.trace);
  const liveHitlEvents = liveEvents.filter(
    (e): e is Extract<LiveEvent, { kind: "hitl_flag" | "hitl_resolved" }> =>
      e.kind === "hitl_flag" || e.kind === "hitl_resolved"
  );
  const liveIntegrationEvents = liveEvents.filter(
    (e): e is Extract<LiveEvent, { kind: "integration" }> => e.kind === "integration"
  );

  if (!chat) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
          <span className="flex gap-1">
            <span className="h-2 w-2 rounded-full bg-[var(--accent)] typing-dot" />
            <span className="h-2 w-2 rounded-full bg-[var(--accent)] typing-dot" />
            <span className="h-2 w-2 rounded-full bg-[var(--accent)] typing-dot" />
          </span>
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left sidebar */}
      <aside className="w-64 shrink-0 bg-[var(--sidebar-bg)] flex flex-col">
        <div className="p-4 border-b border-[var(--sidebar-hover)]">
          <a href="/" className="text-sm font-semibold text-white tracking-tight hover:opacity-80 transition-opacity">
            Lumi
          </a>
        </div>
        <ChatList chats={chats} activeChatId={chatId} />
      </aside>

      {/* Center — Chat */}
      <main className="flex-1 flex flex-col min-w-0 bg-[var(--bg)]">
        <header className="shrink-0 flex items-center justify-between border-b border-[var(--border)] bg-[var(--bg-card)] px-6 py-3">
          <div className="animate-fade-in">
            <h2 className="text-sm font-medium truncate text-[var(--text)]">{chat.title}</h2>
            <p className="text-xs text-[var(--text-muted)] capitalize">{chat.sublab.replace(/-/g, " ")}</p>
          </div>
          <button
            onClick={() => setRightOpen(!rightOpen)}
            className="rounded-lg p-1.5 text-[var(--text-muted)] transition-all hover:bg-[var(--bg-hover)] hover:text-[var(--text)] active:scale-90"
          >
            {rightOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
          </button>
        </header>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {chat.messages.map((msg, i) => (
            <ChatMessage key={msg.id} message={msg} index={i} />
          ))}

          {/* Live streaming — assistant message layout */}
          {streaming && (
            <div className="msg-assistant animate-fade-in">
              <div className="msg-assistant-avatar">
                <FlaskConical size={14} />
              </div>

              <div className={clsx("msg-assistant-content space-y-3", streamText && "streaming-indicator")}>
                {/* Thinking indicator */}
                {liveEvents.length === 0 && !streamText && (
                  <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] typing-dot" />
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] typing-dot" />
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] typing-dot" />
                    </span>
                    Thinking...
                  </div>
                )}

                {/* Agent traces — grouped by division */}
                {liveTracesFromEvents.length > 0 && (
                  <AgentActivityGroup traces={liveTracesFromEvents} isLive />
                )}

                {/* HITL events */}
                {liveHitlEvents.length > 0 && (
                  <div className="space-y-2">
                    {liveHitlEvents.map((e, i) => (
                      <HitlCard key={`h-${i}`} hitl={e.hitl} />
                    ))}
                  </div>
                )}

                {/* Integration events */}
                {liveIntegrationEvents.length > 0 && (
                  <div className="space-y-2">
                    {liveIntegrationEvents.map((e, i) => (
                      <IntegrationCard key={`i-${i}`} call={e.call} />
                    ))}
                  </div>
                )}

                {/* Streaming markdown */}
                {streamText && (
                  <div className="chat-markdown text-sm">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamText}</ReactMarkdown>
                  </div>
                )}

                {/* Typing indicator while streaming text */}
                {streamText && (
                  <div className="flex items-center gap-2">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] typing-dot" />
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] typing-dot" />
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] typing-dot" />
                    </span>
                    <span className="text-xs text-[var(--text-muted)]">Synthesizing report...</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="shrink-0 border-t border-[var(--border)] bg-[var(--bg-card)] p-4">
          <div className="relative max-w-3xl mx-auto">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Follow up..."
              rows={2}
              disabled={streaming}
              className="w-full resize-none rounded-xl border border-[var(--border)] bg-[var(--bg)] px-4 py-3 pr-12 text-sm outline-none transition-all duration-200 focus:border-[var(--border-focus)] focus:ring-2 focus:ring-[var(--border-focus)] focus:ring-opacity-20 placeholder:text-[var(--text-muted)] disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || streaming}
              className="absolute right-3 bottom-3 flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)] text-white transition-all disabled:opacity-30 hover:bg-[var(--accent-dark)] hover:scale-105 active:scale-95"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      </main>

      {/* Right panel */}
      <aside
        className={clsx(
          "shrink-0 border-l border-[var(--border)] bg-[var(--bg-card)] flex flex-col transition-all duration-300 ease-out overflow-hidden",
          rightOpen ? "w-80 opacity-100" : "w-0 opacity-0 border-l-0"
        )}
      >
        <div className="w-80 flex flex-col h-full">
          <div className="flex border-b border-[var(--border)]">
            {(["plan", "agents", "tools"] as RightTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setRightTab(tab)}
                className={clsx(
                  "flex-1 py-2.5 text-xs font-medium capitalize transition-all duration-200 border-b-2 relative",
                  tab === rightTab
                    ? "border-[var(--accent)] text-[var(--accent)]"
                    : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                )}
              >
                {tab}
              </button>
            ))}
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {rightTab === "plan" && <PlanPanel liveTraces={liveTraces} streaming={streaming} />}
            {rightTab === "agents" && <AgentsPanel sublab={chat.sublab} liveTraces={liveTraces} />}
            {rightTab === "tools" && <ToolsPanel />}
          </div>
        </div>
      </aside>
    </div>
  );
}
