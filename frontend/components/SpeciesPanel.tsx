"use client";

import { useEffect, useState } from "react";
import { getSpecies, getSpeciesIntel } from "@/app/lib/api";
import type { Species, SpeciesIntel } from "@/app/lib/types";
import Spinner from "./Spinner";
import AskExpert from "./AskExpert";

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-stone-warm">{label}</dt>
      <dd className="text-sm text-forest-800 mt-0.5">
        {value && value.trim() ? value : <span className="text-stone-warm">Not available</span>}
      </dd>
    </div>
  );
}

export default function SpeciesPanel({ speciesId }: { speciesId: number }) {
  const [species, setSpecies] = useState<Species | null>(null);
  const [intel, setIntel] = useState<SpeciesIntel | null>(null);
  const [loadingIntel, setLoadingIntel] = useState(false);
  const [intelError, setIntelError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setSpecies(null);
    setIntel(null);
    setIntelError(null);
    getSpecies(speciesId)
      .then((s) => active && setSpecies(s))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [speciesId]);

  async function loadIntel() {
    setLoadingIntel(true);
    setIntelError(null);
    try {
      setIntel(await getSpeciesIntel(speciesId));
    } catch (e) {
      setIntelError(
        e instanceof Error ? e.message : "AI enrichment is unavailable right now."
      );
    } finally {
      setLoadingIntel(false);
    }
  }

  if (!species) return <Spinner label="Loading species details…" />;

  return (
    <section className="rounded-2xl border border-forest-700/10 bg-ivory-100/50 p-5 fade-in">
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <div>
          <h3 className="font-serif text-2xl text-forest-800">
            {species.common_name}
          </h3>
          {species.scientific_name ? (
            <p className="italic text-stone-warm">
              {species.scientific_name}
              <span className="not-italic ml-2 text-[11px] rounded-full bg-forest-500/10 px-2 py-0.5 text-forest-600">
                verified
              </span>
            </p>
          ) : (
            <p className="text-sm text-stone-warm">
              Scientific name not verified for this dataset label
            </p>
          )}
        </div>
      </div>

      <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-3 mt-4">
        <Field label="Dataset label" value={species.label} />
        <Field label="Taxonomy source" value={species.taxonomy_source} />
      </dl>

      {/* AI enrichment (Groq), clearly labeled as AI-generated */}
      <div className="mt-5 border-t border-forest-700/10 pt-4">
        {!intel && !loadingIntel && (
          <button
            onClick={loadIntel}
            className="rounded-lg bg-forest-700 px-4 py-2 text-ivory-50 text-sm hover:bg-forest-600 transition"
          >
            ✨ Generate AI species intelligence
          </button>
        )}
        {loadingIntel && <Spinner label="Generating AI species intelligence…" />}
        {intelError && (
          <div
            role="alert"
            className="text-sm text-stone-deep bg-accent-clay/10 rounded-lg px-3 py-2 flex items-center justify-between gap-3 flex-wrap"
          >
            <span>{intelError}</span>
            <button
              onClick={loadIntel}
              className="rounded-lg bg-forest-700 px-3 py-1.5 text-ivory-50 text-xs hover:bg-forest-600 transition shrink-0"
            >
              ↻ Retry
            </button>
          </div>
        )}
        {intel && (
          <div className="fade-in space-y-3">
            <span className="inline-block text-[11px] rounded-full bg-accent-gold/20 px-2 py-0.5 text-stone-deep">
              AI-generated enrichment
            </span>
            <p className="text-sm text-forest-800">{intel.overview}</p>
            <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-3">
              <Field label="Habitat" value={intel.habitat} />
              <Field label="Diet" value={intel.diet} />
              <Field label="Behavior" value={intel.behavior} />
              <Field label="Conservation" value={intel.conservation} />
            </dl>
            {intel.interesting_facts?.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-stone-warm">
                  Interesting facts
                </p>
                <ul className="list-disc list-inside text-sm text-forest-800 mt-1">
                  {intel.interesting_facts.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-[11px] text-stone-warm">{intel._disclaimer}</p>
          </div>
        )}
      </div>

      <AskExpert
        speciesId={speciesId}
        speciesName={species.common_name}
        suggestions={intel?.follow_up_questions}
      />
    </section>
  );
}
