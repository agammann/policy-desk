import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Policy Desk — Answers you can trace",
  description: "Ask questions about your policies and find the evidence behind each answer.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
