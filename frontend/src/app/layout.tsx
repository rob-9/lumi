import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lumi",
  description: "AI-powered drug discovery lab",
};

// Inline script to apply theme before first paint (prevents flash)
const themeScript = `(function(){var t=localStorage.getItem('lumi-theme');if(t==='light')document.documentElement.setAttribute('data-theme','light')})()`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <link
          href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
