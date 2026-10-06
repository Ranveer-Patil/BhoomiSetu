"use client";
import { useState, type FormEvent, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import { stages } from "@/lib/demo-data";
import type { CaseSummary } from "@/lib/types";
import { CaseRecordSummary, useCaseOperations } from "./case-workspace";
import { Loading, QueryError } from "./workspace-common";

function RecordForm({
  title,
  path,
  method = "PUT",
  children,
  transform,
}: {
  title: string;
  path: string;
  method?: string;
  children: ReactNode;
  transform: (form: FormData) => object;
}) {
  const client = useQueryClient();
  const t = useT();
  const demoMode = useAuthStore((state) => state.demoMode);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const values = new FormData(event.currentTarget);
    try {
      await apiFetch(path, { method, body: JSON.stringify(transform(values)) });
      await client.invalidateQueries({ queryKey: ["workspace"] });
      setMessage(t("saved"));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not save this record",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <div className="panelHead">
        <h2>{title}</h2>
      </div>
      <form onSubmit={submit}>
        <div className="formGrid">{children}</div>
        <button className="button primary" disabled={busy || demoMode}>
          {t(busy ? "saving" : "save")}
        </button>
      </form>
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
    </section>
  );
}

export function OperationsForms({ item }: { item: CaseSummary }) {
  const { data, query, demoMode } = useCaseOperations(item);
  const user = useAuthStore((state) => state.user);
  const t = useT();
  if (!demoMode && query.isError)
    return (
      <QueryError error={query.error} retry={() => void query.refetch()} />
    );
  if (!data) return <Loading />;
  if (
    !["authority", "district_admin", "senior_admin"].includes(user?.role ?? "")
  )
    return (
      <>
        <CaseRecordSummary data={data} />
        <p className="notice">
          Project authorities and administrators can update these records.
        </p>
      </>
    );
  const compensation = data.compensation;
  const rr = data.rr;
  return (
    <>
      <p className="notice">
        Enter amounts from an authorized record. BhoomiSetu does not calculate
        legal compensation or issue payments.
      </p>
      <div className="twoColumns">
        <RecordForm
          title={t("compensation")}
          path={`/cases/${item.id}/compensation`}
          transform={(form) => ({
            status: form.get("status"),
            assessed_amount: form.get("assessed_amount") || null,
            disbursed_amount: form.get("disbursed_amount") || null,
            due_date: form.get("due_date") || null,
            reference: form.get("reference"),
          })}
        >
          <label>
            {t("status")}
            <select
              name="status"
              defaultValue={compensation?.status ?? "assessed"}
            >
              {["assessed", "approved", "disbursed"].map((status) => (
                <option key={status} value={status}>
                  {t(status)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("dueDate")}
            <input
              type="date"
              name="due_date"
              defaultValue={compensation?.due_date ?? ""}
            />
          </label>
          <label>
            {t("assessed")} (₹)
            <input
              type="number"
              name="assessed_amount"
              min="0"
              max="99999999999999.99"
              step="0.01"
              defaultValue={compensation?.assessed_amount ?? ""}
            />
          </label>
          <label>
            {t("paid")} (₹)
            <input
              type="number"
              name="disbursed_amount"
              min="0"
              max="99999999999999.99"
              step="0.01"
              defaultValue={compensation?.disbursed_amount ?? ""}
            />
          </label>
          <label className="spanFull">
            {t("reference")}
            <textarea
              name="reference"
              required
              minLength={3}
              maxLength={500}
              defaultValue={compensation?.reference ?? ""}
            />
          </label>
        </RecordForm>
        <RecordForm
          title={t("rr")}
          path={`/cases/${item.id}/rr`}
          transform={(form) => ({
            rehabilitation_stage: form.get("rehabilitation_stage"),
            resettlement_site_assigned: form.get("site") === "on",
            families_supported: Number(form.get("families_supported")),
            notes: form.get("notes"),
          })}
        >
          <label>
            {t("stage")}
            <select
              name="rehabilitation_stage"
              defaultValue={rr?.rehabilitation_stage ?? "assessment"}
            >
              {[
                "assessment",
                "planned",
                "in_progress",
                "completed",
                "not_required",
              ].map((stage) => (
                <option key={stage} value={stage}>
                  {t(stage)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Families supported
            <input
              type="number"
              name="families_supported"
              required
              min={0}
              max={data.affected_family_count}
              defaultValue={rr?.families_supported ?? 0}
            />
          </label>
          <label className="checkboxLabel spanFull">
            <input
              name="site"
              type="checkbox"
              defaultChecked={rr?.resettlement_site_assigned}
            />
            Resettlement site assigned
          </label>
          <label className="spanFull">
            Notes / reference
            <textarea
              name="notes"
              required
              minLength={3}
              maxLength={500}
              defaultValue={rr?.notes ?? ""}
            />
          </label>
        </RecordForm>
        <RecordForm
          title="Family counts"
          path={`/cases/${item.id}/families`}
          method="PATCH"
          transform={(form) => ({
            affected_family_count: Number(form.get("affected")),
            displaced_family_count: Number(form.get("displaced")),
          })}
        >
          <label>
            {t("families")}
            <input
              type="number"
              name="affected"
              required
              min={0}
              defaultValue={data.affected_family_count}
            />
          </label>
          <label>
            {t("displaced")}
            <input
              type="number"
              name="displaced"
              required
              min={0}
              defaultValue={data.displaced_family_count}
            />
          </label>
        </RecordForm>
        <RecordForm
          title="Record a deadline"
          path={`/cases/${item.id}/deadlines`}
          method="POST"
          transform={(form) => ({
            stage: form.get("stage"),
            due_date: form.get("due_date"),
            basis: form.get("basis"),
            reference: form.get("reference"),
          })}
        >
          <label>
            {t("stage")}
            <select name="stage" defaultValue={item.current_stage}>
              {stages.map((stage) => (
                <option key={stage} value={stage}>
                  {t(stage)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("dueDate")}
            <input type="date" name="due_date" required />
          </label>
          <label>
            Deadline basis
            <select name="basis">
              <option value="operational">Operational target</option>
              <option value="statutory">Statutory — authority supplied</option>
            </select>
          </label>
          <label>
            {t("reference")}
            <input
              name="reference"
              required
              minLength={5}
              maxLength={500}
              placeholder="Order, applicable provision and date basis"
            />
          </label>
        </RecordForm>
      </div>
      <CaseRecordSummary data={data} />
    </>
  );
}
