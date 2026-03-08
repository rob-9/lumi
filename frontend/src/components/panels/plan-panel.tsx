"use client";

import { useMemo } from "react";
import type { AgentTrace } from "@/lib/types";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import clsx from "clsx";

interface Phase {
  id: number;
  name: string;
  status: "complete" | "running" | "pending";
  agents: string[];
  cost: string;
}

interface Props {
  liveTraces?: AgentTrace[];
  streaming?: boolean;
}

export function PlanPanel({ liveTraces = [], streaming = false }: Props) {
  const phases = useMemo<Phase[]>(() => {
    // Build phases dynamically from trace divisions (order of first appearance)
    const divisionOrder: string[] = [];
    const divisionMap = new Map<string, AgentTrace[]>();

    for (const t of liveTraces) {
      const div = t.division || "Pipeline";
      if (!divisionMap.has(div)) {
        divisionOrder.push(div);
        divisionMap.set(div, []);
      }
      divisionMap.get(div)!.push(t);
    }

    const derived: Phase[] = divisionOrder.map((div, i) => {
      const traces = divisionMap.get(div)!;
      const allComplete = traces.every((t) => t.status === "complete");
      const anyRunning = traces.some((t) => t.status === "running");
      return {
        id: i,
        name: div,
        status: allComplete ? "complete" : anyRunning ? "running" : "pending",
        agents: traces.map((t) => t.agent_id),
        cost: `$${(traces.length * 0.45).toFixed(2)}`,
      };
    });

    // Always add "Final Synthesis" phase when pipeline has started
    if (derived.length > 0 || streaming) {
      const allDone = derived.length > 0 && derived.every((p) => p.status === "complete");
      derived.push({
        id: derived.length,
        name: "Final Synthesis & Report",
        status: !streaming && allDone ? "complete" : streaming && allDone ? "running" : "pending",
        agents: [],
        cost: "$0.40",
      });
    }

    return derived;
  }, [liveTraces, streaming]);

  const completed = phases.filter((p) => p.status === "complete").length;
  const total = phases.length;
  const totalCost = phases.reduce((sum, p) => {
    const num = parseFloat(p.cost.replace("$", ""));
    return sum + (isNaN(num) ? 0 : num);
  }, 0);

  if (phases.length === 0 && !streaming) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center animate-fade-in">
        <Circle size={24} className="text-[var(--border)] mb-3" />
        <p className="text-xs text-[var(--text-muted)]">Awaiting pipeline execution</p>
        <p className="text-[10px] text-[var(--text-muted)] mt-1">Submit a query to begin</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Progress */}
      <div className="animate-fade-in">
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">Progress</p>
          <span className="text-xs text-[var(--text-secondary)] tabular-nums">{completed}/{total}</span>
        </div>
        <div className="h-2 rounded-full bg-[var(--bg-hover)] overflow-hidden">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-[var(--green)] to-emerald-400 animate-progress-fill transition-all"
            style={{ width: `${total > 0 ? (completed / total) * 100 : 0}%` }}
          />
        </div>
      </div>

      {/* Phases — timeline */}
      <div className="relative">
        <div className="absolute left-[15px] top-4 bottom-4 w-px bg-[var(--border)]" />
        <div className="space-y-0.5">
          {phases.map((phase, i) => (
            <div
              key={phase.id}
              className={clsx(
                "flex items-start gap-2 rounded-lg px-2.5 py-2 transition-all duration-200 hover:bg-[var(--bg-hover)] animate-slide-up relative",
                phase.status === "running" && "bg-[var(--orange-bg)] bg-opacity-50"
              )}
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <span className="relative z-10 mt-0.5 shrink-0 bg-[var(--bg-card)] rounded-full">
                {phase.status === "complete" ? (
                  <CheckCircle2 size={14} className="text-[var(--green)]" />
                ) : phase.status === "running" ? (
                  <Loader2 size={14} className="text-[var(--orange)] animate-spin" />
                ) : (
                  <Circle size={14} className="text-[var(--border)]" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className={clsx("text-xs font-medium", phase.status === "pending" && "text-[var(--text-muted)]")}>
                  {phase.name}
                </p>
                {phase.agents.length > 0 && (
                  <p className="text-[10px] text-[var(--text-muted)] truncate">{phase.agents.join(", ")}</p>
                )}
              </div>
              <span className="shrink-0 text-[10px] text-[var(--text-muted)] tabular-nums">{phase.cost}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Estimated cost */}
      <div className="rounded-lg border border-[var(--border)] px-3 py-2.5 animate-fade-in hover-lift" style={{ animationDelay: "400ms" }}>
        <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Est. Total</p>
        <p className="text-lg font-semibold tabular-nums">${totalCost.toFixed(2)}</p>
      </div>
    </div>
  );
}
