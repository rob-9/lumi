export default function NotFound() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-lg font-semibold text-[var(--text)]">Not found</h2>
        <p className="mt-1 text-sm text-[var(--text-muted)]">This page doesn't exist.</p>
        <a href="/" className="mt-4 inline-block text-sm text-[var(--accent)] hover:underline">
          Back to Lumi
        </a>
      </div>
    </div>
  );
}
