"use client";

import { useState, useEffect, useRef, useCallback, type ReactNode } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  Brain, Shield, Users, Search, FileText,
  CheckCircle2, AlertTriangle, ArrowRight, Sparkles,
  Activity, Dna, Pill, Target, HeartPulse, Beaker,
  BookOpen, Lock, Eye, Zap, MessageSquare, Hash,
  ChevronRight, Bot, Menu, X, Network, GitBranch,
  Microscope, BarChart3, ExternalLink,
} from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

/* ═══════════════════════════════════════════════════════════════
   PALETTE
   ═══════════════════════════════════════════════════════════════ */

const C = {
  bg: "#0a0a10",
  surface: "#121218",
  surface2: "#1a1a24",
  border: "#2a2a3a",
  borderLight: "#3a3a4e",
  text: "#e4e2ea",
  dim: "#9c98b0",
  muted: "#5a5670",
  accent: "#a78bfa",
  accentDim: "#7c5fd6",
  warm: "#e8a44a",
  warmDim: "#a67832",
};

/* ═══════════════════════════════════════════════════════════════
   DATA
   ═══════════════════════════════════════════════════════════════ */

const PIPELINE_PHASES = [
  { name: "CSO Scoping", Icon: Brain, desc: "Strategic query decomposition & feasibility", dur: 1800 },
  { name: "Biosecurity Gate", Icon: Shield, desc: "5-method dual-use risk screening", dur: 1200 },
  { name: "Team Assembly", Icon: Users, desc: "Dynamic division & agent selection", dur: 1400 },
  { name: "Agent Execution", Icon: Zap, desc: "Parallel specialist agent runs", dur: 4500 },
  { name: "Adversarial Review", Icon: Eye, desc: "3-pass review panel with refinement", dur: 2000 },
  { name: "Confidence Routing", Icon: Activity, desc: "HITL routing for low-confidence findings", dur: 1500 },
  { name: "Synthesis", Icon: Sparkles, desc: "Final report with provenance chain", dur: 1800 },
];

const TOOL_CALLS = [
  { agent: "pharmacologist", tool: "pubmed_search", input: "GLP-1 receptor agonist Alzheimer neuroprotection", time: "2.3s" },
  { agent: "neuro_specialist", tool: "uniprot_lookup", input: "GLP1R_HUMAN P43220", time: "1.1s" },
  { agent: "safety_agent", tool: "fda_adverse_events", input: "semaglutide neurological", time: "3.4s" },
  { agent: "lit_synthesis", tool: "semantic_scholar", input: "GLP-1 neuroprotection clinical evidence", time: "1.8s" },
  { agent: "target_biologist", tool: "kegg_pathways", input: "hsa04024 cAMP signaling", time: "2.1s" },
  { agent: "clinical_trialist", tool: "clinicaltrials_gov", input: "GLP-1 Alzheimer phase 2 3", time: "2.7s" },
];

const DIVISIONS = [
  { name: "Target ID", agents: 3, color: "#c4b5fd", Icon: Target, specialists: ["statistical_genetics", "functional_genomics", "single_cell_atlas"] },
  { name: "Target Safety", agents: 3, color: "#e8a44a", Icon: Shield, specialists: ["bio_pathways", "fda_safety", "toxicogenomics"] },
  { name: "Modality", agents: 2, color: "#a78bfa", Icon: Pill, specialists: ["target_biologist", "pharmacologist"] },
  { name: "Molecular Design", agents: 5, color: "#818cf8", Icon: Dna, specialists: ["protein_intelligence", "antibody_engineer", "structure_design", "lead_optimization", "developability"] },
  { name: "Clinical", agents: 1, color: "#c084fc", Icon: HeartPulse, specialists: ["clinical_trialist"] },
  { name: "CompBio", agents: 1, color: "#93c5fd", Icon: BookOpen, specialists: ["literature_synthesis"] },
  { name: "Experimental", agents: 1, color: "#d8b4fe", Icon: Beaker, specialists: ["assay_design"] },
  { name: "Biosecurity", agents: 1, color: "#f87171", Icon: Lock, specialists: ["dual_use_screening"] },
];

const HITL_MSGS: { role: string; name: string; title?: string; text: string }[] = [
  { role: "lumi", name: "Lumi", text: "Clinical claim flagged for expert review:\n\n\"GLP-1 agonists show neuroprotective effects in tau pathology models (confidence: 0.38). Three Phase II trials show mixed endpoints — cognitive improvement trends but not statistically significant.\"" },
  { role: "expert", name: "Dr. Sarah Chen", title: "Neuro-pharmacologist", text: "The tau pathology claim needs qualification. While GLP-1R activation reduces phospho-tau in murine models (Batista et al., 2024), clinical translation is premature. NCT04777396 showed a trend (p=0.08) on ADAS-Cog13 but failed primary endpoint. Downgrade to 'preliminary evidence'." },
  { role: "lumi", name: "Lumi", text: "Revised: \"Preliminary preclinical evidence suggests GLP-1R agonism reduces phospho-tau, but Phase II data remain inconclusive. Recommend monitoring NCT05891496 (est. completion Q4 2026).\"\n\nUpdated confidence: 0.52" },
  { role: "expert", name: "Dr. Sarah Chen", title: "Neuro-pharmacologist", text: "Approved. Fair characterization. Also note the BBB penetrance difference between exenatide (poor) and semaglutide (moderate) — matters for target engagement." },
];

const REPORT_ITEMS: { type: string; text: string; confidence?: number; badge?: string }[] = [
  { type: "title", text: "GLP-1 Receptor Agonists for Alzheimer's Disease" },
  { type: "meta", text: "9-phase pipeline  ·  6 agents  ·  23 tool calls  ·  4m 12s  ·  47 sources" },
  { type: "heading", text: "Executive Summary" },
  { type: "body", text: "GLP-1 receptor agonists represent a mechanistically plausible but clinically unproven approach to Alzheimer's disease. Strong preclinical evidence supports neuroprotective effects via cAMP/PKA signaling, neuroinflammation reduction, and improved cerebral glucose metabolism." },
  { type: "heading", text: "Key Findings" },
  { type: "finding", text: "GLP-1R activation reduces neuroinflammation via NF-\u03BAB suppression in microglia", confidence: 0.82, badge: "high" },
  { type: "finding", text: "Semaglutide crosses BBB at therapeutically relevant concentrations", confidence: 0.71, badge: "medium" },
  { type: "finding", text: "Phase II cognitive endpoints show non-significant improvement trends", confidence: 0.52, badge: "reviewed" },
  { type: "finding", text: "Tau phosphorylation reduction observed in murine models only", confidence: 0.45, badge: "reviewed" },
  { type: "heading", text: "Recommendation" },
  { type: "body", text: "Monitor ongoing Phase III trial (NCT05891496) for semaglutide in early AD. Consider combination approaches targeting both amyloid and metabolic pathways. Prioritize BBB-penetrant GLP-1 analogs for future development." },
];

/* ═══════════════════════════════════════════════════════════════
   HOOKS
   ═══════════════════════════════════════════════════════════════ */

function useInView(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

/* ═══════════════════════════════════════════════════════════════
   PRIMITIVES
   ═══════════════════════════════════════════════════════════════ */

function NoiseOverlay() {
  return (
    <svg className="noise-overlay" xmlns="http://www.w3.org/2000/svg">
      <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" /></filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
  );
}

function MagButton({ children, href, accent = false }: { children: ReactNode; href: string; accent?: boolean }) {
  const isExternal = href.startsWith("http");
  return (
    <a href={href} className="mag-btn"
      {...(isExternal ? { target: "_self", rel: "noopener" } : {})}
      style={{
        padding: accent ? "0.75rem 1.75rem" : "0.75rem 1.5rem",
        background: accent ? C.accent : "transparent",
        color: accent ? C.bg : C.dim,
        border: accent ? "none" : `1px solid ${C.border}`,
      }}>
      <span className="mag-slide pointer-events-none" style={{ background: accent ? "rgba(255,255,255,0.15)" : C.surface2 }} />
      <span className="mag-label pointer-events-none">{children}</span>
    </a>
  );
}

function SectionLabel({ icon: Icon, label }: { icon: typeof Network; label: string }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-[11px] font-medium tracking-wide uppercase mb-5"
      style={{ borderColor: C.border, color: C.muted }}>
      <Icon size={12} /> {label}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   NAVBAR — Pill, Centered, Morphing
   ═══════════════════════════════════════════════════════════════ */

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", h, { passive: true });
    return () => window.removeEventListener("scroll", h);
  }, []);

  const links: [string, string][] = [
    ["Pipeline", "#pipeline"],
    ["Agents", "#agents"],
    ["Human-in-the-Loop", "#hitl"],
    ["Results", "#results"],
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        background: scrolled ? "rgba(10,10,16,0.82)" : "transparent",
        backdropFilter: scrolled ? "blur(16px) saturate(1.4)" : "none",
        WebkitBackdropFilter: scrolled ? "blur(16px) saturate(1.4)" : "none",
        borderBottom: scrolled ? `1px solid ${C.border}60` : "1px solid transparent",
      }}>
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <span className="text-sm font-semibold tracking-tight" style={{ color: C.text }}>Lumi</span>

        <div className="hidden md:flex items-center gap-8">
          {links.map(([label, href]) => (
            <a key={label} href={href} className="text-[13px] font-medium transition-colors duration-200 hover:!text-[#a78bfa]"
              style={{ color: C.dim }}>{label}</a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <a href="http://localhost:3001" className="hidden md:inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-[13px] font-semibold transition-all duration-200 hover:opacity-90"
            style={{ background: C.accent, color: C.bg }}>
            Sign In <ArrowRight size={13} />
          </a>
          <button className="md:hidden" style={{ color: C.text }} onClick={() => setOpen(!open)}>
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {open && (
        <div className="md:hidden border-t px-6 py-4 flex flex-col gap-3 animate-fade-in"
          style={{ background: C.surface, borderColor: C.border }}>
          {links.map(([label, href]) => (
            <a key={label} href={href} className="text-sm py-2" style={{ color: C.dim }}
              onClick={() => setOpen(false)}>{label}</a>
          ))}
          <a href="http://localhost:3001" className="mt-2 text-center py-2.5 rounded-lg text-sm font-semibold"
            style={{ background: C.accent, color: C.bg }} onClick={() => setOpen(false)}>Sign In</a>
        </div>
      )}
    </nav>
  );
}

/* ═══════════════════════════════════════════════════════════════
   PIPELINE DEMO
   ═══════════════════════════════════════════════════════════════ */

function PipelineDemo() {
  const [phase, setPhase] = useState(-1);
  const [done, setDone] = useState<Set<number>>(new Set());
  const [tools, setTools] = useState<number[]>([]);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const clear = () => timers.current.forEach(clearTimeout);

  const run = useCallback(() => {
    clear();
    setPhase(-1); setDone(new Set()); setTools([]);
    let cum = 600;
    PIPELINE_PHASES.forEach((p, i) => {
      timers.current.push(setTimeout(() => setPhase(i), cum));
      if (i === 3) TOOL_CALLS.forEach((_, ti) => {
        timers.current.push(setTimeout(() => setTools(prev => [...prev, ti]), cum + 500 * (ti + 1)));
      });
      cum += p.dur;
      timers.current.push(setTimeout(() => setDone(prev => new Set(prev).add(i)), cum));
    });
    timers.current.push(setTimeout(() => run(), cum + 3500));
  }, []);

  useEffect(() => {
    const t = setTimeout(run, 1200);
    return () => { clearTimeout(t); clear(); };
  }, [run]);

  return (
    <div className="demo-window" style={{ boxShadow: "0 0 80px rgba(167,139,250,0.05), 0 8px 60px rgba(0,0,0,0.4)" }}>
      <div className="demo-chrome">
        <div className="flex gap-1.5">
          <div className="demo-dot" style={{ background: "#f8717150" }} />
          <div className="demo-dot" style={{ background: "#d8b4fe50" }} />
          <div className="demo-dot" style={{ background: "#a78bfa50" }} />
        </div>
        <span className="text-[11px] font-mono" style={{ color: C.muted }}>YOHAS Pipeline</span>
        {phase >= 0 && !done.has(6) && (
          <div className="ml-auto flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: C.accent }} />
            <span className="text-[11px] font-medium" style={{ color: C.accent }}>Running</span>
          </div>
        )}
        {done.has(6) && (
          <div className="ml-auto flex items-center gap-2">
            <CheckCircle2 size={13} color={C.accent} />
            <span className="text-[11px] font-medium" style={{ color: C.accent }}>Complete</span>
          </div>
        )}
      </div>

      {/* Query */}
      <div className="px-5 py-3.5 border-b" style={{ borderColor: C.border }}>
        <div className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl border" style={{ background: C.surface2, borderColor: C.border }}>
          <Search size={14} color={C.muted} />
          <span className="text-[13px]" style={{ color: C.dim }}>Evaluate GLP-1 receptor agonists for Alzheimer&apos;s disease</span>
        </div>
      </div>

      <div className="flex flex-col md:flex-row" style={{ height: 400 }}>
        {/* Phases */}
        <div className="flex-1 px-5 py-4 border-b md:border-b-0 md:border-r" style={{ borderColor: C.border }}>
          <div className="text-[10px] font-semibold uppercase tracking-widest mb-3" style={{ color: C.muted }}>Phases</div>
          <div className="space-y-0.5">
            {PIPELINE_PHASES.map((p, i) => {
              const active = phase === i && !done.has(i);
              const complete = done.has(i);
              return (
                <div key={p.name} className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg transition-all duration-300"
                  style={active ? { background: `${C.accent}0a`, boxShadow: `inset 3px 0 0 ${C.accent}` } : {}}>
                  <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                    style={{ background: complete ? `${C.accent}18` : active ? `${C.accent}10` : `${C.muted}0c` }}>
                    {complete ? <CheckCircle2 size={13} color={C.accent} /> :
                     active ? <p.Icon size={13} color={C.accent} className="animate-pulse" /> :
                     <p.Icon size={13} color={C.muted} />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-medium" style={{ color: complete || active ? C.text : C.muted }}>{p.name}</div>
                    {active && <div className="text-[11px] mt-0.5 animate-fade-in" style={{ color: C.dim }}>{p.desc}</div>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Activity feed */}
        <div className="flex-1 px-5 py-4">
          <div className="text-[10px] font-semibold uppercase tracking-widest mb-3" style={{ color: C.muted }}>Agent Activity</div>

          {phase < 3 && tools.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-2 py-12" style={{ color: C.muted }}>
              {phase >= 0 ? (
                <><div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: C.accent }} />
                <span className="text-[13px]">{PIPELINE_PHASES[phase]?.name}...</span></>
              ) : <span className="text-[13px]">Waiting...</span>}
            </div>
          )}

          <div className="space-y-1">
            {TOOL_CALLS.map((tc, i) => {
              if (!tools.includes(i)) return null;
              const latest = i === Math.max(...tools);
              return (
                <div key={i} className="flex items-start gap-2.5 px-2.5 py-2 rounded-lg animate-slide-up"
                  style={{ background: latest ? `${C.accent}06` : "transparent" }}>
                  <Bot size={13} className="mt-0.5 flex-shrink-0" style={{ color: latest ? C.accent : C.muted }} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[13px] font-medium" style={{ color: C.text }}>{tc.agent}</span>
                      <ChevronRight size={10} color={C.muted} />
                      <span className="text-[13px] font-mono" style={{ color: C.accent }}>{tc.tool}</span>
                    </div>
                    <div className="text-[11px] mt-0.5 font-mono truncate" style={{ color: C.muted }}>&quot;{tc.input}&quot; — {tc.time}</div>
                  </div>
                  <CheckCircle2 size={11} className="mt-1 flex-shrink-0" style={{ color: C.accentDim }} />
                </div>
              );
            })}
          </div>

          {done.has(4) && (
            <div className="mt-3 px-3 py-2.5 rounded-xl border animate-slide-up" style={{ borderColor: C.border, background: C.surface2 }}>
              <div className="flex items-center gap-2 mb-1">
                <Eye size={13} color={C.warm} />
                <span className="text-[13px] font-medium" style={{ color: C.warm }}>Review Panel</span>
              </div>
              <div className="text-[11px] leading-relaxed" style={{ color: C.dim }}>3-pass adversarial review. 2 findings revised. 1 routed to HITL.</div>
            </div>
          )}

          {done.has(6) && (
            <div className="mt-2 px-3 py-2.5 rounded-xl border animate-slide-up"
              style={{ borderColor: `${C.accent}40`, background: `${C.accent}08` }}>
              <div className="flex items-center gap-2 mb-1">
                <Sparkles size={13} color={C.accent} />
                <span className="text-[13px] font-medium" style={{ color: C.accent }}>Synthesis Complete</span>
              </div>
              <div className="text-[11px] leading-relaxed" style={{ color: C.dim }}>4 findings · 47 sources · confidence 0.45–0.82</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   STATS
   ═══════════════════════════════════════════════════════════════ */

function StatsBar() {
  const { ref, visible } = useInView(0.5);
  const stats = [
    { value: "Dynamic", label: "Agent Teams" },
    { value: "119+", label: "MCP Tools" },
    { value: "9", label: "Pipeline Phases" },
    { value: "5", label: "Biosecurity Gates" },
  ];
  return (
    <div ref={ref} className="section" style={{ paddingTop: "2rem", paddingBottom: "2rem" }}>
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((s, i) => (
            <div key={s.label} className={`text-center ${visible ? "animate-slide-up" : "opacity-0"}`}
              style={{ animationDelay: `${i * 80}ms` }}>
              <div className="text-2xl md:text-3xl font-bold font-mono" style={{ color: C.accent }}>{s.value}</div>
              <div className="text-[10px] mt-1 font-medium uppercase tracking-widest" style={{ color: C.muted }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   AGENTS
   ═══════════════════════════════════════════════════════════════ */

function AgentSection() {
  const { ref, visible } = useInView(0.1);
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <section id="agents" ref={ref} className="section">
      <div className="max-w-6xl mx-auto">
        <div className={`text-left mb-12 ${visible ? "animate-slide-up" : "opacity-0"}`}>
          <SectionLabel icon={Network} label="Multi-Agent Research" />
          <h2 className="text-lg md:text-xl font-semibold" style={{ letterSpacing: "-0.01em" }}>
            Agents and divisions generated per query.
          </h2>
        </div>

        {/* Tier 1 */}
        <div className={`flex flex-col items-center mb-8 ${visible ? "animate-slide-up" : "opacity-0"}`} style={{ animationDelay: "100ms" }}>
          <div className="text-[10px] font-semibold uppercase tracking-widest mb-3" style={{ color: C.muted }}>Orchestration</div>
          <div className="flex flex-wrap justify-center gap-2.5">
            {[
              { name: "CSO", sub: "Opus", Icon: Brain, color: C.accent },
              { name: "Chief of Staff", sub: "Haiku", Icon: GitBranch, color: C.dim },
              { name: "Biosecurity", sub: "Sonnet", Icon: Shield, color: "#f87171" },
              { name: "Review Panel", sub: "Sonnet", Icon: Eye, color: C.warm },
            ].map((t) => (
              <div key={t.name} className="flex items-center gap-2 px-3 py-2 rounded-2xl border hover-lift"
                style={{ borderColor: C.border, background: C.surface }}>
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: t.color + "15" }}>
                  <t.Icon size={14} color={t.color} />
                </div>
                <div>
                  <div className="text-[13px] font-medium" style={{ color: C.text }}>{t.name}</div>
                  <div className="text-[10px] font-mono" style={{ color: C.muted }}>{t.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-center mb-8">
          <div className="w-px h-8" style={{ background: `linear-gradient(to bottom, ${C.accent}30, ${C.border})` }} />
        </div>

        {/* Divisions */}
        <div className="text-[10px] font-semibold uppercase tracking-widest mb-3 text-center" style={{ color: C.muted }}>Example SubLab — Drug Discovery</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {DIVISIONS.map((d, i) => (
            <button key={d.name}
              className={`text-left px-3.5 py-3.5 rounded-2xl border transition-all duration-200 hover-lift ${visible ? "animate-slide-up" : "opacity-0"}`}
              style={{ borderColor: expanded === i ? d.color + "50" : C.border, background: expanded === i ? d.color + "06" : C.surface, animationDelay: `${200 + i * 50}ms` }}
              onClick={() => setExpanded(expanded === i ? null : i)}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: d.color + "18" }}>
                    <d.Icon size={12} color={d.color} />
                  </div>
                  <span className="text-[13px] font-semibold" style={{ color: C.text }}>{d.name}</span>
                </div>
                <span className="text-[11px] font-mono px-1.5 py-0.5 rounded-md" style={{ background: d.color + "12", color: d.color }}>{d.agents}</span>
              </div>
              {expanded === i && (
                <div className="mt-2 pt-2 border-t space-y-1 animate-fade-in" style={{ borderColor: C.border }}>
                  {d.specialists.map(s => (
                    <div key={s} className="flex items-center gap-1.5 text-[11px]" style={{ color: C.dim }}>
                      <Bot size={10} color={d.color} />
                      <span className="font-mono">{s}</span>
                    </div>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}


/* ═══════════════════════════════════════════════════════════════
   HITL — Slack Integration Demo
   ═══════════════════════════════════════════════════════════════ */

function HITLSection() {
  const { ref, visible } = useInView(0.1);
  const [step, setStep] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [msgs, setMsgs] = useState<number[]>([]);
  const [approved, setApproved] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const clearTimers = () => timers.current.forEach(clearTimeout);

  const runSequence = useCallback(() => {
    clearTimers();
    setStep(0); setConfidence(0); setMsgs([]); setApproved(false);
    const seq = [
      { d: 800, fn: () => setStep(1) },
      { d: 1000, fn: () => { setStep(2); setConfidence(38); } },
      { d: 1500, fn: () => setStep(3) },
      { d: 1200, fn: () => { setStep(4); setMsgs([0]); } },
      { d: 2500, fn: () => setMsgs([0, 1]) },
      { d: 3000, fn: () => setMsgs([0, 1, 2]) },
      { d: 3000, fn: () => { setMsgs([0, 1, 2, 3]); setApproved(true); } },
      { d: 5000, fn: () => runSequence() },
    ];
    let cum = 0;
    seq.forEach(({ d, fn }) => { cum += d; timers.current.push(setTimeout(fn, cum)); });
  }, []);

  useEffect(() => {
    if (!visible) return;
    const t = setTimeout(runSequence, 500);
    return () => { clearTimeout(t); clearTimers(); };
  }, [visible, runSequence]);

  return (
    <section id="hitl" ref={ref} className="section">
      <div className="max-w-6xl mx-auto">
        <div className={`text-left mb-12 ${visible ? "animate-slide-up" : "opacity-0"}`}>
          <SectionLabel icon={MessageSquare} label="Human-in-the-Loop" />
          <h2 className="text-lg md:text-xl font-semibold" style={{ letterSpacing: "-0.01em" }}>
            Below-threshold findings route to experts via Slack.
          </h2>
        </div>

        <div className={`flex flex-col lg:flex-row gap-3 ${visible ? "animate-slide-up" : "opacity-0"}`} style={{ animationDelay: "100ms" }}>
          {/* Confidence routing */}
          <div className="lg:w-[300px] flex-shrink-0">
            <div className="demo-window" style={{ height: 420 }}>
              <div className="demo-chrome">
                <Activity size={13} color={C.warm} />
                <span className="text-[11px] font-mono" style={{ color: C.muted }}>Confidence Router</span>
              </div>
              <div className="px-4 py-4 space-y-4 overflow-y-auto" style={{ maxHeight: 370 }}>
                {step >= 1 && (
                  <div className="animate-slide-up">
                    <div className="text-[10px] font-semibold uppercase tracking-widest mb-1.5" style={{ color: C.muted }}>Flagged</div>
                    <div className="px-3 py-2.5 rounded-xl border text-[12px] leading-relaxed" style={{ borderColor: C.border, background: C.surface2, color: C.dim }}>
                      GLP-1 agonists show neuroprotective effects in tau pathology models
                    </div>
                  </div>
                )}
                {step >= 2 && (
                  <div className="animate-slide-up">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: C.muted }}>Confidence</span>
                      <span className="text-[13px] font-mono font-bold" style={{ color: confidence < 50 ? "#f87171" : C.accent }}>{confidence}%</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: C.surface2 }}>
                      <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${confidence}%`, background: confidence < 50 ? "#f87171" : C.accent }} />
                    </div>
                  </div>
                )}
                {step >= 3 && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-xl border animate-scale-in"
                    style={{ borderColor: "#f8717130", background: "#f8717108" }}>
                    <AlertTriangle size={13} color="#f87171" />
                    <span className="text-[12px] font-medium" style={{ color: "#f87171" }}>Below threshold</span>
                  </div>
                )}
                {step >= 4 && !approved && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-xl border animate-scale-in"
                    style={{ borderColor: `${C.warm}30`, background: `${C.warm}08` }}>
                    <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: C.warm }} />
                    <span className="text-[12px] font-medium" style={{ color: C.warm }}>Routing to expert...</span>
                  </div>
                )}
                {approved && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-xl border animate-scale-in"
                    style={{ borderColor: `${C.accent}30`, background: `${C.accent}08` }}>
                    <CheckCircle2 size={13} color={C.accent} />
                    <span className="text-[12px] font-medium" style={{ color: C.accent }}>Approved — 0.52</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Slack mock */}
          <div className="flex-1">
            <div className="demo-window" style={{ height: 420 }}>
              <div className="demo-chrome">
                <Hash size={13} color={C.dim} />
                <span className="text-[13px] font-medium" style={{ color: C.text }}>#expert-review</span>
                <div className="ml-auto flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: step >= 4 ? C.accent : C.muted }} />
                  <span className="text-[11px]" style={{ color: C.muted }}>{step >= 4 ? "Active" : "Idle"}</span>
                </div>
              </div>
              <div className="px-4 py-3 space-y-0.5 overflow-y-auto" style={{ height: 340 }}>
                {step < 4 && (
                  <div className="flex items-center justify-center h-[260px]">
                    <span className="text-[13px]" style={{ color: C.muted }}>Waiting for findings...</span>
                  </div>
                )}
                {msgs.map((mi) => {
                  const m = HITL_MSGS[mi];
                  const isLumi = m.role === "lumi";
                  return (
                    <div key={mi} className="slack-msg animate-slide-up">
                      <div className="slack-avatar" style={{ background: isLumi ? `${C.accent}18` : `${C.warm}18`, color: isLumi ? C.accent : C.warm }}>
                        {isLumi ? <Bot size={13} /> : "SC"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] font-semibold" style={{ color: C.text }}>{m.name}</span>
                          {m.title && <span className="text-[10px] px-1.5 py-0.5 rounded-md" style={{ background: C.surface2, color: C.muted }}>{m.title}</span>}
                        </div>
                        <div className="text-[12px] mt-1 leading-relaxed whitespace-pre-line" style={{ color: C.dim }}>{m.text}</div>
                        {mi === 3 && approved && (
                          <div className="inline-flex items-center gap-1.5 mt-2 px-2 py-1 rounded-lg text-[11px] font-medium animate-scale-in"
                            style={{ background: `${C.accent}12`, color: C.accent }}>
                            <CheckCircle2 size={11} /> Approved
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   VISUALIZATIONS
   ═══════════════════════════════════════════════════════════════ */

function PathwayViz() {
  const nodes = [
    { x: 200, y: 30, r: 18, label: "GLP-1R", color: "#a78bfa" },
    { x: 120, y: 100, r: 14, label: "cAMP", color: "#c4b5fd" },
    { x: 280, y: 100, r: 14, label: "PKA", color: "#c4b5fd" },
    { x: 80, y: 170, r: 12, label: "NF-\u03BAB", color: "#f87171" },
    { x: 160, y: 180, r: 12, label: "CREB", color: "#818cf8" },
    { x: 240, y: 170, r: 12, label: "Akt", color: "#93c5fd" },
    { x: 320, y: 170, r: 12, label: "GSK-3\u03B2", color: "#c084fc" },
    { x: 120, y: 240, r: 11, label: "Apoptosis", color: "#f87171" },
    { x: 200, y: 245, r: 11, label: "Survival", color: "#a78bfa" },
    { x: 290, y: 240, r: 11, label: "Tau-P", color: "#d8b4fe" },
  ];
  const edges = [[0,1],[0,2],[1,3],[1,4],[2,5],[2,6],[3,7],[4,8],[5,8],[6,9]];
  return (
    <svg viewBox="0 0 400 280" className="w-full h-full">
      {edges.map(([a,b], i) => (
        <line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y}
          stroke={C.border} strokeWidth={1.5} strokeDasharray="4 3">
          <animate attributeName="stroke-dashoffset" values="7;0" dur="2s" repeatCount="indefinite" />
        </line>
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.color + "18"} stroke={n.color + "50"} strokeWidth={1.5} />
          <text x={n.x} y={n.y + 3.5} textAnchor="middle" fill={n.color} fontSize={n.r > 14 ? 8 : 7} fontFamily="IBM Plex Mono" fontWeight={500}>{n.label}</text>
        </g>
      ))}
    </svg>
  );
}

function HeatmapViz() {
  const genes = ["GLP1R", "CREB1", "AKT1", "GSK3B", "MAPT", "BDNF", "TNF", "IL6"];
  const conditions = ["Ctrl", "Low", "Med", "High"];
  const data = [[.1,.3,.6,.9],[.2,.4,.7,.8],[.15,.35,.55,.75],[.8,.6,.3,.1],[.7,.5,.3,.15],[.1,.25,.5,.7],[.9,.7,.4,.2],[.85,.65,.35,.15]];
  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex mb-1 pl-14">
        {conditions.map(c => <div key={c} className="flex-1 text-center text-[9px] font-mono" style={{ color: C.muted }}>{c}</div>)}
      </div>
      <div className="flex flex-col gap-0.5 flex-1">
        {genes.map((g, gi) => (
          <div key={g} className="flex items-center gap-1 flex-1">
            <div className="w-12 text-right text-[9px] font-mono truncate" style={{ color: C.dim }}>{g}</div>
            {data[gi].map((v, ci) => <div key={ci} className="flex-1 rounded-sm h-full min-h-[18px]" style={{ background: `rgba(167,139,250,${v * 0.85 + 0.05})` }} />)}
          </div>
        ))}
      </div>
    </div>
  );
}

function AgentTimeline() {
  const agents = [
    { name: "pharmacologist", duration: 65, start: 0, color: "#a78bfa" },
    { name: "neuro_specialist", duration: 45, start: 5, color: "#c4b5fd" },
    { name: "safety_agent", duration: 55, start: 10, color: "#f87171" },
    { name: "lit_synthesis", duration: 40, start: 15, color: "#818cf8" },
    { name: "target_biologist", duration: 50, start: 8, color: "#c084fc" },
    { name: "clinical_trialist", duration: 60, start: 12, color: "#d8b4fe" },
  ];
  return (
    <div className="w-full h-full flex flex-col justify-center gap-1.5 py-2">
      {agents.map(a => (
        <div key={a.name} className="flex items-center gap-1.5">
          <div className="w-20 text-right text-[9px] font-mono truncate" style={{ color: C.dim }}>{a.name}</div>
          <div className="flex-1 h-4 rounded-sm relative" style={{ background: C.surface2 }}>
            <div className="absolute top-0 h-full rounded-sm" style={{
              left: `${a.start}%`, width: `${a.duration}%`, background: a.color + "35",
              borderLeft: `2px solid ${a.color}`,
              animation: "fill-bar 1s ease-out both",
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function VisualizationsSection() {
  const { ref, visible } = useInView(0.1);
  const vizCards = [
    { title: "Pathway Network", desc: "GLP-1R signaling cascade", Icon: Network, content: <PathwayViz /> },
    { title: "Expression Heatmap", desc: "Dose-response expression", Icon: BarChart3, content: <HeatmapViz /> },
    { title: "Agent Timeline", desc: "Parallel orchestration", Icon: Activity, content: <AgentTimeline /> },
  ];
  return (
    <section className="section">
      <div className="max-w-6xl mx-auto">
        <div className={`text-left mb-12 ${visible ? "animate-slide-up" : "opacity-0"}`}>
          <SectionLabel icon={Microscope} label="Visual Context" />
          <h2 className="text-lg md:text-xl font-semibold" style={{ letterSpacing: "-0.01em" }}>
            Pathway diagrams, expression data, agent timelines.
          </h2>
        </div>
        <div ref={ref} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {vizCards.map((v, i) => (
            <div key={v.title} className={`demo-window hover-lift ${visible ? "animate-slide-up" : "opacity-0"}`}
              style={{ animationDelay: `${i * 80}ms` }}>
              <div className="demo-chrome">
                <v.Icon size={13} color={C.accent} />
                <div>
                  <div className="text-[12px] font-medium" style={{ color: C.text }}>{v.title}</div>
                  <div className="text-[10px]" style={{ color: C.muted }}>{v.desc}</div>
                </div>
              </div>
              <div className="p-3.5" style={{ height: 220 }}>{v.content}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   RESULTS
   ═══════════════════════════════════════════════════════════════ */

function ResultSection() {
  const { ref, visible } = useInView(0.15);
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (!visible) return;
    setShown(0);
    const iv = setInterval(() => {
      setShown(prev => { if (prev >= REPORT_ITEMS.length) { clearInterval(iv); return prev; } return prev + 1; });
    }, 450);
    return () => clearInterval(iv);
  }, [visible]);

  const bc = (b?: string) => {
    if (b === "high") return { bg: `${C.accent}15`, color: C.accent };
    if (b === "medium") return { bg: `${C.warm}15`, color: C.warm };
    return { bg: "#f8717115", color: "#f87171" };
  };

  return (
    <section id="results" ref={ref} className="section">
      <div className="max-w-6xl mx-auto">
        <div className={`text-left mb-12 ${visible ? "animate-slide-up" : "opacity-0"}`}>
          <SectionLabel icon={FileText} label="Research Output" />
          <h2 className="text-lg md:text-xl font-semibold" style={{ letterSpacing: "-0.01em" }}>
            Confidence-scored findings with full provenance.
          </h2>
        </div>

        <div className={`demo-window max-w-2xl ${visible ? "animate-slide-up" : "opacity-0"}`} style={{ animationDelay: "100ms" }}>
          <div className="demo-chrome">
            <Sparkles size={13} color={C.accent} />
            <span className="text-[11px] font-mono" style={{ color: C.muted }}>research synthesis</span>
          </div>
          <div className="px-5 md:px-8 py-6 space-y-3">
            {REPORT_ITEMS.slice(0, shown).map((item, i) => {
              if (item.type === "title") return <h3 key={i} className="text-base md:text-lg font-semibold animate-slide-up" style={{ color: C.text, letterSpacing: "-0.01em" }}>{item.text}</h3>;
              if (item.type === "meta") return <div key={i} className="text-[11px] font-mono animate-slide-up" style={{ color: C.muted }}>{item.text}</div>;
              if (item.type === "heading") return <h4 key={i} className="text-[11px] font-semibold uppercase tracking-widest pt-2 animate-slide-up" style={{ color: C.accent }}>{item.text}</h4>;
              if (item.type === "body") return <p key={i} className="text-[13px] leading-relaxed animate-slide-up" style={{ color: C.dim }}>{item.text}</p>;
              if (item.type === "finding") {
                const b = bc(item.badge);
                return (
                  <div key={i} className="flex items-start gap-3 px-3.5 py-2.5 rounded-xl border animate-slide-up" style={{ borderColor: C.border, background: C.surface2 }}>
                    <div className="flex-1 min-w-0"><div className="text-[13px]" style={{ color: C.text }}>{item.text}</div></div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className="text-[11px] font-mono font-bold px-1.5 py-0.5 rounded-md" style={{ background: b.bg, color: b.color }}>{item.confidence?.toFixed(2)}</span>
                      {item.badge === "reviewed" && <span className="text-[9px] px-1.5 py-0.5 rounded-md font-medium" style={{ background: `${C.warm}12`, color: C.warm }}>HITL</span>}
                    </div>
                  </div>
                );
              }
              return null;
            })}
            {shown >= REPORT_ITEMS.length && (
              <div className="flex items-center gap-1.5 pt-2 text-[11px] font-mono animate-fade-in" style={{ color: C.accentDim }}>
                <ExternalLink size={11} /><span>47 sources · full provenance chain</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   CTA
   ═══════════════════════════════════════════════════════════════ */

function CTASection() {
  const { ref, visible } = useInView(0.3);
  return (
    <section id="cta" ref={ref} className="section">
      <div className={`max-w-xl mx-auto text-center ${visible ? "animate-slide-up" : "opacity-0"}`}>
        <p className="text-[13px] mb-8" style={{ color: C.dim }}>
          Deploy Lumi on your research pipeline.
        </p>
        <MagButton href="http://localhost:3001" accent>Sign In <ArrowRight size={15} /></MagButton>
      </div>
    </section>
  );
}


/* ═══════════════════════════════════════════════════════════════
   GSAP SCROLL REVEALS
   ═══════════════════════════════════════════════════════════════ */

function useGsapReveals() {
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(".reveal").forEach((el) => {
        gsap.fromTo(el, { y: 30, opacity: 0 }, {
          y: 0, opacity: 1, duration: 0.8, ease: "power3.out",
          scrollTrigger: { trigger: el, start: "top 88%" },
        });
      });
    });
    return () => ctx.revert();
  }, []);
}

/* ═══════════════════════════════════════════════════════════════
   MAIN
   ═══════════════════════════════════════════════════════════════ */

export default function LandingPage() {
  useGsapReveals();

  return (
    <div style={{ background: C.bg, minHeight: "100vh" }}>
      <NoiseOverlay />
      <Navbar />

      {/* Hero */}
      <section id="pipeline" className="relative z-[1] min-h-screen flex flex-col items-center justify-center px-6 pt-24 pb-12">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full pointer-events-none"
          style={{ background: "radial-gradient(ellipse, rgba(167,139,250,0.06) 0%, transparent 70%)" }} />

        <div className="relative w-full max-w-7xl mx-auto px-6">
          <div className="mb-8 text-left">
            <h2 className="text-lg md:text-xl font-semibold leading-snug tracking-tight max-w-lg"
              style={{ color: C.text }}>
              Lumi orchestrates your research, verifies every claim, and ships confident results.
            </h2>
            <div className="mt-4 flex items-center gap-2.5">
              <a href="http://localhost:3001" className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] font-semibold transition-colors duration-200 hover:opacity-90"
                style={{ background: C.accent, color: C.bg }}>
                See how it works <ArrowRight size={12} />
              </a>
              <a href="#results" className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] font-medium border transition-colors duration-200"
                style={{ borderColor: C.border, color: C.dim }}
                onMouseEnter={e => (e.currentTarget.style.background = C.surface2)}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                View output
              </a>
            </div>
          </div>

          <PipelineDemo />
        </div>
      </section>

      <AgentSection />
      <HITLSection />
      <VisualizationsSection />
      <ResultSection />
      <CTASection />
    </div>
  );
}
