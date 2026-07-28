export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PromptRecord = {
  id: string;
  name: string;
  category: string;
  version: string;
  content: string;
  project_context?: string | null;
  target_model?: string | null;
  target_environment?: string | null;
  model_id?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ModelSettings = {
  provider: string | null;
  model_id: string | null;
  has_api_key: boolean;
  ollama_base_url: string | null;
  updated_at: string | null;
};

export async function api<T>(path: string, init?: RequestInit, adminPassword?: string): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (adminPassword) headers.set("X-Admin-Password", adminPassword);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? payload?.error?.message ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

