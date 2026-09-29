import React, { useEffect, useMemo, useState } from "react";
import { getPatientProfile, searchPatients, type Patient, type PatientProfile } from "./api/patients";
import {
  completeAssessment,
  createAssessment,
  generateAssessmentReport,
  generatePatientClinicalSummary,
  generateRiskRecommendations,
  getRiskAssessment,
  getAIProviderHealth,
  getAIProviderStatus,
  listAssessments,
  listClinicianReviews,
  listRecommendations,
  listReports,
  runClinicalDecisionSupport,
  submitRecommendationForReview,
  submitReportForReview,
  updateRecommendationReview,
  updateReportReview,
  type AssessmentSession,
  type ClinicianReview,
  type Recommendation,
  type Report,
  type RiskAssessmentResult,
} from "./api/clinical";

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

function getAiReportContent(value: unknown): {
  clinical_summary?: string;
  recommendations_summary?: string;
  limitations?: string;
} | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  const ai = record.ai_generated_content;
  if (!ai || typeof ai !== "object") return null;
  const content = ai as Record<string, unknown>;
  const result = {
    clinical_summary: typeof content.clinical_summary === "string" ? content.clinical_summary : undefined,
    recommendations_summary: typeof content.recommendations_summary === "string" ? content.recommendations_summary : undefined,
    limitations: typeof content.limitations === "string" ? content.limitations : undefined,
  };
  return Object.values(result).some(Boolean) ? result : null;
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
    textTransform: "capitalize",
    background: positive ? "#ecfdf5" : waiting ? "#fff7ed" : "#f8fafc",
    color: positive ? "#047857" : waiting ? "#c2410c" : "#475569",
  };
}

type RecordSection =
  | "contacts"
  | "medical_history"
  | "allergies"
  | "medications"
  | "lifestyle"
  | "vital_signs"
  | "assessments";

const recordSectionMeta: Array<{
  key: RecordSection;
  title: string;
  icon: string;
  description: string;
}> = [
  { key: "contacts", title: "Contacts", icon: "☎", description: "Emergency and contact information" },
  { key: "medical_history", title: "Medical History", icon: "⌁", description: "Recorded medical history" },
  { key: "allergies", title: "Allergies", icon: "!", description: "Known or reported allergies" },
  { key: "medications", title: "Medications", icon: "+", description: "Current or recorded medications" },
  { key: "lifestyle", title: "Lifestyle", icon: "◌", description: "Lifestyle and social information" },
  { key: "vital_signs", title: "Vital Signs", icon: "♥", description: "Recorded vital signs" },
  { key: "assessments", title: "Assessments", icon: "✓", description: "Assessment sessions" },
];

function formatRecordLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function formatRecordValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not recorded";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function ClinicalRecordList({
  title,
  rows,
}: {
  title: string;
  rows: unknown[];
}) {
  if (!rows.length) {
    return (
      <div style={{ marginTop: 14, padding: 16, borderRadius: 13, background: "#f8fafc", border: "1px dashed #cbd5e1" }}>
        <strong style={{ color: "#334e68", fontSize: 13 }}>No {title.toLowerCase()} recorded</strong>
        <p style={{ margin: "5px 0 0", color: "#64748b", fontSize: 12 }}>
          There are currently no entries available in this section for clinician review.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
      {rows.map((row, index) => {
        const item = row && typeof row === "object" ? row as Record<string, unknown> : { value: row };
        return (
          <div key={`${title}-${index}`} style={{ padding: 14, borderRadius: 13, border: "1px solid #e2e8f0", background: "#fff" }}>
            <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, marginBottom: 9 }}>
              {title} {index + 1}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "9px 16px" }}>
              {Object.entries(item).map(([key, value]) => (
                <div key={key} style={{ minWidth: 0 }}>
                  <div style={{ color: "#64748b", fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {formatRecordLabel(key)}
                  </div>
                  <div style={{ marginTop: 3, color: "#334e68", fontSize: 13, whiteSpace: "pre-wrap", wordBreak: "break-word", lineHeight: 1.5 }}>
                    {formatRecordValue(value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function ClinicalWorkspace() {
  const [query, setQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientProfile, setPatientProfile] = useState<PatientProfile | null>(null);
  const [selectedRecordSection, setSelectedRecordSection] = useState<RecordSection | null>(null);
  const [recordLoading, setRecordLoading] = useState<RecordSection | null>(null);
  const [recordError, setRecordError] = useState("");
  const [assessments, setAssessments] = useState<AssessmentSession[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<AssessmentSession | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [reviews, setReviews] = useState<ClinicianReview[]>([]);
  const [reviewError, setReviewError] = useState("");
  const [risk, setRisk] = useState<RiskAssessmentResult | null>(null);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [decisionSupport, setDecisionSupport] = useState<string>("");
  const [aiAvailability, setAiAvailability] = useState<{ available: boolean; provider: string; model: string | null; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [assessmentType, setAssessmentType] = useState("clinical_review");
  const [assessmentSummary, setAssessmentSummary] = useState("");
  const [assessmentNotes, setAssessmentNotes] = useState("");

  const reviewByRecommendation = useMemo(() => {
    return new Map(
      reviews
        .filter((review) => review.recommendation_id !== null)
        .map((review) => [review.recommendation_id as number, review]),
    );
  }, [reviews]);

  const reviewByReport = useMemo(() => {
    return new Map(
      reviews
        .filter((review) => review.report_id !== null)
        .map((review) => [review.report_id as number, review]),
    );
  }, [reviews]);

  const clearFeedback = () => {
    setError("");
    setMessage("");
    setReviewError("");
  };

  const run = async (label: string, fn: () => Promise<void>) => {
    setBusyAction(label);
    clearFeedback();
    try {
      await fn();
    } catch (err: any) {
      setError(err?.response?.data?.detail || `Unable to ${label.toLowerCase()}.`);
    } finally {
      setBusyAction("");
    }
  };

  const loadReviewsSafely = async (assessmentId: number) => {
    try {
      const rows = await listClinicianReviews(assessmentId);
      setReviews(rows);
      setReviewError("");
    } catch (err: any) {
      setReviews([]);
      setReviewError(
        err?.response?.data?.detail ||
          "Clinician reviews could not be loaded. Recommendations and reports remain available."
      );
    }
  };

  const loadAssessmentBundle = async (assessment: AssessmentSession) => {
    setSelectedAssessment(assessment);
    setRisk(null);
    setAiSummary("");
    setDecisionSupport("");
    setReviewError("");
    clearFeedback();
    setLoading(true);
    try {
      const [recs, reportRows] = await Promise.all([
        listRecommendations(assessment.id),
        listReports(assessment.id),
      ]);
      setRecommendations(recs);
      setReports(reportRows);
      await loadReviewsSafely(assessment.id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to load the assessment workspace.");
    } finally {
      setLoading(false);
    }
  };

  const selectPatient = async (patient: Patient) => {
    clearFeedback();
    setRecordError("");
    setSelectedPatient(patient);
    setPatientProfile(null);
    setSelectedRecordSection(null);
    setSelectedAssessment(null);
    setAssessments([]);
    setRecommendations([]);
    setReports([]);
    setReviews([]);
    setRisk(null);
    setAiSummary("");
    setDecisionSupport("");
    setLoading(true);

    // Load the patient profile independently from the assessment bundle.
    // A failed assessment request must never disable the patient's record cards.
    try {
      const profile = await getPatientProfile(patient.id);
      setPatientProfile(profile);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Unable to load the patient clinical record.";
      setRecordError(detail);
      setError(detail);
    }

    try {
      const rows = await listAssessments(patient.id);
      setAssessments(rows);
      if (rows[0]) {
        await loadAssessmentBundle(rows[0]);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to load patient assessments.");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordSectionClick = async (section: RecordSection) => {
    clearFeedback();
    setSelectedRecordSection(section);

    if (!selectedPatient) return;

    const scrollToDetails = () => {
      window.requestAnimationFrame(() => {
        document.getElementById("care-clinical-record-details")?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    };

    if (patientProfile) {
      scrollToDetails();
      return;
    }

    setRecordLoading(section);
    setRecordError("");
    try {
      const profile = await getPatientProfile(selectedPatient.id);
      setPatientProfile(profile);
      scrollToDetails();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Unable to retrieve this clinical record.";
      setRecordError(detail);
      setError(detail);
    } finally {
      setRecordLoading(null);
    }
  };

  const search = async () => {
    setLoading(true);
    clearFeedback();
    try {
      const rows = await searchPatients({ search: query.trim() || undefined, limit: 20, offset: 0 });
      setPatients(rows);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to search patients.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void search();
    void (async () => {
      try {
        const [status, health] = await Promise.all([
          getAIProviderStatus(),
          getAIProviderHealth(),
        ]);
        setAiAvailability({
          available: Boolean(status.enabled && health.available),
          provider: health.provider || status.provider,
          model: health.model || null,
          message: health.message,
        });
      } catch {
        setAiAvailability({
          available: false,
          provider: "unknown",
          model: null,
          message: "AI provider status could not be checked.",
        });
      }
    })();
  }, []);

  const createNewAssessment = async () => {
    if (!selectedPatient) return;
    await run("create assessment", async () => {
      const created = await createAssessment(selectedPatient.id, {
        assessment_type: assessmentType.trim() || "clinical_review",
        status: "in_progress",
        summary: assessmentSummary.trim() || undefined,
        notes: assessmentNotes.trim() || undefined,
      });
      const rows = await listAssessments(selectedPatient.id);
      setAssessments(rows);
      setShowCreate(false);
      setAssessmentSummary("");
      setAssessmentNotes("");
      setMessage(`Assessment ${created.id} created.`);
      await loadAssessmentBundle(created);
    });
  };

  const refreshAssessmentBundle = async () => {
    if (!selectedAssessment) return;

    const [recs, reportRows] = await Promise.all([
      listRecommendations(selectedAssessment.id),
      listReports(selectedAssessment.id),
    ]);

    setRecommendations(recs);
    setReports(reportRows);
    await loadReviewsSafely(selectedAssessment.id);
  };

  const runRisk = async () => {
    if (!selectedAssessment) return;
    await run("run risk analysis", async () => {
      const result = await getRiskAssessment(selectedAssessment.id);
      setRisk(result);
      setMessage("Structured risk analysis completed.");
    });
  };

  const generateRecommendations = async () => {
    if (!selectedAssessment) return;
    await run("generate recommendations", async () => {
      const result = await generateRiskRecommendations(selectedAssessment.id);
      setRecommendations(result.recommendations);
      setMessage(`${result.recommendation_count} recommendation(s) saved.`);
      await refreshAssessmentBundle();
    });
  };

  const finishAssessment = async () => {
    if (!selectedAssessment) return;
    await run("complete assessment", async () => {
      const updated = await completeAssessment(selectedAssessment.id);
      setSelectedAssessment(updated);
      setAssessments((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage("Assessment marked completed.");
    });
  };

  const reviewRecommendation = async (recommendation: Recommendation, action: "approve" | "reject") => {
    if (!selectedAssessment) return;
    await run(`${action} recommendation`, async () => {
      const currentReview = reviewByRecommendation.get(recommendation.id);
      if (!currentReview) {
        await submitRecommendationForReview(selectedAssessment.id, recommendation.id);
      }
      await updateRecommendationReview(
        selectedAssessment.id,
        recommendation.id,
        action === "approve" ? "approved" : "rejected",
        action === "approve" ? "Reviewed and approved by clinician." : "Reviewed and rejected by clinician.",
      );
      await refreshAssessmentBundle();
      setMessage(`Recommendation ${action === "approve" ? "approved" : "rejected"}.`);
    });
  };

  const submitRecommendation = async (recommendation: Recommendation) => {
    if (!selectedAssessment) return;
    await run("submit recommendation for review", async () => {
      await submitRecommendationForReview(selectedAssessment.id, recommendation.id);
      await refreshAssessmentBundle();
      setMessage("Recommendation sent to clinician review.");
    });
  };

  const generateReport = async () => {
    if (!selectedAssessment) return;
    await run("generate report", async () => {
      const report = await generateAssessmentReport(selectedAssessment.id);
      await refreshAssessmentBundle();
      setMessage(`Report version ${report.version} generated.`);
    });
  };

  const reviewReport = async (report: Report, action: "approve" | "reject") => {
    if (!selectedAssessment) return;
    await run(`${action} report`, async () => {
      const currentReview = reviewByReport.get(report.id);
      if (!currentReview) await submitReportForReview(selectedAssessment.id, report.id);
      await updateReportReview(
        selectedAssessment.id,
        report.id,
        action === "approve" ? "approved" : "rejected",
        action === "approve" ? "Report reviewed and approved by clinician." : "Report reviewed and rejected by clinician.",
      );
      await refreshAssessmentBundle();
      setMessage(`Report ${action === "approve" ? "approved" : "rejected"}.`);
    });
  };

  const submitReport = async (report: Report) => {
    if (!selectedAssessment) return;
    await run("submit report for review", async () => {
      await submitReportForReview(selectedAssessment.id, report.id);
      await refreshAssessmentBundle();
      setMessage("Report sent to clinician review.");
    });
  };

  return (
    <div style={{ display: "grid", gap: 18, animation: "careFadeUp 420ms ease both" }}>
      <div>
        <div style={{ color: "#0f766e", fontSize: 12, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.1em" }}>Clinical workspace</div>
        <h1 style={{ margin: "4px 0 6px", color: "#102a43", fontSize: 31, letterSpacing: "-0.03em" }}>Clinical Review</h1>
        <p style={{ margin: 0, color: "#627d98" }}>Review patient-submitted information, run structured risk analysis, use clinician-facing AI support, and approve recommendations before they reach the patient.</p>
      </div>

      {message && <div style={{ padding: "11px 13px", background: "#ecfdf5", border: "1px solid #a7f3d0", borderRadius: 11, color: "#047857", fontWeight: 750, fontSize: 13 }}>{message}</div>}
      {error && <div style={{ padding: "11px 13px", background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: 11, color: "#be123c", fontWeight: 750, fontSize: 13 }}>{error}</div>}

      <section style={panel}>
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: 12 }}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void search(); }} placeholder="Search patient name or patient number..." style={input} />
          <button type="button" onClick={() => void search()} disabled={loading} style={primaryButton}>{loading ? "Searching..." : "Search"}</button>
        </div>
        {patients.length > 0 && (
          <div style={{ display: "grid", gap: 8, marginTop: 14 }}>
            {patients.map((patient) => (
              <button key={patient.id} type="button" onClick={() => void selectPatient(patient)} style={{ textAlign: "left", border: "1px solid #e2e8f0", borderRadius: 13, padding: 13, background: selectedPatient?.id === patient.id ? "#f0fdfa" : "#fff", cursor: "pointer" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <div><strong style={{ color: "#102a43" }}>{patient.first_name} {patient.last_name}</strong><div style={{ color: "#627d98", fontSize: 12, marginTop: 3 }}>{patient.patient_number} · {patient.district || "Location not recorded"}</div></div>
                  <span style={statusStyle(patient.status)}>{humanize(patient.status)}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {!selectedPatient ? (
        <section style={panel}><h2 style={{ marginTop: 0, color: "#102a43" }}>Select a patient</h2><p style={{ color: "#627d98" }}>Choose a patient above to open the clinical review workspace.</p></section>
      ) : (
        <>
          <section style={{ ...panel, background: "linear-gradient(135deg, #effcfb 0%, #ffffff 60%, #eff8ff 100%)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 18, flexWrap: "wrap", alignItems: "center" }}>
              <div><div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.1em" }}>Patient record</div><h2 style={{ margin: "4px 0 5px", color: "#102a43", fontSize: 26 }}>{selectedPatient.first_name} {selectedPatient.last_name}</h2><div style={{ color: "#627d98", fontSize: 13 }}>{selectedPatient.patient_number} · {selectedPatient.district || "Location not recorded"} · {humanize(selectedPatient.status)}</div></div>
              <button type="button" onClick={() => setShowCreate((value) => !value)} style={secondaryButton}>{showCreate ? "Close" : "+ New assessment"}</button>
            </div>
            {showCreate && (
              <div style={{ marginTop: 18, padding: 16, borderRadius: 14, background: "rgba(255,255,255,0.78)", border: "1px solid #dcebea", display: "grid", gap: 12 }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: 12 }}>
                  <input value={assessmentType} onChange={(event) => setAssessmentType(event.target.value)} placeholder="Assessment type" style={input} />
                  <input value={assessmentSummary} onChange={(event) => setAssessmentSummary(event.target.value)} placeholder="Assessment summary" style={input} />
                </div>
                <textarea value={assessmentNotes} onChange={(event) => setAssessmentNotes(event.target.value)} placeholder="Clinical notes" style={{ ...input, minHeight: 90, resize: "vertical" }} />
                <button type="button" disabled={Boolean(busyAction)} onClick={() => void createNewAssessment()} style={{ ...primaryButton, justifySelf: "start" }}>{busyAction === "create assessment" ? "Creating..." : "Create assessment"}</button>
              </div>
            )}
          </section>

          <section style={{ ...panel, background: "linear-gradient(135deg, #ffffff 0%, #f8fcff 100%)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
              <div>
                <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>Patient clinical record</div>
                <h3 style={{ margin: "4px 0 5px", color: "#102a43", fontSize: 21 }}>Clinical information</h3>
                <p style={{ margin: 0, color: "#627d98", fontSize: 12 }}>Select a record card to retrieve and review the patient's submitted clinical information.</p>
              </div>
              <span style={{ ...statusStyle("completed"), background: recordError ? "#fff7ed" : "#eff6ff", color: recordError ? "#c2410c" : "#2563eb" }}>
                {recordError ? "Unable to load record" : patientProfile ? "Record loaded" : "Loading record..."}
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, marginTop: 15 }}>
              {recordSectionMeta.map((section) => {
                const rows = patientProfile?.[section.key] ?? [];
                const active = selectedRecordSection === section.key;
                return (
                  <button
                    key={section.key}
                    type="button"
                    onClick={() => void handleRecordSectionClick(section.key)}
                    disabled={recordLoading === section.key}
                    aria-pressed={active}
                    aria-busy={recordLoading === section.key}
                    style={{
                      textAlign: "left",
                      border: active ? "1px solid #5eead4" : "1px solid #e2e8f0",
                      borderRadius: 14,
                      padding: 13,
                      background: active ? "#f0fdfa" : "#fff",
                      cursor: recordLoading === section.key ? "wait" : "pointer",
                      opacity: recordLoading === section.key ? 0.82 : 1,
                      userSelect: "none",
                      boxShadow: active ? "0 8px 22px rgba(15,118,110,0.09)" : "none",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                      <span style={{ width: 32, height: 32, borderRadius: 10, display: "inline-flex", alignItems: "center", justifyContent: "center", background: active ? "#ccfbf1" : "#eff6ff", color: active ? "#0f766e" : "#2563eb", fontWeight: 900 }}>{section.icon}</span>
                      <strong style={{ color: "#102a43", fontSize: 20 }}>{rows.length}</strong>
                    </div>
                    <div style={{ marginTop: 10, color: "#102a43", fontWeight: 800, fontSize: 13 }}>{section.title}</div>
                    <div style={{ marginTop: 3, color: "#64748b", fontSize: 11, lineHeight: 1.4 }}>{section.description}</div>
                  </button>
                );
              })}
            </div>

            {selectedRecordSection && (
              <div
                id="care-clinical-record-details"
                style={{ marginTop: 16, paddingTop: 15, borderTop: "1px solid #e2e8f0", scrollMarginTop: 90 }}
              >
                {(() => {
                  const meta = recordSectionMeta.find((section) => section.key === selectedRecordSection);
                  if (!meta) return null;
                  if (!patientProfile) {
                    return (
                      <div style={{ padding: 16, borderRadius: 13, background: "#f8fafc", border: "1px dashed #cbd5e1", color: "#64748b", fontSize: 13 }}>
                        Loading {meta.title.toLowerCase()} records...
                      </div>
                    );
                  }
                  const rows = patientProfile[selectedRecordSection] ?? [];
                  return (
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                        <div>
                          <h4 style={{ margin: 0, color: "#102a43", fontSize: 16 }}>{meta.title}</h4>
                          <p style={{ margin: "4px 0 0", color: "#627d98", fontSize: 12 }}>{meta.description}</p>
                        </div>
                        <span style={{ ...statusStyle("completed"), background: "#f0fdfa", color: "#0f766e" }}>
                          {rows.length} {rows.length === 1 ? "record" : "records"}
                        </span>
                      </div>
                      <ClinicalRecordList title={meta.title} rows={rows} />
                    </div>
                  );
                })()}
              </div>
            )}
          </section>

          <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 0.85fr) minmax(0, 1.65fr)", gap: 18 }}>
            <section style={panel}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", marginBottom: 12 }}><div><h3 style={{ margin: 0, color: "#102a43" }}>Assessments</h3><p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>Select an assessment to review.</p></div><span style={{ ...statusStyle("completed"), background: "#f0fdfa", color: "#0f766e" }}>{assessments.length} total</span></div>
              {assessments.length === 0 ? <div style={{ padding: 15, borderRadius: 12, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>No assessment sessions yet. Create the first clinical review for this patient.</div> : <div style={{ display: "grid", gap: 8 }}>{assessments.map((assessment) => <button type="button" key={assessment.id} onClick={() => void loadAssessmentBundle(assessment)} style={{ textAlign: "left", border: selectedAssessment?.id === assessment.id ? "1px solid #5eead4" : "1px solid #e2e8f0", borderRadius: 12, padding: 12, background: selectedAssessment?.id === assessment.id ? "#f0fdfa" : "#fff", cursor: "pointer" }}><div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><strong style={{ color: "#102a43" }}>Assessment {assessment.id}</strong><span style={statusStyle(assessment.status)}>{humanize(assessment.status)}</span></div><div style={{ marginTop: 5, color: "#627d98", fontSize: 12 }}>{humanize(assessment.assessment_type)} · {new Date(assessment.started_at).toLocaleString()}</div></button>)}</div>}
            </section>

            <section style={panel}>
              {!selectedAssessment ? <><h3 style={{ marginTop: 0, color: "#102a43" }}>Assessment intelligence</h3><p style={{ color: "#627d98" }}>Select an assessment to begin structured analysis and clinical review.</p></> : <>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 14, alignItems: "flex-start", flexWrap: "wrap" }}>
                  <div><div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>Assessment {selectedAssessment.id}</div><h3 style={{ margin: "4px 0 6px", color: "#102a43", fontSize: 22 }}>{humanize(selectedAssessment.assessment_type)}</h3><p style={{ margin: 0, color: "#627d98", fontSize: 13 }}>{selectedAssessment.summary || "No assessment summary recorded."}</p></div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><span style={statusStyle(selectedAssessment.status)}>{humanize(selectedAssessment.status)}</span>{selectedAssessment.status !== "completed" && <button type="button" onClick={() => void finishAssessment()} disabled={Boolean(busyAction)} style={secondaryButton}>Complete assessment</button>}</div>
                </div>

                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 18 }}>
                  <button type="button" onClick={() => void runRisk()} disabled={Boolean(busyAction)} style={primaryButton}>{busyAction === "run risk analysis" ? "Analyzing..." : "Run risk analysis"}</button>
                  <button type="button" onClick={() => void generateRecommendations()} disabled={Boolean(busyAction)} style={secondaryButton}>{busyAction === "generate recommendations" ? "Generating..." : "Generate recommendations"}</button>
                  <button
                    type="button"
                    onClick={() => void generateReport()}
                    disabled={Boolean(busyAction) || selectedAssessment.status !== "completed"}
                    style={{ ...primaryButton, opacity: selectedAssessment.status === "completed" ? 1 : 0.58 }}
                    title={selectedAssessment.status !== "completed" ? "Complete the assessment before generating a medical report." : "Generate a medical report from this completed assessment."}
                  >
                    {busyAction === "generate report" ? "Generating..." : "Generate Medical Report"}
                  </button>
                </div>
                {selectedAssessment.status !== "completed" && (
                  <div style={{ marginTop: 9, color: "#64748b", fontSize: 12 }}>
                    Complete this assessment first. Once completed, you can generate the medical report for clinician review.
                  </div>
                )}

                {risk && <div style={{ marginTop: 18, display: "grid", gridTemplateColumns: "repeat(3, minmax(0,1fr))", gap: 10 }}><div style={{ padding: 14, borderRadius: 13, background: "#f8fafc" }}><div style={{ color: "#64748b", fontSize: 11, fontWeight: 800, textTransform: "uppercase" }}>Risk score</div><strong style={{ display: "block", marginTop: 5, color: "#102a43", fontSize: 24 }}>{risk.risk_score.score}</strong></div><div style={{ padding: 14, borderRadius: 13, background: "#f8fafc" }}><div style={{ color: "#64748b", fontSize: 11, fontWeight: 800, textTransform: "uppercase" }}>Risk level</div><strong style={{ display: "block", marginTop: 5, color: "#0f766e", fontSize: 18, textTransform: "capitalize" }}>{humanize(risk.risk_score.risk_level)}</strong></div><div style={{ padding: 14, borderRadius: 13, background: "#f8fafc" }}><div style={{ color: "#64748b", fontSize: 11, fontWeight: 800, textTransform: "uppercase" }}>Risk factors</div><strong style={{ display: "block", marginTop: 5, color: "#102a43", fontSize: 24 }}>{risk.risk_factors.factor_count}</strong></div></div>}

                {risk?.risk_factors.factors.length ? <div style={{ marginTop: 16 }}><h4 style={{ margin: "0 0 8px", color: "#102a43" }}>Identified factors</h4><div style={{ display: "grid", gap: 7 }}>{risk.risk_factors.factors.map((factor, index) => <div key={`${factor.factor}-${index}`} style={{ padding: "10px 12px", borderRadius: 11, border: "1px solid #e2e8f0", background: "#fff", display: "flex", justifyContent: "space-between", gap: 10 }}><span style={{ color: "#334e68", fontSize: 13 }}>{humanize(factor.factor)}</span><span style={statusStyle(factor.severity)}>{humanize(factor.severity)}</span></div>)}</div></div> : null}
              </>}
            </section>
          </div>

          {selectedAssessment && <>
            {reviewError && (
              <div style={{ padding: "11px 13px", background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: 11, color: "#c2410c", fontWeight: 750, fontSize: 13 }}>
                {reviewError}
              </div>
            )}
            <section style={panel}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}><div><h3 style={{ margin: 0, color: "#102a43" }}>Recommendations</h3><p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>Recommendations remain drafts or pending until a clinician reviews them.</p></div><span style={statusStyle("pending")}>{recommendations.length} items</span></div>
              {recommendations.length === 0 ? <div style={{ marginTop: 12, padding: 15, background: "#f8fafc", borderRadius: 12, color: "#64748b", fontSize: 13 }}>No recommendations saved yet. Run the recommendation generator after risk analysis.</div> : <div style={{ display: "grid", gap: 10, marginTop: 12 }}>{recommendations.map((recommendation) => { const review = reviewByRecommendation.get(recommendation.id); return <div key={recommendation.id} style={{ padding: 15, borderRadius: 13, border: "1px solid #e2e8f0", background: "#fff" }}><div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}><div><div style={{ display: "flex", gap: 7, flexWrap: "wrap", alignItems: "center" }}><strong style={{ color: "#102a43" }}>{recommendation.title}</strong><span style={statusStyle(recommendation.status)}>{humanize(recommendation.status)}</span></div><p style={{ margin: "7px 0 0", color: "#334e68", lineHeight: 1.55, fontSize: 13 }}>{recommendation.recommendation_text}</p></div><span style={statusStyle(recommendation.priority)}>{humanize(recommendation.priority)}</span></div><div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>{!review && recommendation.status === "draft" && <button type="button" disabled={Boolean(busyAction)} onClick={() => void submitRecommendation(recommendation)} style={secondaryButton}>Submit for review</button>}{review && <span style={statusStyle(review.review_status)}>Review: {humanize(review.review_status)}</span>}{review && review.review_status === "pending" && <><button type="button" disabled={Boolean(busyAction)} onClick={() => void reviewRecommendation(recommendation, "approve")} style={primaryButton}>Approve</button><button type="button" disabled={Boolean(busyAction)} onClick={() => void reviewRecommendation(recommendation, "reject")} style={secondaryButton}>Reject</button></>}</div></div>; })}</div>}
            </section>

            <section style={{ ...panel, background: "linear-gradient(135deg, #ffffff 0%, #f7fbff 100%)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <div>
                  <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>Clinical documentation</div>
                  <h3 style={{ margin: "3px 0 0", color: "#102a43", fontSize: 20 }}>Medical Report</h3>
                  <p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>Generate a structured report from the completed assessment, then submit it for clinician review before patient release.</p>
                </div>
                <span style={{ ...statusStyle("pending"), background: reports.length ? "#f0fdfa" : "#f8fafc", color: reports.length ? "#0f766e" : "#64748b" }}>{reports.length} {reports.length === 1 ? "report" : "reports"}</span>
              </div>

              <div style={{ marginTop: 14, padding: 14, borderRadius: 13, border: "1px dashed #cbd5e1", background: "#fbfdff" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                  <div>
                    <strong style={{ color: "#102a43" }}>Create a new medical report</strong>
                    <p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>
                      {selectedAssessment.status === "completed" ? "The report will summarize this completed assessment, risk findings, and recommendations." : "Complete the assessment above before creating the medical report."}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={Boolean(busyAction) || selectedAssessment.status !== "completed"}
                    onClick={() => void generateReport()}
                    style={{ ...primaryButton, opacity: selectedAssessment.status === "completed" ? 1 : 0.58 }}
                  >
                    {busyAction === "generate report" ? "Generating..." : "Create / Generate Medical Report"}
                  </button>
                </div>
              </div>

              {reports.length === 0 ? (
                <div style={{ marginTop: 12, padding: 15, background: "#f8fafc", borderRadius: 12, color: "#64748b", fontSize: 13 }}>
                  No medical report has been created for this assessment yet.
                </div>
              ) : (
                <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
                  {reports.map((report) => {
                    const review = reviewByReport.get(report.id);
                    const reportText = typeof report.report_content === "string" ? report.report_content : JSON.stringify(report.report_content, null, 2);
                    const aiReportContent = getAiReportContent(report.report_content);
                    return (
                      <div key={report.id} style={{ padding: 15, borderRadius: 13, border: "1px solid #e2e8f0", background: "#fff" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                          <div>
                            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                              <strong style={{ color: "#102a43" }}>{report.report_title}</strong>
                              <span style={statusStyle(report.status)}>{humanize(report.status)}</span>
                            </div>
                            <p style={{ margin: "6px 0 0", color: "#475569", fontSize: 13, lineHeight: 1.5 }}>{report.executive_summary || "No executive summary available."}</p>
                          </div>
                          <span style={{ color: "#64748b", fontSize: 11 }}>v{report.version}</span>
                        </div>

                        {aiReportContent && (
                          <div style={{ marginTop: 10, padding: 12, borderRadius: 11, background: "linear-gradient(135deg, #ecfeff 0%, #eff6ff 100%)", border: "1px solid #bae6fd" }}>
                            <strong style={{ color: "#0f3b5f", fontSize: 12 }}>AI-generated report content</strong>
                            {aiReportContent.clinical_summary && <div style={{ marginTop: 5, color: "#334e68", fontSize: 12, lineHeight: 1.55, whiteSpace: "pre-wrap" }}>{aiReportContent.clinical_summary}</div>}
                            {aiReportContent.recommendations_summary && <div style={{ marginTop: 7, color: "#334e68", fontSize: 12, lineHeight: 1.55, whiteSpace: "pre-wrap" }}><strong>AI recommendation summary</strong><div style={{ marginTop: 3 }}>{aiReportContent.recommendations_summary}</div></div>}
                          </div>
                        )}

                        {report.recommendations_summary && (
                          <div style={{ marginTop: 10, padding: 11, borderRadius: 11, background: "#f8fafc", color: "#334e68", fontSize: 12, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
                            <strong style={{ color: "#102a43" }}>Recommendations summary</strong>
                            <div style={{ marginTop: 5 }}>{report.recommendations_summary}</div>
                          </div>
                        )}

                        <details style={{ marginTop: 10 }}>
                          <summary style={{ cursor: "pointer", color: "#0f766e", fontWeight: 750, fontSize: 12 }}>View report content</summary>
                          <pre style={{ margin: "9px 0 0", padding: 12, borderRadius: 11, background: "#0f172a", color: "#e2e8f0", overflowX: "auto", fontSize: 11, lineHeight: 1.55 }}>{reportText}</pre>
                        </details>

                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
                          {!review && report.status === "draft" && <button type="button" disabled={Boolean(busyAction)} onClick={() => void submitReport(report)} style={secondaryButton}>Submit for review</button>}
                          {review && <span style={statusStyle(review.review_status)}>Review: {humanize(review.review_status)}</span>}
                          {review && review.review_status === "pending" && <>
                            <button type="button" disabled={Boolean(busyAction)} onClick={() => void reviewReport(report, "approve")} style={primaryButton}>Approve</button>
                            <button type="button" disabled={Boolean(busyAction)} onClick={() => void reviewReport(report, "reject")} style={secondaryButton}>Reject</button>
                          </>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            <section style={panel}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
                <div><h3 style={{ margin: 0, color: "#102a43" }}>Clinician-facing AI support</h3><p style={{ margin: "5px 0 0", color: "#627d98", fontSize: 12 }}>AI output is decision support for the clinical team; it is not the final clinical decision.</p></div>
                <span style={statusStyle(aiAvailability?.available ? "active" : "pending")}>{aiAvailability?.available ? `AI ready${aiAvailability.model ? ` · ${aiAvailability.model}` : ""}` : "AI unavailable"}</span>
              </div>
              {aiAvailability && <div style={{ marginTop: 10, color: "#64748b", fontSize: 11 }}>Provider: {humanize(aiAvailability.provider)} · {aiAvailability.message}</div>}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 13 }}><button type="button" disabled={Boolean(busyAction) || aiAvailability?.available === false} onClick={() => void run("generate AI clinical summary", async () => { const result = await generatePatientClinicalSummary(selectedPatient.id); if (!result.summary?.trim()) throw new Error("AI provider returned an empty clinical summary."); setAiSummary(result.summary.trim()); })} style={{ ...secondaryButton, opacity: aiAvailability?.available === false ? 0.58 : 1 }}>{busyAction === "generate AI clinical summary" ? "Generating..." : "Generate AI clinical summary"}</button><button type="button" disabled={Boolean(busyAction) || aiAvailability?.available === false} onClick={() => void run("run AI clinical decision support", async () => { const result = await runClinicalDecisionSupport(selectedPatient.id); if (!result.decision_support?.trim()) throw new Error("AI provider returned empty decision support."); setDecisionSupport(result.decision_support.trim()); })} style={{ ...secondaryButton, opacity: aiAvailability?.available === false ? 0.58 : 1 }}>{busyAction === "run AI clinical decision support" ? "Analyzing..." : "Run AI decision support"}</button></div>
              {aiSummary && <div style={{ marginTop: 14, padding: 14, borderRadius: 12, background: "#f0fdfa", border: "1px solid #ccfbf1" }}><div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}><strong style={{ color: "#102a43" }}>AI clinical summary</strong>{aiAvailability?.model && <span style={{ color: "#64748b", fontSize: 10 }}>{humanize(aiAvailability.provider)} · {aiAvailability.model}</span>}</div><p style={{ margin: "7px 0 0", whiteSpace: "pre-wrap", color: "#334e68", lineHeight: 1.6, fontSize: 13 }}>{aiSummary}</p></div>}
              {decisionSupport && <div style={{ marginTop: 12, padding: 14, borderRadius: 12, background: "#eff6ff", border: "1px solid #dbeafe" }}><div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}><strong style={{ color: "#102a43" }}>AI clinical decision support</strong>{aiAvailability?.model && <span style={{ color: "#64748b", fontSize: 10 }}>{humanize(aiAvailability.provider)} · {aiAvailability.model}</span>}</div><p style={{ margin: "7px 0 0", whiteSpace: "pre-wrap", color: "#334e68", lineHeight: 1.6, fontSize: 13 }}>{decisionSupport}</p></div>}
            </section>
          </>}
        </>
      )}
    </div>
  );
}
