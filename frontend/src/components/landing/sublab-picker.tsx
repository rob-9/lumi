import type { SublabInfo } from "@/lib/types";
import clsx from "clsx";

interface Props {
  sublabs: Record<string, SublabInfo>;
  selected: string;
  onSelect: (id: string) => void;
}

export function SublabPicker({ sublabs, selected, onSelect }: Props) {
  const entries = Object.entries(sublabs);
  if (!entries.length) return null;

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {entries.map(([id, info]) => (
        <button
          key={id}
          onClick={() => onSelect(id)}
          className={clsx(
            "rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
            id === selected
              ? "border-[var(--accent)] bg-[var(--accent)] text-white"
              : "border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:bg-[var(--bg-hover)]"
          )}
        >
          {info.name}
        </button>
      ))}
    </div>
  );
}
