export function LoadingState() {
  return (
    <div className="py-16 text-center">
      <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-[3px] border-border-muted border-t-accent" />
      <p className="text-gray-400">Finding and ranking restaurants…</p>
    </div>
  );
}
