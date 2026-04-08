export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function apiUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${base.replace(/\/$/, "")}${path}`;
}

function errorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object" || !("detail" in data)) {
    return fallback;
  }
  const detail = (data as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .join(", ");
  }
  return fallback;
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = window.localStorage.getItem("token");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(apiUrl(path), { ...options, headers });
  const text = await response.text();
  const data = text ? (JSON.parse(text) as unknown) : null;
  if (response.status === 401 && !path.startsWith("/auth/login")) {
    window.localStorage.removeItem("token");
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(data, response.statusText));
  }
  return data as T;
}

export async function streamRun(
  threadId: number,
  message: string,
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const token = window.localStorage.getItem("token");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(apiUrl(`/threads/${threadId}/runs`), {
    method: "POST",
    headers,
    body: JSON.stringify({ message }),
  });
  if (!response.ok || !response.body) {
    const text = await response.text();
    throw new ApiError(response.status, text || response.statusText);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      let event = "message";
      const dataLines: string[] = [];
      for (const line of chunk.split("\n")) {
        if (line.startsWith("event:")) {
          event = line.slice(6).trim();
        }
        if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trim());
        }
      }
      if (dataLines.length > 0) {
        onEvent(event, JSON.parse(dataLines.join("\n")) as Record<string, unknown>);
      }
    }
  }
}
