"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthTokens, SessionUser } from "./types";

interface AuthState {
  user: SessionUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  demoMode: boolean;
  setSession: (tokens: AuthTokens, demoMode?: boolean) => void;
  updateAccessToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      demoMode: false,
      setSession: (tokens, demoMode = false) => set({
        user: tokens.user,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        demoMode,
      }),
      updateAccessToken: (accessToken) => set({ accessToken }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null, demoMode: false }),
    }),
    { name: "bhoomsetu-session" },
  ),
);
