export interface Candidate {
  species_id: number;
  label: string;
  common_name: string;
  scientific_name: string | null;
  scientific_name_verified: boolean;
  score: number;
}

export interface Prediction {
  prediction_id: string;
  model_version: string;
  top_prediction: Candidate;
  candidates: Candidate[];
  confident: boolean;
  confidence_status: string;
  confidence_note: string;
  inference_ms: number;
}

export interface ModelInfo {
  model_name: string;
  model_version: string;
  available: boolean;
  load_error: string | null;
  num_classes: number;
  input_size: number[];
  preprocessing: Record<string, unknown>;
  dataset_slug: string | null;
  tensorflow_version: string | null;
  parameter_count: number | null;
  artifact_size_mb: number | null;
}

export interface Species {
  species_id: number;
  label: string;
  common_name: string;
  scientific_name: string | null;
  scientific_name_verified: boolean;
  taxonomy_source: string;
}

export interface Gradcam {
  species_id: number;
  common_name: string;
  original_png: string;
  overlay_png: string;
  heatmap_png: string;
  note: string;
}

export interface SpeciesIntel {
  overview: string;
  physical_features: string[];
  habitat: string;
  diet: string;
  behavior: string;
  interesting_facts: string[];
  conservation: string;
  follow_up_questions: string[];
  _disclaimer: string;
}

export interface Observation {
  species_code: string | null;
  common_name: string | null;
  scientific_name: string | null;
  location_name: string | null;
  location_id: string | null;
  observed_at: string | null;
  count: number | null;
  latitude: number | null;
  longitude: number | null;
  distance_km: number | null;
  observation_valid: boolean | null;
  observation_reviewed: boolean | null;
  location_private: boolean | null;
  checklist_id: string | null;
  map_url: string | null;
  source: string;
  source_url: string;
}

export interface SearchCenter {
  lat: number;
  lng: number;
}

export interface Observations {
  status: "ok" | "empty" | "unavailable";
  count: number;
  observations: Observation[];
  message: string | null;
  search_center: SearchCenter;
  radius_km: number;
  back_days: number;
  query: Record<string, number>;
}

export interface Hotspot {
  location_id: string | null;
  name: string | null;
  latitude: number | null;
  longitude: number | null;
  num_species_all_time: number | null;
  latest_obs_dt: string | null;
  distance_km: number | null;
  has_recent_species: boolean;
  map_url: string | null;
  source: string;
}

export interface SpeciesSightings {
  status: "ok" | "empty" | "unavailable" | "unresolved";
  species_id: number;
  common_name: string;
  scientific_name: string | null;
  species_code: string | null;
  search_center: SearchCenter;
  radius_km: number;
  back_days: number;
  sighting_count: number;
  sightings: Observation[];
  hotspots: Hotspot[];
  message: string | null;
  captive_note: string;
}

export interface Metrics {
  status: string;
  model_name?: string;
  num_classes?: number;
  train_images?: number;
  validation_images?: number;
  test_images?: number;
  test_top1_accuracy?: number;
  test_top5_accuracy?: number;
  macro_precision?: number;
  macro_recall?: number;
  macro_f1?: number;
  weighted_f1?: number;
  single_image_latency_ms_mean?: number;
  single_image_latency_ms_p95?: number;
  tensorflow_version?: string;
  dataset_slug?: string;
  input_size?: number[];
  message?: string;
}
