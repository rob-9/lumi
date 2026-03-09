import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lumi — Technical Program Management for Research Labs",
  description:
    "AI-powered TPM for research labs. Multi-agent orchestration, confidence-scored findings, and human-in-the-loop routing.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={{ scrollBehavior: "smooth" }}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
