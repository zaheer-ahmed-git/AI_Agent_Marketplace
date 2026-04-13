"use client";

import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";

import { api, streamRun } from "@/lib/api";

type TraceLine = { id: number; text: string };

export default function PlaygroundPage() {
  const params = useParams<{ id: string }>();
  const [threadId, setThreadId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [answer, setAnswer] = useState("");
  const [trace, setTrace] = useState<TraceLine[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function ensureThread(): Promise<number> {
    if (threadId) {
      return threadId;
    }
    const created = await api<{ id: number }>(`/agents/${params.id}/threads`, {
      method: "POST",
      body: JSON.stringify({ title: "Playground" }),
    });
    setThreadId(created.id);
    return created.id;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setAnswer("");
    setTrace([]);
    try {
      const id = await ensureThread();
      let next = 0;
      await streamRun(id, message, (eventName, data) => {
        if (eventName === "token" && typeof data.text === "string") {
          setAnswer((current) => current + data.text);
        }
        if (eventName === "node" && typeof data.node === "string") {
          const toolNames = Array.isArray(data.tool_calls)
            ? data.tool_calls.map((call) => String((call as { name?: string }).name || "")).filter(Boolean)
            : [];
          const results = Array.isArray(data.tools)
            ? data.tools.map((tool) => String((tool as { name?: string }).name || "")).filter(Boolean)
            : [];
          const extra = [...toolNames, ...results].join(", ");
          const text = extra ? `${data.node}: ${extra}` : data.node;
          const lineId = next;
          next += 1;
          setTrace((current) => [...current, { id: lineId, text }]);
        }
        if (eventName === "done" && data.status === "failed") {
          setError(String(data.error || "Run failed"));
        }
      });
      setMessage("");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="split">
      <form className="panel stack" onSubmit={onSubmit}>
        <h1>Playground</h1>
        <p className="muted">Tokens stream from the API. The trace lists each graph node.</p>
        <label>
          Message
          <textarea value={message} onChange={(event) => setMessage(event.target.value)} />
        </label>
        <button type="submit" disabled={busy}>{busy ? "Running..." : "Send"}</button>
        {error ? <p className="error">{error}</p> : null}
        <div className="chat">
          <p>{answer || "The reply will appear here."}</p>
        </div>
      </form>
      <aside className="panel">
        <h2>Step trace</h2>
        <div className="trace">
          {trace.length === 0 ? <p className="muted">No steps yet.</p> : null}
          {trace.map((line) => (
            <div key={line.id}>{line.text}</div>
          ))}
        </div>
      </aside>
    </section>
  );
}
