import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ava — Visual Agent Canvas",
  description: "Open-source multi-agent DAG orchestration (Phase 1)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
