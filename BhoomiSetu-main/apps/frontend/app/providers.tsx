"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { useLocale } from "@/lib/i18n";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchOnWindowFocus: true,
            refetchInterval: 30_000,
            retry: 1,
          },
        },
      }),
  );
  const locale = useLocale((state) => state.locale);
  useEffect(() => {
    void useLocale.persist.rehydrate();
  }, []);
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
