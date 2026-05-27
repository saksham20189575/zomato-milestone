"use client";

import { Minus, Plus, Sparkles } from "lucide-react";
import { useCallback, useState } from "react";
import type { BudgetUi, FormState } from "@/types";

const BUDGET_OPTIONS: BudgetUi[] = ["Budget", "Medium", "Premium"];

interface PreferenceFormProps {
  locations: string[];
  defaultLocation: string;
  loading: boolean;
  onSubmit: (form: FormState) => void;
}

export function PreferenceForm({
  locations,
  defaultLocation,
  loading,
  onSubmit,
}: PreferenceFormProps) {
  const [location, setLocation] = useState(defaultLocation);
  const [budget, setBudget] = useState<BudgetUi>("Medium");
  const [cuisine, setCuisine] = useState("");
  const [minRating, setMinRating] = useState(4.0);
  const [topK, setTopK] = useState(5);
  const [additional, setAdditional] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      onSubmit({ location, budget, cuisine, minRating, topK, additional });
    },
    [location, budget, cuisine, minRating, topK, additional, onSubmit],
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-[20px] border border-white/[0.08] bg-[rgba(22,22,28,0.85)] p-6 shadow-[0_24px_48px_rgba(0,0,0,0.35)] sm:p-7"
    >
      <div className="grid gap-6 md:grid-cols-2 md:gap-8">
        <div className="space-y-5">
          <Field label="Area">
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className={inputClass}
              required
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Budget range">
            <div className="flex gap-2">
              {BUDGET_OPTIONS.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setBudget(opt)}
                  className={`flex-1 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                    budget === opt
                      ? "border-gray-200 bg-gray-100 text-gray-900"
                      : "border-border-muted bg-surface-input text-gray-400 hover:border-gray-600"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Preferred cuisines">
            <input
              type="text"
              value={cuisine}
              onChange={(e) => setCuisine(e.target.value)}
              placeholder="Search or select cuisines… (e.g. Italian, North Indian)"
              className={inputClass}
            />
          </Field>
        </div>

        <div className="space-y-5">
          <Field label="Minimum rating">
            <div className="flex items-center gap-4">
              <input
                type="range"
                min={0}
                max={5}
                step={0.1}
                value={minRating}
                onChange={(e) => setMinRating(parseFloat(e.target.value))}
                className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-border-muted accent-accent"
              />
              <span className="min-w-[3.5rem] text-right text-lg font-semibold text-white">
                {minRating.toFixed(1)} ★
              </span>
            </div>
          </Field>

          <Field label="Number of results">
            <div className="flex items-center gap-0 overflow-hidden rounded-xl border border-border-muted bg-surface-input">
              <button
                type="button"
                onClick={() => setTopK((k) => Math.max(1, k - 1))}
                className="flex h-11 w-11 items-center justify-center text-gray-400 hover:bg-white/5 hover:text-white"
                aria-label="Decrease results"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="flex flex-1 items-center justify-center text-base font-medium text-white">
                {topK}
              </span>
              <button
                type="button"
                onClick={() => setTopK((k) => Math.min(20, k + 1))}
                className="flex h-11 w-11 items-center justify-center text-gray-400 hover:bg-white/5 hover:text-white"
                aria-label="Increase results"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </Field>

          <Field label="Additional preferences">
            <textarea
              value={additional}
              onChange={(e) => setAdditional(e.target.value)}
              placeholder="Describe your perfect dining experience…"
              rows={4}
              className={`${inputClass} resize-none`}
            />
          </Field>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-6 flex w-full items-center justify-center gap-2 rounded-[14px] bg-gradient-to-b from-[#f0f0f2] to-[#d4d4d8] py-3.5 text-base font-bold text-gray-900 shadow-[0_4px_20px_rgba(255,255,255,0.12)] transition hover:from-white hover:to-[#e4e4e7] disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Sparkles className="h-4 w-4" />
        {loading ? "Finding restaurants…" : "Get AI Recommendations"}
      </button>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-2 block text-[0.7rem] font-semibold uppercase tracking-[0.08em] text-gray-500">
        {label}
      </label>
      {children}
    </div>
  );
}

const inputClass =
  "w-full rounded-xl border border-border-muted bg-surface-input px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-600 focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/30";
