// frontend/app/api/token/route.ts
// FIX: Added try/catch around the backend fetch so a network failure (e.g. Render
// cold start, DNS error) returns a clean 503 JSON response instead of an unhandled
// exception that crashes the Route Handler and shows a Next.js 500 HTML error page.

import { NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY  = process.env.API_KEY ?? "";

export async function POST() {
  if (!API_KEY) {
    return NextResponse.json(
      { error: "Server misconfigured: API_KEY not set" },
      { status: 500 }
    );
  }

  try {
    const res = await fetch(`${BACKEND}/auth/token`, {
      method: "POST",
      headers: { "X-API-Key": API_KEY },
      cache: "no-store",
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return NextResponse.json(body, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json(
      { error: `Backend unreachable: ${message}` },
      { status: 503 }
    );
  }
}