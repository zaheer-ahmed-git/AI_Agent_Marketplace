"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo-password");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      window.localStorage.setItem("token", result.access_token);
      router.push("/");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Login failed");
    }
  }

  return (
    <section className="panel" style={{ maxWidth: 460 }}>
      <h1>Log in</h1>
      <p className="lede">The seeded demo account is demo@example.com / demo-password.</p>
      <form className="stack" onSubmit={onSubmit}>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
        </label>
        <label>
          Password
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Continue</button>
      </form>
    </section>
  );
}
