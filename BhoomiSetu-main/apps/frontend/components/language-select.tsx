"use client";
import { Languages } from "lucide-react";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { locales, useLocale, useT, type Locale } from "@/lib/i18n";

export function LanguageSelect() {
  const { locale, setLocale } = useLocale();
  const t = useT();
  const [message, setMessage] = useState("");
  async function change(value: Locale) {
    setLocale(value);
    setMessage("");
    const session = useAuthStore.getState();
    if (session.user && !session.demoMode) {
      try {
        await apiFetch("/me/preferences", {
          method: "PUT",
          body: JSON.stringify({ locale: value }),
        });
      } catch {
        setMessage(
          "Language saved on this device. Account sync is unavailable.",
        );
      }
    }
  }
  return (
    <div className="languageControl">
      <label>
        <Languages size={16} aria-hidden />
        <span className="srOnly">{t("language")}</span>
        <select
          aria-label={t("language")}
          value={locale}
          onChange={(event) => void change(event.target.value as Locale)}
        >
          {Object.entries(locales).map(([id, name]) => (
            <option value={id} key={id}>
              {name}
            </option>
          ))}
        </select>
      </label>
      {message && <small role="status">{message}</small>}
    </div>
  );
}
