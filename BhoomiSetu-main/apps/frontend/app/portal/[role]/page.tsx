"use client";

import { Suspense, useEffect, useState, useSyncExternalStore } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Search } from "lucide-react";
import { PortalShell, type WorkspaceView } from "@/components/portal-shell";
import {
  CaseJourney,
  CaseRecordSummary,
  DocumentsView,
  GrievancesView,
  useCaseOperations,
} from "@/components/case-workspace";
import { OperationsForms } from "@/components/operations-forms";
import { Overview } from "@/components/overview";
import { ReportsView } from "@/components/reports-view";
import { InboxView } from "@/components/inbox-view";
import { LanguageSelect } from "@/components/language-select";
import {
  Empty,
  Loading,
  QueryError,
  useWorkspaceQuery,
} from "@/components/workspace-common";
import { api, apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { caseReference, demoCases, demoParcels, stages } from "@/lib/demo-data";
import { useT } from "@/lib/i18n";
import type { CaseSummary, ParcelFeature, Role } from "@/lib/types";
import type { Dashboard, Inbox } from "@/lib/operations-types";

const ParcelMap = dynamic(() => import("@/components/parcel-map"), {
  ssr: false,
  loading: () => <Loading />,
});
const validRoles: Role[] = [
  "landowner",
  "officer",
  "authority",
  "district_admin",
  "senior_admin",
];
const views: WorkspaceView[] = [
  "overview",
  "cases",
  "documents",
  "grievances",
  "map",
  "operations",
  "reports",
  "alerts",
  "settings",
];
const subscribe = () => () => undefined;

function demoDashboard(cases: CaseSummary[]): Dashboard {
  const stageCounts = Object.fromEntries(
    stages.map((stage) => [
      stage,
      cases.filter((item) => item.current_stage === stage).length,
    ]),
  );
  return {
    case_count: cases.length,
    project_count: 1,
    affected_families: cases.reduce(
      (sum, item) => sum + (item.affected_family_count ?? 0),
      0,
    ),
    displaced_families: 0,
    area_notified_hectares: 0,
    area_acquired_hectares: 0,
    assessed_amount: null,
    disbursed_amount: null,
    compensation_recorded: 0,
    compensation_disbursed: 0,
    amounts_recorded: 0,
    payment_amounts_recorded: 0,
    rr_recorded: 0,
    rr_completed: 0,
    rr_families_supported: 0,
    possession_cases: stageCounts.possession,
    completion_pct: cases.length
      ? Math.round((stageCounts.possession * 100) / cases.length)
      : 0,
    stages: stageCounts,
    open_grievances: 0,
    alerts_requiring_attention: 0,
    recorded_deadlines_due: 0,
    deadline_breaches: 0,
    timeline_adherence_pct: null,
    projects: [],
    states: [],
    districts: [],
    trend: {
      current_transitions: 0,
      previous_transitions: 0,
      difference: 0,
      label: "History comparisons require an API session.",
    },
    generated_at: "",
    notice:
      "Synthetic preview. Unrecorded amounts and deadlines are not estimated.",
  };
}

function SelectedCase({ item, role }: { item: CaseSummary; role: Role }) {
  const { demoMode } = useAuthStore();
  const t = useT();
  const operations = useCaseOperations(item);
  const detail = useWorkspaceQuery(["case", item.id], () =>
    api.caseDetail(item.id),
  );
  const prediction = useWorkspaceQuery(
    ["prediction", item.id],
    () => api.delayPrediction(item.id),
    role !== "landowner",
  );
  const [fixture, setFixture] = useState("");
  const [checking, setChecking] = useState(false);
  const current = demoMode
    ? demoCases.find((row) => row.id === item.id)
    : detail.data;
  if (!demoMode && detail.isError)
    return (
      <QueryError error={detail.error} retry={() => void detail.refetch()} />
    );
  if (!current) return <Loading />;
  return (
    <div className="caseDetailStack">
      <CaseJourney item={current} />
      {operations.query.isError ? (
        <QueryError
          error={operations.query.error}
          retry={() => void operations.query.refetch()}
        />
      ) : operations.data ? (
        <CaseRecordSummary data={operations.data} />
      ) : (
        <Loading />
      )}
      {role !== "landowner" && (
        <section className="panel">
          <div className="panelHead">
            <h2>Delay estimate</h2>
            <span className="dataBadge">Synthetic-trained model</span>
          </div>
          {prediction.data ? (
            <>
              <div className="predictionNumber">
                {prediction.data.predicted_days_remaining}
                <small>estimated days remaining</small>
              </div>
              <p>
                {prediction.data.risk_band} risk ·{" "}
                {prediction.data.top_features
                  .map((feature) => feature.feature.replaceAll("_", " "))
                  .join(", ")}
              </p>
              <p className="modelDisclosure">
                Synthetic holdout MAE {prediction.data.holdout_mae_days} days.
                Not validated on real case histories. This estimate does not
                determine compensation amounts or legal decisions.
              </p>
            </>
          ) : prediction.isError ? (
            <QueryError
              error={prediction.error}
              retry={() => void prediction.refetch()}
            />
          ) : (
            <p>
              {demoMode
                ? "Sign in to calculate a model estimate."
                : "Calculating…"}
            </p>
          )}
        </section>
      )}
      {role === "authority" && (
        <section className="panel">
          <div className="panelHead">
            <h2>Government adapter preview</h2>
          </div>
          <p className="notice">
            API Setu / NGDRS fixtures — not live government data.
          </p>
          <button
            className="button secondary"
            disabled={demoMode || checking}
            onClick={async () => {
              setChecking(true);
              try {
                const result = await api.landRecord("PRR-1001");
                setFixture(result.source.notice);
              } catch (error) {
                setFixture(
                  error instanceof Error
                    ? error.message
                    : "Adapter unavailable",
                );
              } finally {
                setChecking(false);
              }
            }}
          >
            Inspect sample land-record adapter
          </button>
          <p role="status">{fixture}</p>
          <small>
            {t("survey")}: PRR-1001 · fixed adapter example, unrelated to the
            selected case.
          </small>
        </section>
      )}
    </div>
  );
}

function Workspace() {
  const params = useParams<{ role: Role }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const t = useT();
  const role = params.role;
  const requested = searchParams.get("view") ?? "overview";
  const view: WorkspaceView = views.includes(requested as WorkspaceView)
    ? (requested as WorkspaceView)
    : "overview";
  const { user, demoMode } = useAuthStore();
  const hydrated = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  const authorized =
    hydrated && !!user && user.role === role && validRoles.includes(role);
  const caseQuery = useWorkspaceQuery(["cases"], api.cases, authorized);
  const summaryQuery = useWorkspaceQuery(
    ["dashboard"],
    () => apiFetch<Dashboard>("/dashboard/summary"),
    authorized,
  );
  const mapQuery = useWorkspaceQuery(
    ["parcels"],
    () => apiFetch<ParcelFeature[]>("/gis/parcels"),
    authorized,
  );
  const inboxQuery = useWorkspaceQuery(
    ["alerts"],
    () => apiFetch<Inbox>("/alerts"),
    authorized,
  );
  const [search, setSearch] = useState("");
  const stageFilter = searchParams.get("stage") ?? "all";
  useEffect(() => {
    if (hydrated && !user) router.replace("/login");
    else if (hydrated && (!validRoles.includes(role) || user?.role !== role))
      router.replace("/forbidden");
  }, [hydrated, user, role, router]);
  if (!authorized) return <Loading />;
  const cases = demoMode
    ? role === "landowner"
      ? demoCases.slice(0, 3)
      : demoCases
    : (caseQuery.data ?? []);
  const parcels = demoMode
    ? demoParcels.filter((parcel) =>
        cases.some((item) => item.id === parcel.case_id),
      )
    : (mapQuery.data ?? []);
  const dashboard = demoMode ? demoDashboard(cases) : summaryQuery.data;
  const inbox = demoMode ? { items: [], generated_at: "" } : inboxQuery.data;
  const selected =
    cases.find((item) => item.id === searchParams.get("case")) ?? cases[0];
  const filtered = cases.filter(
    (item) =>
      (stageFilter === "all" || item.current_stage === stageFilter) &&
      `${caseReference(item)} ${parcels.find((parcel) => parcel.case_id === item.id)?.survey_number ?? ""}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const target = (key: string, caseId?: string) =>
    `/portal/${role}?view=${key}${caseId ? `&case=${caseId}` : ""}`;
  const canReport = ["authority", "district_admin", "senior_admin"].includes(
    role,
  );
  let body;
  if (!demoMode && caseQuery.isError)
    body = (
      <QueryError
        error={caseQuery.error}
        retry={() => void caseQuery.refetch()}
      />
    );
  else if (!demoMode && caseQuery.isPending) body = <Loading />;
  else if (view === "overview")
    body = summaryQuery.isError ? (
      <QueryError
        error={summaryQuery.error}
        retry={() => void summaryQuery.refetch()}
      />
    ) : dashboard ? (
      <Overview dashboard={dashboard} inbox={inbox} />
    ) : (
      <Loading />
    );
  else if (view === "reports")
    body = canReport ? (
      <ReportsView dashboard={dashboard} />
    ) : (
      <Empty>This role cannot access management reports.</Empty>
    );
  else if (view === "alerts")
    body = inboxQuery.isError ? (
      <QueryError
        error={inboxQuery.error}
        retry={() => void inboxQuery.refetch()}
      />
    ) : inbox ? (
      <InboxView inbox={inbox} />
    ) : (
      <Loading />
    );
  else if (view === "settings")
    body = (
      <section className="panel">
        <div className="panelHead">
          <h2>{t("account")}</h2>
        </div>
        <dl className="metadataGrid">
          <div>
            <dt>Name</dt>
            <dd>{user.name}</dd>
          </div>
          <div>
            <dt>{t("email")}</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Role</dt>
            <dd>{t(role)}</dd>
          </div>
        </dl>
        <h3>{t("language")}</h3>
        <LanguageSelect />
        <p className="helper">
          Interface labels and stage names are translated. Submitted records and
          extracted text stay in their original language. Read-aloud depends on
          installed browser voices.
        </p>
      </section>
    );
  else if (view === "map")
    body = mapQuery.isError ? (
      <QueryError
        error={mapQuery.error}
        retry={() => void mapQuery.refetch()}
      />
    ) : !demoMode && mapQuery.isPending ? (
      <Loading />
    ) : (
      <section className="panel mapPanel">
        <div className="panelHead">
          <div>
            <h2>{t("map")}</h2>
            <p className="helper">
              {parcels.length} accessible parcels · synthetic showcase
              boundaries, OSM basemap
            </p>
          </div>
        </div>
        {parcels.length ? (
          <ParcelMap
            parcels={parcels}
            onSelect={(id) => router.push(target("cases", id))}
          />
        ) : (
          <Empty>No parcel geometry available for these cases.</Empty>
        )}
        <div className="mapLegend">
          {stages.map((stage) => (
            <span key={stage}>
              <i className={`stage-${stage}`} />
              {t(stage)}
            </span>
          ))}
        </div>
      </section>
    );
  else if (!cases.length) body = <Empty>{t("noCases")}</Empty>;
  else if (view === "cases")
    body = (
      <div className="caseWorkspace">
        <section className="panel">
          <div className="panelHead">
            <h2>{t("cases")}</h2>
            <span className="count">
              {cases.length}
              {!demoMode && cases.length === 500 ? "+" : ""}
            </span>
          </div>
          <div className="caseFilters">
            <label className="searchField">
              <Search size={16} />
              <input
                aria-label={t("search")}
                placeholder={t("search")}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
            <label>
              <span className="srOnly">Stage filter</span>
              <select
                value={stageFilter}
                onChange={(event) => {
                  const params = new URLSearchParams(searchParams.toString());
                  params.set("stage", event.target.value);
                  router.replace(`/portal/${role}?${params}`, {
                    scroll: false,
                  });
                }}
              >
                <option value="all">{t("allStages")}</option>
                {stages.map((stage) => (
                  <option value={stage} key={stage}>
                    {t(stage)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="caseList">
            {filtered.map((item) => {
              const parcel = parcels.find((row) => row.case_id === item.id);
              return (
                <Link
                  className={`caseRow ${selected?.id === item.id ? "selected" : ""}`}
                  href={`${target("cases", item.id)}#case-detail`}
                  key={item.id}
                >
                  <div>
                    <strong>{caseReference(item)}</strong>
                    <span className={`statusBadge stage-${item.current_stage}`}>
                      {t(item.current_stage)}
                    </span>
                  </div>
                  <p>
                    {parcel?.survey_number ?? "Survey not loaded"} ·{" "}
                    {parcel?.village ?? ""}
                  </p>
                  <div
                    className="caseProgress"
                    aria-label={`${stages.indexOf(item.current_stage) + 1} of 6 stages`}
                  >
                    {stages.map((stage, index) => (
                      <i
                        className={
                          index <= stages.indexOf(item.current_stage)
                            ? "done"
                            : ""
                        }
                        key={stage}
                      />
                    ))}
                  </div>
                </Link>
              );
            })}
            {filtered.length === 0 && <Empty>{t("noResults")}</Empty>}
          </div>
        </section>
        {selected && (
          <div id="case-detail" tabIndex={-1} aria-label="Selected case">
            <SelectedCase item={selected} role={role} key={selected.id} />
          </div>
        )}
      </div>
    );
  else
    body = (
      <>
        <div className="caseSelector">
          <label>
            {t("cases")}
            <select
              value={selected?.id}
              onChange={(event) =>
                router.push(target(view, event.target.value))
              }
            >
              {cases.map((item) => (
                <option key={item.id} value={item.id}>
                  {caseReference(item)} · {t(item.current_stage)}
                </option>
              ))}
            </select>
          </label>
          <Link href={target("cases", selected?.id)} className="textLink">
            {t("caseJourney")} →
          </Link>
        </div>
        {view === "documents" ? (
          <DocumentsView item={selected} key={selected.id} />
        ) : view === "grievances" ? (
          <GrievancesView item={selected} key={selected.id} />
        ) : (
          <OperationsForms item={selected} key={selected.id} />
        )}
      </>
    );
  return (
    <PortalShell
      role={role}
      view={view}
      unread={inbox?.items.filter((item) => !item.read).length ?? 0}
    >
      {body}
    </PortalShell>
  );
}
export default function PortalPage() {
  return (
    <Suspense fallback={<Loading />}>
      <Workspace />
    </Suspense>
  );
}
