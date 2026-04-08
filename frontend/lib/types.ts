export type ListingCard = {
  slug: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  install_count: number;
  rating: number | null;
  review_count: number;
  tool_names: string[];
};

export type Review = {
  id: number;
  rating: number;
  comment: string;
  author: string;
  created_at: string;
};

export type ListingDetail = ListingCard & {
  system_prompt: string;
  model: string;
  temperature: number | null;
  max_steps: number | null;
  memory_enabled: boolean;
  reviews: Review[];
};

export type AgentVersion = {
  id: number;
  version_number: number;
  system_prompt: string;
  model: string;
  temperature: number;
  max_steps: number;
  tool_names: string[];
  memory_enabled: boolean;
  created_at: string | null;
};

export type AgentSummary = {
  id: number;
  name: string;
  slug: string;
  description: string;
  status: string;
  updated_at: string | null;
  latest_version: number | null;
};

export type AgentDetail = AgentSummary & {
  versions: AgentVersion[];
  listing: {
    slug: string;
    category: string;
    tags: string[];
    install_count: number;
    version_id: number;
  } | null;
};

export type Summary = {
  run_count: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
};

export type RunRow = {
  id: number;
  thread_id: number;
  agent_name: string;
  status: string;
  latency_ms: number;
  step_count: number;
  estimated_tokens: number;
  error: string | null;
  created_at: string | null;
};

export type TestCase = {
  id: number;
  name: string;
  input_text: string;
  expected_tool: string | null;
  expected_phrase: string | null;
  last_passed: boolean | null;
  last_detail: string | null;
};

export type TestSuite = {
  id: number;
  name: string;
  cases: TestCase[];
};

export type SuiteResult = {
  total: number;
  passed: number;
  results: {
    case_id: number;
    name: string;
    passed: boolean;
    latency_ms: number;
    detail: string;
  }[];
};

export const TOOL_OPTIONS = ["calculator", "clock", "notes", "knowledge_search"] as const;
