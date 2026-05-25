import type { CanvasGraph, CanvasResponse, RunResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function createCanvas(name = "Research pipeline"): Promise<CanvasResponse> {
  return request<CanvasResponse>("/canvases", {
    method: "POST",
    body: JSON.stringify({ name, graph: null }),
  });
}

export async function updateCanvas(id: string, graph: CanvasGraph): Promise<CanvasResponse> {
  return request<CanvasResponse>(`/canvases/${id}`, {
    method: "PUT",
    body: JSON.stringify(graph),
  });
}

export async function startRun(canvasId: string): Promise<RunResponse> {
  return request<RunResponse>("/runs", {
    method: "POST",
    body: JSON.stringify({ canvas_id: canvasId }),
  });
}

export async function startSwarmRun(useDemoPlan = true): Promise<RunResponse> {
  return request<RunResponse>("/swarm/runs", {
    method: "POST",
    body: JSON.stringify({ use_demo_plan: useDemoPlan }),
  });
}

export async function resumeRun(runId: string): Promise<RunResponse> {
  return request<RunResponse>(`/runs/${runId}/resume`, { method: "POST" });
}

export function runEventsUrl(runId: string): string {
  return `${API_URL}/runs/${runId}/events`;
}

export async function getBlockOutput(runId: string, blockId: string) {
  return request<{
    block_id: string;
    output_ref: string;
    content: string | null;
    title: string;
  }>(`/runs/${runId}/blocks/${blockId}/output`);
}

export function artifactDownloadUrl(runId: string, artifactId: string): string {
  return `${API_URL}/runs/${runId}/artifacts/${artifactId}`;
}

export async function startPlanning(brief: string, userId = "default") {
  return request<{
    session_id: string;
    status: string;
    clarifications: string[];
    plan: unknown;
    canvas_preview: unknown;
  }>("/planning/sessions", {
    method: "POST",
    body: JSON.stringify({ brief, user_id: userId }),
  });
}

export async function confirmPlan(sessionId: string, plan?: unknown) {
  return request<{ run_id: string; status: string }>(
    `/planning/sessions/${sessionId}/confirm`,
    {
      method: "POST",
      body: JSON.stringify({ plan }),
    }
  );
}

export async function listConnectors() {
  return request<{ id: string; name: string; capabilities: string[] }[]>("/connectors");
}
