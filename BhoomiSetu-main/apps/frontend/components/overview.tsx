"use client";
import Link from "next/link";
import { api, apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import { stages } from "@/lib/demo-data";
import type { Dashboard, Inbox } from "@/lib/operations-types";
import {
  dateLabel,
  Metric,
  QueryError,
  useMoney,
  useWorkspaceQuery,
} from "./workspace-common";

export function Overview({
  dashboard,
  inbox,
}: {
  dashboard: Dashboard;
  inbox?: Inbox;
}) {
  const t = useT();
  const money = useMoney();
  const { user, demoMode } = useAuthStore();
  const management = user?.role !== "landowner" && user?.role !== "officer";
  const isAdmin =
    user?.role === "district_admin" || user?.role === "senior_admin";
  const predictions = useWorkspaceQuery(
    ["aggregate-predictions"],
    api.aggregatePredictions,
    isAdmin,
  );
  const audit = useWorkspaceQuery(
    ["audit"],
    () =>
      apiFetch<Array<{ id: string; action: string; created_at: string }>>(
        "/audit-log?limit=8",
      ),
    isAdmin,
  );
  const checks = useWorkspaceQuery(
    ["audit-check"],
    () =>
      apiFetch<{ valid: boolean; checked_rows: number; message: string }>(
        "/audit-log/verify",
      ),
    isAdmin,
  );
  const attention =
    inbox?.items.filter((item) => item.severity !== "info").slice(0, 4) ?? [];
  const metrics =
    user?.role === "landowner"
      ? [
          [
            t("activeCases"),
            dashboard.case_count - dashboard.possession_cases,
            "Linked to this account",
          ],
          [
            t("paid"),
            money(dashboard.disbursed_amount),
            `${dashboard.payment_amounts_recorded} payment amounts recorded`,
          ],
          [t("grievances"), dashboard.open_grievances, "Awaiting resolution"],
          [
            t("families"),
            dashboard.affected_families,
            "Recorded affected households",
          ],
        ]
      : user?.role === "officer"
        ? [
            ["Assigned cases", dashboard.case_count, "Visible to your account"],
            [
              "Verification queue",
              dashboard.stages.verification ?? 0,
              "Cases in verification",
            ],
            [
              "Open grievances",
              dashboard.open_grievances,
              "Awaiting resolution",
            ],
            [
              "Needs attention",
              dashboard.alerts_requiring_attention,
              "Generated from records and dates",
            ],
          ]
        : [
            [
              "Notified area",
              `${dashboard.area_notified_hectares.toFixed(2)} ha`,
              `${dashboard.case_count} case parcels`,
            ],
            [
              "Acquired area",
              `${dashboard.area_acquired_hectares.toFixed(2)} ha`,
              "Possession-stage parcels",
            ],
            [
              t("paid"),
              money(dashboard.disbursed_amount),
              `${dashboard.payment_amounts_recorded}/${dashboard.case_count} amounts recorded`,
            ],
            [
              t("families"),
              dashboard.affected_families,
              `${dashboard.displaced_families} displaced families`,
            ],
            [
              "R&R completed",
              dashboard.rr_completed,
              `${dashboard.rr_recorded} cases have R&R records`,
            ],
            [
              "Acquisition progress",
              `${dashboard.completion_pct}%`,
              "Cases reaching possession",
            ],
            [
              "Possession",
              dashboard.possession_cases,
              `${dashboard.case_count} total cases`,
            ],
            [
              "Timeline adherence",
              dashboard.timeline_adherence_pct === null
                ? "Not recorded"
                : `${dashboard.timeline_adherence_pct}%`,
              `${dashboard.recorded_deadlines_due} recorded deadlines due`,
            ],
          ];
  return (
    <>
      <section className={`metricBand ${management ? "executiveMetrics" : ""}`}>
        {metrics.map(([label, value, detail]) => (
          <Metric
            key={label}
            label={String(label)}
            value={value}
            detail={String(detail)}
          />
        ))}
      </section>
      <div className="twoColumns">
        <section className="panel">
          <div className="panelHead">
            <div>
              <p className="eyebrow">Workflow progress</p>
              <h2>Cases by stage</h2>
            </div>
            <span className="count">{dashboard.case_count}</span>
          </div>
          <div className="stageBars">
            {stages.map((stage) => {
              const count = dashboard.stages[stage] ?? 0;
              return (
                <Link
                  href={`/portal/${user?.role}?view=cases&stage=${stage}`}
                  key={stage}
                >
                  <span>{t(stage)}</span>
                  <div>
                    <i
                      className={`stage-${stage}`}
                      style={{
                        width: `${dashboard.case_count ? (count * 100) / dashboard.case_count : 0}%`,
                      }}
                    />
                  </div>
                  <strong>{count}</strong>
                </Link>
              );
            })}
          </div>
        </section>
        <section className="panel">
          <div className="panelHead">
            <div>
              <p className="eyebrow">Action queue</p>
              <h2>Needs attention</h2>
            </div>
            <Link
              href={`/portal/${user?.role}?view=alerts`}
              className="textLink"
            >
              View inbox →
            </Link>
          </div>
          {attention.length ? (
            attention.map((alert) => (
              <Link
                className={`attentionRow ${alert.severity}`}
                href={`/portal/${user?.role}?view=cases&case=${alert.case_id}`}
                key={alert.key}
              >
                <i />
                <div>
                  <strong>{alert.title}</strong>
                  <small>{alert.detail}</small>
                </div>
                <span>→</span>
              </Link>
            ))
          ) : (
            <div className="emptyState">
              <p>No active alerts in the loaded inbox.</p>
              <small>
                Rules check stage age, review queues and recorded deadlines.
              </small>
            </div>
          )}
        </section>
      </div>
      {management && (
        <section className="panel">
          <div className="panelHead">
            <div>
              <p className="eyebrow">Comparative view</p>
              <h2>Project performance</h2>
            </div>
            <Link
              href={`/portal/${user?.role}?view=reports`}
              className="textLink"
            >
              Build a report →
            </Link>
          </div>
          <div className="tableScroll">
            <table>
              <caption className="srOnly">
                Project comparison with state completion rates
              </caption>
              <thead>
                <tr>
                  <th>Project</th>
                  <th>District</th>
                  <th>Cases</th>
                  <th>Families</th>
                  <th>Completion</th>
                  <th>State average</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.projects.map((row) => (
                  <tr key={row.project_id}>
                    <td>{row.group.split(" / ")[0]}</td>
                    <td>{row.district}</td>
                    <td>{row.case_count}</td>
                    <td>{row.affected_families}</td>
                    <td>{row.completion_pct}%</td>
                    <td>
                      {dashboard.states.find(
                        (state) => state.state === row.state,
                      )?.completion_pct ?? 0}
                      %
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="trendStrip">
            <span>
              <strong>{dashboard.trend.current_transitions}</strong> workflow
              changes this month
            </span>
            <span>
              <strong>{dashboard.trend.previous_transitions}</strong> in the
              previous comparison window
            </span>
            <span>
              <strong>
                {dashboard.trend.difference > 0 ? "+" : ""}
                {dashboard.trend.difference}
              </strong>{" "}
              change in count
            </span>
          </div>
          <p className="helper">
            {dashboard.trend.label}. Changes include any recorded return to
            verification.
          </p>
        </section>
      )}
      {isAdmin && (
        <div className="twoColumns">
          <section className="panel">
            <div className="panelHead">
              <div>
                <p className="eyebrow">Synthetic-trained model</p>
                <h2>Procedural risk</h2>
              </div>
            </div>
            {demoMode ? (
              <p className="notice">
                Sign in to calculate predictions from the stored synthetic
                cases.
              </p>
            ) : predictions.isError ? (
              <QueryError
                error={predictions.error}
                retry={() => void predictions.refetch()}
              />
            ) : predictions.data ? (
              <div className="metricBand">
                <Metric
                  label="Cases at high risk"
                  value={`${predictions.data.high_risk_pct}%`}
                  detail={`${predictions.data.case_count} cases evaluated`}
                />
                <Metric
                  label="Disbursal timeline"
                  value={`${predictions.data.avg_disbursal_days} days`}
                  detail="Model average; not a payment commitment"
                />
              </div>
            ) : (
              <p>Calculating model estimates…</p>
            )}
            <p className="modelDisclosure">
              1,800 synthetic training histories; no real government case data.
              Synthetic holdout: delay MAE 12.92 days (R² 0.951); timeline MAE
              5.83 days (R² 0.898). Real-world accuracy has not been validated.
            </p>
          </section>
          <section className="panel">
            <div className="panelHead">
              <div>
                <p className="eyebrow">Activity record</p>
                <h2>Audit trail</h2>
              </div>
            </div>
            {checks.data && (
              <p className={checks.data.valid ? "successNote" : "errorNote"}>
                {checks.data.message} · {checks.data.checked_rows} rows
              </p>
            )}
            {audit.isError && (
              <QueryError
                error={audit.error}
                retry={() => void audit.refetch()}
              />
            )}
            {audit.data?.map((row) => (
              <details className="auditRow" key={row.id}>
                <summary>
                  {row.action.split(":")[0]}{" "}
                  <small>{dateLabel(row.created_at)}</small>
                </summary>
                <pre>{row.action}</pre>
              </details>
            ))}
            <p className="helper">
              Hash chaining is tamper-evident, not blockchain.
            </p>
          </section>
        </div>
      )}
      <p className="helper">{dashboard.notice}</p>
    </>
  );
}
