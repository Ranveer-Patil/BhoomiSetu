import { afterEach, describe, expect, it, vi } from "vitest";
import { api, apiFetch } from "./api-client";

const authState = vi.hoisted(() => ({
  accessToken: null as string | null,
  refreshToken: null as string | null,
  demoMode: false,
  setSession: vi.fn(),
  logout: vi.fn(),
}));

vi.mock("./auth-store", () => ({
  useAuthStore: { getState: () => authState },
}));

const ok = (body: unknown) =>
  Promise.resolve(new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  }));

describe("portal API mutations", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    authState.accessToken = null;
    authState.refreshToken = null;
    authState.demoMode = false;
  });

  it("normalizes the backend authority role and preserves the real user name", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => ok({
      access_token: "access-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
      user: {
        id: "authority-1",
        name: "Project Authority",
        email: "authority@bhoomsetu.local",
        role: "project_authority",
      },
    }));

    const tokens = await api.login("authority@bhoomsetu.local", "DemoPass123!");

    expect(tokens.user).toMatchObject({
      name: "Project Authority",
      role: "authority",
    });
  });

  it("normalizes backend stage history for the case timeline", async () => {
    authState.accessToken = "access-token";
    vi.spyOn(globalThis, "fetch").mockImplementation(() => ok({
      id: "case-1",
      parcel_id: "parcel-1",
      current_stage: "verification",
      assigned_officer_id: "officer-1",
      affected_family_count: 1,
      created_at: "2026-09-01T00:00:00Z",
      stage_history: [{
        id: "history-1",
        from_stage: "notification",
        to_stage: "verification",
        changed_by: "officer-1",
        reason: "Documents verified",
        changed_at: "2026-09-01T01:00:00Z",
      }],
    }));

    const item = await api.caseDetail("case-1");

    expect(item.stage_history[0]).toMatchObject({
      notes: "Documents verified",
      created_at: "2026-09-01T01:00:00Z",
    });
  });

  it("sends the backend workflow contract with bearer authentication", async () => {
    authState.accessToken = "access-token";
    authState.refreshToken = "refresh-token";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => ok({ id: "case-1" }));

    await api.transition("case-1", "verification", "Documents checked");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://127.0.0.1:8000/cases/case-1/transition");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer access-token");
    expect(JSON.parse(String(init?.body))).toEqual({
      new_stage: "verification",
      reason: "Documents checked",
    });
  });

  it("uploads the selected document as multipart form data", async () => {
    authState.accessToken = "access-token";
    authState.refreshToken = "refresh-token";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => ok({ document_id: "doc-1" }));
    const file = new File(["scan"], "record.png", { type: "image/png" });

    await api.uploadDocument("case-1", file);

    const [, init] = fetchMock.mock.calls[0];
    expect(init?.body).toBeInstanceOf(FormData);
    expect((init?.body as FormData).get("file")).toBe(file);
    expect(new Headers(init?.headers).has("Content-Type")).toBe(false);
  });

  it("submits grievance text to the selected case", async () => {
    authState.accessToken = "access-token";
    authState.refreshToken = "refresh-token";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => ok({ id: "grievance-1" }));

    await api.createGrievance("case-1", "Compensation has not arrived after approval.");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://127.0.0.1:8000/cases/case-1/grievances");
    expect(JSON.parse(String(init?.body))).toEqual({
      description: "Compensation has not arrived after approval.",
    });
  });
});


describe("API failures and downloads", () => {
  afterEach(() => { vi.restoreAllMocks(); authState.refreshToken = null; });
  it("returns CSV as a downloadable blob", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("group,case_count\nPune,3", { headers: { "Content-Type": "text/csv" } }));
    const blob = await apiFetch<Blob>("/reports/project");
    expect(blob.size).toBeGreaterThan(0);
    expect(blob.type).toContain("text/csv");
  });
  it("shows validation messages instead of raw JSON", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: [{ msg: "Displaced families cannot exceed affected families" }] }), { status: 422 }));
    await expect(apiFetch("/cases/test/families", { method: "PATCH" })).rejects.toThrow("Displaced families cannot exceed affected families");
  });
  it("does not retry a wrong password with the previous session", async () => {
    authState.refreshToken = "old-refresh";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({detail: "Incorrect email or password"}), { status: 401 }));
    await expect(api.login("wrong@example.test", "incorrect-password")).rejects.toThrow("Incorrect email or password");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
