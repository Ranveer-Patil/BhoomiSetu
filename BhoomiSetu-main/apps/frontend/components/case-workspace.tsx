"use client";
import { useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  LoaderCircle,
  UploadCloud,
} from "lucide-react";
import { api, apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { caseReference, stages } from "@/lib/demo-data";
import { useT } from "@/lib/i18n";
import type { CaseDetail, CaseSummary } from "@/lib/types";
import type {
  CaseOperations,
  StoredDocument,
  StoredGrievance,
} from "@/lib/operations-types";
import { ReadAloud } from "./read-aloud";
import {
  dateLabel,
  Empty,
  Loading,
  QueryError,
  useMoney,
  useWorkspaceQuery,
} from "./workspace-common";

export function CaseJourney({ item }: { item: CaseDetail }) {
  const t = useT();
  const { user, demoMode } = useAuthStore();
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [reason, setReason] = useState("");
  const current = stages.indexOf(item.current_stage);
  const next = stages[current + 1];
  const text = `${caseReference(item)}. ${t("stage")}: ${t(item.current_stage)}. ${t("nextStep")}: ${t(next ?? "complete")}.`;
  async function advance(destination = next) {
    if (!destination || !reason.trim()) return;
    setBusy(true);
    setMessage("");
    try {
      await api.transition(item.id, destination, reason.trim());
      await client.invalidateQueries({ queryKey: ["workspace"] });
      setReason("");
      setMessage(t("saved"));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Stage change failed",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <div className="panelHead">
        <div>
          <p className="eyebrow">{caseReference(item)}</p>
          <h2>{t("caseJourney")}</h2>
        </div>
        <span className={`statusBadge stage-${item.current_stage}`}>
          {t(item.current_stage)}
        </span>
      </div>
      <ol className="caseTimeline">
        {stages.map((stage, index) => {
          const event = item.stage_history
            .filter((entry) => entry.to_stage === stage)
            .at(-1);
          return (
            <li
              className={
                index < current ? "done" : index === current ? "current" : ""
              }
              key={stage}
            >
              <span className="timelineDot">
                {index < current ? <CheckCircle2 size={18} /> : index + 1}
              </span>
              <div>
                <strong>{t(stage)}</strong>
                <small>
                  {event
                    ? dateLabel(event.created_at)
                    : index === 0
                      ? dateLabel(item.created_at)
                      : index === current
                        ? t("stage")
                        : t("nextStep")}
                </small>
              </div>
            </li>
          );
        })}
      </ol>
      <div className="nextStep">
        <span>{t("nextStep")}</span>
        <strong>{t(next ?? "complete")}</strong>
      </div>
      {user?.role === "landowner" && <ReadAloud text={text} />}
      {user?.role !== "landowner" && next && (
        <form
          className="inlineForm"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(
              event.currentTarget,
              (event.nativeEvent as SubmitEvent).submitter,
            );
            void advance(
              data.get("destination") === "verification"
                ? "verification"
                : next,
            );
          }}
        >
          <label>
            Reason for stage change
            <input
              required
              maxLength={500}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <button
            disabled={busy || demoMode}
            className="button primary"
            type="submit"
          >
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <ArrowRight size={16} />
            )}{" "}
            Advance to {t(next)}
          </button>
          {item.current_stage === "objection" && (
            <button
              className="button secondary"
              type="submit"
              name="destination"
              value="verification"
              disabled={busy || demoMode}
            >
              Return to verification
            </button>
          )}
        </form>
      )}
      {item.stage_history.length > 0 && (
        <details className="history">
          <summary>Recorded activity ({item.stage_history.length})</summary>
          {[...item.stage_history].reverse().map((entry) => (
            <p key={entry.id}>
              <strong>{t(entry.to_stage)}</strong> ·{" "}
              {dateLabel(entry.created_at)}
              <br />
              <span>{entry.notes || "Stage updated"}</span>
            </p>
          ))}
        </details>
      )}
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
    </section>
  );
}

export function useCaseOperations(item: CaseSummary) {
  const query = useWorkspaceQuery(["case-operations", item.id], () =>
    apiFetch<CaseOperations>(`/cases/${item.id}/operations`),
  );
  const demoMode = useAuthStore((state) => state.demoMode);
  const empty: CaseOperations = {
    compensation: null,
    rr: null,
    documents: [],
    grievances: [],
    deadlines: [],
    affected_family_count: item.affected_family_count ?? 0,
    displaced_family_count: 0,
  };
  return { query, data: demoMode ? empty : query.data, demoMode };
}

export function CaseRecordSummary({ data }: { data: CaseOperations }) {
  const t = useT();
  const money = useMoney();
  return (
    <section className="panel">
      <div className="panelHead">
        <h2>
          {t("compensation")} &amp; {t("rehabilitation")}
        </h2>
      </div>
      <dl className="metadataGrid">
        <div>
          <dt>{t("assessed")}</dt>
          <dd>{money(data.compensation?.assessed_amount)}</dd>
        </div>
        <div>
          <dt>{t("paid")}</dt>
          <dd>{money(data.compensation?.disbursed_amount)}</dd>
        </div>
        <div>
          <dt>{t("status")}</dt>
          <dd>{t(data.compensation?.status ?? "notRecorded")}</dd>
        </div>
        <div>
          <dt>{t("dueDate")}</dt>
          <dd>
            {data.compensation?.due_date
              ? dateLabel(data.compensation.due_date)
              : t("notRecorded")}
          </dd>
        </div>
        <div>
          <dt>{t("rr")}</dt>
          <dd>{t(data.rr?.rehabilitation_stage ?? "notRecorded")}</dd>
        </div>
        <div>
          <dt>{t("families")}</dt>
          <dd>{data.affected_family_count}</dd>
        </div>
      </dl>
      {data.compensation?.reference && (
        <p className="helper">{data.compensation.reference}</p>
      )}
      {data.deadlines.length > 0 && (
        <div className="deadlineList">
          <h3>Recorded deadlines</h3>
          {data.deadlines.map((deadline) => (
            <p key={deadline.id}>
              <strong>
                {t(deadline.stage)} · {dateLabel(deadline.due_date)}
              </strong>
              <br />
              {deadline.basis} · {deadline.reference}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}

function DocumentReview({ document }: { document: StoredDocument }) {
  const { demoMode, user } = useAuthStore();
  const client = useQueryClient();
  const t = useT();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const form = new FormData(
      event.currentTarget,
      (event.nativeEvent as SubmitEvent).submitter,
    );
    const fields: Record<string, string | number | null> = {};
    for (const key of [
      "owner_name",
      "khasra_survey_number",
      "area_hectares",
      "document_date",
      "document_type",
    ]) {
      const value = String(form.get(key) ?? "").trim();
      fields[key] =
        key === "area_hectares"
          ? value === ""
            ? null
            : Number(value)
          : value || null;
    }
    try {
      await apiFetch(`/documents/${document.id}/confirm`, {
        method: "POST",
        body: JSON.stringify({
          fields,
          approved: form.get("decision") === "approve",
        }),
      });
      await client.invalidateQueries({ queryKey: ["workspace"] });
      setMessage(t("saved"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Review failed");
    } finally {
      setBusy(false);
    }
  }
  const fields = document.extracted_fields ?? {};
  return (
    <details className="documentRow">
      <summary>
        <FileText size={18} />
        <span>
          <strong>
            {t(document.document_type)} · v{document.version}
          </strong>
          <small>{dateLabel(document.created_at)}</small>
        </span>
        <span className={`statusBadge ${document.status}`}>
          {t(document.status)}
        </span>
      </summary>
      <div className="reviewBody">
        <p className="helper">
          {fields.extraction_method === "vision_llm"
            ? "Vision adapter"
            : "Tesseract OCR"}{" "}
          ·{" "}
          {typeof fields.confidence === "number"
            ? `${Math.round(fields.confidence * 100)}% extraction confidence`
            : "Confidence not recorded"}
          . Check the original document before approval.
        </p>
        <form onSubmit={confirm}>
          <div className="formGrid">
            {[
              ["owner_name", "Owner name"],
              ["khasra_survey_number", t("survey")],
              ["area_hectares", "Area (hectares)"],
              ["document_date", "Document date"],
              ["document_type", "Extracted document description"],
            ].map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  name={key}
                  type={key === "area_hectares" ? "number" : "text"}
                  min={key === "area_hectares" ? 0 : undefined}
                  step={key === "area_hectares" ? "any" : undefined}
                  defaultValue={String(fields[key] ?? "")}
                  readOnly={user?.role === "landowner"}
                />
              </label>
            ))}
          </div>
          {user?.role !== "landowner" && (
            <div className="buttonRow">
              <button
                type="submit"
                name="decision"
                value="approve"
                disabled={busy || demoMode}
                className="button primary"
              >
                Verify record
              </button>
              <button
                type="submit"
                name="decision"
                value="reject"
                disabled={busy || demoMode}
                className="button secondary"
              >
                Reject
              </button>
            </div>
          )}
        </form>
        {message && (
          <p role="status" className="notice">
            {message}
          </p>
        )}
      </div>
    </details>
  );
}

export function DocumentsView({ item }: { item: CaseSummary }) {
  const { data, query, demoMode } = useCaseOperations(item);
  const t = useT();
  const client = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState("land_record");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setMessage("The image must be 10 MB or smaller.");
      return;
    }
    if (!["image/png", "image/jpeg", "image/tiff"].includes(file.type)) {
      setMessage("Choose a PNG, JPEG or TIFF image.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const result = await api.uploadDocument(item.id, file, type);
      setMessage(
        `${t(result.status)} · ${Math.round(result.fields.confidence * 100)}% extraction confidence`,
      );
      setFile(null);
      await client.invalidateQueries({ queryKey: ["workspace"] });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }
  if (!demoMode && query.isError)
    return (
      <QueryError error={query.error} retry={() => void query.refetch()} />
    );
  if (!data) return <Loading />;
  return (
    <div className="twoColumns">
      <section className="panel">
        <div className="panelHead">
          <h2>{t("documents")}</h2>
          <span className="count">{data.documents.length}</span>
        </div>
        {data.documents.length ? (
          data.documents.map((document) => (
            <DocumentReview
              document={document}
              key={`${document.id}-${document.status}`}
            />
          ))
        ) : (
          <Empty>{t("noDocuments")}</Empty>
        )}
      </section>
      <section className="panel">
        <div className="panelHead">
          <h2>{t("chooseFile")}</h2>
        </div>
        <form onSubmit={upload}>
          <label>
            {t("documentType")}
            <select
              value={type}
              onChange={(event) => setType(event.target.value)}
            >
              {[
                "land_record",
                "sale_deed",
                "identity_proof",
                "award_notice",
                "other",
              ].map((key) => (
                <option value={key} key={key}>
                  {t(key)}
                </option>
              ))}
            </select>
          </label>
          <label className="dropzone">
            <UploadCloud size={30} />
            <strong>{file?.name ?? t("chooseFile")}</strong>
            <small>PNG, JPEG, TIFF · 10 MB maximum</small>
            <input
              type="file"
              required
              accept="image/png,image/jpeg,image/tiff"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <button
            type="submit"
            className="button primary full"
            disabled={busy || demoMode || !file}
          >
            {busy ? (
              <>
                <LoaderCircle className="spin" size={16} /> Reading document…
              </>
            ) : (
              t("upload")
            )}
          </button>
        </form>
        {message && (
          <p className="notice" role="status">
            {message}
          </p>
        )}
        <p className="helper">
          Extracted fields and versions are retained. Original scan files are
          not stored by this prototype.
        </p>
      </section>
    </div>
  );
}

function GrievanceResponseForm({ item }: { item: StoredGrievance }) {
  const client = useQueryClient();
  const t = useT();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const values = new FormData(event.currentTarget);
    try {
      await apiFetch(`/grievances/${item.id}/confirm`, {
        method: "POST",
        body: JSON.stringify({
          category: values.get("category"),
          priority: values.get("priority"),
          department: values.get("department"),
        }),
      });
      await apiFetch(`/grievances/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: values.get("status"),
          response: values.get("response"),
        }),
      });
      await client.invalidateQueries({ queryKey: ["workspace"] });
      setMessage(t("saved"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save} className="inlineForm">
      <label>
        Confirm category
        <select name="category" defaultValue={item.category}>
          {[
            "compensation",
            "ownership",
            "measurement",
            "rehabilitation",
            "process",
          ].map((category) => (
            <option key={category} value={category}>
              {t(category)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Confirm priority
        <select name="priority" defaultValue={item.priority}>
          {["low", "medium", "high", "urgent"].map((priority) => (
            <option key={priority}>{priority}</option>
          ))}
        </select>
      </label>
      <label>
        Confirm department
        <input
          name="department"
          required
          minLength={3}
          maxLength={120}
          defaultValue={item.department}
        />
      </label>
      <label>
        {t("status")}
        <select name="status" defaultValue={item.status}>
          {["open", "assigned", "resolved"].map((status) => (
            <option value={status} key={status}>
              {t(status)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Response
        <textarea
          name="response"
          required
          minLength={3}
          maxLength={4000}
          defaultValue={item.response ?? ""}
        />
      </label>
      <button disabled={busy} className="button primary">
        {t("save")}
      </button>
      {message && <p role="status">{message}</p>}
    </form>
  );
}

export function GrievancesView({ item }: { item: CaseSummary }) {
  const { data, query, demoMode } = useCaseOperations(item);
  const t = useT();
  const client = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const result = await api.createGrievance(item.id, description);
      setMessage(
        `${t(result.classification.category)} · ${result.classification.suggested_department}. Human confirmation required.`,
      );
      setDescription("");
      await client.invalidateQueries({ queryKey: ["workspace"] });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Submission failed");
    } finally {
      setBusy(false);
    }
  }
  if (!demoMode && query.isError)
    return (
      <QueryError error={query.error} retry={() => void query.refetch()} />
    );
  if (!data) return <Loading />;
  return (
    <div className="twoColumns">
      <section className="panel">
        <div className="panelHead">
          <h2>{t("grievances")}</h2>
          <span className="count">{data.grievances.length}</span>
        </div>
        {data.grievances.length === 0 && <Empty>{t("noGrievances")}</Empty>}
        {data.grievances.map((grievance) => (
          <article className="grievanceItem" key={grievance.id}>
            <div>
              <span className="eyebrow">
                GRV-{grievance.id.slice(0, 8).toUpperCase()}
              </span>
              <span className={`statusBadge ${grievance.status}`}>
                {t(grievance.status)}
              </span>
            </div>
            <h3>{t(grievance.category)}</h3>
            <p>
              {grievance.description ??
                "Description was not retained for this older record."}
            </p>
            <small>
              {grievance.department} · {grievance.priority} ·{" "}
              {dateLabel(grievance.created_at)}
            </small>
            {grievance.response && (
              <blockquote>{grievance.response}</blockquote>
            )}
            {user?.role !== "landowner" && !demoMode && (
              <details>
                <summary>Review and respond</summary>
                <GrievanceResponseForm item={grievance} />
              </details>
            )}
          </article>
        ))}
      </section>
      <section className="panel">
        <div className="panelHead">
          <h2>{t("submit")}</h2>
        </div>
        <form onSubmit={submit}>
          <label>
            {t("describeIssue")}
            <textarea
              required
              minLength={10}
              maxLength={4000}
              rows={7}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          <button className="button primary" disabled={busy || demoMode}>
            {busy ? <LoaderCircle className="spin" size={17} /> : t("submit")}
          </button>
        </form>
        {message && (
          <p role="status" className="notice">
            {message}
          </p>
        )}
        <p className="helper">
          Classification suggests a category and department. An officer must
          review the suggestion.
        </p>
      </section>
    </div>
  );
}
