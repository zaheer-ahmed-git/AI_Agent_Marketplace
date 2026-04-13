"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { api } from "@/lib/api";
import { TOOL_OPTIONS, type AgentDetail } from "@/lib/types";

export default function AgentEditorPage() {
  const params = useParams<{ id: string }>();
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [model, setModel] = useState("gpt-4o-mini");
  const [temperature, setTemperature] = useState("0.2");
  const [maxSteps, setMaxSteps] = useState("6");
  const [memory, setMemory] = useState(true);
  const [tools, setTools] = useState<string[]>([]);
  const [category, setCategory] = useState("productivity");
  const [tags, setTags] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api<AgentDetail>(`/agents/${params.id}`)
      .then((row) => {
        const latest = row.versions[row.versions.length - 1];
        setAgent(row);
        setName(row.name);
        setDescription(row.description);
        if (latest) {
          setSystemPrompt(latest.system_prompt);
          setModel(latest.model);
          setTemperature(String(latest.temperature));
          setMaxSteps(String(latest.max_steps));
          setMemory(latest.memory_enabled);
          setTools(latest.tool_names);
        }
        if (row.listing) {
          setCategory(row.listing.category);
          setTags(row.listing.tags.join(", "));
          setSlug(row.listing.slug);
        }
      })
      .catch((exc: Error) => setError(exc.message));
  }, [params.id]);

  function toggleTool(tool: string) {
    setTools((current) => (current.includes(tool) ? current.filter((item) => item !== tool) : [...current, tool]));
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    const row = await api<AgentDetail>(`/agents/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify({ name, description }),
    });
    setAgent(row);
    setNotice("Name and description saved.");
  }

  async function saveVersion(event: FormEvent) {
    event.preventDefault();
    await api(`/agents/${params.id}/versions`, {
      method: "POST",
      body: JSON.stringify({
        system_prompt: systemPrompt,
        model,
        temperature: Number(temperature),
        max_steps: Number(maxSteps),
        tool_names: tools,
        memory_enabled: memory,
      }),
    });
    const row = await api<AgentDetail>(`/agents/${params.id}`);
    setAgent(row);
    setNotice("Saved a new immutable version.");
  }

  async function publish(event: FormEvent) {
    event.preventDefault();
    const row = await api<AgentDetail>(`/agents/${params.id}/publish`, {
      method: "POST",
      body: JSON.stringify({
        category,
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        slug: slug || null,
      }),
    });
    setAgent(row);
    setNotice(row.listing ? `Published as /marketplace/${row.listing.slug}` : "Published.");
  }

  async function archive() {
    const row = await api<AgentDetail>(`/agents/${params.id}/archive`, { method: "POST" });
    setAgent(row);
    setNotice("Agent archived. It leaves the catalog.");
  }

  if (!agent) {
    return <p className={error ? "error" : "muted"}>{error || "Loading agent..."}</p>;
  }

  return (
    <section>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>{agent.name}</h1>
        <div className="actions">
          <Link href={`/studio/${agent.id}/playground`}>Playground</Link>
          <Link href={`/studio/${agent.id}/tests`}>Tests</Link>
        </div>
      </div>
      <p className="meta">Status: {agent.status}</p>
      {notice ? <p>{notice}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <div className="split">
        <div className="stack">
          <form className="panel stack" onSubmit={(event) => saveProfile(event).catch((exc: Error) => setError(exc.message))}>
            <h2>Profile</h2>
            <label>Name<input value={name} onChange={(event) => setName(event.target.value)} /></label>
            <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>
            <button type="submit">Save profile</button>
          </form>
          <form className="panel stack" onSubmit={(event) => saveVersion(event).catch((exc: Error) => setError(exc.message))}>
            <h2>New version</h2>
            <label>System prompt<textarea value={systemPrompt} onChange={(event) => setSystemPrompt(event.target.value)} /></label>
            <label>Model<input value={model} onChange={(event) => setModel(event.target.value)} /></label>
            <label>Temperature<input value={temperature} onChange={(event) => setTemperature(event.target.value)} type="number" min="0" max="2" step="0.1" /></label>
            <label>Max steps<input value={maxSteps} onChange={(event) => setMaxSteps(event.target.value)} type="number" min="1" max="20" /></label>
            <div className="checks">
              {TOOL_OPTIONS.map((tool) => (
                <label key={tool}>
                  <input type="checkbox" checked={tools.includes(tool)} onChange={() => toggleTool(tool)} />
                  {tool}
                </label>
              ))}
            </div>
            <label className="checks">
              <input type="checkbox" checked={memory} onChange={(event) => setMemory(event.target.checked)} />
              Keep conversation memory
            </label>
            <button type="submit">Save version</button>
          </form>
        </div>
        <div className="stack">
          <form className="panel stack" onSubmit={(event) => publish(event).catch((exc: Error) => setError(exc.message))}>
            <h2>Publish</h2>
            <label>Category<input value={category} onChange={(event) => setCategory(event.target.value)} /></label>
            <label>Tags<input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="notes, support" /></label>
            <label>Slug<input value={slug} onChange={(event) => setSlug(event.target.value)} placeholder="optional-public-slug" /></label>
            <button type="submit">Publish latest version</button>
            <button className="secondary" type="button" onClick={() => archive().catch((exc: Error) => setError(exc.message))}>
              Archive
            </button>
          </form>
          <article className="panel">
            <h2>Version history</h2>
            {agent.versions.map((version) => (
              <p key={version.id}>
                <strong>v{version.version_number}</strong> · {version.model} · {version.tool_names.join(", ") || "no tools"}
                <br />
                <span className="muted">{version.system_prompt}</span>
              </p>
            ))}
          </article>
        </div>
      </div>
    </section>
  );
}
