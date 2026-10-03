export interface User {
  id: string;
  name: string;
  email: string;
}
export interface Task {
  id: string;
  title: string;
  category: string;
  difficulty: string;
  prompt: string;
  starter: string;
  test_count: number;
  examples: [unknown, unknown][];
}
export interface Agent {
  id: string;
  name: string;
  kind: string;
  description: string;
  available: boolean;
}
export interface Catalog {
  version: string;
  tasks: Task[];
  agents: Agent[];
  runner_mode: string;
  provider_requires_docker: boolean;
}
export interface Run {
  id: string;
  name: string;
  agent: string;
  repeats: number;
  suite_version: string;
  suite_hash: string;
  state: string;
  created: number;
  finished: number | null;
  error: string | null;
  cancel_requested: boolean;
  completed_trials: number;
  expected_trials: number;
  passed: number;
  total: number;
  score: number | null;
  median_latency_ms: number | null;
  cost_usd: string | null;
  failed_trials: number;
}
export interface Case {
  index: number;
  passed: boolean;
  expected?: unknown;
  actual?: unknown;
  error?: string;
  mutated_input?: boolean;
}
export interface Trial {
  id: string;
  task_id: string;
  repeat: number;
  state: string;
  passed: number;
  total: number;
  generation_ms: number | null;
  execution_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: string | null;
  model: string | null;
  source: string | null;
  source_hash: string | null;
  cases: Case[];
  error: string | null;
}
export interface Detail extends Run {
  tasks: Task[];
  trials: Trial[];
}
export interface RunPage {
  items: Run[];
  total: number;
  page: number;
  size: number;
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-AgentBench-Request": "browser",
    },
    body: method === "GET" ? undefined : JSON.stringify(body ?? {}),
  });
  if (!response.ok) {
    if (response.status === 401 && path != "/auth/login")
      window.dispatchEvent(new Event("agentbench:expired"));
    const error = await response
      .json()
      .catch(() => ({ detail: "Request failed" }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Check the submitted fields",
    );
  }
  return response.json();
}
export function errorMessage(e: unknown) {
  return e instanceof Error ? e.message : "Something went wrong";
}
