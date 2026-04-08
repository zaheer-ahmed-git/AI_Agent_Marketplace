import type { Metadata } from "next";

import { Shell } from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent Market",
  description: "Create, publish, run, and test custom AI agents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
