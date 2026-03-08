import type { Message } from "@/lib/types";
import { AgentTraceCard } from "./agent-trace";
import { HitlCard } from "./hitl-card";
import { IntegrationCard } from "./integration-card";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

interface Props {
  message: Message;
  index?: number;
}

export function ChatMessage({ message, index = 0 }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className="flex gap-3 animate-slide-up"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Label */}
      <div className="w-12 shrink-0 pt-0.5">
        <p className={clsx(
          "text-xs font-medium",
          isUser ? "text-[var(--text-muted)]" : "text-[var(--accent)]"
        )}>
          {isUser ? "You" : "Lumi"}
        </p>
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1 space-y-3">
        {/* Agent traces */}
        {message.agent_traces.length > 0 && (
          <div className="space-y-2">
            {message.agent_traces.map((trace, i) => (
              <AgentTraceCard key={trace.agent_id} trace={trace} index={i} />
            ))}
          </div>
        )}

        {/* HITL events */}
        {message.hitl_events?.length > 0 && (
          <div className="space-y-2">
            {message.hitl_events.map((hitl, i) => (
              <HitlCard key={`hitl-${i}`} hitl={hitl} />
            ))}
          </div>
        )}

        {/* Integration events */}
        {message.integration_events?.length > 0 && (
          <div className="space-y-2">
            {message.integration_events.map((call, i) => (
              <IntegrationCard key={`int-${i}`} call={call} />
            ))}
          </div>
        )}

        {/* Text */}
        {isUser ? (
          <p className="text-sm leading-relaxed">{message.content}</p>
        ) : (
          <div className="chat-markdown text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
