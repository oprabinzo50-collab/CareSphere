import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import PatientAvatar from "./components/PatientAvatar";
import { searchPatients, type Patient } from "./api/patients";
import {
  completeAssessment,
  generateAssessmentReport,
  listAssessments,
  listClinicianReviews,
  listReports,
  getReportPatientAccess,
  releaseReportToPatient as releaseReportToPatientApi,
  submitReportForReview,
  updateReportReview,
  listAdminReviewedReports,
  deleteReport,
  type AdminReviewedReport,
  type AssessmentSession,
  type ClinicianReview,
  type Report,
} from "./api/clinical";
import { listUsers, type CareUser } from "./api/users";

const panel: React.CSSProperties = {
  background: "rgba(255,255,255,0.97)",
  border: "1px solid rgba(148,163,184,0.16)",
  borderRadius: 18,
  padding: 22,
  boxShadow: "0 14px 36px rgba(15,23,42,0.055)",
};

const primaryButton: React.CSSProperties = {
  border: 0,
  borderRadius: 11,
  padding: "10px 14px",
  background: "linear-gradient(135deg, #0f766e, #0ea5a4)",
  color: "#fff",
  fontWeight: 800,
  cursor: "pointer",
};

const secondaryButton: React.CSSProperties = {
  border: "1px solid #cfe0e6",
  borderRadius: 11,
  padding: "10px 14px",
  background: "#fff",
  color: "#334e68",
  fontWeight: 750,
  cursor: "pointer",
};

const dangerButton: React.CSSProperties = {
  border: "1px solid #fecaca",
  borderRadius: 11,
  padding: "10px 14px",
  background: "#fff",
  color: "#b91c1c",
  fontWeight: 800,
  cursor: "pointer",
};

const input: React.CSSProperties = {
  width: "100%",
  border: "1px solid #d7e2e8",
  borderRadius: 11,
  padding: "11px 12px",
  background: "#fff",
  color: "#102a43",
  boxSizing: "border-box",
};

function humanize(value: string | null | undefined) {
  if (!value) return "Not recorded";
  return value
    .replace(/_/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function statusStyle(status: string | null | undefined): React.CSSProperties {
  const value = (status || "").toLowerCase();
  const positive = ["approved", "completed", "active"].includes(value);
  const waiting = ["pending", "pending_review", "awaiting_review"].includes(value);
  return {
    display: "inline-flex",
    alignItems: "center",
    padding: "6px 9px",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 800,
    background: positive ? "#ecfdf5" : waiting ? "#fff7ed" : "#f8fafc",
    color: positive ? "#047857" : waiting ? "#c2410c" : "#475569",
  };
}

function stringifyReportContent(value: unknown) {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value ?? "");
  }
}

type ReportPayload = {
  assessment_type?: string;
  summary?: string;
  risk_assessment?: { score?: number | null; risk_level?: string | null };
  risk_factors?: Array<{ factor?: string; severity?: string }>;
  health_concerns?: string[];
  recommendations?: Array<{ title?: string; recommendation_text?: string; priority?: string; status?: string }>;
};

function parseReportPayload(value: unknown): ReportPayload {
  if (value && typeof value === "object") return value as ReportPayload;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" ? parsed as ReportPayload : {};
    } catch {
      return {};
    }
  }
  return {};
}

function reportAiContent(value: unknown) {
  const payload = parseReportPayload(value) as ReportPayload & { ai_generated_content?: Record<string, unknown> };
  const ai = payload.ai_generated_content;
  if (!ai) return null;
  return {
    clinical_summary: typeof ai.clinical_summary === "string" ? ai.clinical_summary : "",
    recommendations_summary: typeof ai.recommendations_summary === "string" ? ai.recommendations_summary : "",
  };
}

function reportDate(value: string | null | undefined) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function ReportsPreview({
  report,
  patient,
  preparedBy,
  clinicianGuidance,
  reviewStatus,
  patientReviewedAt,
  releasedToPatient,
}: {
  report: Report;
  patient: Patient;
  preparedBy: string;
  clinicianGuidance?: string;
  reviewStatus?: string;
  patientReviewedAt?: string | null;
  releasedToPatient?: boolean;
}) {
  const payload = parseReportPayload(report.report_content);
  const ai = reportAiContent(report.report_content);
  const effectiveGuidance = clinicianGuidance || report.clinician_guidance || "";
  const effectiveReviewStatus = reviewStatus || report.clinician_review_status || report.status;
  const effectiveReleased = releasedToPatient ?? report.released_to_patient ?? false;
  const effectivePatientReviewedAt = patientReviewedAt || report.patient_reviewed_at || null;
  const factors = Array.isArray(payload.risk_factors) ? payload.risk_factors : [];
  const concerns = Array.isArray(payload.health_concerns) ? payload.health_concerns : [];
  const recommendations = Array.isArray(payload.recommendations) ? payload.recommendations : [];
  const demographics = [
    ["Patient number", patient.patient_number],
    ["Date of birth", patient.date_of_birth || "Not recorded"],
    ["Sex", patient.sex ? humanize(patient.sex) : "Not recorded"],
    ["Location", [patient.district, patient.country].filter(Boolean).join(", ") || "Not recorded"],
    ["Status", humanize(patient.status)],
  ];
  return (
    <article className="care-report-document">
      <header className="care-report-cover">
        <div className="care-report-cover-main">
          <PatientAvatar patientId={patient.id} firstName={patient.first_name} lastName={patient.last_name} size={72} radius={22} />
          <div>
            <div className="care-report-kicker">CareSphere clinical report</div>
            <h3>{report.report_title}</h3>
            <p>{humanize(payload.assessment_type || report.report_type)} · Version {report.version}</p>
          </div>
        </div>
        <div className="care-report-status-block">
          <span style={statusStyle(report.status)}>{humanize(report.status)}</span>
          <small>Generated {reportDate(report.generated_at)}</small>
        </div>
      </header>
      <section className="care-report-section"><div className="care-report-section-heading"><span>01</span><div><h4>Patient information</h4><p>Identity and related record context.</p></div></div><div className="care-report-patient-strip"><div><strong>{patient.first_name} {patient.last_name}</strong><span>Patient</span></div><div className="care-report-demographics">{demographics.map(([label,value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div></div></section>
      <section className="care-report-section"><div className="care-report-section-heading"><span>02</span><div><h4>Executive summary</h4><p>Concise report overview.</p></div></div><div className="care-report-callout care-report-callout-primary"><p>{report.executive_summary || payload.summary || "No executive summary was recorded."}</p></div></section>
      <section className="care-report-section"><div className="care-report-section-heading"><span>03</span><div><h4>Clinical findings</h4><p>Structured findings preserved from the generated report.</p></div></div>{ai?.clinical_summary ? <div className="care-report-callout care-report-ai"><div className="care-report-label">AI-supported narrative</div><p>{ai.clinical_summary}</p></div> : null}<div className="care-report-grid-two"><div className="care-report-mini-card"><small>Risk score</small><strong>{payload.risk_assessment?.score ?? "Not recorded"}</strong></div><div className="care-report-mini-card"><small>Risk level</small><strong>{humanize(payload.risk_assessment?.risk_level)}</strong></div></div></section>
      <section className="care-report-section"><div className="care-report-section-heading"><span>04</span><div><h4>Key risk factors & health concerns</h4><p>Documented items from the report.</p></div></div><div className="care-report-item-columns"><div><div className="care-report-label">Risk factors</div>{factors.length ? factors.map((factor,index)=><div className="care-report-list-item" key={`${factor.factor || "factor"}-${index}`}><span>{humanize(factor.factor)}</span><span style={statusStyle(factor.severity)}>{humanize(factor.severity)}</span></div>) : <div className="care-report-empty">No documented risk factors.</div>}</div><div><div className="care-report-label">Health concerns</div>{concerns.length ? concerns.map((concern,index)=><div className="care-report-list-item" key={`${concern}-${index}`}><span>{concern}</span></div>) : <div className="care-report-empty">No documented health concerns.</div>}</div></div></section>
      <section className="care-report-section"><div className="care-report-section-heading"><span>05</span><div><h4>Recommendations</h4><p>Existing recommendations as recorded.</p></div></div>{ai?.recommendations_summary || report.recommendations_summary ? <div className="care-report-callout care-report-ai"><div className="care-report-label">System / AI recommendation summary</div><p>{ai?.recommendations_summary || report.recommendations_summary}</p></div> : null}<div className="care-report-recommendations">{recommendations.length ? recommendations.map((recommendation,index)=><div className="care-report-recommendation" key={`${recommendation.title || "recommendation"}-${index}`}><div><strong>{recommendation.title || `Recommendation ${index+1}`}</strong><p>{recommendation.recommendation_text || "No recommendation text recorded."}</p></div><div className="care-report-recommendation-meta">{recommendation.priority ? <span style={statusStyle(recommendation.priority)}>{humanize(recommendation.priority)}</span>:null}{recommendation.status?<span style={statusStyle(recommendation.status)}>{humanize(recommendation.status)}</span>:null}</div></div>) : <div className="care-report-empty">No structured recommendations were recorded.</div>}</div></section>
      {effectiveGuidance ? <section className="care-report-section care-report-clinician-guidance"><div className="care-report-section-heading"><span>06</span><div><h4>Clinician guidance</h4><p>Additional guidance prepared for the patient.</p></div></div><div className="care-report-callout care-report-clinician-callout"><div className="care-report-label">Clinician-authored</div><p>{effectiveGuidance}</p></div></section> : null}
      <section className="care-report-section care-report-clinician-guidance"><div className="care-report-section-heading"><span>{effectiveGuidance ? "07" : "06"}</span><div><h4>Clinician recommendation & release</h4><p>Clinician-authored guidance, review state, and patient delivery status.</p></div></div><div className="care-report-footer-grid"><div><small>Clinician guidance</small><strong>{effectiveGuidance || "Not yet added"}</strong></div><div><small>Clinician review</small><strong>{humanize(effectiveReviewStatus)}</strong></div><div><small>Patient release</small><strong>{effectiveReleased ? "Sent to patient" : "Not sent"}</strong></div></div></section>
      <section className="care-report-section"><div className="care-report-section-heading"><span>{effectiveGuidance ? "08" : "07"}</span><div><h4>Report provenance</h4><p>Prepared, review, and release information.</p></div></div><div className="care-report-footer-grid"><div><small>Prepared by</small><strong>{preparedBy}</strong></div><div><small>Review status</small><strong>{humanize(effectiveReviewStatus)}</strong></div><div><small>Generated</small><strong>{reportDate(report.generated_at)}</strong></div><div><small>Patient access</small><strong>{effectiveReleased ? (effectivePatientReviewedAt ? `Reviewed ${reportDate(effectivePatientReviewedAt)}` : "Released · awaiting review") : "Not released"}</strong></div></div><p className="care-report-limitations">{report.limitations || "This report supports clinical review and does not independently establish a diagnosis or treatment decision."}</p></section>
      <details className="care-report-source"><summary>View source report payload</summary><pre>{stringifyReportContent(report.report_content)}</pre></details>
    </article>
  );
}

function ReportsWorkspaceStyles() {
  return <style>{`
    .care-report-document{border:1px solid #dbe6eb;border-radius:20px;background:#fff;box-shadow:0 18px 48px rgba(15,23,42,.07);overflow:hidden}
    .care-report-cover{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;padding:24px;background:linear-gradient(135deg,#f0fdfa 0%,#fff 55%,#eff6ff 100%);border-bottom:1px solid #e2e8f0}
    .care-report-cover-main{display:flex;gap:15px;align-items:center;min-width:0}.care-report-kicker,.care-report-label{color:#0f766e;font-size:10px;font-weight:900;letter-spacing:.09em;text-transform:uppercase}.care-report-cover h3{margin:3px 0 5px;color:#102a43;font-size:22px;letter-spacing:-.025em}.care-report-cover p,.care-report-status-block small{margin:0;color:#627d98;font-size:12px}.care-report-status-block{display:grid;justify-items:end;gap:7px;text-align:right}
    .care-report-section{padding:22px 24px;border-bottom:1px solid #edf2f5}.care-report-section:last-of-type{border-bottom:0}.care-report-section-heading{display:flex;gap:11px;align-items:flex-start;margin-bottom:15px}.care-report-section-heading>span{display:grid;place-items:center;width:30px;height:30px;border-radius:9px;background:#ecfeff;color:#0f766e;font-size:10px;font-weight:900}.care-report-section-heading h4{margin:0;color:#102a43;font-size:15px}.care-report-section-heading p{margin:3px 0 0;color:#78909c;font-size:11px}.care-report-patient-strip{display:grid;grid-template-columns:minmax(180px,.7fr) minmax(0,1.8fr);gap:18px}.care-report-patient-strip>div:first-child{padding:15px;border-radius:14px;background:#f8fafc}.care-report-patient-strip strong{display:block;color:#102a43;font-size:17px}.care-report-patient-strip span{display:block;margin-top:3px;color:#627d98;font-size:11px}.care-report-demographics{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:10px}.care-report-demographics>div,.care-report-footer-grid>div{padding:11px 12px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}.care-report-demographics small,.care-report-footer-grid small,.care-report-mini-card small{display:block;color:#64748b;font-size:9px;font-weight:850;text-transform:uppercase;letter-spacing:.05em}.care-report-demographics strong,.care-report-footer-grid strong{display:block;margin-top:4px;color:#102a43;font-size:12px;word-break:break-word}.care-report-callout{padding:15px;border-radius:14px}.care-report-callout p{margin:7px 0 0;color:#334e68;font-size:13px;line-height:1.7;white-space:pre-wrap}.care-report-callout-primary{background:#f8fbff;border:1px solid #dbeafe}.care-report-ai{background:linear-gradient(135deg,#ecfeff,#eff6ff);border:1px solid #bae6fd}.care-report-grid-two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin-top:12px}.care-report-mini-card{padding:13px;border:1px solid #e2e8f0;border-radius:13px;background:#fbfdff}.care-report-mini-card strong{display:block;margin-top:5px;color:#102a43;font-size:22px}.care-report-item-columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.care-report-list-item{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:10px 11px;margin-top:7px;border-radius:11px;border:1px solid #e2e8f0;background:#fff;color:#334e68;font-size:12px}.care-report-empty{padding:11px 12px;margin-top:7px;border-radius:11px;background:#f8fafc;color:#94a3b8;font-size:12px}.care-report-recommendation{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;padding:14px;margin-top:9px;border-radius:13px;border:1px solid #e2e8f0;background:#fff}.care-report-recommendation strong{color:#102a43;font-size:13px}.care-report-recommendation p{margin:6px 0 0;color:#475569;font-size:12px;line-height:1.6;white-space:pre-wrap}.care-report-recommendation-meta{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.care-report-clinician-guidance{background:linear-gradient(180deg,#fcfffe,#f8fbff)}.care-report-clinician-callout{background:#f0fdfa;border:1px solid #99f6e4}.care-report-footer-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.care-report-limitations{margin:13px 0 0;color:#64748b;font-size:11px;line-height:1.6}.care-report-source{padding:0 24px 22px}.care-report-source summary{cursor:pointer;color:#0f766e;font-weight:800;font-size:11px;padding-top:3px}.care-report-source pre{margin:9px 0 0;padding:13px;border-radius:12px;background:#0f172a;color:#e2e8f0;overflow:auto;font-size:10px;line-height:1.55}@media(max-width:900px){.care-report-admin-meta{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:760px){.care-report-cover{flex-direction:column}.care-report-status-block{justify-items:start;text-align:left}.care-report-patient-strip,.care-report-item-columns,.care-report-footer-grid{grid-template-columns:1fr}.care-report-recommendation{flex-direction:column}.care-report-recommendation-meta{justify-content:flex-start}}
  `}</style>;
}

export default function ReportsWorkspace() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [assessments, setAssessments] = useState<AssessmentSession[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<AssessmentSession | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [reviews, setReviews] = useState<ClinicianReview[]>([]);
  const [reviewError, setReviewError] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [guidanceByReport, setGuidanceByReport] = useState<Record<number, string>>({});
  const [patientAccessByReport, setPatientAccessByReport] = useState<Record<number, { released_to_patient: boolean; patient_reviewed_at: string | null }>>({});
  const [users, setUsers] = useState<CareUser[]>([]);
  const [reviewedReports, setReviewedReports] = useState<AdminReviewedReport[]>([]);
  const [reviewedReportsLoading, setReviewedReportsLoading] = useState(false);
  const [reviewedReportsError, setReviewedReportsError] = useState("");

  const refreshReviewedReports = async () => {
    if (user?.role !== "administrator") return;
    setReviewedReportsLoading(true);
    try {
      const rows = await listAdminReviewedReports(100);
      setReviewedReports(rows);
      setReviewedReportsError("");
    } catch (err: any) {
      setReviewedReportsError(err?.response?.data?.detail || "Reviewed reports could not be loaded.");
    } finally {
      setReviewedReportsLoading(false);
    }
  };

  React.useEffect(() => {
    if (user?.role !== "administrator") return;
    void listUsers({ limit: 100 }).then(setUsers).catch(() => setUsers([]));
    void refreshReviewedReports();
  }, [user?.role]);

  React.useEffect(() => {
    void searchPatients({ search: "", limit: 100 }).then(setPatients).catch(() => setPatients([]));
  }, []);

  const reviewByReport = useMemo(() => {
    const next = new Map<number, ClinicianReview>();
    for (const review of reviews) {
      if (review.report_id !== null && !next.has(review.report_id)) {
        next.set(review.report_id, review);
      }
    }
    return next;
  }, [reviews]);

  const run = async (label: string, fn: () => Promise<void>) => {
    setBusy(label);
    setMessage("");
    setError("");
    try {
      await fn();
    } catch (err: any) {
      setError(err?.response?.data?.detail || `Unable to ${label.toLowerCase()}.`);
    } finally {
      setBusy("");
    }
  };

  const findPatients = async (event?: React.FormEvent) => {
    event?.preventDefault();
    await run("search patients", async () => {
      const rows = await searchPatients({ search: query.trim(), limit: 50 });
      setPatients(rows);
      if (!rows.length) setMessage("No patients matched the search.");
    });
  };

  const selectPatient = async (patient: Patient) => {
    setSelectedPatient(patient);
    setSelectedAssessment(null);
    setAssessments([]);
    setReports([]);
    setReviews([]);
    setMessage("");
    setError("");

    await run("load assessments", async () => {
      const rows = await listAssessments(patient.id);
      setAssessments(rows);
      if (rows.length === 1) await selectAssessment(rows[0]);
    });
  };

  const refreshReportData = async (assessmentId: number) => {
    const reportRows = await listReports(assessmentId);
    setReports(reportRows);
    setGuidanceByReport((current) => {
      const next = { ...current };
      for (const report of reportRows) {
        if (report.clinician_guidance && !next[report.id]) {
          next[report.id] = report.clinician_guidance;
        }
      }
      return next;
    });
    try {
      const rows = await listClinicianReviews(assessmentId);
      setReviews(rows);
      setReviewError("");
      setGuidanceByReport(Object.fromEntries(rows.filter((row) => row.report_id !== null).map((row) => [row.report_id as number, row.clinical_comment || ""])));
    } catch (err: any) {
      setReviews([]);
      setReviewError(err?.response?.data?.detail || "Clinician reviews could not be loaded. Reports remain available.");
    }
    const accessEntries = await Promise.all(reportRows.map(async (report) => {
      try {
        const access = await getReportPatientAccess(report.id);
        return [report.id, { released_to_patient: access.released_to_patient, patient_reviewed_at: access.patient_reviewed_at }] as const;
      } catch {
        return [report.id, { released_to_patient: report.released_to_patient ?? ["approved", "completed"].includes(report.status), patient_reviewed_at: report.patient_reviewed_at ?? null }] as const;
      }
    }));
    setPatientAccessByReport(Object.fromEntries(accessEntries));
  };

  const selectAssessment = async (assessment: AssessmentSession) => {
    setSelectedAssessment(assessment);
    setReviewError("");
    await run("load reports", async () => {
      await refreshReportData(assessment.id);
    });
  };

  const finishAssessment = async () => {
    if (!selectedAssessment) return;
    await run("complete assessment", async () => {
      const updated = await completeAssessment(selectedAssessment.id);
      setSelectedAssessment(updated);
      setAssessments((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage("Assessment marked completed. Report generation is now available.");
    });
  };

  const generateReport = async () => {
    if (!selectedAssessment) return;
    await run("generate medical report", async () => {
      await generateAssessmentReport(selectedAssessment.id);
      await refreshReportData(selectedAssessment.id);
      setMessage("Medical report generated successfully.");
    });
  };

  const saveClinicianGuidance = async (report: Report) => {
    const guidance = (guidanceByReport[report.id] || "").trim();
    await run("save clinician guidance", async () => {
      if (!reviewByReport.has(report.id)) {
        await submitReportForReview(report.assessment_id, report.id);
      }
      const status = ["reviewed", "approved", "completed"].includes(report.status)
        ? report.status as "reviewed" | "approved" | "completed"
        : "pending";
      await updateReportReview(report.assessment_id, report.id, status, guidance || undefined, "Clinician-authored patient guidance");
      await refreshReportData(report.assessment_id);
      setMessage("Clinician guidance saved.");
    });
  };

  const markReportReviewed = async (report: Report) => {
    await run("mark report reviewed", async () => {
      if (!reviewByReport.has(report.id)) {
        await submitReportForReview(report.assessment_id, report.id);
      }
      const guidance = (guidanceByReport[report.id] || "").trim();
      await updateReportReview(
        report.assessment_id,
        report.id,
        "reviewed",
        guidance || "Report reviewed by clinician.",
        "Clinician completed report review",
      );
      await refreshReportData(report.assessment_id);
      await refreshReviewedReports();
      setMessage("Report marked reviewed and is ready for approval and patient release.");
    });
  };

  const removeReport = async (report: Report) => {
    const confirmed = window.confirm(
      `Delete \"${report.report_title}\" from CareSphere? This removes the report, its clinician-review record, and any patient portal access for this report.`,
    );
    if (!confirmed) return;

    await run("delete report", async () => {
      await deleteReport(report.id);
      setReports((current) => current.filter((item) => item.id !== report.id));
      setReviews((current) => current.filter((item) => item.report_id !== report.id));
      setGuidanceByReport((current) => {
        const next = { ...current };
        delete next[report.id];
        return next;
      });
      setPatientAccessByReport((current) => {
        const next = { ...current };
        delete next[report.id];
        return next;
      });
      await refreshReviewedReports();
      setMessage("Report deleted from CareSphere.");
    });
  };

  const releaseReportToPatient = async (report: Report) => {
    const guidance = (guidanceByReport[report.id] || "").trim();
    await run("release report to patient", async () => {
      await releaseReportToPatientApi(
        report.assessment_id,
        report.id,
        guidance || undefined,
      );
      await refreshReportData(report.assessment_id);
      await refreshReviewedReports();
      setMessage("Report approved and sent to the patient My Health portal.");
    });
  };

  const preparedByLabel = (report: Report) => {
    const raw = report.created_by ?? report.generated_by;
    const userId = raw === null || raw === undefined ? NaN : Number(raw);
    const matched = Number.isFinite(userId) ? users.find((item) => item.id === userId) : undefined;
    return matched?.full_name || matched?.username || (raw ? `User #${raw}` : "CareSphere");
  };

  const submitReport = async (report: Report) => {
    if (!selectedAssessment) return;
    await run("submit report for review", async () => {
      await submitReportForReview(selectedAssessment.id, report.id);
      await refreshReportData(selectedAssessment.id);
      setMessage("Report submitted for clinician review.");
    });
  };

  const rejectReport = async (report: Report) => {
    if (!selectedAssessment) return;
    await run("reject report", async () => {
      if (!reviewByReport.has(report.id)) {
        await submitReportForReview(selectedAssessment.id, report.id);
      }
      await updateReportReview(
        selectedAssessment.id,
        report.id,
        "rejected",
        "Report reviewed and rejected by clinician.",
      );
      await refreshReportData(selectedAssessment.id);
      await refreshReviewedReports();
      setMessage("Report rejected. It is not available to the patient.");
    });
  };

  return (
    <>
      <ReportsWorkspaceStyles />
      <div style={{ display: "grid", gap: 18, animation: "careFadeUp 420ms ease both" }}>
      <section style={{ ...panel, background: "linear-gradient(135deg, #ffffff 0%, #f3fbfb 100%)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.1em" }}>Clinical documentation</div>
            <h1 style={{ margin: "4px 0 6px", color: "#102a43", fontSize: 31, letterSpacing: "-0.03em" }}>Medical Reports</h1>
            <p style={{ margin: 0, color: "#627d98", maxWidth: 760 }}>
              Find a patient, select a completed assessment, review generated medical reports, and manage clinician approval before a report is released to the patient.
            </p>
          </div>
          <button type="button" onClick={() => navigate("/clinical-workspace")} style={secondaryButton}>
            Open Clinical Review
          </button>
        </div>
      </section>

      {message && <div style={{ padding: "11px 13px", background: "#ecfdf5", border: "1px solid #a7f3d0", borderRadius: 11, color: "#047857", fontWeight: 750, fontSize: 13 }}>{message}</div>}
      {error && <div style={{ padding: "11px 13px", background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: 11, color: "#be123c", fontWeight: 750, fontSize: 13 }}>{error}</div>}

      {user?.role === "administrator" && (
        <section style={{ ...panel, background: "linear-gradient(135deg, #ffffff 0%, #f7fbff 100%)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 14, alignItems: "flex-start", flexWrap: "wrap" }}>
            <div>
              <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>Administrative oversight</div>
              <h2 style={{ margin: "4px 0 5px", color: "#102a43", fontSize: 20 }}>Reviewed reports</h2>
              <p style={{ margin: 0, color: "#627d98", fontSize: 12 }}>Reports with a completed clinician review action, including patient release and patient-review state.</p>
            </div>
            <span style={{ ...statusStyle("reviewed"), background: "#ecfeff", color: "#0f766e" }}>{reviewedReports.length} reviewed</span>
          </div>

          {reviewedReportsLoading ? (
            <div style={{ marginTop: 14, padding: 14, borderRadius: 12, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>Loading reviewed reports...</div>
          ) : reviewedReportsError ? (
            <div style={{ marginTop: 14, padding: 12, borderRadius: 12, background: "#fff7ed", border: "1px solid #fed7aa", color: "#c2410c", fontSize: 12 }}>{reviewedReportsError}</div>
          ) : reviewedReports.length === 0 ? (
            <div style={{ marginTop: 14, padding: 14, borderRadius: 12, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>No reviewed reports are recorded yet.</div>
          ) : (
            <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
              {reviewedReports.map((item) => (
                <div key={item.report.id} style={{ display: "grid", gap: 11, padding: 14, border: "1px solid #e2e8f0", borderRadius: 14, background: "#fff" }}>
                  <div style={{ display: "flex", gap: 12, justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap" }}>
                    <div style={{ display: "flex", gap: 11, alignItems: "center", minWidth: 0 }}>
                      <PatientAvatar patientId={item.patient.id} firstName={item.patient.first_name} lastName={item.patient.last_name} size={42} radius={13} />
                      <div>
                        <strong style={{ color: "#102a43", display: "block" }}>{item.report.report_title}</strong>
                        <span style={{ color: "#627d98", fontSize: 11 }}>{item.patient.first_name} {item.patient.last_name} · {item.patient.patient_number} · Assessment {item.report.assessment_id}</span>
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <span style={statusStyle(item.review_status)}>{humanize(item.review_status)}</span>
                      <span style={statusStyle(item.released_to_patient ? "completed" : "pending")}>{item.released_to_patient ? "Released" : "Not released"}</span>
                    </div>
                  </div>
                  <div className="care-report-admin-meta" style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8 }}>
                    <div style={{ padding: 10, borderRadius: 11, background: "#f8fafc" }}><small style={{ color: "#64748b", fontSize: 9, fontWeight: 850, textTransform: "uppercase" }}>Clinician</small><strong style={{ display: "block", marginTop: 4, color: "#102a43", fontSize: 11 }}>{item.clinician.full_name || item.clinician.username}</strong></div>
                    <div style={{ padding: 10, borderRadius: 11, background: "#f8fafc" }}><small style={{ color: "#64748b", fontSize: 9, fontWeight: 850, textTransform: "uppercase" }}>Reviewed</small><strong style={{ display: "block", marginTop: 4, color: "#102a43", fontSize: 11 }}>{reportDate(item.reviewed_at)}</strong></div>
                    <div style={{ padding: 10, borderRadius: 11, background: "#f8fafc" }}><small style={{ color: "#64748b", fontSize: 9, fontWeight: 850, textTransform: "uppercase" }}>Patient</small><strong style={{ display: "block", marginTop: 4, color: "#102a43", fontSize: 11 }}>{item.patient_reviewed_at ? `Reviewed ${reportDate(item.patient_reviewed_at)}` : item.released_to_patient ? "Awaiting review" : "Not released"}</strong></div>
                    <div style={{ padding: 10, borderRadius: 11, background: "#f8fafc" }}><small style={{ color: "#64748b", fontSize: 9, fontWeight: 850, textTransform: "uppercase" }}>Version</small><strong style={{ display: "block", marginTop: 4, color: "#102a43", fontSize: 11 }}>v{item.report.version}</strong></div>
                  </div>
                  {item.report.executive_summary && <p style={{ margin: 0, color: "#475569", fontSize: 12, lineHeight: 1.55 }}>{item.report.executive_summary}</p>}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button type="button" onClick={() => void selectPatient(item.patient)} style={secondaryButton}>Open patient workspace</button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 10, color: "#94a3b8", fontSize: 10 }}>The administrative view reads the existing report/review records; it does not create duplicate reports.</div>
        </section>
      )}

      <section style={panel}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 19, color: "#102a43" }}>1. Find patient</h2>
            <p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>Search by patient number, name, district, or other supported patient fields.</p>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr)", gap: 10, marginTop: 14 }}>
          <label htmlFor="reports-patient-select" style={{ color: "#334e68", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.07em" }}>Select existing patient</label>
          <select id="reports-patient-select" value={selectedPatient?.id ?? ""} onChange={(event) => { const patient = patients.find((item) => item.id === Number(event.target.value)); if (patient) void selectPatient(patient); }} style={{ ...input, appearance: "auto", cursor: "pointer" }}>
            <option value="">Choose a patient...</option>
            {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.first_name} {patient.last_name} · {patient.patient_number}</option>)}
          </select>
        </div>
        <form onSubmit={findPatients} style={{ display: "flex", gap: 9, marginTop: 12, flexWrap: "wrap" }}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search patient name or patient number..." style={{ ...input, flex: "1 1 280px" }} />
          <button type="submit" disabled={Boolean(busy)} style={secondaryButton}>{busy === "search patients" ? "Searching..." : "Search"}</button>
        </form>

        {patients.length > 0 && (
          <div style={{ marginTop: 10, color: "#627d98", fontSize: 12 }}>
            {patients.length} matching patient{patients.length === 1 ? "" : "s"} available in the selector.
          </div>
        )}
      </section>

      <section style={panel}>
        <div>
          <h2 style={{ margin: 0, fontSize: 19, color: "#102a43" }}>2. Select assessment</h2>
          <p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>
            {selectedPatient ? `Assessments for ${selectedPatient.first_name} ${selectedPatient.last_name}.` : "Select a patient first."}
          </p>
        </div>
        {!selectedPatient ? (
          <div style={{ marginTop: 13, padding: 14, borderRadius: 12, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>Choose a patient above to load clinical assessments.</div>
        ) : assessments.length === 0 ? (
          <div style={{ marginTop: 13, padding: 14, borderRadius: 12, background: "#fff7ed", border: "1px solid #fed7aa", color: "#9a3412", fontSize: 13 }}>No assessments are recorded for this patient yet. Create one from Clinical Review.</div>
        ) : (
          <div style={{ display: "grid", gap: 9, marginTop: 13 }}>
            {assessments.map((assessment) => (
              <button key={assessment.id} type="button" onClick={() => void selectAssessment(assessment)} style={{ textAlign: "left", border: selectedAssessment?.id === assessment.id ? "1px solid #5eead4" : "1px solid #e2e8f0", borderRadius: 13, padding: 13, background: selectedAssessment?.id === assessment.id ? "#f0fdfa" : "#fff", cursor: "pointer" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <strong style={{ color: "#102a43" }}>Assessment {assessment.id}</strong>
                  <span style={statusStyle(assessment.status)}>{humanize(assessment.status)}</span>
                </div>
                <div style={{ marginTop: 5, color: "#627d98", fontSize: 12 }}>{humanize(assessment.assessment_type)} · {new Date(assessment.started_at).toLocaleString()}</div>
              </button>
            ))}
          </div>
        )}
      </section>

      {reviewError && (
        <div style={{ padding: "11px 13px", background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: 11, color: "#c2410c", fontWeight: 750, fontSize: 13 }}>
          {reviewError}
        </div>
      )}

      <section style={panel}>
        {!selectedAssessment ? (
          <>
            <h2 style={{ margin: 0, fontSize: 19, color: "#102a43" }}>3. Report review</h2>
            <p style={{ margin: "7px 0 0", color: "#627d98" }}>Select an assessment to view, generate, and review its medical reports.</p>
          </>
        ) : (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 14, alignItems: "flex-start", flexWrap: "wrap" }}>
              <div>
                <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>Assessment {selectedAssessment.id}</div>
                <h2 style={{ margin: "4px 0 6px", color: "#102a43", fontSize: 23 }}>{humanize(selectedAssessment.assessment_type)}</h2>
                <p style={{ margin: 0, color: "#627d98", fontSize: 13 }}>{selectedAssessment.summary || "No assessment summary recorded."}</p>
              </div>
              <span style={statusStyle(selectedAssessment.status)}>{humanize(selectedAssessment.status)}</span>
            </div>

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 15 }}>
              {selectedAssessment.status !== "completed" && (
                <button type="button" disabled={Boolean(busy)} onClick={() => void finishAssessment()} style={secondaryButton}>
                  {busy === "complete assessment" ? "Completing..." : "Complete Assessment"}
                </button>
              )}
              <button type="button" disabled={Boolean(busy) || selectedAssessment.status !== "completed"} onClick={() => void generateReport()} style={{ ...primaryButton, opacity: selectedAssessment.status === "completed" ? 1 : 0.55 }} title={selectedAssessment.status !== "completed" ? "Complete the assessment before generating a report." : undefined}>
                {busy === "generate medical report" ? "Generating..." : "Generate Medical Report"}
              </button>
            </div>

            {reports.length === 0 ? (
              <div style={{ marginTop: 15, padding: 15, borderRadius: 13, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>
                No medical report exists for this assessment yet.
              </div>
            ) : (
              <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
                {reports.map((report) => {
                  const review = reviewByReport.get(report.id);
                  return (
                    <div style={{ display: "grid", gap: 12 }}>
                      <ReportsPreview
                        report={report}
                        patient={selectedPatient!}
                        preparedBy={preparedByLabel(report)}
                        clinicianGuidance={guidanceByReport[report.id] || ""}
                        reviewStatus={review?.review_status}
                        patientReviewedAt={patientAccessByReport[report.id]?.patient_reviewed_at}
                        releasedToPatient={patientAccessByReport[report.id]?.released_to_patient}
                      />

                      {user?.role === "clinician" && (
                        <div style={{ display: "grid", gap: 10, padding: 13, borderRadius: 13, background: "#f8fafc", border: "1px solid #e2e8f0" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                            <div><strong style={{ color: "#102a43", fontSize: 13 }}>Clinician recommendation / guidance</strong><div style={{ marginTop: 3, color: "#627d98", fontSize: 11 }}>Add or update the patient-facing recommendation without altering the generated report.</div></div>
                            <span style={{ color: "#0f766e", fontSize: 10, fontWeight: 850 }}>Clinician-authored</span>
                          </div>
                          <textarea value={guidanceByReport[report.id] || ""} onChange={(event) => setGuidanceByReport((current) => ({ ...current, [report.id]: event.target.value }))} placeholder="Add the clinician-authored recommendation or next-step guidance for the patient." style={{ ...input, minHeight: 92, resize: "vertical" }} />
                        </div>
                      )}

                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", padding: 13, borderRadius: 13, background: "#f8fafc", border: "1px solid #e2e8f0", alignItems: "center" }}>
                        {review && <span style={statusStyle(review.review_status)}>Review: {humanize(review.review_status)}</span>}
                        {!review && report.status === "draft" && <button type="button" disabled={Boolean(busy)} onClick={() => void submitReport(report)} style={secondaryButton}>{busy === "submit report for review" ? "Submitting..." : "Submit for Review"}</button>}
                        {user?.role === "clinician" && ["draft", "pending_review", "awaiting_review", "rejected"].includes(report.status) && <button type="button" disabled={Boolean(busy)} onClick={() => void markReportReviewed(report)} style={primaryButton}>{busy === "mark report reviewed" ? "Reviewing..." : "Review Report"}</button>}
                        {user?.role === "clinician" && <button type="button" disabled={Boolean(busy)} onClick={() => void saveClinicianGuidance(report)} style={secondaryButton}>{busy === "save clinician guidance" ? "Saving..." : "Save guidance"}</button>}
                        {user?.role === "clinician" && ["reviewed", "approved"].includes(report.status) && <button type="button" disabled={Boolean(busy)} onClick={() => void releaseReportToPatient(report)} style={primaryButton}>{busy === "release report to patient" ? "Sending..." : "Approve & Send to Patient"}</button>}
                        {user?.role === "clinician" && report.status === "completed" && <span style={{ ...statusStyle("completed"), background: "#eff6ff", color: "#0369a1" }}>Released</span>}
                        {user?.role === "clinician" && ["reviewed", "approved"].includes(report.status) && <button type="button" disabled={Boolean(busy)} onClick={() => void rejectReport(report)} style={secondaryButton}>Reject Report</button>}
                        {user?.role === "clinician" && <button type="button" disabled={Boolean(busy)} onClick={() => void removeReport(report)} style={dangerButton}>Delete Report</button>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </section>

      <section style={{ ...panel, background: "linear-gradient(135deg, #f0fdfa 0%, #eff6ff 100%)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>AI support</div>
            <h3 style={{ margin: "3px 0 5px", color: "#102a43" }}>AI analysis remains clinician-facing</h3>
            <p style={{ margin: 0, color: "#475569", fontSize: 12, maxWidth: 740 }}>Live Gemini analysis is available from Clinical Review. Reports should only become patient-facing after clinician review and approval.</p>
          </div>
          <button type="button" onClick={() => navigate("/clinical-workspace")} style={primaryButton}>Go to Clinical Review</button>
        </div>
      </section>
    </div>
    </>
  );
}
