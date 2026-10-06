"use client";

import {
  Bell,
  Building2,
  ChevronRight,
  FileText,
  Gauge,
  Home,
  Landmark,
  LogOut,
  Map,
  Menu,
  MessageSquareText,
  Settings,
  ShieldCheck,
  Table2,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import type { Role } from "@/lib/types";
import { Brand } from "./brand";
import { LanguageSelect } from "./language-select";

export type WorkspaceView =
  | "overview"
  | "cases"
  | "documents"
  | "grievances"
  | "map"
  | "operations"
  | "reports"
  | "alerts"
  | "settings";
const roleIcon = {
  landowner: Home,
  officer: ShieldCheck,
  authority: Building2,
  district_admin: Landmark,
  senior_admin: Gauge,
};

export function PortalShell({
  role,
  view,
  children,
  unread = 0,
}: {
  role: Role;
  view: WorkspaceView;
  children: ReactNode;
  unread?: number;
}) {
  const router = useRouter();
  const client = useQueryClient();
  const t = useT();
  const { user, demoMode, logout } = useAuthStore();
  const dialog = useRef<HTMLDialogElement>(null);
  const Icon = roleIcon[role];
  useEffect(() => {
    dialog.current?.close();
  }, [view]);
  const items = [
    { key: "overview", icon: Gauge },
    { key: "cases", icon: FileText },
    { key: "documents", icon: FileText },
    { key: "grievances", icon: MessageSquareText },
    { key: "map", icon: Map },
    ...(role !== "landowner" ? [{ key: "operations", icon: Landmark }] : []),
    ...(["authority", "district_admin", "senior_admin"].includes(role)
      ? [{ key: "reports", icon: Table2 }]
      : []),
    { key: "alerts", icon: Bell },
    { key: "settings", icon: Settings },
  ];
  const link = (key: string) => `/portal/${role}?view=${key}`;
  function signOut() {
    logout();
    client.clear();
    router.push("/login");
  }
  const side = (
    <>
      <div className="sideBrand">
        <Brand />
      </div>
      <div className="rolePill">
        <Icon size={18} />
        <span>{t(role)}</span>
      </div>
      <nav className="sideNav" aria-label="Workspace navigation">
        {items.map(({ key, icon: ItemIcon }) => (
          <Link
            key={key}
            href={link(key)}
            className={view === key ? "active" : ""}
            aria-current={view === key ? "page" : undefined}
          >
            <ItemIcon size={18} />
            {t(key)}
            {key === "alerts" && unread > 0 && (
              <span className="navCount">{unread}</span>
            )}
          </Link>
        ))}
      </nav>
      <div className="sideFooter">
        <div>
          <strong>{user?.name}</strong>
          <small>{t(demoMode ? "demo" : "liveData")}</small>
        </div>
        <button
          className="iconButton"
          aria-label={t("logout")}
          onClick={signOut}
        >
          <LogOut size={19} />
        </button>
      </div>
    </>
  );
  return (
    <div className="portalLayout">
      <a href="#workspace-content" className="skipLink">
        Skip to content
      </a>
      <aside className="sidebar">{side}</aside>
      <dialog
        ref={dialog}
        className="mobileNav"
        onClick={(event) => {
          if (event.target === dialog.current) dialog.current?.close();
        }}
      >
        <button
          className="closeNav iconButton"
          aria-label={t("close")}
          onClick={() => dialog.current?.close()}
        >
          <X />
        </button>
        {side}
      </dialog>
      <div className="portalMain">
        <header className="portalTopbar">
          <button
            className="menuButton iconButton"
            aria-label={t("menu")}
            onClick={() => dialog.current?.showModal()}
          >
            <Menu />
          </button>
          <span className="breadcrumb">
            BhoomiSetu <ChevronRight size={13} /> {t(view)}
          </span>
          <div className="headerControls">
            <LanguageSelect />
            <Link
              href={link("alerts")}
              className="iconButton"
              aria-label={`${t("alerts")}: ${unread}`}
            >
              <Bell size={19} />
              {unread > 0 && <span className="notificationDot" />}
            </Link>
            <span className="avatar" aria-label={user?.name}>
              {user?.name
                .split(" ")
                .map((part) => part[0])
                .slice(0, 2)
                .join("")}
            </span>
          </div>
        </header>
        <header className="workspaceHeading">
          <div>
            <p className="eyebrow">{t(role)} · BhoomiSetu</p>
            <h1>{t(view)}</h1>
            <p>
              {role === "landowner"
                ? "Your land, documents and next steps in one place."
                : "Track progress, review exceptions and record decisions."}
            </p>
          </div>
          <span className="dataBadge">
            <i />
            {t(demoMode ? "demo" : "liveData")}
          </span>
        </header>
        <main id="workspace-content" className="workspaceContent">
          {demoMode && (
            <p className="notice">
              Synthetic preview. Sign in to the API to save records. No
              government case data is used.
            </p>
          )}
          {children}
        </main>
        <footer className="workspaceFooter">
          SIH26016 prototype · Seeded cases and predictive training data are
          synthetic. Government adapters are fixtures.
        </footer>
      </div>
    </div>
  );
}
