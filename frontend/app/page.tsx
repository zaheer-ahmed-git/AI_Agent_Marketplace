"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { ListingCard } from "@/lib/types";

export default function CatalogPage() {
  const [query, setQuery] = useState("");
  const [applied, setApplied] = useState("");
  const [category, setCategory] = useState("");
  const [minRating, setMinRating] = useState("");
  const [items, setItems] = useState<ListingCard[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (applied) params.set("q", applied);
    if (category) params.set("category", category);
    if (minRating) params.set("min_rating", minRating);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    api<ListingCard[]>(`/marketplace${suffix}`)
      .then((rows) => {
        setItems(rows);
        setError("");
      })
      .catch((exc: Error) => setError(exc.message));
  }, [applied, category, minRating]);

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setApplied(query.trim());
  }

  return (
    <section>
      <h1>Find an agent worth cloning</h1>
      <p className="lede">
        Published agents stay in the catalog. Install copies the prompt, tools, and limits into your studio. Runs are free and recorded in the usage ledger.
      </p>
      <form className="filters" onSubmit={onSearch}>
        <label>
          Search
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="research, notes, math" />
        </label>
        <label>
          Category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All</option>
            <option value="research">Research</option>
            <option value="support">Support</option>
            <option value="productivity">Productivity</option>
            <option value="education">Education</option>
          </select>
        </label>
        <label>
          Minimum rating
          <select value={minRating} onChange={(event) => setMinRating(event.target.value)}>
            <option value="">Any</option>
            <option value="3">3+</option>
            <option value="4">4+</option>
            <option value="5">5</option>
          </select>
        </label>
        <button type="submit">Search</button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <div className="grid">
        {items.map((item) => (
          <Link key={item.slug} href={`/marketplace/${item.slug}`} className="card">
            <span className="pill">{item.category}</span>
            <h2>{item.name}</h2>
            <p>{item.description}</p>
            <p className="meta">
              {item.rating === null ? "No reviews yet" : `${item.rating.toFixed(1)} · ${item.review_count} reviews`}
              {" · "}
              {item.install_count} installs
            </p>
          </Link>
        ))}
      </div>
      {items.length === 0 && !error ? <p className="muted">No listings match these filters.</p> : null}
    </section>
  );
}
