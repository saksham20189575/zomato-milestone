import type { Restaurant } from "@/types";

const BUDGET_LABELS: Record<string, string> = {
  low: "Budget",
  medium: "Medium",
  high: "Premium",
};

export function formatCost(cost: number): string {
  return `₹${Math.round(cost).toLocaleString("en-IN")} for two`;
}

export function formatBudgetBand(band: string): string {
  return BUDGET_LABELS[band] ?? band;
}

export function truncateLocation(location: string, max = 22): string {
  if (location.length <= max) return location;
  return `${location.slice(0, max - 3).trim()}...`;
}
