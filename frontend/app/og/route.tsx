import { NextResponse } from "next/server";

export function GET() {
  const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#000"/>
      <stop offset="100%" style="stop-color:#060606"/>
    </linearGradient>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#33ff88"/>
      <stop offset="100%" style="stop-color:#00c3ff"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="0" y="0" width="1200" height="4" fill="url(#g)"/>
  <circle cx="100" cy="100" r="300" fill="#33ff88" opacity="0.03"/>
  <circle cx="1100" cy="530" r="300" fill="#00c3ff" opacity="0.03"/>
  <text x="80" y="260" font-family="Arial" font-weight="900" font-size="96" fill="url(#g)">OpsPilot AI</text>
  <text x="84" y="330" font-family="Arial" font-size="32" fill="#888">AI-Powered CI/CD Incident Intelligence</text>
  <rect x="80" y="390" width="180" height="48" rx="12" fill="#33ff8820" stroke="#33ff88" stroke-width="1.5"/>
  <text x="170" y="421" text-anchor="middle" font-family="Arial" font-weight="700" font-size="18" fill="#33ff88">● LIVE</text>
  <rect x="280" y="390" width="220" height="48" rx="12" fill="#00c3ff20" stroke="#00c3ff" stroke-width="1.5"/>
  <text x="390" y="421" text-anchor="middle" font-family="Arial" font-weight="700" font-size="18" fill="#00c3ff">GROQ ACTIVE</text>
</svg>`;
  return new NextResponse(svg, {
    headers: { "Content-Type": "image/svg+xml", "Cache-Control": "public, max-age=86400" },
  });
}
