export type Role =
  "landowner" | "officer" | "authority" | "district_admin" | "senior_admin";

export type CaseStage =
  | "notification"
  | "verification"
  | "objection"
  | "award"
  | "compensation"
  | "possession";

export interface SessionUser {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: SessionUser;
}

export interface CaseSummary {
  id: string;
  case_number?: string;
  project_id?: string;
  parcel_id: string;
  landowner_id?: string;
  current_stage: CaseStage;
  status?: string;
  assigned_officer_id?: string | null;
  affected_family_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface StageHistory {
  id: string;
  from_stage?: CaseStage | null;
  to_stage: CaseStage;
  notes?: string | null;
  created_at: string;
}

export interface CaseDetail extends CaseSummary {
  stage_history: StageHistory[];
}

export interface ParcelFeature {
  id: string;
  survey_number: string;
  village: string;
  area_hectares: number;
  case_id: string;
  stage: CaseStage;
  coordinates: [number, number][];
}

export interface LandRecordFixture {
  source: { is_fixture: boolean; notice: string; intended_provider: string };
  survey_number: string;
  owner: { name: string; relationship: string };
  area: { value: number; unit: string };
  land_use_classification: string;
  encumbrance: { has_encumbrance: boolean; status: string };
}

export interface DocumentExtraction {
  document_id: string;
  status: string;
  fields: {
    owner_name?: string | null;
    khasra_survey_number?: string | null;
    area_hectares?: number | null;
    document_type?: string | null;
    document_date?: string | null;
    confidence: number;
    extraction_method: "vision_llm" | "tesseract_ocr";
    raw_text_excerpt: string;
  };
}

export interface GrievanceResult {
  id: string;
  case_id: string;
  classification: {
    category: string;
    priority: string;
    suggested_department: string;
    confidence: number;
    rationale: string;
  };
  human_confirmation_required: boolean;
}

export interface PredictionResult {
  predicted_days_remaining: number;
  risk_band: "low" | "medium" | "high";
  top_features: Array<{ feature: string; importance: number }>;
  model_version: string;
  training_data: "synthetic";
  validated_on_real_data: false;
  holdout_mae_days: number;
}

export interface AggregatePrediction {
  case_count: number;
  high_risk_pct: number;
  avg_disbursal_days: number;
  trend: "up" | "stable" | "down";
}
