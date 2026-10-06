import type { CaseStage } from "./types";

export interface Compensation {
  status: "assessed" | "approved" | "disbursed";
  assessed_amount: string | null;
  disbursed_amount: string | null;
  due_date: string | null;
  reference: string;
}
export interface Rehabilitation {
  rehabilitation_stage: string;
  resettlement_site_assigned: boolean;
  families_supported: number;
  notes: string;
}
export interface StoredDocument {
  id: string;
  version: number;
  document_type: string;
  file_url: string;
  status: string;
  created_at: string | null;
  extracted_fields: Record<string, string | number | null> | null;
}
export interface StoredGrievance {
  id: string;
  description: string | null;
  response: string | null;
  category: string;
  priority: string;
  department: string;
  status: "open" | "assigned" | "resolved";
  created_at: string | null;
}
export interface Deadline {
  id: string;
  stage: CaseStage;
  due_date: string;
  basis: "statutory" | "operational";
  reference: string;
}
export interface CaseOperations {
  compensation: Compensation | null;
  rr: Rehabilitation | null;
  affected_family_count: number;
  displaced_family_count: number;
  documents: StoredDocument[];
  grievances: StoredGrievance[];
  deadlines: Deadline[];
}
export interface Summary {
  case_count: number;
  project_count: number;
  affected_families: number;
  displaced_families: number;
  area_notified_hectares: number;
  area_acquired_hectares: number;
  assessed_amount: string | null;
  disbursed_amount: string | null;
  compensation_recorded: number;
  compensation_disbursed: number;
  amounts_recorded: number;
  payment_amounts_recorded: number;
  rr_recorded: number;
  rr_completed: number;
  rr_families_supported: number;
  possession_cases: number;
  completion_pct: number;
  stages: Partial<Record<CaseStage, number>>;
}
export interface GroupSummary extends Summary {
  group: string;
  project_id: string;
  state: string;
  district: string;
}
export interface Dashboard extends Summary {
  open_grievances: number;
  alerts_requiring_attention: number;
  recorded_deadlines_due: number;
  deadline_breaches: number;
  timeline_adherence_pct: number | null;
  projects: GroupSummary[];
  states: GroupSummary[];
  districts: GroupSummary[];
  trend: {
    current_transitions: number;
    previous_transitions: number;
    difference: number;
    label: string;
  };
  notice: string;
  generated_at: string;
}
export interface AlertItem {
  key: string;
  case_id: string;
  kind: string;
  severity: "info" | "warning" | "urgent";
  title: string;
  detail: string;
  date: string;
  read: boolean;
}
export interface Inbox {
  items: AlertItem[];
  generated_at: string;
}
export interface ProjectRecord {
  id: string;
  name: string;
  state: string;
  district: string;
  project_type: string;
}
