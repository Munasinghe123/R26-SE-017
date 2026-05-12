/* ============================================================
   API Client — communicates with the FastAPI backend
   ============================================================ */

import type { GenerateRequest, GenerateResponse, HealthResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    let detail = `HTTP ${res.status}`;
    try {
      const json = JSON.parse(body);
      detail = json.detail || detail;
    } catch {
      /* plain text error */
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

/** Check backend health */
export function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

/** Generate LLD diagrams from custom input */
export function generateLLD(data: GenerateRequest): Promise<GenerateResponse> {
  return request<GenerateResponse>("/api/generate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Generate diagrams using sample data by index */
export function generateSample(sampleId: number): Promise<GenerateResponse> {
  return request<GenerateResponse>(`/api/generate/sample/${sampleId}`, {
    method: "POST",
  });
}
