import type { Metadata } from "next";
import Link from "next/link";
import { Settings2, Sparkles } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Prompt Engineer — Prompts that produce outcomes",
  description: "Turn rough ideas into structured, testable prompts for modern websites, web applications, and agent workflows.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link className="brand" href="/" aria-label="Prompt Engineer home">
            <span className="brand-mark"><Sparkles size={17} /></span>
            <span>Prompt Engineer</span>
          </Link>
          <nav aria-label="Primary navigation">
            <Link href="/">Agent</Link>
            <Link href="/prompts">Prompt Library</Link>
            <Link className="settings-link" href="/admin/models"><Settings2 size={16} /> Models</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}

