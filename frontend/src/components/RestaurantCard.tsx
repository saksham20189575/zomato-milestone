import { Heart, MapPin, Sparkles, Star, UtensilsCrossed } from "lucide-react";
import type { Recommendation } from "@/types";
import { formatBudgetBand, formatCost, truncateLocation } from "@/lib/format";

interface RestaurantCardProps {
  recommendation: Recommendation;
}

export function RestaurantCard({ recommendation }: RestaurantCardProps) {
  const { restaurant, rank, explanation, match_percent: matchPercent } = recommendation;

  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-surface-card p-4 transition hover:border-[#3a3a48] hover:shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
      <div className="mb-1 flex items-start justify-between">
        <span className="text-[0.65rem] font-semibold uppercase tracking-wider text-gray-500">
          Rank #{rank}
        </span>
        <span className="rounded-md border border-accent/35 bg-accent-muted px-2 py-0.5 text-[0.6rem] font-bold tracking-wide text-accent">
          {matchPercent}% MATCH
        </span>
      </div>

      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-lg font-bold tracking-tight text-white">{restaurant.name}</h3>
        <button
          type="button"
          className="text-gray-600 transition hover:text-gray-400"
          aria-label="Save restaurant"
        >
          <Heart className="h-5 w-5" strokeWidth={1.5} />
        </button>
      </div>

      <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-400">
        <span className="inline-flex items-center gap-1">
          <Star className="h-3.5 w-3.5 fill-accent text-accent" />
          {restaurant.rating.toFixed(1)}
        </span>
        <span className="inline-flex items-center gap-1">
          <UtensilsCrossed className="h-3.5 w-3.5" />
          {formatBudgetBand(restaurant.budget_band)}
        </span>
      </div>

      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-sm">
        <span className="inline-flex items-center gap-1 text-gray-400">
          <MapPin className="h-3.5 w-3.5 shrink-0" />
          {truncateLocation(restaurant.location)}
        </span>
        <span className="font-semibold text-accent">{formatCost(restaurant.estimated_cost)}</span>
      </div>

      <div className="mb-3 flex flex-wrap gap-1.5">
        {restaurant.cuisines.slice(0, 6).map((c) => (
          <span
            key={c}
            className="rounded-md border border-border-muted bg-surface-elevated px-2 py-0.5 text-[0.68rem] text-gray-400"
          >
            {c.toLowerCase()}
          </span>
        ))}
        {restaurant.cuisines.length > 6 && (
          <span className="rounded-md border border-border-muted bg-surface-elevated px-2 py-0.5 text-[0.68rem] text-gray-500">
            +{restaurant.cuisines.length - 6}
          </span>
        )}
      </div>

      <div className="mt-auto rounded-xl border border-[#1f1f28] bg-[#0e0e14] p-3">
        <div className="mb-2 flex items-center gap-1.5 text-[0.6rem] font-bold uppercase tracking-wider text-gray-500">
          <Sparkles className="h-3 w-3" />
          Why AI picked it
        </div>
        <p className="text-[0.78rem] italic leading-relaxed text-gray-400">&ldquo;{explanation}&rdquo;</p>
      </div>
    </article>
  );
}
