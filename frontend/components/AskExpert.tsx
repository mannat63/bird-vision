"use client";

import { useState } from "react";
import { askExpert } from "@/app/lib/api";
import Spinner from "./Spinner";

interface Turn {
  q: string;
  a: string | null;
  error?: string;
}

export default function AskExpert({
  speciesId,
  speciesName,
  suggestions,
}: {
  speciesId: number;
  speciesName: string;
  suggestions?: string[];
}) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);

  async function submit(q: string) {
    const query = q.trim();
    if (!query || busy) return;
    setBusy(true);
    setQuestion("");
    const idx = turns.length;
    setTurns((t) => [...t, { q: query, a: null }]);
    try {
      const res = await askExpert(speciesId, query);
      setTurns((t) =>
        t.map((turn, i) => (i === idx ? { ...turn, a: res.answer } : turn))
      );
    } catch (e) {
      setTurns((t) =>
        t.map((turn, i) =>
          i === idx
            ? {
                ...turn,
                a: null,
                error:
                  e instanceof Error ? e.message : "The expert is unavailable.",
              }
            : turn
        )
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-5 border-t border-forest-700/10 pt-4">
      <h4 className="font-serif text-lg text-forest-800">
        Ask the bird expert
      </h4>
      <p className="text-xs text-stone-warm mb-3">
        AI answers about {speciesName}. Not a substitute for a field guide.
      </p>

      {suggestions && suggestions.length > 0 && turns.length === 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="text-xs rounded-full border border-forest-700/20 px-3 py-1 text-forest-700 hover:bg-forest-700/5 transition"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="space-y-3 mb-3">
        {turns.map((t, i) => (
          <div key={i} className="text-sm">
            <p className="font-medium text-forest-800">· {t.q}</p>
            {t.a === null && !t.error && <Spinner />}
            {t.error && <p className="text-accent-clay">{t.error}</p>}
            {t.a && <p className="text-stone-deep mt-1">{t.a}</p>}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="flex gap-2"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What distinguishes it from similar species?"
          className="flex-1 rounded-lg border border-forest-700/20 bg-ivory-50 px-3 py-2 text-sm outline-none focus:border-forest-500"
          aria-label="Ask a question about this species"
        />
        <button
          type="submit"
          disabled={busy || !question.trim()}
          className="rounded-lg bg-forest-700 px-4 py-2 text-ivory-50 text-sm hover:bg-forest-600 transition disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
