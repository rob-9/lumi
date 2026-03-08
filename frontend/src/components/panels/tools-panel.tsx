"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ToolInfo, IntegrationInfo } from "@/lib/types";
import { Wrench, Plug } from "lucide-react";
import clsx from "clsx";

export function ToolsPanel() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [integrations, setIntegrations] = useState<IntegrationInfo[]>([]);

  useEffect(() => {
    api.listTools().then(setTools);
    api.listIntegrations().then(setIntegrations);
  }, []);

  // Group tools by server
  const byServer = tools.reduce<Record<string, ToolInfo[]>>((acc, tool) => {
    (acc[tool.server] ??= []).push(tool);
    return acc;
  }, {});

  return (
    <div className="space-y-5">
      {/* Integrations */}
      <div>
        <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-2">
          Integrations
        </p>
        <div className="space-y-1">
          {integrations.map((int, i) => (
            <div
              key={int.name}
              className="flex items-center gap-2 rounded-lg px-2.5 py-2 hover:bg-[var(--bg-hover)] transition-all duration-200 hover-lift animate-slide-up"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <Plug size={12} className="shrink-0 text-[var(--accent)]" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium">{int.name}</p>
                <p className="text-[10px] text-[var(--text-muted)] truncate">{int.description}</p>
              </div>
              <span className={clsx(
                "shrink-0 rounded-full px-2 py-0.5 text-[10px]",
                int.status === "available"
                  ? "bg-[var(--green-bg)] text-[var(--green)]"
                  : "bg-[var(--bg-hover)] text-[var(--text-muted)]"
              )}>
                {int.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* MCP Tools */}
      <div>
        <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-2">
          MCP Tools
        </p>
        {Object.entries(byServer).map(([server, serverTools], sIdx) => (
          <div key={server} className="mb-3 animate-fade-in" style={{ animationDelay: `${sIdx * 100}ms` }}>
            <p className="text-[10px] font-medium text-[var(--text-secondary)] mb-1 px-2.5">
              {server}
            </p>
            <div className="space-y-0.5">
              {serverTools.map((tool, i) => (
                <div
                  key={tool.name}
                  className="flex items-start gap-2 rounded-lg px-2.5 py-1.5 hover:bg-[var(--bg-hover)] transition-all duration-200 animate-slide-up"
                  style={{ animationDelay: `${sIdx * 100 + i * 30}ms` }}
                >
                  <Wrench size={11} className="mt-0.5 shrink-0 text-[var(--text-muted)]" />
                  <div className="min-w-0">
                    <p className="font-mono text-[11px]">{tool.name}</p>
                    <p className="text-[10px] text-[var(--text-muted)] truncate">{tool.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {tools.length === 0 && (
          <div className="space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-7 rounded-lg shimmer" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
