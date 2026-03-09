"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { FlaskConical, User, Hash, CheckCircle2, XCircle, RotateCcw, ArrowLeft } from "lucide-react";
import clsx from "clsx";

interface ReviewMessage {
  role: "agent" | "expert";
  name: string;
  title: string;
  text: string;
}

const CONVERSATIONS: Record<string, { channel: string; messages: ReviewMessage[] }> = {
  glp1r: {
    channel: "neuro-repurposing",
    messages: [
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "I've flagged a clinical finding for your review. The evidence suggests GLP-1R agonists may be disease-modifying in Parkinson's, but confidence is low (38%). The primary evidence is a single Phase II trial with 62 participants (Athauda et al., 2017).",
      },
      {
        role: "expert",
        name: "Dr. Sarah Chen",
        title: "Neuropharmacologist",
        text: "The Athauda 2017 exenatide trial showed motor improvement at 60 weeks, but it was open-label initially. What was the effect size in the placebo-controlled phase? And are there any replication studies underway?",
      },
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "MDS-UPDRS Part 3 off-medication: exenatide -1.0 pts vs placebo +2.1 pts (adjusted difference: -3.5, 95% CI: -6.7 to -0.3, p=0.04). No independent replication yet, but Exenatide-PD3 Phase III (NCT04232969, n=200) is actively recruiting. Lixisenatide and NLY01 (brain-penetrant GLP-1 agonist) Phase II trials also ongoing.",
      },
      {
        role: "expert",
        name: "Dr. Sarah Chen",
        title: "Neuropharmacologist",
        text: "Effect size is modest but statistically significant. Given it's a single underpowered trial, I'll approve this for inclusion with an explicit uncertainty label. The open-label extension showed benefit persisted at 2 years, which is encouraging. Track the Phase III for definitive evidence.",
      },
    ],
  },
  parp: {
    channel: "tnbc-combination-therapy",
    messages: [
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "I've flagged a finding on PD-L1/PARP-trapping bispecific antibody feasibility for expert review. Confidence is 32%. The concept has mechanistic rationale — simultaneous PARP trapping and immune checkpoint blockade in BRCA1-deficient TNBC — but no experimental validation exists. The PARP-trapping moiety has never been successfully conjugated to an antibody scaffold.",
      },
      {
        role: "expert",
        name: "Dr. James Rodriguez",
        title: "Antibody Engineering Lead",
        text: "Interesting concept. What structural data supports a bispecific format here? PARP trapping requires the inhibitor to physically trap PARP1 on DNA — how would you achieve that from an antibody-conjugated payload? And what does your Rosetta modeling show for linker geometry?",
      },
      {
        role: "agent",
        name: "Lumi Agent",
        title: "AI Scientist",
        text: "Rosetta modeling suggests a PEG\u2088-linked talazoparib warhead on the Fab arm could maintain PARP-trapping activity (predicted IC\u2085\u2080 shift: 3.2x vs free talazoparib). The anti-PD-L1 arm uses the atezolizumab CDR scaffold. DMS analysis shows linker orientation is critical — 4/12 configurations maintain >50% trapping efficiency. CMC concern: the talazoparib-linker conjugate shows 15% aggregation at 40\u00b0C/4wk in accelerated stability.",
      },
      {
        role: "expert",
        name: "Dr. James Rodriguez",
        title: "Antibody Engineering Lead",
        text: "The 3x IC\u2085\u2080 shift is concerning but not disqualifying for proof-of-concept. I'll approve this for in silico exploration only — do NOT include as a clinical recommendation. The CMC challenges alone (dual-payload stability, 15% aggregation, conjugation-site heterogeneity) make this 3-5 years from IND-enabling studies at best. Flag clearly as exploratory and focus near-term efforts on the conventional olaparib + atezolizumab combination.",
      },
    ],
  },
};

function getConversation(finding: string): { channel: string; messages: ReviewMessage[] } {
  const f = finding.toLowerCase();
  if (f.includes("parp") || f.includes("bispecific") || f.includes("brca") || f.includes("tnbc")) {
    return CONVERSATIONS.parp;
  }
  return CONVERSATIONS.glp1r;
}

function ReviewContent() {
  const searchParams = useSearchParams();
  const finding = searchParams.get("finding") || "No finding specified";
  const agent = searchParams.get("agent") || "unknown_agent";
  const confidence = parseFloat(searchParams.get("confidence") || "0");
  const reason = searchParams.get("reason") || "";
  const findingId = searchParams.get("finding_id") || "review_001";
  const chatId = searchParams.get("chat_id") || "";

  const conv = getConversation(finding);
  const channelName = searchParams.get("channel") || conv.channel;
  const mockMessages = conv.messages;

  const [visibleMessages, setVisibleMessages] = useState<ReviewMessage[]>([]);
  const [typing, setTyping] = useState(false);
  const [resolved, setResolved] = useState<"approved" | "revised" | "rejected" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const playedRef = useRef(false);

  async function submitDecision(decision: "approved" | "revised" | "rejected") {
    setSubmitting(true);
    setResolved(decision);
    if (chatId) {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";
        await fetch(`${apiBase}/chats/${chatId}/review/${findingId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            status: decision === "revised" ? "rejected" : decision,
            feedback: decision === "revised" ? "Sent back for revision" : "",
          }),
        });
      } catch (err) {
        console.error("Failed to submit review decision:", err);
      }
    }
    setSubmitting(false);
  }

  const confidencePct = Math.round((isNaN(confidence) ? 0 : confidence) * 100);

  useEffect(() => {
    if (playedRef.current) return;
    playedRef.current = true;

    let cancelled = false;
    async function playConversation() {
      for (let i = 0; i < mockMessages.length; i++) {
        if (cancelled) return;
        setTyping(true);
        await new Promise((r) => setTimeout(r, i === 0 ? 1500 : 2500));
        if (cancelled) return;
        setTyping(false);
        setVisibleMessages((prev) => [...prev, mockMessages[i]]);
        await new Promise((r) => setTimeout(r, 500));
      }
      if (!cancelled) {
        await new Promise((r) => setTimeout(r, 1000));
        if (!cancelled) setResolved("approved");
      }
    }
    playConversation();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [visibleMessages, typing, resolved]);

  return (
    <div className="flex h-screen flex-col bg-[var(--bg)]">
      {/* Header bar */}
      <header className="shrink-0 flex items-center gap-3 border-b border-[var(--border)] bg-[var(--bg-card)] px-5 py-3">
        <button
          onClick={() => window.history.back()}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-hover)] hover:text-[var(--text)]"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--accent-light)] text-[var(--accent)]">
          <FlaskConical size={14} />
        </div>
        <div className="flex items-center gap-1.5">
          <Hash size={13} className="text-[var(--text-muted)]" />
          <span className="text-sm font-semibold text-[var(--text)]">{channelName}</span>
        </div>
        <span className="text-[10px] uppercase tracking-wider font-medium text-[var(--text-muted)]">Expert Review</span>
        <div className="ml-auto flex items-center gap-2.5">
          <span
            className={clsx(
              "rounded-full px-2.5 py-0.5 text-[10px] font-semibold text-white",
              confidencePct >= 70 ? "bg-[var(--green)]" : confidencePct >= 50 ? "bg-[var(--orange)]" : "bg-[var(--orange)]"
            )}
          >
            {confidencePct}% confidence
          </span>
          <span className="text-[10px] text-[var(--text-muted)] font-mono">{findingId}</span>
        </div>
      </header>

      {/* Finding summary */}
      <div className="shrink-0 border-b border-[var(--border)] bg-[var(--orange-bg)] px-5 py-3">
        <div className="flex items-start gap-3 max-w-3xl mx-auto">
          <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-[var(--orange)] bg-opacity-20 text-[var(--orange)]">
            <span className="text-xs font-bold">!</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-[var(--text)] leading-snug">{finding}</p>
            <div className="mt-1.5 flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
              <span>Agent: <span className="font-mono text-[var(--text-secondary)]">{agent}</span></span>
              {reason && <span className="truncate">{reason}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Message thread */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-5">
        <div className="max-w-3xl mx-auto space-y-5">
          {visibleMessages.map((msg, i) => (
            <div
              key={i}
              className="flex items-start gap-3 animate-slide-up"
              style={{ animationDelay: "0ms" }}
            >
              {/* Avatar */}
              <div
                className={clsx(
                  "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white",
                  msg.role === "agent" ? "bg-[var(--accent)]" : "bg-emerald-600"
                )}
              >
                {msg.role === "agent" ? <FlaskConical size={14} /> : <User size={14} />}
              </div>

              {/* Message body */}
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-semibold text-[var(--text)]">{msg.name}</span>
                  <span className="text-[11px] text-[var(--text-muted)]">{msg.title}</span>
                  <span className="text-[10px] text-[var(--border-hover)]">
                    {new Date(Date.now() - (mockMessages.length - i) * 60000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                <p className="mt-1 text-sm leading-relaxed text-[var(--text-secondary)] whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {typing && !resolved && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--bg-hover)]">
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--text-muted)] typing-dot" />
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--text-muted)] typing-dot" />
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--text-muted)] typing-dot" />
                </span>
              </div>
              <div className="pt-2.5">
                <span className="text-[11px] text-[var(--text-muted)]">typing...</span>
              </div>
            </div>
          )}

          {/* Resolution banner */}
          {resolved && (
            <div
              className={clsx(
                "rounded-lg border px-4 py-3 flex items-center gap-3 animate-scale-in",
                resolved === "approved"
                  ? "border-[var(--green)] bg-[var(--green-bg)]"
                  : resolved === "revised"
                    ? "border-[var(--orange)] bg-[var(--orange-bg)]"
                    : "border-[var(--red)] bg-[var(--red-bg)]"
              )}
            >
              {resolved === "approved" ? (
                <CheckCircle2 size={16} className="text-[var(--green)] shrink-0" />
              ) : resolved === "rejected" ? (
                <XCircle size={16} className="text-[var(--red)] shrink-0" />
              ) : (
                <RotateCcw size={16} className="text-[var(--orange)] shrink-0" />
              )}
              <div>
                <p className="text-sm font-semibold text-[var(--text)] capitalize">
                  Finding {resolved}
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  {resolved === "approved"
                    ? "Include with explicit uncertainty label. Track Phase III for definitive evidence."
                    : resolved === "revised"
                      ? "Finding sent back for revision with expert feedback."
                      : "Finding rejected. Will not be included in final report."}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="shrink-0 border-t border-[var(--border)] bg-[var(--bg-card)] px-5 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <button
            onClick={() => submitDecision("approved")}
            disabled={resolved !== null || submitting}
            className={clsx(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all",
              resolved === "approved"
                ? "bg-[var(--green)] text-white"
                : resolved !== null
                  ? "bg-[var(--bg-hover)] text-[var(--text-muted)] cursor-not-allowed"
                  : "bg-[var(--green)] text-white hover:brightness-110 active:scale-95"
            )}
          >
            <CheckCircle2 size={14} />
            Approve with caveat
          </button>
          <button
            onClick={() => submitDecision("revised")}
            disabled={resolved !== null || submitting}
            className={clsx(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all",
              resolved === "revised"
                ? "bg-[var(--orange)] text-white"
                : resolved !== null
                  ? "bg-[var(--bg-hover)] text-[var(--text-muted)] cursor-not-allowed"
                  : "border border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] active:scale-95"
            )}
          >
            <RotateCcw size={14} />
            Revise
          </button>
          <button
            onClick={() => submitDecision("rejected")}
            disabled={resolved !== null || submitting}
            className={clsx(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all",
              resolved === "rejected"
                ? "bg-[var(--red)] text-white"
                : resolved !== null
                  ? "bg-[var(--bg-hover)] text-[var(--text-muted)] cursor-not-allowed"
                  : "border border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] active:scale-95"
            )}
          >
            <XCircle size={14} />
            Reject
          </button>
          {resolved && (
            <span className="ml-auto text-[11px] text-[var(--text-muted)]">
              Decision recorded.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-[var(--bg)]">
          <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
            <span className="flex gap-1">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)] typing-dot" />
              <span className="h-2 w-2 rounded-full bg-[var(--accent)] typing-dot" />
              <span className="h-2 w-2 rounded-full bg-[var(--accent)] typing-dot" />
            </span>
            Loading review...
          </div>
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
