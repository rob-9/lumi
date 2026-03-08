"use client";

import { useState, useRef, useEffect } from "react";
import type { AgentTrace } from "@/lib/types";
import { ChevronDown, ChevronRight, Loader2, CheckCircle2, AlertCircle, Wrench } from "lucide-react";
import clsx from "clsx";

interface Props {
  trace: AgentTrace;
  index?: number;
}

export function AgentTraceCard({ trace, index = 0 }: Props) {
  const [open, setOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState(0);
  const isRunning = trace.status === "running";
  const isError = trace.status === "error";

  useEffect(() => {
    if (open && contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [open, trace.tools_called]);

  return (
    <div
      className={clsx(
        "rounded-lg border bg-[var(--bg)] text-sm transition-all duration-300 hover-lift animate-slide-up",
        isRunning ? "border-[var(--orange)] border-opacity-40" : "border-[var(--border)]"
      )}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Header */}
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-[var(--bg-hover)] rounded-lg"
      >
        {/* Status icon */}
        {isRunning ? (
          <Loader2 size={14} className="shrink-0 text-[var(--orange)] animate-spin" />
        ) : isError ? (
          <AlertCircle size={14} className="shrink-0 text-[var(--red)] animate-scale-in" />
        ) : (
          <CheckCircle2 size={14} className="shrink-0 text-[var(--green)] animate-scale-in" />
        )}

        {/* Agent name + division */}
        <span className="font-mono text-xs font-medium">{trace.agent_id}</span>
        {trace.division && (
          <span className="text-[10px] text-[var(--text-muted)]">{trace.division}</span>
        )}

        {/* Confidence */}
        {trace.confidence_level && (
          <span
            className={clsx(
              "ml-auto mr-2 rounded-full px-2 py-0.5 text-[10px] font-semibold transition-colors duration-300",
              trace.confidence_level === "HIGH" && "bg-[var(--green-bg)] text-[var(--green)]",
              trace.confidence_level === "MEDIUM" && "bg-[var(--orange-bg)] text-[var(--orange)]",
              trace.confidence_level === "LOW" && "bg-[var(--red-bg)] text-[var(--red)]"
            )}
          >
            {trace.confidence_level} {trace.confidence_score !== null && `${Math.round(trace.confidence_score * 100)}%`}
          </span>
        )}

        {/* Duration */}
        {trace.duration_ms !== null && (
          <span className="text-[10px] text-[var(--text-muted)] tabular-nums">
            {(trace.duration_ms / 1000).toFixed(1)}s
          </span>
        )}

        {/* Chevron */}
        <span className={clsx("shrink-0 text-[var(--text-muted)] transition-transform duration-200", open && "rotate-90")}>
          <ChevronRight size={14} />
        </span>
      </button>

      {/* Expanded details — smooth height transition */}
      <div
        className="overflow-hidden transition-all duration-300 ease-out"
        style={{ maxHeight: open ? `${contentHeight + 20}px` : "0px", opacity: open ? 1 : 0 }}
      >
        <div ref={contentRef} className="border-t border-[var(--border)] px-3 py-2 space-y-2">
          {/* Message */}
          {trace.message && (
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{trace.message}</p>
          )}

          {/* Tool calls */}
          {trace.tools_called.length > 0 && (
            <div className="space-y-1">
              {trace.tools_called.map((tool, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded-md bg-[var(--bg-hover)] px-2.5 py-1.5 animate-fade-in transition-colors hover:bg-[var(--border)]"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <Wrench size={12} className="mt-0.5 shrink-0 text-[var(--text-muted)]" />
                  <div className="min-w-0">
                    <span className="font-mono text-[11px] font-medium">{tool.tool_name}</span>
                    {tool.result && (
                      <p className="text-[11px] text-[var(--text-muted)] truncate">{tool.result}</p>
                    )}
                  </div>
                  {tool.duration_ms !== null && (
                    <span className="ml-auto shrink-0 text-[10px] text-[var(--text-muted)] tabular-nums">
                      {tool.duration_ms}ms
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
