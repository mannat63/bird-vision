export default function Spinner({ label }: { label?: string }) {
  return (
    <div
      className="flex items-center gap-3 text-forest-600"
      role="status"
      aria-live="polite"
    >
      <span
        className="spin inline-block h-5 w-5 rounded-full border-2 border-forest-400 border-t-transparent"
        aria-hidden
      />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
