"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { TOOL_OPTIONS } from "@/lib/types";

export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful agent. Use only the enabled tools.");
  const [model, setModel] = useState("gpt-4o-mini");
  const [temperature, setTemperature] = useState("0.2");
  const [maxSteps, setMaxSteps] = useState("6");
  const [memory, setMemory] = useState(true);
  const [tools, setTools] = useState<string[]>(["notes"]);
  const [error, setError] = useState("");

  function toggleTool(tool: string) {
    setTools((current) => (current.includes(tool) ? current.filter((item) => item !== tool) : [...current, tool]));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      const created = await api<{ id: number }>("/agents", {
        method: "POST",
        body: JSON.stringify({
          name,
          description,
          system_prompt: systemPrompt,
          model,
          temperature: Number(temperature),
          max_steps: Number(maxSteps),
          tool_names: tools,
          memory_enabled: memory,
        }),
      });
      router.push(`/studio/${created.id}`);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not create the agent");
    }
  }

  return (
    <section className="panel">
      <h1>New agent</h1>
      <form className="stack" onSubmit={onSubmit}>
        <label>Name<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
        <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>
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
        <label>
          <span className="checks">
            <input type="checkbox" checked={memory} onChange={(event) => setMemory(event.target.checked)} />
            Keep conversation memory
          </span>
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Create draft</button>
      </form>
    </section>
  );
}
