import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/context/ThemeContext";
import ErrorBoundary from "@/components/ErrorBoundary";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  title: { default: "OpsPilot AI", template: "%s | OpsPilot AI" },
  description: "AI-Powered CI/CD Incident Intelligence Platform — detect, analyse, and remediate pipeline failures automatically.",
  metadataBase: new URL(BASE_URL),
  openGraph: {
    title: "OpsPilot AI",
    description: "AI-Powered CI/CD Incident Intelligence Platform",
    url: BASE_URL,
    siteName: "OpsPilot AI",
    images: [{ url: "/og", width: 1200, height: 630, alt: "OpsPilot AI" }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "OpsPilot AI",
    description: "AI-Powered CI/CD Incident Intelligence Platform",
    images: ["/og"],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}
