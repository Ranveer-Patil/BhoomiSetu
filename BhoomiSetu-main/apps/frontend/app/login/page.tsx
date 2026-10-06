"use client";

import {
  ArrowRight,
  Building2,
  Eye,
  EyeOff,
  Gauge,
  Home,
  Landmark,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Brand } from "@/components/brand";
import { LanguageSelect } from "@/components/language-select";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { demoAccounts } from "@/lib/demo-data";
import { useLocale, useT, type Locale } from "@/lib/i18n";
import type { AuthTokens, Role } from "@/lib/types";

const icons = {
  landowner: Home,
  officer: ShieldCheck,
  authority: Building2,
  district_admin: Landmark,
  senior_admin: Gauge,
};
const roles = Object.keys(demoAccounts) as Role[];
export default function LoginPage() {
  const router = useRouter();
  const client = useQueryClient();
  const t = useT();
  const setSession = useAuthStore((state) => state.setSession);
  const [role, setRole] = useState<Role>("landowner");
  const [email, setEmail] = useState(demoAccounts.landowner.email);
  const [password, setPassword] = useState(demoAccounts.landowner.password);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  function chooseRole(value: Role) {
    setRole(value);
    setEmail(demoAccounts[value].email);
    setPassword(demoAccounts[value].password);
    setMessage("");
  }
  async function signIn(demo = false) {
    setLoading(true);
    setMessage("");
    try {
      const tokens: AuthTokens = demo
        ? {
            access_token: `demo-${role}`,
            refresh_token: "demo",
            token_type: "bearer",
            user: {
              id: `demo-${role}`,
              email,
              name: demoAccounts[role].name,
              role,
            },
          }
        : await api.login(email, password);
      if (!demo && tokens.user.role !== role) {
        setMessage(
          "This account belongs to a different role. Select the matching workspace.",
        );
        return;
      }
      client.clear();
      setSession(tokens, demo);
      const locale = (tokens.user as typeof tokens.user & { locale?: Locale })
        .locale;
      if (locale && ["en", "hi", "mr", "gu", "kn"].includes(locale))
        useLocale.getState().setLocale(locale);
      router.push(`/portal/${tokens.user.role}`);
    } catch (error) {
      setMessage(
        error instanceof Error && error.name !== "TypeError"
          ? error.message
          : "The API could not be reached. It may be waking up; try again in a minute.",
      );
    } finally {
      setLoading(false);
    }
  }
  return (
    <main className="authPage">
      <section className="authStory">
        <Brand />
        <div className="authStatement">
          <p className="eyebrow">भूमि से विश्वास तक</p>
          <h1>
            One system.
            <br />
            Five accountable
            <br />
            <em>views.</em>
          </h1>
          <p>
            Landowners follow their cases. Field teams verify records.
            Authorities keep the journey moving.
          </p>
        </div>
        <p className="authFootnote">
          <ShieldCheck size={18} /> Role-based access · Attributable actions
        </p>
      </section>
      <section className="loginPanel">
        <div className="loginTop">
          <LanguageSelect />
        </div>
        <div className="loginBox">
          <p className="eyebrow">BhoomiSetu workspace</p>
          <h2>Welcome back.</h2>
          <p className="muted">Choose your role to sign in.</p>
          <div
            className="rolePicker"
            role="group"
            aria-label="Choose your role"
          >
            {roles.map((item) => {
              const Icon = icons[item];
              return (
                <button
                  type="button"
                  disabled={loading}
                  className={role === item ? "active" : ""}
                  aria-pressed={role === item}
                  key={item}
                  onClick={() => chooseRole(item)}
                >
                  <Icon size={19} />
                  <span>{t(item)}</span>
                </button>
              );
            })}
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void signIn();
            }}
          >
            <label>
              {t("email")}
              <input
                autoComplete="username"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
              />
            </label>
            <label>
              {t("password")}
              <span className="passwordField">
                <input
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type={showPassword ? "text" : "password"}
                />
                <button
                  type="button"
                  className="iconButton"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>
            {message && (
              <p className="errorNote" role="alert">
                {message}
              </p>
            )}
            <button
              type="submit"
              className="button primary full"
              disabled={loading}
            >
              {loading ? (
                <>
                  <LoaderCircle className="spin" size={18} /> Connecting…
                </>
              ) : (
                <>
                  {t("signIn")} <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
          <button
            className="demoButton"
            disabled={loading}
            onClick={() => void signIn(true)}
          >
            Explore with demo data
          </button>
          <p className="helper">
            Prefilled accounts access the synthetic showcase. Staff roles are
            provisioned by an administrator.
          </p>
        </div>
      </section>
    </main>
  );
}
