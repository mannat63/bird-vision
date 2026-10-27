"use client";

import { useState } from "react";
import { explain } from "@/app/lib/api";
import type { Gradcam as GradcamData } from "@/app/lib/types";
import Spinner from "./Spinner";

export default function Gradcam({ file }: { file: File }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<GradcamData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggle() {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (data || loading) return;
    setLoading(true);
    setError(null);
    try {
      setData(await explain(file));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Grad-CAM failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-forest-700/10 bg-ivory-100/50 p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-serif text-xl text-forest-800">
            Model attention (Grad-CAM)
          </h3>
          <p className="text-sm text-stone-warm">
            See which regions drove the prediction.
          </p>
        </div>
        <button
          onClick={toggle}
          aria-expanded={open}
          className="rounded-lg bg-forest-700 px-4 py-2 text-ivory-50 text-sm hover:bg-forest-600 transition shrink-0"
        >
          {open ? "Hide" : "Show heatmap"}
        </button>
      </div>

      {open && (
        <div className="mt-4 fade-in">
          {loading && <Spinner label="Computing attention map…" />}
          {error && (
            <p role="alert" className="text-sm text-accent-clay">
              {error} — the prediction above is unaffected.
            </p>
          )}
          {data && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  ["Original", data.original_png],
                  ["Heatmap", data.heatmap_png],
                  ["Overlay", data.overlay_png],
                ].map(([label, src]) => (
                  <figure key={label}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={src}
                      alt={`${label} for ${data.common_name}`}
                      className="w-full rounded-lg border border-forest-700/10"
                    />
                    <figcaption className="text-xs text-center text-stone-warm mt-1">
                      {label}
                    </figcaption>
                  </figure>
                ))}
              </div>
              <p className="mt-3 text-[11px] leading-relaxed text-stone-warm">
                {data.note}
              </p>
            </>
          )}
        </div>
      )}
    </section>
  );
}
