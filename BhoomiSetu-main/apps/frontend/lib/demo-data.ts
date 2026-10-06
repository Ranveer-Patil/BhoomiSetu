import type { CaseDetail, CaseStage, ParcelFeature, Role } from "./types";

export const stages: CaseStage[] = [
  "notification",
  "verification",
  "objection",
  "award",
  "compensation",
  "possession",
];

export const caseReference = (item: Pick<CaseDetail, "id" | "case_number">) =>
  item.case_number ?? `BS-${item.id.slice(0, 8).toUpperCase()}`;

export const demoAccounts: Record<Role, { email: string; password: string; name: string }> = {
  landowner: { email: "citizen@bhoomsetu.local", password: "DemoPass123!", name: "Anita Patil" },
  officer: { email: "officer@bhoomsetu.local", password: "DemoPass123!", name: "Field Officer" },
  authority: { email: "authority@bhoomsetu.local", password: "DemoPass123!", name: "Project Authority" },
  district_admin: { email: "district@bhoomsetu.local", password: "DemoPass123!", name: "District Administrator" },
  senior_admin: { email: "senior@bhoomsetu.local", password: "DemoPass123!", name: "Senior Administrator" },
};

const now = new Date("2026-08-31T09:30:00+05:30").toISOString();

export const demoCases: CaseDetail[] = Array.from({ length: 20 }, (_, index) => {
  const stage = stages[index % stages.length];
  const stageIndex = stages.indexOf(stage);
  return {
    id: `case-${String(index + 1).padStart(3, "0")}`,
    case_number: `MH-PUN-2026-${String(index + 1).padStart(4, "0")}`,
    project_id: "project-kharadi-bypass",
    parcel_id: `parcel-${String(index + 1).padStart(3, "0")}`,
    landowner_id: `owner-${String((index % 8) + 1).padStart(3, "0")}`,
    current_stage: stage,
    status: index % 7 === 0 ? "needs_attention" : "active",
    assigned_officer_id: `officer-${(index % 3) + 1}`,
    created_at: now,
    updated_at: now,
    stage_history: stages.slice(0, stageIndex + 1).map((to_stage, historyIndex) => ({
      id: `history-${index}-${historyIndex}`,
      from_stage: historyIndex ? stages[historyIndex - 1] : null,
      to_stage,
      notes: historyIndex === stageIndex ? "Current verified stage" : "Completed",
      created_at: new Date(Date.parse(now) - (stageIndex - historyIndex) * 86400000 * 5).toISOString(),
    })),
  };
});

const road = [18.5519, 73.9474] as const;
export const demoParcels: ParcelFeature[] = demoCases.map((item, index) => {
  const row = Math.floor(index / 5);
  const col = index % 5;
  const lat = road[0] + row * 0.00115;
  const lng = road[1] + col * 0.00155;
  return {
    id: item.parcel_id,
    survey_number: `KH-${101 + index}`,
    village: "Kharadi",
    area_hectares: 0.72 + (index % 5) * 0.13,
    case_id: item.id,
    stage: item.current_stage,
    coordinates: [
      [lat, lng], [lat, lng + 0.0012], [lat + 0.00082, lng + 0.0012],
      [lat + 0.00082, lng], [lat, lng],
    ],
  };
});
