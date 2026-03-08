interface Props {
  examples: string[];
  onSelect: (text: string) => void;
}

export function SuggestionChips({ examples, onSelect }: Props) {
  return (
    <div className="mt-4 flex flex-col gap-2">
      {examples.map((example, i) => (
        <button
          key={i}
          onClick={() => onSelect(example)}
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-card)] px-4 py-2.5 text-left text-sm text-[var(--text-secondary)] transition-colors hover:border-[var(--border-hover)] hover:bg-[var(--bg-hover)]"
        >
          {example}
        </button>
      ))}
    </div>
  );
}
