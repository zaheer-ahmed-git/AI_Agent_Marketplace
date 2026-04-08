"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { api } from "@/lib/api";
import type { ListingDetail } from "@/lib/types";

export default function ListingPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const slug = params.slug;
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [rating, setRating] = useState("5");
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api<ListingDetail>(`/marketplace/${slug}`)
      .then((row) => {
        if (active) {
          setListing(row);
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
  }, [slug]);

  async function install() {
    const created = await api<{ agent_id: number }>(`/marketplace/${slug}/install`, { method: "POST" });
    router.push(`/studio/${created.agent_id}`);
  }

  async function review(event: FormEvent) {
    event.preventDefault();
    try {
      await api(`/marketplace/${slug}/reviews`, {
        method: "POST",
        body: JSON.stringify({ rating: Number(rating), comment }),
      });
      setComment("");
      const row = await api<ListingDetail>(`/marketplace/${slug}`);
      setListing(row);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Review failed");
    }
  }

  if (!listing) {
    return <p className={error ? "error" : "muted"}>{error || "Loading listing..."}</p>;
  }

  return (
    <section className="split">
      <article className="panel">
        <span className="pill">{listing.category}</span>
        <h1>{listing.name}</h1>
        <p>{listing.description}</p>
        <p className="meta">
          {listing.rating === null ? "No reviews yet" : `${listing.rating.toFixed(1)} from ${listing.review_count} reviews`}
          {" · "}
          {listing.install_count} installs · {listing.model}
        </p>
        <p><strong>Tools:</strong> {listing.tool_names.join(", ") || "none"}</p>
        <h2>System prompt</h2>
        <p>{listing.system_prompt}</p>
        <button type="button" onClick={() => install().catch((exc: Error) => setError(exc.message))}>
          Install
        </button>
        {error ? <p className="error">{error}</p> : null}
      </article>
      <aside className="panel">
        <h2>Reviews</h2>
        {listing.reviews.length === 0 ? <p className="muted">Be the first to leave a note.</p> : null}
        {listing.reviews.map((review) => (
          <p key={review.id}>
            <strong>{review.rating}/5</strong> · {review.author}
            <br />
            {review.comment}
          </p>
        ))}
        <form className="stack" onSubmit={review}>
          <label>
            Rating
            <select value={rating} onChange={(event) => setRating(event.target.value)}>
              <option value="5">5</option>
              <option value="4">4</option>
              <option value="3">3</option>
              <option value="2">2</option>
              <option value="1">1</option>
            </select>
          </label>
          <label>
            Comment
            <textarea value={comment} onChange={(event) => setComment(event.target.value)} />
          </label>
          <button type="submit">Submit review</button>
        </form>
      </aside>
    </section>
  );
}
