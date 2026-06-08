/** @type {import('next').NextConfig} */

// M FIX: Added Content-Security-Policy header.
// Adjust script-src / connect-src as needed when adding third-party services.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const csp = [
  "default-src 'self'",
  // Next.js requires 'unsafe-inline' for its runtime CSS-in-JS; nonce-based CSP
  // is the stricter alternative but requires middleware — this is a safe baseline.
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  `connect-src 'self' ${API_URL}`,
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const nextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options",         value: "DENY" },
          { key: "X-Content-Type-Options",   value: "nosniff" },
          { key: "Referrer-Policy",          value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy",       value: "camera=(), microphone=(), geolocation=()" },
          { key: "X-DNS-Prefetch-Control",   value: "on" },
          // M FIX: Content-Security-Policy was missing
          { key: "Content-Security-Policy",  value: csp },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
