"use client";

import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import clsx from "clsx";

const MOCK_PHASES = [
  { id: 1, name: "Genetic Evidence Collection", division: "Target Identification", status: "complete" as const, cost: "$1.50" },
  { id: 2, name: "Safety Assessment", division: "Target Safety", status: "complete" as const, cost: "$1.20" },
  { id: 3, name: "Literature Synthesis", division: "Computational Biology", status: "running" as const, cost: "$0.80" },
  { id: 4, name: "Clinical Translatability", division: "Clinical Intelligence", status: "pending" as const, cost: "$0.70" },
  { id: 5, name: "Final Synthesis & Report", division: null, status: "pending" as const, cost: "$0.50" },
];

export function PlanPanel() {
  const completed = MOCK_PHASES.filter((p) => p.status === "complete").length;
  const total = MOCK_PHASES.length;

  return (
    <div className="space-y-4">
      {/* Progress */}
      <div className="animate-fade-in">
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
            Progress
          </p>
          <span className="text-xs text-[var(--text-secondary)] tabular-nums">
            {completed}/{total}
          </span>
        </div>
        <div className="h-2 rounded-full bg-[var(--bg-hover)] overflow-hidden">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-[var(--green)] to-emerald-400 animate-progress-fill transition-all"
            style={{ width: `${(completed / total) * 100}%` }}
          />
        </div>
      </div>

      {/* Phases — timeline style */}
      <div className="relative">
        {/* Vertical connector line */}
        <div className="absolute left-[15px] top-4 bottom-4 w-px bg-[var(--border)]" />

        <div className="space-y-0.5">
          {MOCK_PHASES.map((phase, i) => (
            <div
              key={phase.id}
              className={clsx(
                "flex items-start gap-2 rounded-lg px-2.5 py-2 transition-all duration-200 hover:bg-[var(--bg-hover)] animate-slide-up relative",
                phase.status === "running" && "bg-[var(--orange-bg)] bg-opacity-50"
              )}
              style={{ animationDelay: `${i * 80}ms` }}
            >
              {/* Status icon — over the connector line */}
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
                <p className={clsx(
                  "text-xs font-medium",
                  phase.status === "pending" && "text-[var(--text-muted)]"
                )}>
                  {phase.name}
                </p>
                {phase.division && (
                  <p className="text-[10px] text-[var(--text-muted)]">{phase.division}</p>
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
        <p className="text-lg font-semibold tabular-nums">$4.70</p>
      </div>
    </div>
  );
}
