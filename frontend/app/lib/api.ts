import type {
  Gradcam,
  Metrics,
  ModelInfo,
  Observations,
  Prediction,
  Species,
  SpeciesIntel,
  SpeciesSightings,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || body.error || body.message || detail;
    } catch {
      /* non-JSON error */
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

export async function getModelInfo(): Promise<ModelInfo> {
  return handle(await fetch(`${BASE}/api/model-info`, { cache: "no-store" }));
}

export async function getMetrics(): Promise<Metrics> {
  return handle(await fetch(`${BASE}/api/metrics`, { cache: "no-store" }));
}

export async function predict(file: File): Promise<Prediction> {
  const fd = new FormData();
  fd.append("file", file);
  return handle(await fetch(`${BASE}/api/predict`, { method: "POST", body: fd }));
}

export async function explain(file: File): Promise<Gradcam> {
  const fd = new FormData();
  fd.append("file", file);
  return handle(await fetch(`${BASE}/api/explain`, { method: "POST", body: fd }));
}

export async function getSpecies(id: number): Promise<Species> {
  return handle(await fetch(`${BASE}/api/species/${id}`, { cache: "no-store" }));
}

export async function getSpeciesIntel(id: number): Promise<SpeciesIntel> {
  return handle(
    await fetch(`${BASE}/api/species/${id}/intel`, { cache: "no-store" })
  );
}

export async function askExpert(
  id: number,
  question: string
): Promise<{ answer: string; _disclaimer: string }> {
  return handle(
    await fetch(`${BASE}/api/species/${id}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
  );
}

export async function getNearby(
  lat: number,
  lng: number,
  dist = 25,
  back = 14
): Promise<Observations> {
  const q = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    dist: String(dist),
    back: String(back),
    max_results: "50",
  });
  return handle(
    await fetch(`${BASE}/api/observations/nearby?${q}`, { cache: "no-store" })
  );
}

export async function getSpeciesSightings(
  id: number,
  lat: number,
  lng: number,
  dist = 25,
  back = 14
): Promise<SpeciesSightings> {
  const q = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    dist: String(dist),
    back: String(back),
  });
  return handle(
    await fetch(`${BASE}/api/species/${id}/sightings?${q}`, {
      cache: "no-store",
    })
  );
}

export { BASE as API_BASE };
