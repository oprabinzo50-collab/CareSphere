import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  getPatientCareGaps,
  getPatientFollowUp,
  getPatientNotifications,
  listAuditLogs,
  markAllPatientNotificationsRead,
  markNotificationRead,
  synchronizePatientNotifications,
  type AuditLogRecord,
  type CareGap,
  type FollowUpItem,
  type NotificationRecord,
  type PatientCareGapsResponse,
  type PatientFollowUpResponse,
  type PatientNotificationsResponse,
} from "../../api/workflow";
import { type Patient } from "../../api/patients";
import Icon from "../ui/Icon";
import MetricCard from "../ui/MetricCard";
import PageHeader from "../ui/PageHeader";
import PatientSelector from "../ui/PatientSelector";
import StatusPill from "../ui/StatusPill";


function getErrorMessage(error: unknown, fallback: string) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response;
    if (typeof response?.data?.detail === "string") return response.data.detail;
  }
  return fallback;
}

const toneForSeverity = (value?: string) => {
  switch (String(value).toLowerCase()) {
    case "high":
    case "critical":
      return "danger" as const;
    case "medium":
    case "warning":
      return "warning" as const;
    case "low":
    case "completed":
    case "resolved":
      return "success" as const;
    default:
      return "info" as const;
  }
};

const pretty = (value?: string | null) =>
  String(value || "Not recorded")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
};

function WorkflowShell({
  children,
  eyebrow,
  title,
  description,
  icon,
  selector,
}: {
  children: ReactNode;
  eyebrow: string;
  title: string;
  description: string;
  icon: "activity" | "bell" | "calendar" | "file";
  selector: React.ReactNode;
}) {
  return (
    <div className="care-workflow-page">
      <PageHeader eyebrow={eyebrow} title={title} description={description} icon={icon} />
      <section className="care-workflow-toolbar">
        {selector}
      </section>
      {children}
    </div>
  );
}

export function FollowUpsPage() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [data, setData] = useState<PatientFollowUpResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!patient) {
      setData(null);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getPatientFollowUp(patient.id)
      .then((result) => !cancelled && setData(result))
      .catch((err) => !cancelled && setError(getErrorMessage(err, "Unable to load follow-up workflow.")))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [patient]);

  const followUps = data?.items ?? [];

  return (
    <WorkflowShell
      eyebrow="Care coordination"
      title="Follow-ups"
      description="Bring unfinished clinical actions into one focused work queue without changing the existing assessment workflow."
      icon="calendar"
      selector={<PatientSelector value={patient} onChange={setPatient} />}
    >
      {!patient ? (
        <div className="care-empty-hero">
          <span className="care-empty-icon"><Icon name="calendar" size={28} /></span>
          <div>
            <h2>Select a patient to review follow-up needs</h2>
            <p>The current backend derives follow-up items from existing assessments, recommendations, reports and clinician reviews.</p>
          </div>
        </div>
      ) : loading ? (
        <div className="care-panel care-skeleton-panel"><div className="care-skeleton care-skeleton-wide" /><div className="care-skeleton care-skeleton-row" /><div className="care-skeleton care-skeleton-row" /></div>
      ) : error ? (
        <div className="care-alert care-alert-danger"><Icon name="x" size={16} />{error}</div>
      ) : data ? (
        <>
          <div className="care-metric-grid">
            <MetricCard label="Open follow-ups" value={data.follow_up_count} icon="calendar" tone="teal" helper={pretty(data.follow_up_status)} />
            <MetricCard label="Pending reviews" value={data.counts.pending_reviews} icon="clipboard" tone="amber" helper="Clinician review" />
            <MetricCard label="Pending recommendations" value={data.counts.pending_recommendations} icon="sparkles" tone="blue" helper="Needs review" />
            <MetricCard label="Incomplete assessments" value={data.counts.incomplete_assessments} icon="activity" tone="rose" helper="Workflow still open" />
          </div>
          <section className="care-panel">
            <div className="care-section-heading">
              <div><div className="care-section-kicker">Patient context</div><h2>{data.patient.first_name} {data.patient.last_name}</h2><p>{data.patient.patient_number} · {pretty(data.patient.status)}</p></div>
              <StatusPill tone={toneForSeverity(data.follow_up_status)}>{pretty(data.follow_up_status)}</StatusPill>
            </div>
            <div className="care-mini-grid">
              <div><span>Assessments</span><strong>{data.assessment_count}</strong></div>
              <div><span>Latest assessment</span><strong>{data.latest_assessment ? pretty(data.latest_assessment.status) : "None"}</strong></div>
              <div><span>Completed without follow-up</span><strong>{data.counts.completed_without_follow_up}</strong></div>
            </div>
          </section>
          <section className="care-panel">
            <div className="care-section-heading"><div><div className="care-section-kicker">Action queue</div><h2>Items requiring attention</h2></div><span className="care-result-count">{followUps.length} item{followUps.length === 1 ? "" : "s"}</span></div>
            {followUps.length === 0 ? <div className="care-empty-state"><Icon name="check" size={24} /><h3>No outstanding follow-up items</h3><p>The current workflow has no derived follow-up requirement for this patient.</p></div> : <div className="care-list">{followUps.map((item: FollowUpItem, index) => <FollowUpCard key={`${item.follow_up_type}-${item.record_id ?? index}`} item={item} />)}</div>}
          </section>
        </>
      ) : null}
    </WorkflowShell>
  );
}

function FollowUpCard({ item }: { item: FollowUpItem }) {
  const navigate = useNavigate();
  return (
    <article className="care-list-card">
      <div className={`care-severity-rail care-rail-${toneForSeverity(item.priority)}`} />
      <div className="care-list-icon"><Icon name={item.follow_up_type.includes("recommendation") ? "sparkles" : item.follow_up_type.includes("report") ? "file" : "calendar"} size={18} /></div>
      <div className="care-list-main">
        <div className="care-list-meta"><StatusPill tone={toneForSeverity(item.priority)}>{pretty(item.priority)} priority</StatusPill><span>{pretty(item.follow_up_type)}</span></div>
        <h3>{item.title}</h3>
        <p>{item.description}</p>
        <div className="care-list-action"><strong>Suggested action:</strong> {item.action}</div>
      </div>
      <button className="care-ghost-button" type="button" onClick={() => navigate("/clinical-workspace")}>Open clinical workspace <Icon name="chevronRight" size={16} /></button>
    </article>
  );
}

export function CareGapsPage() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [data, setData] = useState<PatientCareGapsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!patient) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getPatientCareGaps(patient.id)
      .then((result) => !cancelled && setData(result))
      .catch((err) => !cancelled && setError(getErrorMessage(err, "Unable to load care gaps.")))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [patient]);

  return (
    <WorkflowShell eyebrow="Clinical quality" title="Care Gaps" description="Surface incomplete parts of the existing care workflow as clear, prioritised clinical work items." icon="activity" selector={<PatientSelector value={patient} onChange={setPatient} />}>
      {!patient ? <div className="care-empty-hero"><span className="care-empty-icon"><Icon name="activity" size={28} /></span><div><h2>Select a patient to review care gaps</h2><p>Care gaps are derived from the existing CareSphere assessment, report and review workflow.</p></div></div> : loading ? <div className="care-panel care-skeleton-panel"><div className="care-skeleton care-skeleton-wide" /><div className="care-skeleton care-skeleton-row" /><div className="care-skeleton care-skeleton-row" /></div> : error ? <div className="care-alert care-alert-danger"><Icon name="x" size={16} />{error}</div> : data ? <CareGapsContent data={data} /> : null}
    </WorkflowShell>
  );
}

function CareGapsContent({ data }: { data: PatientCareGapsResponse }) {
  const navigate = useNavigate();
  return (
    <>
      <div className="care-metric-grid">
        <MetricCard label="Total gaps" value={data.gap_count} icon="activity" tone="teal" helper={pretty(data.status)} />
        <MetricCard label="High priority" value={data.severity_counts.high} icon="heartPulse" tone="rose" helper="Immediate attention" />
        <MetricCard label="Medium priority" value={data.severity_counts.medium} icon="clock" tone="amber" helper="Workflow follow-through" />
        <MetricCard label="Low priority" value={data.severity_counts.low} icon="check" tone="blue" helper="Monitor and resolve" />
      </div>
      <section className="care-panel">
        <div className="care-section-heading"><div><div className="care-section-kicker">Patient context</div><h2>{data.patient.first_name} {data.patient.last_name}</h2><p>{data.patient.patient_number} · {pretty(data.patient.status)}</p></div><StatusPill tone={toneForSeverity(data.status)}>{pretty(data.status)}</StatusPill></div>
      </section>
      <section className="care-panel">
        <div className="care-section-heading"><div><div className="care-section-kicker">Gap register</div><h2>Outstanding opportunities</h2></div><span className="care-result-count">{data.gaps.length} gap{data.gaps.length === 1 ? "" : "s"}</span></div>
        {data.gaps.length === 0 ? <div className="care-empty-state"><Icon name="check" size={24} /><h3>No care gaps identified</h3><p>The current rules found no outstanding workflow gaps for this patient.</p></div> : <div className="care-list">{data.gaps.map((gap: CareGap, index) => <article className="care-list-card" key={`${gap.gap_type}-${gap.record_id ?? gap.assessment_id ?? index}`}><div className={`care-severity-rail care-rail-${toneForSeverity(gap.severity)}`} /><div className="care-list-icon"><Icon name="activity" size={18} /></div><div className="care-list-main"><div className="care-list-meta"><StatusPill tone={toneForSeverity(gap.severity)}>{pretty(gap.severity)}</StatusPill><span>{pretty(gap.gap_type)}</span></div><h3>{gap.title}</h3><p>{gap.description}</p><div className="care-list-action"><strong>Next action:</strong> {gap.action}</div></div><button className="care-ghost-button" type="button" onClick={() => navigate("/clinical-workspace")}>Review clinical context <Icon name="chevronRight" size={16} /></button></article>)}</div>}
      </section>
    </>
  );
}

export function NotificationsPage() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [data, setData] = useState<PatientNotificationsResponse | null>(null);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  const refresh = async (target = patient) => {
    if (!target) return;
    setLoading(true);
    setError("");
    try {
      await synchronizePatientNotifications(target.id);
      const result = await getPatientNotifications(target.id, { unreadOnly, limit: 100 });
      setData(result);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Unable to load notifications."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (patient) refresh(patient);
    else setData(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patient, unreadOnly]);

  const handleRead = async (notification: NotificationRecord) => {
    await markNotificationRead(notification.id);
    if (patient) await refresh(patient);
  };

  const handleReadAll = async () => {
    if (!patient) return;
    setSyncing(true);
    try {
      await markAllPatientNotificationsRead(patient.id);
      await refresh(patient);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <WorkflowShell eyebrow="Care coordination" title="Notifications" description="Keep system-generated patient actions visible, prioritised and linked to the underlying workflow." icon="bell" selector={<PatientSelector value={patient} onChange={setPatient} />}>
      {!patient ? <div className="care-empty-hero"><span className="care-empty-icon"><Icon name="bell" size={28} /></span><div><h2>Select a patient to open the notification inbox</h2><p>Notifications are currently patient-scoped by the existing backend contract, so the selector preserves that security model.</p></div></div> : <><div className="care-notification-toolbar"><label className="care-check"><input type="checkbox" checked={unreadOnly} onChange={(event) => setUnreadOnly(event.target.checked)} /> Unread only</label><div className="care-toolbar-spacer" /><span className="care-result-count">{data?.unread_count ?? 0} unread</span><button className="care-ghost-button" disabled={syncing || !data?.unread_count} type="button" onClick={handleReadAll}>{syncing ? "Updating..." : "Mark all read"}</button></div>{error && <div className="care-alert care-alert-danger"><Icon name="x" size={16} />{error}</div>}{loading ? <div className="care-panel care-skeleton-panel"><div className="care-skeleton care-skeleton-row" /><div className="care-skeleton care-skeleton-row" /><div className="care-skeleton care-skeleton-row" /></div> : <NotificationList notifications={data?.notifications ?? []} onRead={handleRead} />}</>}
    </WorkflowShell>
  );
}

function NotificationList({ notifications, onRead }: { notifications: NotificationRecord[]; onRead: (notification: NotificationRecord) => void }) {
  if (!notifications.length) return <div className="care-empty-state"><Icon name="check" size={24} /><h3>No notifications</h3><p>The current inbox has no matching notifications.</p></div>;
  return <div className="care-notification-list">{notifications.map((notification) => <article key={notification.id} className={`care-notification ${notification.is_read ? "is-read" : "is-unread"}`}><div className="care-list-icon"><Icon name="bell" size={18} /></div><div className="care-list-main"><div className="care-list-meta"><StatusPill tone={toneForSeverity(notification.priority)}>{pretty(notification.priority)}</StatusPill><span>{pretty(notification.notification_type)}</span><span>{formatDate(notification.created_at)}</span></div><h3>{notification.title}</h3><p>{notification.message}</p><div className="care-list-action">Source: <strong>{pretty(notification.source)}</strong></div></div>{!notification.is_read && <button className="care-ghost-button" type="button" onClick={() => onRead(notification)}>Mark read <Icon name="check" size={16} /></button>}</article>)}</div>;
}

export function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<AuditLogRecord | null>(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setLogs(await listAuditLogs({ action: action.trim() || undefined, entityType: entityType.trim() || undefined, limit: 200 }));
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Unable to load audit logs."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const entityOptions = useMemo(() => Array.from(new Set(logs.map((log) => log.entity_type).filter(Boolean))).sort() as string[], [logs]);
  const actionOptions = useMemo(() => Array.from(new Set(logs.map((log) => log.action).filter(Boolean))).sort(), [logs]);

  return (
    <div className="care-workflow-page">
      <PageHeader eyebrow="System oversight" title="Audit Logs" description="Review administrator-visible activity across users, patients, clinical workflows and system actions." icon="file" />
      <section className="care-panel care-audit-filter-panel">
        <div className="care-filter-heading"><div><div className="care-section-kicker">Activity search</div><h2>Filter the event stream</h2></div><button className="care-search-button" type="button" onClick={load}><Icon name="filter" size={16} /> Apply filters</button></div>
        <div className="care-filter-grid">
          <label className="care-field-label">Action<select className="care-input" value={action} onChange={(event) => setAction(event.target.value)}><option value="">All actions</option>{actionOptions.map((item) => <option key={item} value={item}>{pretty(item)}</option>)}</select></label>
          <label className="care-field-label">Entity<select className="care-input" value={entityType} onChange={(event) => setEntityType(event.target.value)}><option value="">All entities</option>{entityOptions.map((item) => <option key={item} value={item}>{pretty(item)}</option>)}</select></label>
          <div className="care-filter-summary"><span>Events loaded</span><strong>{logs.length}</strong></div>
        </div>
      </section>
      {error && <div className="care-alert care-alert-danger"><Icon name="x" size={16} />{error}</div>}
      <section className="care-panel">
        <div className="care-section-heading"><div><div className="care-section-kicker">Event stream</div><h2>Recent system activity</h2></div><span className="care-result-count">Latest first</span></div>
        {loading ? <div className="care-skeleton-table"><div className="care-skeleton care-skeleton-row" /><div className="care-skeleton care-skeleton-row" /><div className="care-skeleton care-skeleton-row" /></div> : logs.length === 0 ? <div className="care-empty-state"><Icon name="log" size={24} /><h3>No audit events match these filters</h3><p>Try broadening the action or entity filters.</p></div> : <div className="care-audit-table-wrap"><table className="care-audit-table"><thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Description</th><th /></tr></thead><tbody>{logs.map((log) => <tr key={log.id}><td>{formatDate(log.created_at)}</td><td>User #{log.user_id ?? "—"}</td><td><StatusPill tone="info">{pretty(log.action)}</StatusPill></td><td>{pretty(log.entity_type)}</td><td>{log.description || "—"}</td><td><button type="button" className="care-ghost-button care-small-button" onClick={() => setSelected(log)}>Details</button></td></tr>)}</tbody></table></div>}
      </section>
      {selected && <div className="care-modal-backdrop" role="presentation" onMouseDown={() => setSelected(null)}><div className="care-modal" role="dialog" aria-modal="true" aria-labelledby="audit-details-title" onMouseDown={(event) => event.stopPropagation()}><div className="care-modal-head"><div><div className="care-section-kicker">Audit event #{selected.id}</div><h2 id="audit-details-title">{pretty(selected.action)}</h2></div><button className="care-icon-button" type="button" onClick={() => setSelected(null)}><Icon name="x" size={18} /></button></div><div className="care-audit-detail-grid"><div><span>User</span><strong>{selected.user_id ?? "System"}</strong></div><div><span>Entity</span><strong>{pretty(selected.entity_type)} #{selected.entity_id ?? "—"}</strong></div><div><span>Timestamp</span><strong>{formatDate(selected.created_at)}</strong></div><div><span>IP</span><strong>{selected.ip_address || "Not recorded"}</strong></div></div><div className="care-detail-block"><span>Description</span><p>{selected.description || "No description recorded."}</p></div><div className="care-detail-block"><span>Metadata</span><pre>{JSON.stringify(selected.log_metadata ?? {}, null, 2)}</pre></div></div></div>}
    </div>
  );
}
