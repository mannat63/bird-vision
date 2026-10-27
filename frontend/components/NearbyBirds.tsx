"use client";

import { useEffect, useState } from "react";
import { getSpeciesSightings } from "@/app/lib/api";
import type { SpeciesSightings } from "@/app/lib/types";
import Spinner from "./Spinner";

const PRESETS = [
  { name: "Boston, US", lat: 42.3601, lng: -71.0589 },
  { name: "London, UK", lat: 51.5074, lng: -0.1278 },
  { name: "Bengaluru, IN", lat: 12.9716, lng: 77.5946 },
  { name: "Sydney, AU", lat: -33.8688, lng: 151.2093 },
];

export default function NearbyBirds({
  speciesId,
  speciesName,
}: {
  speciesId: number;
  speciesName: string;
}) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<SpeciesSightings | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [dist, setDist] = useState(25);
  const [back, setBack] = useState(14);
  const [manual, setManual] = useState({ lat: "", lng: "" });
  const [lastCenter, setLastCenter] = useState<{ lat: number; lng: number } | null>(
    null
  );

  // Invalidate all results when the identified species changes (P5).
  useEffect(() => {
    setData(null);
    setStatus(null);
    setLastCenter(null);
  }, [speciesId]);

  async function search(lat: number, lng: number, radius = dist, days = back) {
    setLoading(true);
    setStatus(null);
    setData(null);
    setLastCenter({ lat, lng });
    try {
      setData(await getSpeciesSightings(speciesId, lat, lng, radius, days));
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function useMyLocation() {
    setStatus(null);
    if (!navigator.geolocation) {
      setStatus("Geolocation is not supported by this browser.");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => search(pos.coords.latitude, pos.coords.longitude),
      (err) => {
        setLoading(false);
        setStatus(
          err.code === err.PERMISSION_DENIED
            ? "Location permission denied. Use a preset or enter coordinates manually."
            : "Could not determine your location."
        );
      },
      { timeout: 10000 }
    );
  }

  function searchManual() {
    const lat = parseFloat(manual.lat);
    const lng = parseFloat(manual.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      setStatus("Enter valid numeric latitude and longitude.");
      return;
    }
    search(lat, lng);
  }

  function broaden() {
    if (!lastCenter) return;
    const newDist = Math.min(50, dist + 25);
    const newBack = Math.min(30, back + 14);
    setDist(newDist);
    setBack(newBack);
    search(lastCenter.lat, lastCenter.lng, newDist, newBack);
  }

  return (
    <section className="rounded-2xl border border-forest-700/10 bg-ivory-100/50 p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-serif text-xl text-forest-800">
            Where can I see this {speciesName} near me?
          </h3>
          <p className="text-sm text-stone-warm">
            Recent community-reported eBird sightings of{" "}
            <span className="italic">this exact species</span>, plus birding hotspots.
          </p>
        </div>
        <button
          onClick={() => setOpen((o) => !o)}
          className="rounded-lg bg-forest-700 px-4 py-2 text-ivory-50 text-sm hover:bg-forest-600 transition shrink-0"
        >
          {open ? "Hide" : "Find sightings"}
        </button>
      </div>

      {open && (
        <div className="mt-4 fade-in space-y-4">
          {/* Species filter chip tied to the current identification */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs rounded-full bg-forest-500/10 px-3 py-1 text-forest-700">
              🔎 Searching for: <strong>{speciesName}</strong>
            </span>
          </div>

          <p className="text-xs text-stone-warm">
            Location is optional and only requested when you choose “Use my location”.
            Coordinates are sent to eBird to fetch sightings and are not stored.
          </p>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={useMyLocation}
              className="rounded-lg border border-forest-700/30 px-3 py-2 text-forest-700 text-sm hover:bg-forest-700/5 transition"
            >
              📍 Use my location
            </button>
            {PRESETS.map((p) => (
              <button
                key={p.name}
                onClick={() => search(p.lat, p.lng)}
                className="rounded-lg border border-forest-700/20 px-3 py-2 text-forest-700 text-sm hover:bg-forest-700/5 transition"
              >
                {p.name}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <label className="text-sm">
              <span className="block text-xs text-stone-warm">Latitude</span>
              <input
                value={manual.lat}
                onChange={(e) => setManual((m) => ({ ...m, lat: e.target.value }))}
                className="w-28 rounded-lg border border-forest-700/20 bg-ivory-50 px-2 py-1.5 outline-none focus:border-forest-500"
                placeholder="latitude"
              />
            </label>
            <label className="text-sm">
              <span className="block text-xs text-stone-warm">Longitude</span>
              <input
                value={manual.lng}
                onChange={(e) => setManual((m) => ({ ...m, lng: e.target.value }))}
                className="w-28 rounded-lg border border-forest-700/20 bg-ivory-50 px-2 py-1.5 outline-none focus:border-forest-500"
                placeholder="longitude"
              />
            </label>
            <label className="text-sm">
              <span className="block text-xs text-stone-warm">Radius: {dist} km</span>
              <input
                type="range"
                min={1}
                max={50}
                value={dist}
                onChange={(e) => setDist(Number(e.target.value))}
                className="w-32 accent-forest-600"
              />
            </label>
            <label className="text-sm">
              <span className="block text-xs text-stone-warm">Last {back} days</span>
              <input
                type="range"
                min={1}
                max={30}
                value={back}
                onChange={(e) => setBack(Number(e.target.value))}
                className="w-32 accent-forest-600"
              />
            </label>
            <button
              onClick={searchManual}
              className="rounded-lg bg-forest-700 px-4 py-2 text-ivory-50 text-sm hover:bg-forest-600 transition"
            >
              Search
            </button>
          </div>

          {loading && <Spinner label={`Searching eBird for ${speciesName}…`} />}
          {status && (
            <p role="alert" className="text-sm text-accent-clay bg-accent-clay/10 rounded-lg px-3 py-2">
              {status}
            </p>
          )}

          {/* What was actually searched (P3 integrity) */}
          {data && (
            <p className="text-xs text-stone-warm">
              Searched center{" "}
              <strong className="tabular-nums">
                {data.search_center.lat.toFixed(4)}, {data.search_center.lng.toFixed(4)}
              </strong>{" "}
              · radius {data.radius_km} km · last {data.back_days} days
              {data.species_code && <> · eBird taxon <code>{data.species_code}</code></>}
            </p>
          )}

          {data?.status === "unresolved" && (
            <p className="text-sm text-stone-deep bg-accent-gold/15 rounded-lg px-3 py-2">
              {data.message}
            </p>
          )}
          {data?.status === "unavailable" && (
            <p className="text-sm text-stone-deep bg-accent-gold/15 rounded-lg px-3 py-2">
              {data.message} — this is an API/config issue, not “no birds here”.
            </p>
          )}

          {/* Recent wild sightings */}
          {data?.status === "ok" && (
            <div>
              <h4 className="font-serif text-lg text-forest-800">
                Recent wild sightings ({data.sighting_count})
              </h4>
              <p className="text-[11px] text-stone-warm mb-2">
                Community-reported to eBird — not guaranteed current sightings.
              </p>
              <ul className="divide-y divide-forest-700/10 rounded-xl border border-forest-700/10 overflow-hidden">
                {data.sightings.slice(0, 15).map((o, i) => (
                  <li key={`${o.checklist_id}-${i}`} className="px-4 py-3 bg-ivory-50/60">
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="text-forest-800">
                        {o.location_name || "Unnamed location"}
                      </span>
                      <span className="text-xs text-stone-warm tabular-nums shrink-0">
                        {o.distance_km != null ? `${o.distance_km} km` : ""}
                      </span>
                    </div>
                    <p className="text-xs text-stone-deep mt-0.5">
                      {o.observed_at}
                      {o.count ? ` · count ${o.count}` : ""}
                      {o.map_url && (
                        <>
                          {" · "}
                          <a
                            href={o.map_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-forest-600 underline"
                          >
                            directions ↗
                          </a>
                        </>
                      )}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data?.status === "empty" && (
            <div className="space-y-2">
              <p className="text-sm text-stone-deep">{data.message}</p>
              {lastCenter && (dist < 50 || back < 30) && (
                <button
                  onClick={broaden}
                  className="rounded-lg border border-forest-700/30 px-4 py-2 text-forest-700 text-sm hover:bg-forest-700/5 transition"
                >
                  Broaden search (wider radius &amp; longer window)
                </button>
              )}
            </div>
          )}

          {/* Birding hotspots */}
          {data && (data.status === "ok" || data.status === "empty") && data.hotspots.length > 0 && (
            <div>
              <h4 className="font-serif text-lg text-forest-800">
                Nearby birding hotspots
              </h4>
              <p className="text-[11px] text-stone-warm mb-2">
                General eBird hotspots near the search center. A ✓ marks hotspots where this
                species was in the recent reports above — otherwise treat as a general
                birding spot, not proof the species is present.
              </p>
              <ul className="divide-y divide-forest-700/10 rounded-xl border border-forest-700/10 overflow-hidden">
                {data.hotspots.slice(0, 10).map((h) => (
                  <li key={h.location_id} className="px-4 py-3 bg-ivory-50/60">
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="text-forest-800">
                        {h.has_recent_species && (
                          <span className="text-forest-600 mr-1" title="recently reported here">
                            ✓
                          </span>
                        )}
                        {h.name}
                      </span>
                      <span className="text-xs text-stone-warm tabular-nums shrink-0">
                        {h.distance_km != null ? `${h.distance_km} km` : ""}
                      </span>
                    </div>
                    <p className="text-xs text-stone-deep mt-0.5">
                      {h.num_species_all_time != null
                        ? `${h.num_species_all_time} species all-time`
                        : ""}
                      {h.latest_obs_dt ? ` · latest ${h.latest_obs_dt}` : ""}
                      {h.map_url && (
                        <>
                          {" · "}
                          <a
                            href={h.map_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-forest-600 underline"
                          >
                            directions ↗
                          </a>
                        </>
                      )}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data && (
            <p className="text-[11px] text-stone-warm">
              {data.captive_note} Observation data © eBird (Cornell Lab of Ornithology).
            </p>
          )}
        </div>
      )}
    </section>
  );
}
