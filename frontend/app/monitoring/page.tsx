"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { RunRow, Summary } from "@/lib/types";

export default function MonitoringPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api<Summary>("/monitoring/summary"), api<RunRow[]>("/monitoring/runs")])
      .then(([cards, rows]) => {
        setSummary(cards);
        setRuns(rows);
      })
      .catch((exc: Error) => setError(exc.message));
  }, []);

  const errors = runs.filter((run) => run.status === "failed" || run.error);

  return (
    <section>
      <h1>Monitoring</h1>
      <p className="lede">Counts come from your usage ledger: status, latency, step count, and estimated tokens.</p>
      {error ? <p className="error">{error}</p> : null}
      {summary ? (
        <div className="stats">
          <article className="card"><span className="muted">Runs</span><strong>{summary.run_count}</strong></article>
          <article className="card"><span className="muted">Success rate</span><strong>{Math.round(summary.success_rate * 100)}%</strong></article>
          <article className="card"><span className="muted">p50 latency</span><strong>{summary.p50_latency_ms} ms</strong></article>
          <article className="card"><span className="muted">p95 latency</span><strong>{summary.p95_latency_ms} ms</strong></article>
        </div>
      ) : null}
      <article className="panel" style={{ marginTop: 16 }}>
        <h2>Errors</h2>
        {errors.length === 0 ? <p className="muted">No failed runs.</p> : null}
        {errors.map((run) => (
          <p key={run.id}>
            <strong>{run.agent_name}</strong> · {run.error || run.status}
          </p>
        ))}
      </article>
    </section>
  );
}
