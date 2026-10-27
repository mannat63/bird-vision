"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/Header";
import Spinner from "@/components/Spinner";
import { getMetrics, getModelInfo } from "@/app/lib/api";
import type { Metrics, ModelInfo } from "@/app/lib/types";

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-forest-700/10 bg-ivory-100/50 p-4">
      <p className="text-xs uppercase tracking-wide text-stone-warm">{label}</p>
      <p className="font-serif text-2xl text-forest-800 mt-1">{value}</p>
      {sub && <p className="text-[11px] text-stone-warm mt-0.5">{sub}</p>}
    </div>
  );
}

interface PerClass {
  name: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export default function Insights() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [perClass, setPerClass] = useState<PerClass[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [sortWorst, setSortWorst] = useState(true);

  useEffect(() => {
    Promise.allSettled([getMetrics(), getModelInfo()]).then(([m, i]) => {
      if (m.status === "fulfilled") setMetrics(m.value);
      if (i.status === "fulfilled") setInfo(i.value);
      setLoaded(true);
    });
    fetch("/insights/classification_report.csv")
      .then((r) => r.text())
      .then((text) => {
        const rows = text.trim().split("\n").slice(1);
        const parsed: PerClass[] = [];
        for (const row of rows) {
          const [name, p, rc, f1, sup] = row.split(",");
          if (["accuracy", "macro avg", "weighted avg"].includes(name)) continue;
          parsed.push({
            name: name.replace(/^\d+\./, "").replace(/_/g, " "),
            precision: parseFloat(p),
            recall: parseFloat(rc),
            f1: parseFloat(f1),
            support: parseFloat(sup),
          });
        }
        setPerClass(parsed);
      })
      .catch(() => {});
  }, []);

  const sorted = useMemo(
    () =>
      [...perClass].sort((a, b) => (sortWorst ? a.f1 - b.f1 : b.f1 - a.f1)),
    [perClass, sortWorst]
  );

  const pct = (n?: number) => (n == null ? "—" : `${(n * 100).toFixed(1)}%`);

  return (
    <>
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:py-12">
        <h1 className="font-serif text-3xl sm:text-4xl text-forest-800">
          Model Insights
        </h1>
        <p className="mt-2 text-stone-deep max-w-2xl">
          Every figure below comes from a real evaluation artifact produced on
          the held-out CUB-200-2011 test set — nothing here is illustrative.
        </p>

        {!loaded && <div className="mt-8"><Spinner label="Loading metrics…" /></div>}

        {metrics?.status === "not_evaluated" && (
          <p className="mt-6 rounded-xl bg-accent-gold/15 px-4 py-3 text-sm">
            Not yet evaluated — no metrics artifact was found on the server.
          </p>
        )}

        {metrics && metrics.status === "ok" && (
          <>
            {/* Headline metrics */}
            <section className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Stat label="Test top-1" value={pct(metrics.test_top1_accuracy)}
                sub="held-out test set" />
              <Stat label="Test top-5" value={pct(metrics.test_top5_accuracy)} />
              <Stat label="Macro F1" value={pct(metrics.macro_f1)} />
              <Stat label="Weighted F1" value={pct(metrics.weighted_f1)} />
            </section>

            <section className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Stat label="Macro precision" value={pct(metrics.macro_precision)} />
              <Stat label="Macro recall" value={pct(metrics.macro_recall)} />
              <Stat
                label="Inference latency"
                value={
                  metrics.single_image_latency_ms_mean
                    ? `${metrics.single_image_latency_ms_mean.toFixed(0)} ms`
                    : "—"
                }
                sub={
                  metrics.single_image_latency_ms_p95
                    ? `p95 ${metrics.single_image_latency_ms_p95.toFixed(0)} ms`
                    : undefined
                }
              />
              <Stat
                label="Model size"
                value={info?.artifact_size_mb ? `${info.artifact_size_mb} MB` : "—"}
                sub={
                  info?.parameter_count
                    ? `${(info.parameter_count / 1e6).toFixed(1)}M params`
                    : undefined
                }
              />
            </section>

            {/* Architecture / dataset */}
            <section className="mt-8 grid md:grid-cols-2 gap-6">
              <div className="rounded-xl border border-forest-700/10 bg-ivory-100/50 p-5">
                <h2 className="font-serif text-xl text-forest-800">Architecture</h2>
                <dl className="mt-3 text-sm space-y-2">
                  <div className="flex justify-between"><dt className="text-stone-warm">Model</dt><dd>{metrics.model_name} (transfer learning)</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">Version</dt><dd>{info?.model_version ?? "—"}</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">Input</dt><dd>{(metrics.input_size ?? [224,224,3]).join(" × ")}</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">Classes</dt><dd>{metrics.num_classes}</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">TensorFlow</dt><dd>{metrics.tensorflow_version}</dd></div>
                </dl>
              </div>
              <div className="rounded-xl border border-forest-700/10 bg-ivory-100/50 p-5">
                <h2 className="font-serif text-xl text-forest-800">Dataset &amp; splits</h2>
                <dl className="mt-3 text-sm space-y-2">
                  <div className="flex justify-between"><dt className="text-stone-warm">Dataset</dt><dd>CUB-200-2011</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">Train</dt><dd>{metrics.train_images?.toLocaleString()}</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">Validation</dt><dd>{metrics.validation_images?.toLocaleString()}</dd></div>
                  <div className="flex justify-between"><dt className="text-stone-warm">Test (held-out)</dt><dd>{metrics.test_images?.toLocaleString()}</dd></div>
                </dl>
                <p className="mt-3 text-[11px] text-stone-warm">
                  Source mirror: {metrics.dataset_slug}
                </p>
              </div>
            </section>

            {/* Plots */}
            <section className="mt-8 grid md:grid-cols-2 gap-6">
              <figure className="rounded-xl border border-forest-700/10 bg-ivory-100/50 p-4">
                <figcaption className="font-serif text-lg text-forest-800 mb-2">Training &amp; validation curves</figcaption>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/insights/training_curves.png" alt="Training and validation curves" className="w-full rounded-lg" />
              </figure>
              <figure className="rounded-xl border border-forest-700/10 bg-ivory-100/50 p-4">
                <figcaption className="font-serif text-lg text-forest-800 mb-2">Confusion matrix (top classes)</figcaption>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/insights/confusion_matrix_top_classes.png" alt="Confusion matrix for top classes" className="w-full rounded-lg" />
              </figure>
            </section>

            <figure className="mt-6 rounded-xl border border-forest-700/10 bg-ivory-100/50 p-4 max-w-xl">
              <figcaption className="font-serif text-lg text-forest-800 mb-2">Grad-CAM example</figcaption>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/insights/gradcam_example.png" alt="Grad-CAM example" className="w-full rounded-lg" />
            </figure>

            {/* Per-class */}
            {sorted.length > 0 && (
              <section className="mt-8">
                <div className="flex items-center justify-between">
                  <h2 className="font-serif text-xl text-forest-800">Per-class performance</h2>
                  <button
                    onClick={() => setSortWorst((s) => !s)}
                    className="text-sm rounded-lg border border-forest-700/20 px-3 py-1.5 text-forest-700 hover:bg-forest-700/5"
                  >
                    {sortWorst ? "Showing weakest first" : "Showing strongest first"}
                  </button>
                </div>
                <div className="mt-3 overflow-x-auto rounded-xl border border-forest-700/10">
                  <table className="w-full text-sm">
                    <thead className="bg-forest-700/5 text-stone-deep">
                      <tr>
                        <th className="text-left px-4 py-2">Species</th>
                        <th className="text-right px-4 py-2">Precision</th>
                        <th className="text-right px-4 py-2">Recall</th>
                        <th className="text-right px-4 py-2">F1</th>
                        <th className="text-right px-4 py-2">Support</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sorted.slice(0, 20).map((c) => (
                        <tr key={c.name} className="odd:bg-ivory-50/60 border-t border-forest-700/5">
                          <td className="px-4 py-2 text-forest-800">{c.name}</td>
                          <td className="px-4 py-2 text-right tabular-nums">{pct(c.precision)}</td>
                          <td className="px-4 py-2 text-right tabular-nums">{pct(c.recall)}</td>
                          <td className="px-4 py-2 text-right tabular-nums">{pct(c.f1)}</td>
                          <td className="px-4 py-2 text-right tabular-nums">{c.support}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-2 text-[11px] text-stone-warm">
                  Showing 20 of {perClass.length} classes. Full per-class report in
                  classification_report.csv.
                </p>
              </section>
            )}

            {/* Limitations */}
            <section className="mt-8 rounded-xl border border-accent-gold/40 bg-accent-gold/10 p-5">
              <h2 className="font-serif text-xl text-forest-800">Known limitations</h2>
              <ul className="mt-2 text-sm text-stone-deep list-disc list-inside space-y-1">
                <li>
                  ~19-point train/validation gap indicates some overfitting; test
                  top-1 is {pct(metrics.test_top1_accuracy)}.
                </li>
                <li>
                  Softmax scores are uncalibrated — treat them as relative, not as
                  true probabilities.
                </li>
                <li>
                  The abstention threshold does not guarantee out-of-distribution
                  detection for non-bird or unsupported species.
                </li>
                <li>
                  Trained on 200 North-American-centric species; other species
                  will be misclassified as the nearest known class.
                </li>
                <li>
                  Visually similar species (e.g. albatrosses, gulls, sparrows) are
                  the most common confusions.
                </li>
              </ul>
            </section>
          </>
        )}
      </main>
      <div className="h-10" />
    </>
  );
}
