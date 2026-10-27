import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BirdVision AI — Identify the wild",
  description:
    "Upload a bird photograph and receive a genuine CNN-based species prediction, explainability, and real nearby observations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased min-h-screen">{children}</body>
    </html>
  );
}
