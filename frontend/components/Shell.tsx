"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    const token = window.localStorage.getItem("token");
    if (!token) {
      setName(null);
      return;
    }
    api<{ display_name: string }>("/auth/me")
      .then((me) => setName(me.display_name))
      .catch(() => setName(null));
  }, [pathname]);

  function logout() {
    window.localStorage.removeItem("token");
    setName(null);
    router.push("/login");
  }

  return (
    <div className="shell">
      <header className="nav">
        <Link className="brand" href="/">Agent Market</Link>
        <nav className="nav-links">
          <Link href="/">Catalog</Link>
          <Link href="/studio">Studio</Link>
          <Link href="/monitoring">Monitoring</Link>
          {name ? (
            <button className="secondary" onClick={logout} type="button">{name} · Log out</button>
          ) : (
            <Link href="/login">Log in</Link>
          )}
        </nav>
      </header>
      <main className="page">{children}</main>
    </div>
  );
}
