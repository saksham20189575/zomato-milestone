import type { RecommendationRequest, RecommendationResponse } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* use statusText */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }

  return res.json() as Promise<T>;
}

export async function fetchLocations(): Promise<string[]> {
  const data = await request<{ locations: string[] }>("/api/v1/metadata/locations");
  return data.locations;
}

export async function fetchRecommendations(
  body: RecommendationRequest,
): Promise<RecommendationResponse> {
  return request<RecommendationResponse>("/api/v1/recommendations", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function checkHealth(): Promise<boolean> {
  try {
    const data = await request<{ status: string }>("/api/v1/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}
