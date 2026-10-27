"use client";

import type { Candidate, Prediction } from "@/app/lib/types";

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`;
}

function CandidateRow({
  c,
  primary,
  onSelect,
  selected,
}: {
  c: Candidate;
  primary?: boolean;
  onSelect: () => void;
  selected: boolean;
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left rounded-xl px-4 py-3 transition border ${
        selected
          ? "border-forest-500 bg-forest-500/5"
          : "border-transparent hover:bg-forest-700/[0.03]"
      }`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span
          className={`${
            primary ? "font-serif text-lg text-forest-800" : "text-forest-700"
          }`}
        >
          {c.common_name}
        </span>
        <span className="text-sm tabular-nums text-stone-deep">{pct(c.score)}</span>
      </div>
      {c.scientific_name ? (
        <span className="text-xs italic text-stone-warm">{c.scientific_name}</span>
      ) : (
        <span className="text-xs text-stone-warm">
          scientific name not verified
        </span>
      )}
      <div className="mt-2 h-1.5 w-full rounded-full bg-forest-700/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-forest-500"
          style={{ width: `${Math.max(2, c.score * 100)}%` }}
        />
      </div>
    </button>
  );
}

export default function ResultCard({
  prediction,
  previewUrl,
  selectedId,
  onSelect,
}: {
  prediction: Prediction;
  previewUrl: string;
  selectedId: number;
  onSelect: (id: number) => void;
}) {
  const uncertain = !prediction.confident;

  return (
    <div className="fade-in grid md:grid-cols-[1fr_1.1fr] gap-6">
      <div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={previewUrl}
          alt="Uploaded bird"
          className="w-full rounded-2xl object-cover shadow-soft max-h-[420px]"
        />
        <p className="mt-2 text-xs text-stone-warm">
          Model {prediction.model_version} · inference{" "}
          {prediction.inference_ms.toFixed(0)} ms
        </p>
      </div>

      <div>
        {uncertain ? (
          <div className="rounded-xl bg-accent-gold/15 border border-accent-gold/40 px-4 py-3 mb-4">
            <p className="font-semibold text-stone-deep">
              Unable to identify reliably
            </p>
            <p className="text-sm text-stone-deep/80 mt-1">
              {prediction.confidence_note}
            </p>
          </div>
        ) : (
          <div className="mb-4">
            <p className="text-xs uppercase tracking-wide text-stone-warm">
              Top prediction
            </p>
            <h2 className="font-serif text-3xl text-forest-800 leading-tight">
              {prediction.top_prediction.common_name}
            </h2>
            {prediction.top_prediction.scientific_name && (
              <p className="italic text-stone-warm">
                {prediction.top_prediction.scientific_name}
              </p>
            )}
          </div>
        )}

        <p className="text-xs uppercase tracking-wide text-stone-warm mb-1">
          {uncertain ? "Closest candidates" : "Top-3 candidates"}
        </p>
        <div className="space-y-1">
          {prediction.candidates.map((c, i) => (
            <CandidateRow
              key={c.species_id}
              c={c}
              primary={i === 0 && !uncertain}
              selected={c.species_id === selectedId}
              onSelect={() => onSelect(c.species_id)}
            />
          ))}
        </div>

        <p className="mt-3 text-[11px] leading-relaxed text-stone-warm">
          {prediction.confidence_note}
        </p>
      </div>
    </div>
  );
}
