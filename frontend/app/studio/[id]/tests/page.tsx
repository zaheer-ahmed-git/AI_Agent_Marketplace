"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { api } from "@/lib/api";
import type { SuiteResult, TestSuite } from "@/lib/types";

export default function TestsPage() {
  const params = useParams<{ id: string }>();
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [result, setResult] = useState<SuiteResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    api<{ suites: TestSuite[] }>(`/agents/${params.id}/tests`)
      .then((payload) => {
        if (active) {
          setSuites(payload.suites);
          setError("");
        }
      })
      .catch((exc: Error) => {
        if (active) {
          setError(exc.message);
        }
      });
    return () => {
      active = false;
    };
  }, [params.id]);

  async function runSuite() {
    setBusy(true);
    try {
      const payload = await api<SuiteResult>(`/agents/${params.id}/tests/run`, { method: "POST" });
      setResult(payload);
      const refreshed = await api<{ suites: TestSuite[] }>(`/agents/${params.id}/tests`);
      setSuites(refreshed.suites);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Suite failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>Test lab</h1>
        <button type="button" onClick={() => runSuite()} disabled={busy || suites.length === 0}>
          {busy ? "Running..." : "Run suite"}
        </button>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {result ? <p>{result.passed} of {result.total} passed.</p> : null}
      {suites.length === 0 ? <p className="muted">This agent has no automated cases yet.</p> : null}
      {suites.map((suite) => (
        <div key={suite.id}>
          <h2>{suite.name}</h2>
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Input</th>
                <th>Expect</th>
                <th>Last result</th>
              </tr>
            </thead>
            <tbody>
              {suite.cases.map((testCase) => (
                <tr key={testCase.id}>
                  <td>{testCase.name}</td>
                  <td>{testCase.input_text}</td>
                  <td>{[testCase.expected_tool, testCase.expected_phrase].filter(Boolean).join(" · ")}</td>
                  <td>
                    {testCase.last_passed === null ? "Not run" : testCase.last_passed ? "Pass" : "Fail"}
                    {testCase.last_detail ? ` · ${testCase.last_detail}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}
