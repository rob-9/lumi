"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Chat, SublabInfo } from "@/lib/types";
import { Send, ChevronRight } from "lucide-react";
import clsx from "clsx";

export default function Landing() {
  const router = useRouter();
  const [sublabs, setSublabs] = useState<Record<string, SublabInfo>>({});
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedSublab, setSelectedSublab] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api.listSublabs().then(setSublabs);
    api.listChats().then(setChats);
    // Trigger entrance animation after mount
    requestAnimationFrame(() => setLoaded(true));
  }, []);

  async function handleSubmit() {
    if (!query.trim() || submitting) return;
    setSubmitting(true);
    const sublab = selectedSublab || Object.keys(sublabs)[0] || "target-validation";
    const chat = await api.createChat(sublab, query.trim());
    router.push(`/chat/${chat.id}`);
  }

  function selectExample(sublabId: string, example: string) {
    setQuery(example);
    setSelectedSublab(sublabId);
  }

  return (
    <div className="min-h-screen flex">
      {/* Left sidebar */}
      <aside className="w-72 shrink-0 border-r border-[var(--border)] bg-[var(--bg-card)] flex flex-col">
        {/* Project header */}
        <div className="px-5 pt-5 pb-3">
          <p className="text-[10px] font-medium uppercase tracking-widest text-[var(--text-muted)]">Project</p>
          <h2 className="text-base font-semibold text-[var(--text)] mt-0.5">Lumi</h2>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-4 px-5 border-b border-[var(--border)] text-xs font-medium">
          <button className="pb-2.5 border-b-2 border-[var(--text)] text-[var(--text)]">Tasks</button>
          <button className="pb-2.5 border-b-2 border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors">Files</button>
        </div>

        {/* Task list / recent chats */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
          {chats.length > 0 ? (
            chats.slice(0, 10).map((chat, i) => (
              <a
                key={chat.id}
                href={`/chat/${chat.id}`}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all hover:bg-[var(--bg-hover)] hover:translate-x-0.5 group animate-slide-up"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent)] transition-transform group-hover:scale-125" />
                <span className="truncate text-[var(--text-secondary)] group-hover:text-[var(--text)] transition-colors">
                  {chat.title}
                </span>
              </a>
            ))
          ) : (
            <p className="px-3 py-2 text-xs text-[var(--text-muted)] animate-fade-in">No tasks yet. Start a new research query.</p>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center px-8">
        <div className={clsx("w-full max-w-2xl transition-all duration-700", loaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4")}>
          {/* Greeting */}
          <div className="mb-8">
            <h1 className="text-3xl font-semibold tracking-tight text-[var(--text)]">
              Lumi
            </h1>
            <p className="text-[15px] text-[var(--text-muted)] mt-1.5 leading-relaxed">
              Plan, execute, and review computational drug discovery research. Coordinate specialist agents across targets, safety, and clinical translation.
            </p>
          </div>

          {/* Input card */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] shadow-sm transition-shadow duration-300 hover:shadow-md focus-within:shadow-md focus-glow">
            {/* Specs bar */}
            <div className="flex items-center gap-1.5 px-5 pt-3.5 text-xs text-[var(--text-muted)]">
              {["9-phase pipeline", "8 divisions", "17 agents", "Adversarial review"].map((spec, i) => (
                <span key={spec} className="flex items-center gap-1.5">
                  {i > 0 && <span className="text-[var(--border)]">&middot;</span>}
                  <span>{spec}</span>
                </span>
              ))}
            </div>

            {/* Textarea */}
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Define a research objective..."
              rows={4}
              className="w-full resize-none bg-transparent px-5 py-3 text-sm outline-none placeholder:text-[var(--text-muted)]"
            />

            {/* Toolbar */}
            <div className="flex items-center justify-end px-4 pb-3.5">
              <button
                onClick={() => handleSubmit()}
                disabled={!query.trim() || submitting}
                className={clsx(
                  "flex h-9 w-9 items-center justify-center rounded-full bg-[var(--accent)] text-white transition-all disabled:opacity-30 hover:bg-[var(--accent-dark)] hover:scale-105 active:scale-95",
                  submitting && "animate-pulse"
                )}
              >
                <Send size={16} className={clsx("transition-transform", query.trim() && "translate-x-px -translate-y-px")} />
              </button>
            </div>
          </div>

          {/* Sublab chips */}
          <div className="mt-5 flex gap-2 overflow-x-auto no-scrollbar pb-1">
            {Object.entries(sublabs).map(([id, info], i) => (
              <button
                key={id}
                onClick={() => setSelectedSublab(selectedSublab === id ? null : id)}
                className={clsx(
                  "shrink-0 rounded-full border px-4 py-2 text-xs font-medium transition-all duration-200 hover:scale-[1.03] active:scale-[0.97] animate-slide-up",
                  selectedSublab === id
                    ? "border-[var(--accent)] bg-[var(--accent-light)] text-[var(--accent-dark)] shadow-sm"
                    : "border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:bg-[var(--bg-hover)]"
                )}
                style={{ animationDelay: `${300 + i * 60}ms` }}
              >
                {info.name}
              </button>
            ))}
            <ChevronRight size={16} className="shrink-0 self-center text-[var(--text-muted)] animate-fade-in" style={{ animationDelay: "600ms" }} />
          </div>

          {/* Expanded sublab examples */}
          {selectedSublab && sublabs[selectedSublab] && (
            <div className="mt-3 rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden animate-scale-in shadow-sm">
              <div className="px-4 py-2.5 border-b border-[var(--border)]">
                <p className="text-xs font-medium text-[var(--text)]">
                  {sublabs[selectedSublab].name}
                </p>
                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                  {sublabs[selectedSublab].description}
                </p>
              </div>
              <div className="py-1">
                {sublabs[selectedSublab].examples.map((example, i) => (
                  <button
                    key={i}
                    onClick={() => selectExample(selectedSublab, example)}
                    className="w-full px-4 py-2.5 text-left text-sm text-[var(--text-secondary)] transition-all hover:bg-[var(--accent-light)] hover:text-[var(--accent-dark)] hover:pl-5 animate-fade-in"
                    style={{ animationDelay: `${i * 50}ms` }}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
