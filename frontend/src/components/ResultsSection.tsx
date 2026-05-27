import type { RecommendationResponse } from "@/types";
import { RestaurantCard } from "./RestaurantCard";

interface ResultsSectionProps {
  response: RecommendationResponse;
}

export function ResultsSection({ response }: ResultsSectionProps) {
  const { summary, recommendations, meta } = response;

  if (recommendations.length === 0) {
    return (
      <div className="py-16 text-center">
        <h3 className="text-lg font-semibold text-gray-300">No restaurants match</h3>
        <p className="mt-2 text-gray-500">
          Try relaxing your area, cuisine, minimum rating, or budget.
        </p>
      </div>
    );
  }

  return (
    <section className="mt-10">
      {Boolean(meta.fallback_used) && (
        <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          AI ranking was unavailable — showing top-rated matches from your filters.
        </div>
      )}

      {summary && (
        <div className="mb-6 rounded-xl border border-accent/25 bg-accent-muted px-5 py-4 text-sm leading-relaxed text-cyan-100/90">
          {summary}
        </div>
      )}

      <h2 className="mb-5 text-2xl font-bold tracking-tight text-white">Your recommendations</h2>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {recommendations.map((rec) => (
          <RestaurantCard key={rec.restaurant.id + rec.rank} recommendation={rec} />
        ))}
      </div>

      <details className="mt-8 rounded-xl border border-border bg-surface-card px-4 py-3 text-sm text-gray-400">
        <summary className="cursor-pointer font-medium text-gray-300">Search details</summary>
        <dl className="mt-3 space-y-1">
          <div>
            <dt className="inline font-medium text-gray-500">Candidates considered: </dt>
            <dd className="inline">{String(meta.candidates_considered ?? "—")}</dd>
          </div>
          <div>
            <dt className="inline font-medium text-gray-500">Sent to AI: </dt>
            <dd className="inline">{String(meta.candidates_sent_to_llm ?? "—")}</dd>
          </div>
          <div>
            <dt className="inline font-medium text-gray-500">Filter time: </dt>
            <dd className="inline">{String(meta.filter_latency_ms ?? "—")} ms</dd>
          </div>
          <div>
            <dt className="inline font-medium text-gray-500">AI time: </dt>
            <dd className="inline">{String(meta.llm_latency_ms ?? "—")} ms</dd>
          </div>
        </dl>
      </details>
    </section>
  );
}
