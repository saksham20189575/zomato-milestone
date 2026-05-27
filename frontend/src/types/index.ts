export type BudgetApi = "low" | "medium" | "high";

export type BudgetUi = "Budget" | "Medium" | "Premium";

export const BUDGET_UI_TO_API: Record<BudgetUi, BudgetApi> = {
  Budget: "low",
  Medium: "medium",
  Premium: "high",
};

export interface RecommendationRequest {
  location: string;
  budget: BudgetApi;
  cuisine: string;
  min_rating: number;
  additional_preferences?: string | null;
  top_k: number;
}

export interface Restaurant {
  id: string;
  name: string;
  location: string;
  cuisines: string[];
  rating: number;
  estimated_cost: number;
  budget_band: string;
}

export interface Recommendation {
  rank: number;
  restaurant: Restaurant;
  explanation: string;
  match_percent: number;
}

export interface RecommendationResponse {
  summary: string | null;
  recommendations: Recommendation[];
  meta: Record<string, unknown>;
}

export interface FormState {
  location: string;
  budget: BudgetUi;
  cuisine: string;
  minRating: number;
  topK: number;
  additional: string;
}
