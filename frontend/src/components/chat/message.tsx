import type { Message } from "@/lib/types";
import { AgentActivityGroup } from "./agent-activity-group";
import { HitlCard } from "./hitl-card";
import { IntegrationCard } from "./integration-card";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  message: Message;
  index?: number;
}

export function ChatMessage({ message, index = 0 }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div
        className="msg-user animate-slide-up"
        style={{ animationDelay: `${index * 60}ms` }}
      >
        <div className="msg-bubble">
          <p className="text-sm leading-relaxed text-[var(--text)]">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="msg-assistant animate-slide-up"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="msg-assistant-content space-y-3">
        <span className="text-xs font-semibold" style={{ color: "var(--accent)" }}>Lumi</span>
        {message.agent_traces.length > 0 && (
          <AgentActivityGroup traces={message.agent_traces} />
        )}

        {message.hitl_events?.length > 0 && (
          <div className="space-y-2">
            {message.hitl_events.map((hitl, i) => (
              <HitlCard key={`hitl-${i}`} hitl={hitl} />
            ))}
          </div>
        )}

        {message.integration_events?.length > 0 && (
          <div className="space-y-2">
            {message.integration_events.map((call, i) => (
              <IntegrationCard key={`int-${i}`} call={call} />
            ))}
          </div>
        )}

        {message.content && (
          <div className="chat-markdown text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
