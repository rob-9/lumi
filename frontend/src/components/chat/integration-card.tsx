import type { IntegrationCall } from "@/lib/types";
import { CheckCircle2 } from "lucide-react";

interface Props {
  call: IntegrationCall;
}

export function IntegrationCard({ call }: Props) {
  return (
    <div className="rounded-lg border border-[var(--accent)] border-opacity-30 bg-[var(--accent-light)] px-4 py-2.5 text-sm animate-slide-up hover-lift">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={13} className="text-[var(--accent)] shrink-0" />
          <span className="font-medium text-xs text-[var(--accent-dark)]">{call.integration}</span>
          <span className="text-xs text-[var(--text-secondary)]">{call.action}</span>
        </div>
        <span className="rounded-full bg-[var(--accent)] px-2 py-0.5 text-[10px] font-medium text-white">
          {call.status}
        </span>
      </div>
      {call.detail && (
        <p className="mt-1 text-[11px] text-[var(--text-muted)] pl-[21px]">{call.detail}</p>
      )}
    </div>
  );
}
