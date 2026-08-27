import type { Metadata, Viewport } from "next";

import "katex/dist/katex.min.css";
import "mathlive/fonts.css";
import "./globals.css";

export const metadata: Metadata = {
  description: "A focused mathematics coaching workspace for paper-first problem solving.",
  title: "Math Coach",
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#163b45",
  width: "device-width",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
