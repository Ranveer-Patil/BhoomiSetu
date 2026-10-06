"use client";
import { useEffect, useState } from "react";
import { Download, Printer } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import type { Dashboard } from "@/lib/operations-types";
import {
  Empty,
  Loading,
  QueryError,
  useWorkspaceQuery,
} from "./workspace-common";

const columnOptions = {
  group: "Group",
  state: "State",
  district: "District",
  case_count: "Cases",
  area_notified_hectares: "Notified area (ha)",
  area_acquired_hectares: "Acquired area (ha)",
  affected_families: "Affected families",
  displaced_families: "Displaced families",
  assessed_amount: "Assessed amount (INR)",
  disbursed_amount: "Disbursed amount (INR)",
  compensation_recorded: "Compensation records",
  amounts_recorded: "Assessed amounts recorded",
  payment_amounts_recorded: "Payment amounts recorded",
  compensation_disbursed: "Fully disbursed cases",
  rr_recorded: "R&R records",
  rr_completed: "R&R completed",
  rr_families_supported: "Families supported",
  possession_cases: "Possession cases",
  completion_pct: "Completion (%)",
};
type Column = keyof typeof columnOptions;
export function ReportsView({ dashboard }: { dashboard?: Dashboard }) {
  const [type, setType] = useState("project");
  const [state, setState] = useState("");
  const [district, setDistrict] = useState("");
  const [columns, setColumns] = useState<Column[]>([
    "group",
    "case_count",
    "affected_families",
    "disbursed_amount",
    "rr_completed",
    "completion_pct",
  ]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [downloadFile, setDownloadFile] = useState<{
    url: string;
    name: string;
  } | null>(null);
  useEffect(
    () => () => {
      if (downloadFile) URL.revokeObjectURL(downloadFile.url);
    },
    [downloadFile],
  );
  const demoMode = useAuthStore((session) => session.demoMode);
  const params = new URLSearchParams({
    columns: columns.join(","),
    ...(state ? { state } : {}),
    ...(district ? { district } : {}),
  });
  const path = `/reports/${type}?${params}`;
  const query = useWorkspaceQuery(
    ["report", path],
    () =>
      apiFetch<{
        rows: Record<string, string | number | null>[];
        generated_at: string;
      }>(`${path}&format=json`),
    columns.length > 0,
  );
  async function download() {
    setBusy(true);
    setMessage("");
    try {
      const blob = await apiFetch<Blob>(`${path}&format=csv`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `bhoomisetu-${type}.csv`;
      setDownloadFile({ url, name: link.download });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Export failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel reportPanel">
      <div className="panelHead">
        <div>
          <h2>Custom MIS report</h2>
          <p className="helper">
            Choose columns and filters, then export CSV or print to PDF.
          </p>
        </div>
        <div className="reportActions">
          <button
            className="button secondary"
            disabled={
              demoMode ||
              !query.data?.rows.length ||
              columns.length === 0 ||
              query.isError ||
              query.isPending
            }
            onClick={() => window.print()}
          >
            <Printer size={16} /> Print / save PDF
          </button>
          <button
            className="button primary"
            disabled={
              busy ||
              demoMode ||
              columns.length === 0 ||
              query.isPending ||
              query.isError
            }
            onClick={() => void download()}
          >
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>
      <p className="printOnly">
        BhoomiSetu · {type} report · {state || "All states"} /{" "}
        {district || "All districts"}. Generated:{" "}
        {query.data
          ? new Date(query.data.generated_at).toLocaleString("en-IN")
          : ""}
        . Synthetic showcase; amounts are recorded entries.
      </p>
      <div className="filterBar">
        <label>
          Report by
          <select
            value={type}
            onChange={(event) => setType(event.target.value)}
          >
            {["project", "state", "district", "compensation"].map((key) => (
              <option value={key} key={key}>
                {key[0].toUpperCase() + key.slice(1)}
              </option>
            ))}
          </select>
        </label>
        <label>
          State
          <select
            value={state}
            onChange={(event) => {
              setState(event.target.value);
              setDistrict("");
            }}
          >
            <option value="">All states</option>
            {dashboard?.states.map((row) => (
              <option key={row.state}>{row.state}</option>
            ))}
          </select>
        </label>
        <label>
          District
          <select
            value={district}
            onChange={(event) => setDistrict(event.target.value)}
          >
            <option value="">All districts</option>
            {dashboard?.districts
              .filter((row) => !state || row.state === state)
              .map((row) => (
                <option key={row.group}>{row.district}</option>
              ))}
          </select>
        </label>
      </div>
      <details className="reportColumns">
        <summary>Choose report columns ({columns.length})</summary>
        <div>
          {Object.entries(columnOptions).map(([key, label]) => (
            <label className="checkboxLabel" key={key}>
              <input
                type="checkbox"
                checked={columns.includes(key as Column)}
                onChange={(event) =>
                  setColumns(
                    event.target.checked
                      ? [...columns, key as Column]
                      : columns.filter((column) => column !== key),
                  )
                }
              />
              {label}
            </label>
          ))}
        </div>
      </details>
      {demoMode ? (
        <Empty>CSV reports require an API session.</Empty>
      ) : columns.length === 0 ? (
        <Empty>Select at least one column.</Empty>
      ) : query.isError ? (
        <QueryError error={query.error} retry={() => void query.refetch()} />
      ) : !query.data ? (
        <Loading />
      ) : query.data.rows.length === 0 ? (
        <Empty>No records match these filters.</Empty>
      ) : (
        <div className="tableScroll">
          <table>
            <caption className="srOnly">{type} MIS report</caption>
            <thead>
              <tr>
                {columns.map((key) => (
                  <th key={key}>{columnOptions[key]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {query.data.rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((key) => (
                    <td key={key}>{row[key] ?? "Not recorded"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {downloadFile && (
        <p className="notice reportDownload" role="status">
          CSV is ready.{" "}
          <a href={downloadFile.url} download={downloadFile.name}>
            Download {downloadFile.name}
          </a>
        </p>
      )}
      {message && (
        <p role="status" className="errorNote">
          {message}
        </p>
      )}
      <p className="helper">
        Amounts reflect entered records, never predictions. Blank amounts mean
        not recorded. Acquired area includes possession-stage parcels. Showcase
        data is synthetic.
      </p>
    </section>
  );
}
