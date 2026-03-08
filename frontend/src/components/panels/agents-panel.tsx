"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AgentInfo, AgentTrace } from "@/lib/types";
import { Loader2, CheckCircle2 } from "lucide-react";
import clsx from "clsx";

interface Props {
  sublab: string;
  liveTraces: AgentTrace[];
}

export function AgentsPanel({ sublab, liveTraces }: Props) {
  const [agents, setAgents] = useState<AgentInfo[]>([]);

  useEffect(() => {
    api.getSublabAgents(sublab).then(setAgents);
  }, [sublab]);

  const liveMap = new Map(liveTraces.map((t) => [t.agent_id, t]));

  // Group by division
  const byDivision = agents.reduce<Record<string, AgentInfo[]>>((acc, agent) => {
    (acc[agent.division] ??= []).push(agent);
    return acc;
  }, {});

  let globalIndex = 0;

  return (
    <div className="space-y-4">
      {Object.entries(byDivision).map(([division, divAgents], divIdx) => (
        <div key={division} className="animate-fade-in" style={{ animationDelay: `${divIdx * 80}ms` }}>
          <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
            {division}
          </p>
          <div className="space-y-1">
            {divAgents.map((agent) => {
              const live = liveMap.get(agent.id);
              const idx = globalIndex++;
              return (
                <div
                  key={agent.id}
                  className={clsx(
                    "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs transition-all duration-300 animate-slide-up",
                    live?.status === "running"
                      ? "bg-[var(--orange-bg)] shadow-sm"
                      : live?.status === "complete"
                        ? "bg-[var(--green-bg)] bg-opacity-50"
                        : "hover:bg-[var(--bg-hover)]"
                  )}
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  {/* Status indicator */}
                  {live?.status === "running" ? (
                    <Loader2 size={12} className="shrink-0 text-[var(--orange)] animate-spin" />
                  ) : live?.status === "complete" ? (
                    <CheckCircle2 size={12} className="shrink-0 text-[var(--green)] animate-scale-in" />
                  ) : (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-[var(--border)] transition-colors" />
                  )}

                  <span className="font-mono text-[11px]">{agent.id}</span>

                  {live?.confidence_score !== undefined && live.confidence_score !== null && (
                    <span className="ml-auto text-[10px] text-[var(--text-muted)] tabular-nums animate-fade-in">
                      {Math.round(live.confidence_score * 100)}%
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {agents.length === 0 && (
        <div className="space-y-2 py-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-8 rounded-lg shimmer" />
          ))}
        </div>
      )}
    </div>
  );
}
