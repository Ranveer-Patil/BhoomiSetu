import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./styles.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "BhoomiSetu",
  description: "Clear, accountable land-acquisition case tracking.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
