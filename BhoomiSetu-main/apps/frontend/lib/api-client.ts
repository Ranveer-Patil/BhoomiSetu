import { useAuthStore } from "./auth-store";
import type {
  AuthTokens,
  CaseDetail,
  CaseSummary,
  DocumentExtraction,
  GrievanceResult,
  LandRecordFixture,
  PredictionResult,
  AggregatePrediction,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type BackendAuthTokens = Omit<AuthTokens, "user"> & {
  user: Omit<AuthTokens["user"], "role"> & {
    role: AuthTokens["user"]["role"] | "project_authority";
  };
};

type BackendCaseDetail = Omit<CaseDetail, "stage_history"> & {
  stage_history: Array<{
    id: string;
    from_stage: CaseDetail["current_stage"];
    to_stage: CaseDetail["current_stage"];
    changed_by: string;
    reason?: string | null;
    changed_at: string;
  }>;
};

function normalizeTokens(tokens: BackendAuthTokens): AuthTokens {
  return {
    ...tokens,
    user: {
      ...tokens.user,
      role:
        tokens.user.role === "project_authority"
          ? "authority"
          : tokens.user.role,
    },
  };
}

function normalizeCaseDetail(item: BackendCaseDetail): CaseDetail {
  return {
    ...item,
    stage_history: item.stage_history.map((entry) => ({
      id: entry.id,
      from_stage: entry.from_stage,
      to_stage: entry.to_stage,
      notes: entry.reason,
      created_at: entry.changed_at,
    })),
  };
}

let refreshRequest: { token: string; promise: Promise<string | null> } | null =
  null;

async function refreshAccessToken(): Promise<string | null> {
  const state = useAuthStore.getState();
  const refreshToken = state.refreshToken;
  if (!refreshToken || state.demoMode) return null;
  if (refreshRequest?.token === refreshToken) return refreshRequest.promise;
  const promise = (async () => {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      signal: AbortSignal.timeout(75_000),
    });
    if (!response.ok) return null;
    const tokens = normalizeTokens(
      (await response.json()) as BackendAuthTokens,
    );
    if (useAuthStore.getState().refreshToken !== refreshToken) return null;
    state.setSession(tokens);
    return tokens.access_token;
  })();
  refreshRequest = { token: refreshToken, promise };
  try {
    return await promise;
  } finally {
    if (refreshRequest?.promise === promise) refreshRequest = null;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const authenticated = ![
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
  ].includes(path);
  const userId = useAuthStore.getState().user?.id;
  const token = authenticated ? useAuthStore.getState().accessToken : null;
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    signal: init.signal ?? AbortSignal.timeout(75_000),
  });
  if (response.status === 401 && retry && authenticated) {
    if (useAuthStore.getState().user?.id !== userId)
      throw new Error("Your session changed. Please retry.");
    if (useAuthStore.getState().accessToken !== token)
      return apiFetch<T>(path, init, false);
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiFetch<T>(path, init, false);
    if (useAuthStore.getState().accessToken === token)
      useAuthStore.getState().logout();
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: { msg: string }) => item.msg).join(". ")
          : `Request failed (${response.status}). Please try again.`,
    );
  }
  if (response.status === 204) return undefined as T;
  if (response.headers.get("content-type")?.includes("text/csv"))
    return response.blob() as Promise<T>;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    apiFetch<BackendAuthTokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }).then(normalizeTokens),
  cases: () => apiFetch<CaseSummary[]>("/cases?limit=500"),
  caseDetail: (id: string) =>
    apiFetch<BackendCaseDetail>(`/cases/${id}`).then(normalizeCaseDetail),
  transition: (id: string, newStage: string, reason: string) =>
    apiFetch<CaseSummary>(`/cases/${id}/transition`, {
      method: "POST",
      body: JSON.stringify({ new_stage: newStage, reason }),
    }),
  uploadDocument: (id: string, file: File, documentType = "land_record") => {
    const body = new FormData();
    body.append("file", file);
    body.append("document_type", documentType);
    return apiFetch<DocumentExtraction>(`/cases/${id}/documents`, {
      method: "POST",
      body,
    });
  },
  createGrievance: (id: string, description: string) =>
    apiFetch<GrievanceResult>(`/cases/${id}/grievances`, {
      method: "POST",
      body: JSON.stringify({ description }),
    }),
  delayPrediction: (id: string) =>
    apiFetch<PredictionResult>(`/cases/${id}/prediction/delay`),
  compensationPrediction: (id: string) =>
    apiFetch<PredictionResult>(`/cases/${id}/prediction/compensation-timeline`),
  aggregatePredictions: () =>
    apiFetch<AggregatePrediction>("/predictions/aggregate"),
  landRecord: (surveyNumber: string) =>
    apiFetch<LandRecordFixture>(
      `/integrations/apisetu/land-records/${surveyNumber}`,
    ),
};
