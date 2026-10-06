"use client";
import Link from "next/link";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import type { Inbox } from "@/lib/operations-types";
import { dateLabel, Empty } from "./workspace-common";
export function InboxView({ inbox }: { inbox: Inbox }) {
  const client = useQueryClient();
  const t = useT();
  const user = useAuthStore((state) => state.user);
  const [unread, setUnread] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const items = inbox.items.filter((item) => !unread || !item.read);
  async function markRead(key: string) {
    setBusy(key);
    setMessage("");
    try {
      await apiFetch(`/alerts/read?key=${encodeURIComponent(key)}`, {
        method: "PUT",
      });
      await client.invalidateQueries({ queryKey: ["workspace"] });
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not mark read",
      );
    } finally {
      setBusy("");
    }
  }
  return (
    <section className="panel">
      <div className="panelHead">
        <div>
          <h2>{t("alerts")}</h2>
          <p className="helper">
            Evaluated automatically on refresh, every 30 seconds while this
            workspace is open.
          </p>
        </div>
        <label className="checkboxLabel">
          <input
            checked={unread}
            type="checkbox"
            onChange={(event) => setUnread(event.target.checked)}
          />
          Unread only
        </label>
      </div>
      {items.length === 0 && <Empty>{t("noAlerts")}</Empty>}
      {items.map((item) => (
        <article
          key={item.key}
          className={`inboxItem ${item.severity} ${item.read ? "isRead" : ""}`}
        >
          <div>
            <span className="statusBadge">{item.kind}</span>
            <small>{dateLabel(item.date)}</small>
          </div>
          <Link href={`/portal/${user?.role}?view=cases&case=${item.case_id}`}>
            <h3>{item.title}</h3>
            <p>{item.detail}</p>
          </Link>
          {!item.read && (
            <button
              disabled={busy === item.key}
              className="button secondary small"
              onClick={() => void markRead(item.key)}
            >
              {t("read")}
            </button>
          )}
        </article>
      ))}
      {message && (
        <p role="status" className="errorNote">
          {message}
        </p>
      )}
      <p className="helper">
        Operational review thresholds are prototype settings. Statutory alerts
        require a deadline and reference recorded by an authority. No SMS or
        email is sent.
      </p>
    </section>
  );
}
