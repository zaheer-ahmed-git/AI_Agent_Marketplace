"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AgentSummary } from "@/lib/types";

export default function StudioPage() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<AgentSummary[]>("/agents")
      .then(setAgents)
      .catch((exc: Error) => setError(exc.message));
  }, []);

  return (
    <section>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>Studio</h1>
        <Link className="button" href="/studio/new">New agent</Link>
      </div>
      <p className="lede">Drafts stay private until you publish a version to the catalog.</p>
      {error ? <p className="error">{error}</p> : null}
      <div className="grid">
        {agents.map((agent) => (
          <article key={agent.id} className="card">
            <span className="pill">{agent.status}</span>
            <h2>{agent.name}</h2>
            <p>{agent.description || "No description yet."}</p>
            <p className="meta">Version {agent.latest_version ?? "—"}</p>
            <div className="actions">
              <Link href={`/studio/${agent.id}`}>Configure</Link>
              <Link href={`/studio/${agent.id}/playground`}>Playground</Link>
              <Link href={`/studio/${agent.id}/tests`}>Tests</Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
