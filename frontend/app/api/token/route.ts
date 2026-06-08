// C-5 FIX: This server-side Route Handler proxies the /auth/token request to the backend.
// The master API_KEY lives only in process.env (server-side), never in NEXT_PUBLIC_*.
// The browser calls /api/token (this endpoint) instead of the backend directly.

import { NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY  = process.env.API_KEY ?? "";  // server-side only — never NEXT_PUBLIC_

export async function POST() {
  if (!API_KEY) {
    return NextResponse.json({ error: "Server misconfigured: API_KEY not set" }, { status: 500 });
  }

  const res = await fetch(`${BACKEND}/auth/token`, {
    method: "POST",
    headers: { "X-API-Key": API_KEY },
    // Prevent Next.js from caching the token response
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    return NextResponse.json(body, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
