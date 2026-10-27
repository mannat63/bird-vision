"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import UploadZone from "@/components/UploadZone";
import ResultCard from "@/components/ResultCard";
import Gradcam from "@/components/Gradcam";
import SpeciesPanel from "@/components/SpeciesPanel";
import NearbyBirds from "@/components/NearbyBirds";
import Spinner from "@/components/Spinner";
import { getModelInfo, predict } from "@/app/lib/api";
import type { ModelInfo, Prediction } from "@/app/lib/types";

export default function Home() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [modelDown, setModelDown] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getModelInfo()
      .then((info) => {
        setModelInfo(info);
        setModelDown(!info.available);
      })
      .catch(() => setModelDown(true));
  }, []);

  async function handleFile(f: File, url: string) {
    // Clear any stale result before running a new request.
    setFile(f);
    setPreviewUrl(url);
    setPrediction(null);
    setSelectedId(null);
    setError(null);
    setLoading(true);
    try {
      const result = await predict(f);
      setPrediction(result);
      setSelectedId(result.top_prediction.species_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setPreviewUrl(null);
    setPrediction(null);
    setSelectedId(null);
    setError(null);
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:py-12">
        {/* Hero */}
        {!prediction && !loading && (
          <section className="text-center mb-8 fade-in">
            <h1 className="font-serif text-4xl sm:text-5xl text-forest-800 text-balance">
              Identify the wild.
            </h1>
            <p className="mt-3 text-stone-deep max-w-xl mx-auto">
              Upload a bird photograph and a trained EfficientNetB0 convolutional
              network returns a real species prediction — with confidence,
              explainability, and genuine nearby observations.
            </p>
          </section>
        )}

        {modelDown && (
          <div
            role="alert"
            className="mb-6 rounded-xl bg-accent-clay/10 border border-accent-clay/30 px-4 py-3 text-sm text-stone-deep"
          >
            <strong>Model unavailable.</strong> The inference service is not
            serving the CNN right now
            {modelInfo?.load_error ? `: ${modelInfo.load_error}` : ""}. Uploads
            are disabled until it recovers — no predictions are faked.
          </div>
        )}

        {/* Upload */}
        {!prediction && (
          <section className="max-w-2xl mx-auto">
            <UploadZone onFile={handleFile} disabled={loading || modelDown} />
            <div className="mt-4 text-center text-xs text-stone-warm">
              <p>
                3-step process: upload → the Python backend runs the CNN → you
                get the top species, alternatives and a confidence reading.
              </p>
            </div>
          </section>
        )}

        {loading && (
          <section className="max-w-2xl mx-auto mt-8 flex flex-col items-center gap-4">
            {previewUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewUrl}
                alt="Uploaded bird"
                className="w-56 rounded-2xl object-cover shadow-soft"
              />
            )}
            <Spinner label="Running CNN inference…" />
          </section>
        )}

        {error && !loading && (
          <div
            role="alert"
            className="max-w-2xl mx-auto mt-6 rounded-xl bg-accent-clay/10 border border-accent-clay/30 px-4 py-3 text-sm text-stone-deep"
          >
            {error}
            <button onClick={reset} className="ml-3 underline">
              Try another image
            </button>
          </div>
        )}

        {/* Results */}
        {prediction && previewUrl && selectedId !== null && (
          <section className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="font-serif text-2xl text-forest-800">
                Identification
              </h2>
              <button
                onClick={reset}
                className="rounded-lg border border-forest-700/30 px-4 py-2 text-forest-700 text-sm hover:bg-forest-700/5 transition"
              >
                ↺ New photo
              </button>
            </div>

            <ResultCard
              prediction={prediction}
              previewUrl={previewUrl}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />

            {file && <Gradcam key={prediction.prediction_id} file={file} />}
            <SpeciesPanel speciesId={selectedId} />
            <NearbyBirds
              speciesId={selectedId}
              speciesName={
                prediction.candidates.find((c) => c.species_id === selectedId)
                  ?.common_name ?? prediction.top_prediction.common_name
              }
            />
          </section>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 py-10 text-center text-xs text-stone-warm">
        BirdVision AI · EfficientNetB0 on CUB-200-2011 · predictions are a
        machine-learning model&apos;s best guess, not expert verification.
      </footer>
    </>
  );
}
