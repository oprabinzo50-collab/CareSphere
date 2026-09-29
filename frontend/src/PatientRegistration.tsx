import React, { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { registerPatient } from "./api/patientPortal";
import { useAuth } from "./auth/AuthContext";

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "12px 13px",
  borderRadius: "11px",
  border: "1px solid #cbd5e1",
  boxSizing: "border-box",
  outline: "none",
  color: "#102a43",
  background: "#fff",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  marginBottom: "7px",
  fontSize: "12px",
  fontWeight: 750,
  color: "#334e68",
};

export default function PatientRegistration() {
  const navigate = useNavigate();
  const { loginUser } = useAuth();
  const [form, setForm] = useState({
    username: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
    date_of_birth: "",
    sex: "",
    marital_status: "",
    occupation: "",
    preferred_language: "",
    residence: "",
    district: "",
    country: "Uganda",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const update = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setSaving(true);
    try {
      const result = await registerPatient({
        username: form.username.trim(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        date_of_birth: form.date_of_birth || undefined,
        sex: form.sex || undefined,
        marital_status: form.marital_status || undefined,
        occupation: form.occupation.trim() || undefined,
        preferred_language: form.preferred_language.trim() || undefined,
        residence: form.residence.trim() || undefined,
        district: form.district.trim() || undefined,
        country: form.country.trim() || undefined,
      });
      loginUser(result.access_token, result.user);
      navigate("/patient-portal", { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to create your account.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", padding: "32px 18px", background: "radial-gradient(circle at 10% 0%, rgba(29,185,177,0.12), transparent 32%), #f4f8fb" }}>
      <div style={{ width: "min(760px, 100%)", margin: "0 auto", background: "rgba(255,255,255,0.96)", borderRadius: "24px", padding: "34px", boxShadow: "0 28px 70px rgba(16,42,67,0.12)", border: "1px solid #e6eef2" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "20px", flexWrap: "wrap", marginBottom: "26px" }}>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "#0f766e", letterSpacing: "0.11em", textTransform: "uppercase" }}>CareSphere Patient Portal</div>
            <h1 style={{ margin: "8px 0 6px", color: "#102a43", fontSize: "30px" }}>Create your account</h1>
            <p style={{ margin: 0, color: "#627d98" }}>Create your own secure patient record. You can complete the rest of your health information after signing in.</p>
          </div>
          <button type="button" onClick={() => navigate("/login")} style={{ border: "1px solid #d8e5ea", background: "#fff", borderRadius: "11px", padding: "10px 13px", color: "#334e68", fontWeight: 700 }}>Back to sign in</button>
        </div>

        <form onSubmit={submit}>
          <section style={{ marginBottom: "26px" }}>
            <h2 style={{ fontSize: "17px", color: "#102a43", marginBottom: "16px" }}>Account</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "16px" }}>
              <div><label style={labelStyle}>Username</label><input style={inputStyle} autoComplete="username" value={form.username} onChange={(e) => update("username", e.target.value)} required /></div>
              <div><label style={labelStyle}>Password</label><input style={inputStyle} type="password" autoComplete="new-password" value={form.password} onChange={(e) => update("password", e.target.value)} minLength={8} required /></div>
              <div><label style={labelStyle}>Confirm password</label><input style={inputStyle} type="password" autoComplete="new-password" value={form.confirmPassword} onChange={(e) => update("confirmPassword", e.target.value)} minLength={8} required /></div>
            </div>
          </section>

          <section style={{ marginBottom: "26px" }}>
            <h2 style={{ fontSize: "17px", color: "#102a43", marginBottom: "16px" }}>Personal information</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "16px" }}>
              <div><label style={labelStyle}>First name</label><input style={inputStyle} value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required /></div>
              <div><label style={labelStyle}>Last name</label><input style={inputStyle} value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required /></div>
              <div><label style={labelStyle}>Date of birth</label><input style={inputStyle} type="date" value={form.date_of_birth} onChange={(e) => update("date_of_birth", e.target.value)} /></div>
              <div><label style={labelStyle}>Sex</label><select style={inputStyle} value={form.sex} onChange={(e) => update("sex", e.target.value)}><option value="">Select</option><option value="female">Female</option><option value="male">Male</option><option value="prefer_not_to_say">Prefer not to say</option></select></div>
              <div><label style={labelStyle}>Marital status</label><select style={inputStyle} value={form.marital_status} onChange={(e) => update("marital_status", e.target.value)}><option value="">Select</option><option value="single">Single</option><option value="married">Married</option><option value="divorced">Divorced</option><option value="widowed">Widowed</option></select></div>
              <div><label style={labelStyle}>Occupation</label><input style={inputStyle} value={form.occupation} onChange={(e) => update("occupation", e.target.value)} /></div>
              <div><label style={labelStyle}>Preferred language</label><input style={inputStyle} value={form.preferred_language} onChange={(e) => update("preferred_language", e.target.value)} placeholder="e.g. English" /></div>
              <div><label style={labelStyle}>District</label><input style={inputStyle} value={form.district} onChange={(e) => update("district", e.target.value)} /></div>
              <div style={{ gridColumn: "1 / -1" }}><label style={labelStyle}>Residence</label><textarea style={{ ...inputStyle, minHeight: "90px", resize: "vertical" }} value={form.residence} onChange={(e) => update("residence", e.target.value)} /></div>
            </div>
          </section>

          {error && <div style={{ padding: "11px 13px", borderRadius: "11px", background: "#fff1f2", color: "#be123c", border: "1px solid #fecdd3", marginBottom: "16px", fontSize: "13px", fontWeight: 650 }}>{error}</div>}

          <button type="submit" disabled={saving} style={{ width: "100%", border: 0, borderRadius: "12px", padding: "13px 16px", background: "linear-gradient(135deg, #0f766e, #0b8f86)", color: "#fff", fontWeight: 800, cursor: saving ? "wait" : "pointer" }}>
            {saving ? "Creating your secure account..." : "Create patient account"}
          </button>
        </form>
      </div>
    </div>
  );
}
