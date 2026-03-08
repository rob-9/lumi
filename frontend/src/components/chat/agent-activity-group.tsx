"use client";

import { useState, useMemo } from "react";
import type { AgentTrace } from "@/lib/types";
import { AgentTraceCard } from "./agent-trace";
import { ChevronDown, ChevronRight, Activity } from "lucide-react";
import clsx from "clsx";

interface Props {
  traces: AgentTrace[];
  isLive?: boolean;
}

interface DivisionGroup {
  division: string;
  traces: AgentTrace[];
  hasRunning: boolean;
}

export function AgentActivityGroup({ traces, isLive = false }: Props) {
  const [collapsedDivisions, setCollapsedDivisions] = useState<Set<string>>(new Set());

  const groups = useMemo<DivisionGroup[]>(() => {
    const map = new Map<string, AgentTrace[]>();
    for (const t of traces) {
      const div = t.division || "Pipeline";
      if (!map.has(div)) map.set(div, []);
      map.get(div)!.push(t);
    }
    return Array.from(map.entries()).map(([division, divTraces]) => ({
      division,
      traces: divTraces,
      hasRunning: divTraces.some((t) => t.status === "running"),
    }));
  }, [traces]);

  const completedCount = traces.filter((t) => t.status === "complete").length;
  const totalCount = traces.length;

  function toggleDivision(div: string) {
    setCollapsedDivisions((prev) => {
      const next = new Set(prev);
      if (next.has(div)) next.delete(div);
      else next.add(div);
      return next;
    });
  }

  if (traces.length === 0) return null;

  return (
    <div className="space-y-2 animate-fade-in">
      {/* Summary header */}
      <div className="flex items-center gap-2 px-1">
        <Activity size={13} className={clsx("text-[var(--accent)]", isLive && "animate-pulse")} />
        <span className="text-xs font-medium text-[var(--text-secondary)]">
          Agent Activity
        </span>
        <span className="text-[10px] text-[var(--text-muted)] tabular-nums">
          {completedCount}/{totalCount} complete
        </span>
        {/* Mini progress bar */}
        <div className="flex-1 max-w-[80px] h-1 rounded-full bg-[var(--border)] overflow-hidden">
          <div
            className="h-full rounded-full bg-[var(--accent)] transition-all duration-500 ease-out animate-progress-fill"
            style={{ width: `${totalCount > 0 ? (completedCount / totalCount) * 100 : 0}%` }}
          />
        </div>
      </div>

      {/* Division groups */}
      {groups.map((group) => {
        const isCollapsed = collapsedDivisions.has(group.division);
        // Auto-expand divisions with running agents in live mode
        const showTraces = isLive ? (group.hasRunning || !isCollapsed) : !isCollapsed;

        return (
          <div key={group.division} className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
            {/* Division header */}
            <button
              onClick={() => toggleDivision(group.division)}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs transition-colors hover:bg-[var(--bg-hover)]"
            >
              <span className={clsx("shrink-0 text-[var(--text-muted)] transition-transform duration-200", showTraces && "rotate-90")}>
                <ChevronRight size={12} />
              </span>
              <span className="font-medium text-[var(--text-secondary)] capitalize">
                {group.division.replace(/_/g, " ")}
              </span>
              <span className="text-[10px] text-[var(--text-muted)] tabular-nums ml-auto">
                {group.traces.filter((t) => t.status === "complete").length}/{group.traces.length}
              </span>
              {group.hasRunning && (
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--orange)] animate-pulse" />
              )}
            </button>

            {/* Traces within division */}
            {showTraces && (
              <div className="px-2 pb-2 space-y-1.5">
                {group.traces.map((trace, i) => (
                  <AgentTraceCard key={trace.agent_id} trace={trace} index={i} />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
