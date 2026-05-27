"use client";

import { useCallback, useEffect, useState } from "react";
import { Hero } from "@/components/Hero";
import { LoadingState } from "@/components/LoadingState";
import { Nav } from "@/components/Nav";
import { PreferenceForm } from "@/components/PreferenceForm";
import { ResultsSection } from "@/components/ResultsSection";
import { fetchLocations, fetchRecommendations } from "@/lib/api";
import type { FormState, RecommendationResponse } from "@/types";
import { BUDGET_UI_TO_API } from "@/types";

type PageStatus = "idle" | "loading" | "results" | "error";

export default function HomePage() {
  const [locations, setLocations] = useState<string[]>([]);
  const [locationsError, setLocationsError] = useState<string | null>(null);
  const [status, setStatus] = useState<PageStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<RecommendationResponse | null>(null);

  useEffect(() => {
    fetchLocations()
      .then(setLocations)
      .catch((e) => setLocationsError(e instanceof Error ? e.message : "Failed to load areas"));
  }, []);

  const defaultLocation =
    locations.find((l) => l.toLowerCase() === "bellandur") ?? locations[0] ?? "Bellandur";

  const handleSubmit = useCallback(async (form: FormState) => {
    setError(null);
    setStatus("loading");
    setResponse(null);

    const cuisine = form.cuisine.trim() || "Indian";

    try {
      const result = await fetchRecommendations({
        location: form.location,
        budget: BUDGET_UI_TO_API[form.budget],
        cuisine,
        min_rating: form.minRating,
        additional_preferences: form.additional.trim() || null,
        top_k: form.topK,
      });
      setResponse(result);
      setStatus("results");
      window.scrollTo({ top: document.body.scrollHeight * 0.35, behavior: "smooth" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setStatus("error");
    }
  }, []);

  return (
    <main className="mx-auto min-h-screen max-w-[1100px] px-4 py-8 pb-16 sm:px-6">
      <Nav />
      <Hero />

      {locationsError && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {locationsError}. Is the API running at{" "}
          {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}?
        </div>
      )}

      {locations.length > 0 && (
        <PreferenceForm
          locations={locations}
          defaultLocation={defaultLocation}
          loading={status === "loading"}
          onSubmit={handleSubmit}
        />
      )}

      {status === "loading" && <LoadingState />}

      {status === "error" && error && (
        <div className="mt-8 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {status === "results" && response && <ResultsSection response={response} />}
    </main>
  );
}
