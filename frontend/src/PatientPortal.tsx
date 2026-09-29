import React, { useEffect, useState } from "react";
import { getMyPatientProfile } from "./api/patients";
import {
  addMyAllergy,
  addMyContact,
  addMyLifestyle,
  addMyMedicalHistory,
  addMyMedication,
  addMyVitalSigns,
  getMyCareSummary,
  markMyReportReviewed,
  updateMyPatientProfile,
  type PatientCareSummary,
} from "./api/patientPortal";
import type { PatientProfile } from "./api/patients";
import PatientAvatar from "./components/PatientAvatar";
import { uploadMyProfilePicture } from "./api/profileImages";

const field: React.CSSProperties = { width: "100%", padding: "11px 12px", borderRadius: "10px", border: "1px solid #d7e2e8", background: "#fff", boxSizing: "border-box", color: "#102a43" };
const label: React.CSSProperties = { display: "block", marginBottom: "6px", fontSize: "11px", fontWeight: 800, color: "#627d98", textTransform: "uppercase", letterSpacing: "0.06em" };
const card: React.CSSProperties = { background: "rgba(255,255,255,0.96)", border: "1px solid #e6eef2", borderRadius: "18px", padding: "22px", boxShadow: "0 12px 32px rgba(16,42,67,0.05)" };

function FormRow({ children }: { children: React.ReactNode }) { return <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: "14px" }}>{children}</div>; }

function stringifyReportContent(value: unknown) {
  if (typeof value === "string") return value;
  try { return JSON.stringify(value, null, 2); } catch { return String(value ?? ""); }
}

export default function PatientPortal() {
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [care, setCare] = useState<PatientCareSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [avatarRefreshKey, setAvatarRefreshKey] = useState(0);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [section, setSection] = useState<string | null>(null);
  const [reviewingReportId, setReviewingReportId] = useState<number | null>(null);

  const [personal, setPersonal] = useState({ first_name: "", last_name: "", date_of_birth: "", sex: "", marital_status: "", occupation: "", preferred_language: "", residence: "", district: "", country: "" });
  const [contact, setContact] = useState({ phone: "", email: "", address: "", next_of_kin: "", next_of_kin_phone: "", emergency_contact: "", emergency_phone: "", relationship: "" });
  const [history, setHistory] = useState({ condition_name: "", description: "", diagnosed_date: "", status: "active", notes: "" });
  const [allergy, setAllergy] = useState({ allergen: "", reaction: "", severity: "", notes: "" });
  const [medication, setMedication] = useState({ medication_name: "", dose: "", frequency: "", route: "", start_date: "", end_date: "", status: "active", prescribed_by: "", notes: "" });
  const [lifestyle, setLifestyle] = useState({ smoking_status: "", alcohol_use: "", physical_activity_level: "", exercise_frequency: "", diet_pattern: "", sleep_duration_hours: "", sleep_quality: "", stress_level: "", additional_notes: "" });
  const [vitals, setVitals] = useState({ height: "", weight: "", blood_pressure_systolic: "", blood_pressure_diastolic: "", pulse: "", temperature: "", oxygen_saturation: "", bmi: "" });

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [p, c] = await Promise.all([getMyPatientProfile(), getMyCareSummary()]);
      setProfile(p); setCare(c);
      const x = p.patient;
      setPersonal({ first_name: x.first_name ?? "", last_name: x.last_name ?? "", date_of_birth: x.date_of_birth ?? "", sex: x.sex ?? "", marital_status: x.marital_status ?? "", occupation: x.occupation ?? "", preferred_language: x.preferred_language ?? "", residence: x.residence ?? "", district: x.district ?? "", country: x.country ?? "" });
      if (p.contacts[0]) setContact({ ...contact, ...Object.fromEntries(Object.entries(p.contacts[0] as any).filter(([k]) => k in contact)) } as any);
    } catch (err: any) { setError(err?.response?.data?.detail || "Unable to load your patient portal."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const handleProfilePictureUpload = async (file: File) => {
    setUploadingAvatar(true);
    setError("");
    setMessage("");
    try {
      await uploadMyProfilePicture(file);
      setAvatarRefreshKey((value) => value + 1);
      setMessage("Profile picture updated successfully.");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to update your profile picture.");
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleReportReviewed = async (reportId: number) => {
    setReviewingReportId(reportId);
    setError("");
    setMessage("");
    try {
      await markMyReportReviewed(reportId);
      await load();
      setMessage("Report marked as reviewed.");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to mark this report as reviewed.");
    } finally {
      setReviewingReportId(null);
    }
  };

  if (loading) return <section style={card}><h1 style={{ marginTop: 0 }}>My Health</h1><p style={{ color: "#627d98" }}>Loading your secure patient portal...</p></section>;
  if (error || !profile) return <section style={card}><h1 style={{ marginTop: 0 }}>My Health</h1><p style={{ color: "#be123c" }}>{error || "Patient record unavailable."}</p></section>;

  const p = profile.patient;
  const save = async (fn: () => Promise<unknown>) => { setSaving(true); setError(""); setMessage(""); try { await fn(); await load(); setMessage("Saved successfully."); setSection(null); } catch (err: any) { setError(err?.response?.data?.detail || "Unable to save this information."); } finally { setSaving(false); } };

  return (
    <div style={{ display: "grid", gap: "18px" }}>
      <section style={{ ...card, padding: 0, overflow: "hidden", background: "linear-gradient(135deg, #073b4c, #087f78)" }}>
        <div style={{ padding: "24px", display: "flex", justifyContent: "space-between", gap: "18px", alignItems: "center", flexWrap: "wrap", color: "#fff" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px", minWidth: 0 }}>
            <PatientAvatar
              patientId={p.id}
              firstName={p.first_name}
              lastName={p.last_name}
              size={76}
              radius={22}
              refreshKey={avatarRefreshKey}
              label={`${p.first_name} ${p.last_name} profile picture`}
            />
            <div style={{ minWidth: 0 }}><div style={{ fontSize: "11px", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.78 }}>Patient portal</div><h1 style={{ margin: "5px 0", fontSize: "29px" }}>{p.first_name} {p.last_name}</h1><div style={{ opacity: 0.85 }}>Patient number {p.patient_number}</div></div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 9, flexWrap: "wrap" }}>
            <label className="care-photo-upload-button" style={{ background: "rgba(255,255,255,0.92)" }}>
              <span>{uploadingAvatar ? "Uploading..." : "Change photo"}</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                disabled={uploadingAvatar}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  event.currentTarget.value = "";
                  if (file) void handleProfilePictureUpload(file);
                }}
                style={{ display: "none" }}
              />
            </label>
            <div style={{ padding: "8px 11px", borderRadius: "999px", background: "rgba(255,255,255,0.14)", fontSize: "12px", fontWeight: 800 }}>Account active</div>
          </div>
        </div>
      </section>

      {message && <div style={{ padding: "11px 13px", background: "#ecfdf5", border: "1px solid #a7f3d0", borderRadius: "11px", color: "#047857", fontSize: "13px", fontWeight: 700 }}>{message}</div>}
      {error && <div style={{ padding: "11px 13px", background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: "11px", color: "#be123c", fontSize: "13px", fontWeight: 700 }}>{error}</div>}

      <section style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "18px" }}><div><h2 style={{ margin: 0, color: "#102a43" }}>Your information</h2><p style={{ margin: "5px 0 0", color: "#627d98", fontSize: "13px" }}>Keep your basic details current so your care team has accurate information.</p></div><button onClick={() => setSection(section === "personal" ? null : "personal")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "personal" ? "Close" : "Edit"}</button></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0,1fr))", gap: "14px" }}><div><b style={label}>Date of birth</b>{p.date_of_birth || "Not recorded"}</div><div><b style={label}>Sex</b>{p.sex || "Not recorded"}</div><div><b style={label}>Occupation</b>{p.occupation || "Not recorded"}</div><div><b style={label}>District</b>{p.district || "Not recorded"}</div></div>
        {section === "personal" && <div style={{ marginTop: "20px", display: "grid", gap: "14px" }}><FormRow><div><label style={label}>First name</label><input style={field} value={personal.first_name} onChange={e => setPersonal({ ...personal, first_name: e.target.value })} /></div><div><label style={label}>Last name</label><input style={field} value={personal.last_name} onChange={e => setPersonal({ ...personal, last_name: e.target.value })} /></div><div><label style={label}>Date of birth</label><input style={field} type="date" value={personal.date_of_birth} onChange={e => setPersonal({ ...personal, date_of_birth: e.target.value })} /></div><div><label style={label}>Preferred language</label><input style={field} value={personal.preferred_language} onChange={e => setPersonal({ ...personal, preferred_language: e.target.value })} /></div></FormRow><div><label style={label}>Residence</label><textarea style={{ ...field, minHeight: "85px" }} value={personal.residence} onChange={e => setPersonal({ ...personal, residence: e.target.value })} /></div><button disabled={saving} onClick={() => save(() => updateMyPatientProfile(personal))} style={{ justifySelf: "start", border: 0, background: "#0f766e", color: "#fff", borderRadius: "10px", padding: "10px 14px", fontWeight: 800 }}>{saving ? "Saving..." : "Save details"}</button></div>}
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: "18px" }}>
        <section style={card}><h3 style={{ margin: 0, color: "#102a43" }}>Medical history <span style={{ color: "#0f766e" }}>{profile.medical_history.length}</span></h3><p style={{ color: "#627d98", fontSize: "13px" }}>Tell your care team about previous or ongoing conditions.</p><button onClick={() => setSection(section === "history" ? null : "history")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "history" ? "Close" : "Add history"}</button>{section === "history" && <div style={{ marginTop: 15, display: "grid", gap: 12 }}><input style={field} placeholder="Condition name" value={history.condition_name} onChange={e => setHistory({ ...history, condition_name: e.target.value })} /><input style={field} type="date" value={history.diagnosed_date} onChange={e => setHistory({ ...history, diagnosed_date: e.target.value })} /><textarea style={{ ...field, minHeight: 75 }} placeholder="Description / notes" value={history.notes} onChange={e => setHistory({ ...history, notes: e.target.value })} /><button disabled={saving} onClick={() => save(() => addMyMedicalHistory({ ...history, diagnosed_date: history.diagnosed_date || undefined }))} style={{ border: 0, background: "#0f766e", color: "#fff", borderRadius: 10, padding: 10, fontWeight: 800 }}>Save medical history</button></div>}</section>
        <section style={card}><h3 style={{ margin: 0, color: "#102a43" }}>Allergies <span style={{ color: "#0f766e" }}>{profile.allergies.length}</span></h3><p style={{ color: "#627d98", fontSize: "13px" }}>Record medicines, foods or substances that cause reactions.</p><button onClick={() => setSection(section === "allergy" ? null : "allergy")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "allergy" ? "Close" : "Add allergy"}</button>{section === "allergy" && <div style={{ marginTop: 15, display: "grid", gap: 12 }}><input style={field} placeholder="Allergen" value={allergy.allergen} onChange={e => setAllergy({ ...allergy, allergen: e.target.value })} /><input style={field} placeholder="Reaction" value={allergy.reaction} onChange={e => setAllergy({ ...allergy, reaction: e.target.value })} /><select style={field} value={allergy.severity} onChange={e => setAllergy({ ...allergy, severity: e.target.value })}><option value="">Severity</option><option value="mild">Mild</option><option value="moderate">Moderate</option><option value="severe">Severe</option></select><button disabled={saving} onClick={() => save(() => addMyAllergy(allergy))} style={{ border: 0, background: "#0f766e", color: "#fff", borderRadius: 10, padding: 10, fontWeight: 800 }}>Save allergy</button></div>}</section>
        <section style={card}><h3 style={{ margin: 0, color: "#102a43" }}>Medications <span style={{ color: "#0f766e" }}>{profile.medications.length}</span></h3><p style={{ color: "#627d98", fontSize: "13px" }}>Add current or previous medicines you want your care team to know about.</p><button onClick={() => setSection(section === "medication" ? null : "medication")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "medication" ? "Close" : "Add medication"}</button>{section === "medication" && <div style={{ marginTop: 15, display: "grid", gap: 12 }}><input style={field} placeholder="Medication name" value={medication.medication_name} onChange={e => setMedication({ ...medication, medication_name: e.target.value })} /><FormRow><input style={field} placeholder="Dose" value={medication.dose} onChange={e => setMedication({ ...medication, dose: e.target.value })} /><input style={field} placeholder="Frequency" value={medication.frequency} onChange={e => setMedication({ ...medication, frequency: e.target.value })} /></FormRow><textarea style={{ ...field, minHeight: 75 }} placeholder="Notes" value={medication.notes} onChange={e => setMedication({ ...medication, notes: e.target.value })} /><button disabled={saving} onClick={() => save(() => addMyMedication({ medication_name: medication.medication_name, dose: medication.dose || undefined, frequency: medication.frequency || undefined, route: medication.route || undefined, start_date: medication.start_date || undefined, end_date: medication.end_date || undefined, status: medication.status || "active", prescribed_by: medication.prescribed_by || "Self-reported", notes: medication.notes || undefined }))} style={{ border: 0, background: "#0f766e", color: "#fff", borderRadius: 10, padding: 10, fontWeight: 800 }}>Save medication</button></div>}</section>
        <section style={card}><h3 style={{ margin: 0, color: "#102a43" }}>Lifestyle <span style={{ color: "#0f766e" }}>{profile.lifestyle.length}</span></h3><p style={{ color: "#627d98", fontSize: "13px" }}>Share lifestyle factors that may help your care team understand your health context.</p><button onClick={() => setSection(section === "lifestyle" ? null : "lifestyle")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "lifestyle" ? "Close" : "Add lifestyle"}</button>{section === "lifestyle" && <div style={{ marginTop: 15, display: "grid", gap: 12 }}><FormRow><input style={field} placeholder="Smoking status" value={lifestyle.smoking_status} onChange={e => setLifestyle({ ...lifestyle, smoking_status: e.target.value })} /><input style={field} placeholder="Alcohol use" value={lifestyle.alcohol_use} onChange={e => setLifestyle({ ...lifestyle, alcohol_use: e.target.value })} /></FormRow><FormRow><input style={field} placeholder="Physical activity" value={lifestyle.physical_activity_level} onChange={e => setLifestyle({ ...lifestyle, physical_activity_level: e.target.value })} /><input style={field} placeholder="Exercise frequency" value={lifestyle.exercise_frequency} onChange={e => setLifestyle({ ...lifestyle, exercise_frequency: e.target.value })} /></FormRow><input style={field} placeholder="Diet pattern" value={lifestyle.diet_pattern} onChange={e => setLifestyle({ ...lifestyle, diet_pattern: e.target.value })} /><button disabled={saving} onClick={() => save(() => addMyLifestyle({ ...lifestyle, sleep_duration_hours: lifestyle.sleep_duration_hours ? Number(lifestyle.sleep_duration_hours) : undefined }))} style={{ border: 0, background: "#0f766e", color: "#fff", borderRadius: 10, padding: 10, fontWeight: 800 }}>Save lifestyle</button></div>}</section>
        <section style={card}><h3 style={{ margin: 0, color: "#102a43" }}>Vital signs <span style={{ color: "#0f766e" }}>{profile.vital_signs.length}</span></h3><p style={{ color: "#627d98", fontSize: "13px" }}>Add current measurements so your care team has up-to-date information.</p><button onClick={() => setSection(section === "vitals" ? null : "vitals")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "vitals" ? "Close" : "Add vital signs"}</button>{section === "vitals" && <div style={{ marginTop: 15, display: "grid", gap: 12 }}><FormRow><input style={field} placeholder="Height" value={vitals.height} onChange={e => setVitals({ ...vitals, height: e.target.value })} /><input style={field} placeholder="Weight" value={vitals.weight} onChange={e => setVitals({ ...vitals, weight: e.target.value })} /></FormRow><FormRow><input style={field} placeholder="Systolic BP" value={vitals.blood_pressure_systolic} onChange={e => setVitals({ ...vitals, blood_pressure_systolic: e.target.value })} /><input style={field} placeholder="Diastolic BP" value={vitals.blood_pressure_diastolic} onChange={e => setVitals({ ...vitals, blood_pressure_diastolic: e.target.value })} /></FormRow><FormRow><input style={field} placeholder="Pulse" value={vitals.pulse} onChange={e => setVitals({ ...vitals, pulse: e.target.value })} /><input style={field} placeholder="Oxygen saturation" value={vitals.oxygen_saturation} onChange={e => setVitals({ ...vitals, oxygen_saturation: e.target.value })} /></FormRow><button disabled={saving} onClick={() => save(() => addMyVitalSigns({ height: vitals.height ? Number(vitals.height) : undefined, weight: vitals.weight ? Number(vitals.weight) : undefined, bmi: vitals.bmi ? Number(vitals.bmi) : undefined, blood_pressure_systolic: vitals.blood_pressure_systolic ? Number(vitals.blood_pressure_systolic) : undefined, blood_pressure_diastolic: vitals.blood_pressure_diastolic ? Number(vitals.blood_pressure_diastolic) : undefined, pulse: vitals.pulse ? Number(vitals.pulse) : undefined, temperature: vitals.temperature ? Number(vitals.temperature) : undefined, oxygen_saturation: vitals.oxygen_saturation ? Number(vitals.oxygen_saturation) : undefined }))} style={{ border: 0, background: "#0f766e", color: "#fff", borderRadius: 10, padding: 10, fontWeight: 800 }}>Save vital signs</button></div>}</section>
        <section style={card}><h3 style={{ margin: 0, color: "#102a43" }}>Contact & emergency information</h3><p style={{ color: "#627d98", fontSize: "13px" }}>{profile.contacts.length} contact record{profile.contacts.length === 1 ? "" : "s"} on file.</p><button onClick={() => setSection(section === "contact" ? null : "contact")} style={{ border: "1px solid #cfe0e6", background: "#fff", borderRadius: "10px", padding: "9px 12px", fontWeight: 750 }}>{section === "contact" ? "Close" : "Add / update contact"}</button>{section === "contact" && <div style={{ marginTop: 15, display: "grid", gap: 12 }}><FormRow><input style={field} placeholder="Phone" value={contact.phone} onChange={e => setContact({ ...contact, phone: e.target.value })} /><input style={field} placeholder="Email" value={contact.email} onChange={e => setContact({ ...contact, email: e.target.value })} /></FormRow><FormRow><input style={field} placeholder="Next of kin" value={contact.next_of_kin} onChange={e => setContact({ ...contact, next_of_kin: e.target.value })} /><input style={field} placeholder="Next of kin phone" value={contact.next_of_kin_phone} onChange={e => setContact({ ...contact, next_of_kin_phone: e.target.value })} /></FormRow><FormRow><input style={field} placeholder="Emergency contact" value={contact.emergency_contact} onChange={e => setContact({ ...contact, emergency_contact: e.target.value })} /><input style={field} placeholder="Emergency phone" value={contact.emergency_phone} onChange={e => setContact({ ...contact, emergency_phone: e.target.value })} /></FormRow><input style={field} placeholder="Relationship" value={contact.relationship} onChange={e => setContact({ ...contact, relationship: e.target.value })} /><button disabled={saving} onClick={() => { const fn = profile.contacts[0] ? async () => { const r = await import("./api/patientPortal"); return r.updateMyContact((profile.contacts[0] as any).id, contact); } : () => addMyContact(contact); save(fn); }} style={{ border: 0, background: "#0f766e", color: "#fff", borderRadius: 10, padding: 10, fontWeight: 800 }}>Save contact</button></div>}</section>
      </div>

      <section style={card}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ color: "#0f766e", fontSize: 11, fontWeight: 850, textTransform: "uppercase", letterSpacing: "0.08em" }}>Your care updates</div>
          <h2 style={{ margin: "3px 0 5px", color: "#102a43" }}>Clinician recommendations & health reports</h2>
          <p style={{ margin: 0, color: "#627d98", fontSize: 13 }}>Reports are shown here after clinician review. AI analysis is supporting information, while clinician guidance is clearly identified as authored by your care team.</p>
        </div>
        <div style={{ display: "grid", gap: 14 }}>
          <div>
            <h3 style={{ margin: "0 0 9px", color: "#102a43" }}>Clinician-approved recommendations</h3>
            {care?.recommendations.length ? <div style={{ display: "grid", gap: 10 }}>{care.recommendations.map(r => <div key={r.id} style={{ padding: 14, borderRadius: 13, background: "#f0fdfa", border: "1px solid #ccfbf1" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}><b style={{ color: "#102a43" }}>{r.title}</b><span style={{ padding: "5px 8px", borderRadius: 999, background: r.ai_generated ? "#eef2ff" : "#ecfdf5", color: r.ai_generated ? "#4338ca" : "#047857", fontSize: 10, fontWeight: 850 }}>{r.ai_generated ? "AI-assisted" : "Care team"}</span></div>
              <p style={{ margin: "7px 0 0", color: "#334e68", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{r.recommendation_text}</p>
              {r.source_type && <div style={{ marginTop: 7, color: "#64748b", fontSize: 10 }}>Source: {r.source_type.replace(/_/g, " ")}</div>}
            </div>)}</div> : <div style={{ padding: 16, borderRadius: 13, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>No clinician-approved recommendations are available yet.</div>}
          </div>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}><h3 style={{ margin: 0, color: "#102a43" }}>Periodic health reports</h3><span style={{ color: "#64748b", fontSize: 11 }}>{care?.reports.length || 0} available</span></div>
            {care?.reports.length ? <div style={{ display: "grid", gap: 12, marginTop: 10 }}>{care.reports.map(report => {
              const reviewed = Boolean(report.patient_reviewed_at);
              return <article key={report.id} style={{ padding: 16, borderRadius: 15, border: "1px solid #dfeaec", background: "linear-gradient(145deg,#ffffff,#f8fcfc)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
                  <div><div style={{ display: "flex", gap: 7, alignItems: "center", flexWrap: "wrap" }}><strong style={{ color: "#102a43", fontSize: 15 }}>{report.report_title}</strong><span style={{ padding: "5px 8px", borderRadius: 999, background: "#ecfdf5", color: "#047857", fontSize: 10, fontWeight: 850 }}>{report.status === "completed" ? "Released" : "Approved"}</span></div><div style={{ marginTop: 5, color: "#64748b", fontSize: 11 }}>Assessment {report.assessment_id} · {new Date(report.generated_at).toLocaleString()} · Version {report.version}</div></div>
                  <span style={{ color: "#64748b", fontSize: 10 }}>{report.ai_generated ? "AI-assisted report" : "Clinical report"}</span>
                </div>
                <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                  {report.executive_summary && <div style={{ padding: 12, borderRadius: 12, background: "#f0fdfa", color: "#334e68", fontSize: 12, lineHeight: 1.55 }}><strong style={{ color: "#102a43" }}>Health analysis summary</strong><div style={{ marginTop: 5, whiteSpace: "pre-wrap" }}>{report.executive_summary}</div></div>}
                  {report.recommendations_summary && <div style={{ padding: 12, borderRadius: 12, background: "#f8fafc", color: "#334e68", fontSize: 12, lineHeight: 1.55 }}><strong style={{ color: "#102a43" }}>AI / report recommendations</strong><div style={{ marginTop: 5, whiteSpace: "pre-wrap" }}>{report.recommendations_summary}</div></div>}
                  {report.clinician_guidance && <div style={{ padding: 13, borderRadius: 12, background: "linear-gradient(135deg,#fff7ed,#fffbeb)", border: "1px solid #fed7aa", color: "#7c2d12", fontSize: 12, lineHeight: 1.55 }}><div style={{ fontWeight: 850, color: "#9a3412" }}>Your clinician's additional guidance</div><div style={{ marginTop: 5, whiteSpace: "pre-wrap" }}>{report.clinician_guidance}</div></div>}
                  <details><summary style={{ cursor: "pointer", color: "#0f766e", fontSize: 12, fontWeight: 800 }}>View full health analysis report</summary><pre style={{ margin: "9px 0 0", padding: 12, borderRadius: 11, background: "#0f172a", color: "#e2e8f0", overflowX: "auto", fontSize: 10, lineHeight: 1.55, whiteSpace: "pre-wrap" }}>{stringifyReportContent(report.report_content)}</pre></details>
                  {report.limitations && <div style={{ color: "#7b8da1", fontSize: 10, lineHeight: 1.45 }}>Report note: {report.limitations}</div>}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap", marginTop: 13, paddingTop: 11, borderTop: "1px solid #e6eef2" }}>
                  <div style={{ color: "#64748b", fontSize: 10 }}>{reviewed ? `Reviewed ${new Date(report.patient_reviewed_at as string).toLocaleString()}` : "Not yet marked as reviewed"}</div>
                  <button type="button" disabled={reviewed || reviewingReportId === report.id} onClick={() => void handleReportReviewed(report.id)} style={{ border: 0, borderRadius: 10, padding: "9px 12px", background: reviewed ? "#e2e8f0" : "linear-gradient(135deg,#0f766e,#0ea5a4)", color: reviewed ? "#64748b" : "#fff", fontWeight: 850, cursor: reviewed ? "default" : "pointer" }}>{reviewingReportId === report.id ? "Saving..." : reviewed ? "Reviewed" : "Mark as reviewed"}</button>
                </div>
              </article>;
            })}</div> : <div style={{ marginTop: 10, padding: 16, borderRadius: 13, background: "#f8fafc", color: "#64748b", fontSize: 13 }}>No released health reports are available yet. Your care team will publish them here after review.</div>}
          </div>
        </div>
      </section>
    </div>
  );
}
