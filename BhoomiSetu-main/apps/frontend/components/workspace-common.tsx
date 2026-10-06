"use client";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { useLocale, useT } from "@/lib/i18n";

export function useWorkspaceQuery<T>(
  key: readonly unknown[],
  queryFn: () => Promise<T>,
  enabled = true,
) {
  const { user, demoMode } = useAuthStore();
  return useQuery({
    queryKey: ["workspace", user?.id, ...key],
    queryFn,
    enabled: enabled && !!user && !demoMode,
  });
}
export function Loading() {
  const t = useT();
  return (
    <div className="emptyState" role="status">
      <LoaderCircle className="spin" />
      <p>{t("loading")}</p>
    </div>
  );
}
export function QueryError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  const t = useT();
  return (
    <div className="errorState" role="alert">
      <AlertCircle />
      <h2>Unable to load this view</h2>
      <p>
        {error instanceof Error
          ? error.message
          : "Please check the API connection."}
      </p>
      <button className="button secondary" onClick={retry}>
        {t("retry")}
      </button>
    </div>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="emptyState">
      <p>{children}</p>
    </div>
  );
}
export function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <div className="metric">
      <p>{label}</p>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </div>
  );
}
export function useMoney() {
  const locale = useLocale((state) => state.locale);
  const t = useT();
  return (amount: string | number | null | undefined) =>
    amount === null || amount === undefined
      ? t("notRecorded")
      : new Intl.NumberFormat(`${locale}-IN`, {
          style: "currency",
          currency: "INR",
          maximumFractionDigits: 2,
        }).format(Number(amount));
}
export function dateLabel(value: string | null | undefined) {
  return value
    ? new Intl.DateTimeFormat("en-IN", {
        dateStyle: "medium",
        timeZone: "Asia/Kolkata",
      }).format(new Date(value))
    : "Not recorded";
}
