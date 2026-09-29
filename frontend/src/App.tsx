import { AuthProvider, useAuth } from "./auth/AuthContext";
import React, {
  useEffect,
  useState,
} from "react";
import PatientRegistration from "./PatientRegistration";
import PatientPortalPage from "./PatientPortal";
import ClinicalWorkspace from "./ClinicalWorkspace";
import ReportsWorkspace from "./ReportsWorkspace";
import type { FormEvent } from "react"
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  useNavigate
} from "react-router-dom";

import {
  searchPatients,
  createPatient,
  getPatientProfile,
  type Patient,
  type PatientCreateRequest,
  type PatientProfile,
} from "./api/patients";
import { login } from "./api/auth";
import {
  getDashboardSummary,
  type DashboardSummary,
} from "./api/dashboard";
import {
  createUser,
  listUsers,
  updateUser,
  updateUserStatus,
  type CareUser,
  type UserRole,
  type UserStatus,
} from "./api/users";
import Icon from "./components/ui/Icon";
import PatientAvatar from "./components/PatientAvatar";
import MetricCard from "./components/ui/MetricCard";
import WorkflowWorkspaceFrame from "./WorkflowWorkspaceFrame";
import TaskCenter from "./TaskCenter";
import { AuditLogsPage, CareGapsPage, FollowUpsPage, NotificationsPage } from "./components/workflow/WorkflowPages";
function Login() {
  const navigate = useNavigate();
  const { user, loading: authLoading, loginUser } = useAuth();

  const [selectedRole, setSelectedRole] = useState<"clinician" | "administrator" | "patient">("clinician");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const roleHome =
    selectedRole === "administrator"
      ? "/admin"
      : selectedRole === "patient"
        ? "/patient-portal"
        : "/";

  const authenticatedHome =
    user?.role === "administrator"
      ? "/admin"
      : user?.role === "patient"
        ? "/patient-portal"
        : "/";

  if (authLoading) {
    return (
      <div style={styles.loginPage}>
        <div style={styles.loginCard}>
          <h1 style={styles.loginLogo}>CareSphere</h1>
          <p style={styles.loginSubtitle}>Checking your secure session...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to={authenticatedHome} replace />;
  }

  const roles = [
    {
      key: "clinician" as const,
      title: "Clinician",
      description: "Patients, assessments, clinical records and care coordination",
      icon: "activity" as const,
    },
    {
      key: "administrator" as const,
      title: "Administrator",
      description: "Users, permissions, system oversight and audit functions",
      icon: "shield" as const,
    },
    {
      key: "patient" as const,
      title: "Patient",
      description: "Your personal health information, assessments and reports",
      icon: "heartPulse" as const,
    },
  ];

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await login({
        username: username.trim(),
        password,
        login_role: selectedRole,
      });

      loginUser(result.access_token, result.user);
      navigate(roleHome, { replace: true });
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Unable to sign in. Please check your credentials.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.loginPage}>
      <div style={styles.loginCard}>
        <div style={styles.loginBrandRow}>
          <div>
            <h1 style={styles.loginLogo}>CareSphere</h1>
            <p style={styles.loginSubtitle}>
              Secure healthcare intelligence and care coordination
            </p>
          </div>
          <span style={styles.loginSecureBadge}>Secure access</span>
        </div>

        <div style={styles.roleGrid}>
          {roles.map((role) => {
            const active = selectedRole === role.key;
            return (
              <button
                key={role.key}
                type="button"
                onClick={() => {
                  setSelectedRole(role.key);
                  setError("");
                }}
                style={{
                  ...styles.roleCard,
                  ...(active ? styles.roleCardActive : {}),
                }}
              >
                <span style={styles.roleIcon}><Icon name={role.icon} size={18} /></span>
                <span style={styles.roleTitle}>{role.title}</span>
                <span style={styles.roleDescription}>{role.description}</span>
              </button>
            );
          })}
        </div>

        <div style={styles.loginSelectedRole}>
          Signing in as <strong>{roles.find((role) => role.key === selectedRole)?.title}</strong>
        </div>

        {selectedRole === "patient" && (
          <div style={{ margin: "0 0 16px", padding: "11px 12px", borderRadius: "11px", background: "#f0fdfa", border: "1px solid #ccfbf1", color: "#0f766e", fontSize: "12px" }}>
            New patient? <button type="button" onClick={() => navigate("/register/patient")} style={{ border: 0, background: "transparent", color: "#0f766e", fontWeight: 850, cursor: "pointer", padding: 0 }}>Create your account</button>
          </div>
        )}

        <form onSubmit={handleLogin}>
          <label style={styles.label}>Username</label>
          <input
            style={styles.input}
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter username"
            autoComplete="username"
            required
          />

          <label style={styles.label}>Password</label>
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter password"
            autoComplete="current-password"
            required
          />

          {error && <div style={styles.error}>{error}</div>}

          <button
            type="submit"
            style={styles.loginButton}
            disabled={loading}
          >
            {loading ? "Signing in..." : `Sign in as ${roles.find((role) => role.key === selectedRole)?.title}`}
          </button>
        </form>
      </div>
    </div>
  );
}
function CareSphere3DMark() {
  return (
    <div className="care-3d-logo-wrap" aria-label="CareSphere animated mark" role="img">
      <div className="care-3d-logo-orbit care-3d-orbit-a" />
      <div className="care-3d-logo-orbit care-3d-orbit-b" />
      <div className="care-3d-logo-core"><span>CS</span></div>
      <div className="care-3d-logo-caption">CareSphere</div>
    </div>
  );
}

function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] =
    useState<DashboardSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then((data) => {
        setSummary(data);
      })
      .catch((err: any) => {
        console.error(err);

        setError(
          err?.response?.data?.detail ||
            "Unable to load dashboard data.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <p style={styles.muted}>
        Loading dashboard...
      </p>
    );
  }

  if (error) {
    return (
      <p style={styles.error}>
        {error}
      </p>
    );
  }

  if (!summary) {
    return (
      <p style={styles.muted}>
        No dashboard data available.
      </p>
    );
  }

  const quickLinks = user?.role === "administrator"
    ? [
        { label: "Review patients", detail: "Search and open patient records", path: "/patients", icon: "patient" as const },
        { label: "Manage users", detail: "Accounts, roles and access", path: "/users", icon: "users" as const },
        { label: "Open reports", detail: "Review generated clinical reports", path: "/reports", icon: "file" as const },
      ]
    : [
        { label: "Review patients", detail: "Open a patient for clinical review", path: "/patients", icon: "patient" as const },
        { label: "Clinical workspace", detail: "Assessments, risk and recommendations", path: "/clinical-workspace", icon: "activity" as const },
        { label: "Open reports", detail: "Review generated clinical reports", path: "/reports", icon: "file" as const },
      ];

  const assessmentCompletionRate = summary.assessments.total
    ? Math.round((summary.assessments.completed / summary.assessments.total) * 100)
    : 0;
  const patientActivationRate = summary.patients.total
    ? Math.round((summary.patients.active / summary.patients.total) * 100)
    : 0;
  const reviewClearanceRate = summary.clinician_reviews.total
    ? Math.round((summary.clinician_reviews.approved / summary.clinician_reviews.total) * 100)
    : 0;

  return (
    <div className="care-dashboard-page">
      <section className="care-dashboard-hero">
        <div>
          <div className="care-section-kicker">{user?.role === "administrator" ? "System overview" : "Clinical overview"}</div>
          <h1 className="care-dashboard-title">Welcome back, {user?.full_name || "Care team"}</h1>
          <p className="care-dashboard-subtitle">Patient care intelligence, operational visibility and review activity in one workspace.</p>
        </div>
        <div className="care-dashboard-hero-visual">
          <CareSphere3DMark />
          <div className="care-dashboard-hero-badge">
          <span className="care-dashboard-hero-dot" />
          Workspace active
          </div>
        </div>
      </section>

      <section className="care-dashboard-metrics">
        <MetricCard label="Patients" value={summary.patients.total} icon="patient" helper={`${summary.patients.active} active`} />
        <MetricCard label="Active Patients" value={summary.patients.active} icon="activity" tone="blue" helper={`${summary.patients.inactive} inactive`} />
        <MetricCard label="Health Concerns" value={summary.health_concerns} icon="heartPulse" tone="rose" helper="Across current records" />
        <MetricCard label="Care Recommendations" value={summary.recommendations} icon="sparkles" tone="amber" helper={`${summary.clinician_reviews.pending} awaiting review`} />
      </section>

      <section className="care-dashboard-quick-grid" aria-label="Quick access">
        {quickLinks.map((item, index) => (
          <NavLink key={item.path} to={item.path} className="care-quick-card" style={{ animationDelay: `${index * 70}ms` }}>
            <span className="care-quick-icon"><Icon name={item.icon} size={18} /></span>
            <span className="care-quick-copy">
              <strong>{item.label}</strong>
              <span>{item.detail}</span>
            </span>
            <Icon name="chevronRight" size={16} className="care-quick-arrow" />
          </NavLink>
        ))}
      </section>

      <section className="care-profile-card care-dashboard-summary" style={styles.panel}>
        <div>
          <div className="care-section-kicker">Patient intelligence</div>
          <h2 style={{ margin: "5px 0 0", color: "#102a43" }}>At a glance</h2>
          <p style={{ ...styles.muted, marginTop: "7px" }}>
            {summary.assessments.total} assessments, {summary.reports} reports, and {summary.clinician_reviews.pending} pending clinician reviews.
          </p>
        </div>
        <div className="care-dashboard-summary-pills">
          <span><strong>{summary.assessments.total}</strong> assessments</span>
          <span><strong>{summary.reports}</strong> reports</span>
          <span><strong>{summary.clinician_reviews.pending}</strong> pending reviews</span>
        </div>
      </section>


      <section className="care-analytics-card" style={styles.panel}>
        <div className="care-analytics-heading">
          <div>
            <div className="care-section-kicker">System analytics</div>
            <h2 style={{ margin: "5px 0 0", color: "#102a43" }}>Operational health</h2>
          </div>
          <span className="care-analytics-note">Derived from existing dashboard data</span>
        </div>
        <div className="care-analytics-grid">
          {[
            { label: "Assessment completion", value: assessmentCompletionRate, detail: `${summary.assessments.completed} of ${summary.assessments.total} completed` },
            { label: "Active patient ratio", value: patientActivationRate, detail: `${summary.patients.active} of ${summary.patients.total} active` },
            { label: "Review clearance", value: reviewClearanceRate, detail: `${summary.clinician_reviews.approved} approved of ${summary.clinician_reviews.total}` },
          ].map((metric, index) => (
            <div key={metric.label} className="care-analytics-metric" style={{ animationDelay: `${index * 70}ms` }}>
              <div className="care-analytics-metric-top"><span>{metric.label}</span><strong>{metric.value}%</strong></div>
              <div className="care-analytics-track"><span style={{ width: `${metric.value}%` }} /></div>
              <small>{metric.detail}</small>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
function Patients() {
  const [search, setSearch] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showAddPatient, setShowAddPatient] = useState(false);
  const [savingPatient, setSavingPatient] = useState(false);

  const [selectedPatientId, setSelectedPatientId] =
    useState<number | null>(null);
  const [profile, setProfile] =
    useState<PatientProfile | null>(null);
  const [profileLoading, setProfileLoading] =
    useState(false);

  const [form, setForm] =
    useState<PatientCreateRequest>({
      first_name: "",
      last_name: "",
      date_of_birth: "",
      sex: "",
      marital_status: "",
      occupation: "",
      preferred_language: "",
      residence: "",
      district: "",
      country: "",
    });

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const results = await searchPatients({
        search: search.trim() || undefined,
        limit: 50,
        offset: 0,
      });

      setPatients(results);
    } catch (err: any) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load patients.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (
    field: keyof PatientCreateRequest,
    value: string,
  ) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleCreatePatient = async (
    event: FormEvent,
  ) => {
    event.preventDefault();

    setSavingPatient(true);
    setError("");
    setSuccess("");

    try {
      const patientData: PatientCreateRequest = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        date_of_birth:
          form.date_of_birth || undefined,
        sex: form.sex || undefined,
        marital_status:
          form.marital_status || undefined,
        occupation:
          form.occupation?.trim() || undefined,
        preferred_language:
          form.preferred_language?.trim() || undefined,
        residence:
          form.residence?.trim() || undefined,
        district:
          form.district?.trim() || undefined,
        country:
          form.country?.trim() || undefined,
      };

      const createdPatient =
        await createPatient(patientData);

      setSuccess(
        `Patient ${createdPatient.patient_number} was created successfully.`,
      );

      setForm({
        first_name: "",
        last_name: "",
        date_of_birth: "",
        sex: "",
        marital_status: "",
        occupation: "",
        preferred_language: "",
        residence: "",
        district: "",
        country: "",
      });

      setShowAddPatient(false);

      const refreshedPatients =
        await searchPatients({
          search: "",
          limit: 50,
          offset: 0,
        });

      setPatients(refreshedPatients);
    } catch (err: any) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Unable to create patient.",
      );
    } finally {
      setSavingPatient(false);
    }
  };

  const handleViewProfile = async (
    patientId: number,
  ) => {
    setProfileLoading(true);
    setError("");
    setSuccess("");

    try {
      const data =
        await getPatientProfile(patientId);

      setProfile(data);
      setSelectedPatientId(patientId);
    } catch (err: any) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load patient profile.",
      );
    } finally {
      setProfileLoading(false);
    }
  };

  const handleBackToPatients = () => {
    setSelectedPatientId(null);
    setProfile(null);
    setError("");
  };

  if (selectedPatientId && profile) {
    const patient = profile.patient;

    const locationLabel = [patient.district, patient.country]
      .filter(Boolean)
      .join(", ") || "Location not provided";
    const statusIsActive = patient.status === "active";

    return (
      <>
        <CareSpherePatientProfileStyles />

        <div className="care-profile-page">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "18px",
              gap: "16px",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: 800,
                  color: "#0f766e",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  marginBottom: "5px",
                }}
              >
                Patients / Record
              </div>
              <h1 style={{ ...styles.title, marginBottom: "4px" }}>
                Patient Profile
              </h1>
              <p style={styles.subtitle}>
                Complete patient information and care-record overview
              </p>
            </div>

            <button
              type="button"
              onClick={handleBackToPatients}
              style={{
                ...styles.searchButton,
                background: "#ffffff",
                color: "#334155",
                border: "1px solid #dbe4ea",
                boxShadow: "0 7px 18px rgba(15, 23, 42, 0.06)",
              }}
            >
              ← Back to Patients
            </button>
          </div>

          <section
            className="care-profile-hero"
            style={{
              ...styles.panel,
              marginBottom: "22px",
              padding: "26px",
              background:
                "linear-gradient(135deg, #effcfb 0%, #ffffff 58%, #eff8ff 100%)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "22px",
                flexWrap: "wrap",
                position: "relative",
                zIndex: 1,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "18px",
                  minWidth: 0,
                }}
              >
                <div className="care-profile-avatar-shell">
                  <PatientAvatar patientId={patient.id} firstName={patient.first_name} lastName={patient.last_name} size={84} radius={24} label={`Photo of ${patient.first_name} ${patient.last_name}`} />
                </div>

                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: 800,
                      color: "#0f766e",
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      marginBottom: "5px",
                    }}
                  >
                    Patient
                  </div>

                  <h2
                    style={{
                      margin: 0,
                      fontSize: "clamp(24px, 4vw, 32px)",
                      color: "#102a43",
                      letterSpacing: "-0.025em",
                    }}
                  >
                    {patient.first_name} {patient.last_name}
                  </h2>

                  <div className="care-profile-meta">
                    <span className="care-profile-chip">
                      <span aria-hidden="true">#</span>
                      {patient.patient_number}
                    </span>
                    <span className="care-profile-chip">
                      <span aria-hidden="true">⌖</span>
                      {locationLabel}
                    </span>
                    {patient.preferred_language && (
                      <span className="care-profile-chip">
                        <span aria-hidden="true">◉</span>
                        {patient.preferred_language}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="care-profile-hero-actions">
                <div
                  className="care-profile-status"
                  style={{
                    background: statusIsActive ? "#ecfdf5" : "#f8fafc",
                    color: statusIsActive ? "#047857" : "#64748b",
                    border: statusIsActive
                      ? "1px solid #bbf7d0"
                      : "1px solid #e2e8f0",
                  }}
                >
                  <span className="care-profile-status-dot" />
                  {patient.status || "Unknown"}
                </div>
              </div>
            </div>
          </section>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "20px",
            }}
          >
          <section className="care-profile-card" style={styles.panel}>
            <div style={profileSectionHeaderStyle}>
              <div style={profileIconStyle}>
                👤
              </div>

              <div>
                <h2 style={profileHeadingStyle}>
                  Personal Information
                </h2>

                <p style={profileDescriptionStyle}>
                  Basic patient identity and demographic
                  information
                </p>
              </div>
            </div>

            <div style={profileGridStyle}>
              <ProfileField
                label="First Name"
                value={patient.first_name}
              />

              <ProfileField
                label="Last Name"
                value={patient.last_name}
              />

              <ProfileField
                label="Date of Birth"
                value={
                  patient.date_of_birth || "Not provided"
                }
              />

              <ProfileField
                label="Sex"
                value={
                  patient.sex
                    ? patient.sex.replace(
                        /_/g,
                        " ",
                      )
                    : "Not provided"
                }
              />

              <ProfileField
                label="Marital Status"
                value={
                  patient.marital_status
                    ? patient.marital_status.replace(
                        /_/g,
                        " ",
                      )
                    : "Not provided"
                }
              />

              <ProfileField
                label="Occupation"
                value={
                  patient.occupation || "Not provided"
                }
              />
            </div>
          </section>

          <section style={styles.panel}>
            <div style={profileSectionHeaderStyle}>
              <div style={profileIconStyle}>
                🌍
              </div>

              <div>
                <h2 style={profileHeadingStyle}>
                  Location & Communication
                </h2>

                <p style={profileDescriptionStyle}>
                  Residence, district, country and
                  language information
                </p>
              </div>
            </div>

            <div style={profileGridStyle}>
              <ProfileField
                label="Residence"
                value={
                  patient.residence || "Not provided"
                }
              />

              <ProfileField
                label="District"
                value={
                  patient.district || "Not provided"
                }
              />

              <ProfileField
                label="Country"
                value={
                  patient.country || "Not provided"
                }
              />

              <ProfileField
                label="Preferred Language"
                value={
                  patient.preferred_language ||
                  "Not provided"
                }
              />
            </div>
          </section>

          <section
            className="care-profile-card"
            style={{
              ...styles.panel,
              gridColumn: "1 / -1",
            }}
          >
            <div style={profileSectionHeaderStyle}>
              <div style={profileIconStyle}>
                🏥
              </div>

              <div>
                <h2 style={profileHeadingStyle}>
                  Clinical Record
                </h2>

                <p style={profileDescriptionStyle}>
                  Clinical information will appear here
                  as the patient's care record is built.
                </p>
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "12px",
              }}
            >
              <ProfileSummaryCard
                title="Contacts"
                value={profile.contacts.length}
                icon="☎"
              />

              <ProfileSummaryCard
                title="Medical History"
                value={profile.medical_history.length}
                icon="⌁"
              />

              <ProfileSummaryCard
                title="Allergies"
                value={profile.allergies.length}
                icon="!"
              />

              <ProfileSummaryCard
                title="Medications"
                value={profile.medications.length}
                icon="+"
              />

              <ProfileSummaryCard
                title="Vital Signs"
                value={profile.vital_signs.length}
                icon="♥"
              />

              <ProfileSummaryCard
                title="Assessments"
                value={profile.assessments.length}
                icon="✓"
              />
            </div>
          </section>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <h1 style={styles.title}>Patients</h1>

      <p style={styles.subtitle}>
        Search, register and access patient records
      </p>

      <section style={styles.panel}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "24px",
            gap: "16px",
            flexWrap: "wrap",
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                color: "#102a43",
              }}
            >
              Patient Records
            </h2>

            <p
              style={{
                margin: "6px 0 0",
                color: "#627d98",
                fontSize: "14px",
              }}
            >
              Register a new patient or find an existing
              record.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              setShowAddPatient(
                (current) => !current,
              );
              setError("");
              setSuccess("");
            }}
            style={{
              ...styles.searchButton,
              padding: "11px 18px",
              fontWeight: 700,
            }}
          >
            {showAddPatient
              ? "Cancel"
              : "+ Add Patient"}
          </button>
        </div>

        {showAddPatient && (
          <form
            onSubmit={handleCreatePatient}
            style={{
              marginBottom: "28px",
              padding: "24px",
              borderRadius: "16px",
              border: "1px solid rgba(148,163,184,0.18)",
              background: "#f7fafb",
            }}
          >
            <div style={formSectionTitleStyle}>
              <div>
                <h3 style={formSectionHeadingStyle}>
                  Personal Information
                </h3>

                <p style={formSectionDescriptionStyle}>
                  Enter the patient's basic identity and
                  demographic information.
                </p>
              </div>
            </div>

            <div style={formGridStyle}>
              <FormField
                label="First Name"
                required
              >
                <input
                  type="text"
                  required
                  value={form.first_name}
                  onChange={(event) =>
                    handleFormChange(
                      "first_name",
                      event.target.value,
                    )
                  }
                  placeholder="Enter first name"
                  style={formInputStyle}
                />
              </FormField>

              <FormField
                label="Last Name"
                required
              >
                <input
                  type="text"
                  required
                  value={form.last_name}
                  onChange={(event) =>
                    handleFormChange(
                      "last_name",
                      event.target.value,
                    )
                  }
                  placeholder="Enter last name"
                  style={formInputStyle}
                />
              </FormField>

              <FormField label="Date of Birth">
                <input
                  type="date"
                  value={form.date_of_birth}
                  onChange={(event) =>
                    handleFormChange(
                      "date_of_birth",
                      event.target.value,
                    )
                  }
                  style={formInputStyle}
                />
              </FormField>

              <FormField label="Sex">
                <select
                  value={form.sex}
                  onChange={(event) =>
                    handleFormChange(
                      "sex",
                      event.target.value,
                    )
                  }
                  style={formInputStyle}
                >
                  <option value="">
                    Select sex
                  </option>
                  <option value="female">
                    Female
                  </option>
                  <option value="male">
                    Male
                  </option>
                  <option value="other">
                    Other
                  </option>
                  <option value="prefer_not_to_say">
                    Prefer not to say
                  </option>
                </select>
              </FormField>

              <FormField label="Marital Status">
                <select
                  value={form.marital_status}
                  onChange={(event) =>
                    handleFormChange(
                      "marital_status",
                      event.target.value,
                    )
                  }
                  style={formInputStyle}
                >
                  <option value="">
                    Select marital status
                  </option>
                  <option value="single">
                    Single
                  </option>
                  <option value="married">
                    Married
                  </option>
                  <option value="divorced">
                    Divorced
                  </option>
                  <option value="widowed">
                    Widowed
                  </option>
                  <option value="separated">
                    Separated
                  </option>
                </select>
              </FormField>

              <FormField label="Occupation">
                <input
                  type="text"
                  value={form.occupation}
                  onChange={(event) =>
                    handleFormChange(
                      "occupation",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Teacher, Farmer, Nurse"
                  style={formInputStyle}
                />
              </FormField>
            </div>

            <div style={formDividerStyle} />

            <div style={formSectionTitleStyle}>
              <div>
                <h3 style={formSectionHeadingStyle}>
                  Location & Communication
                </h3>

                <p style={formSectionDescriptionStyle}>
                  Add information that helps clinicians
                  communicate with and locate the patient.
                </p>
              </div>
            </div>

            <div style={formGridStyle}>
              <FormField label="Preferred Language">
                <input
                  type="text"
                  value={form.preferred_language}
                  onChange={(event) =>
                    handleFormChange(
                      "preferred_language",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. English, Luganda"
                  style={formInputStyle}
                />
              </FormField>

              <FormField label="District">
                <input
                  type="text"
                  value={form.district}
                  onChange={(event) =>
                    handleFormChange(
                      "district",
                      event.target.value,
                    )
                  }
                  placeholder="Enter district"
                  style={formInputStyle}
                />
              </FormField>

              <FormField label="Country">
                <input
                  type="text"
                  value={form.country}
                  onChange={(event) =>
                    handleFormChange(
                      "country",
                      event.target.value,
                    )
                  }
                  placeholder="Enter country"
                  style={formInputStyle}
                />
              </FormField>

              <FormField
                label="Residence"
                fullWidth
              >
                <input
                  type="text"
                  value={form.residence}
                  onChange={(event) =>
                    handleFormChange(
                      "residence",
                      event.target.value,
                    )
                  }
                  placeholder="Village, town, street or other residence details"
                  style={formInputStyle}
                />
              </FormField>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "12px",
                marginTop: "28px",
                paddingTop: "20px",
                borderTop:
                  "1px solid #e2e8f0",
              }}
            >
              <button
                type="button"
                onClick={() =>
                  setShowAddPatient(false)
                }
                disabled={savingPatient}
                style={{
                  padding: "11px 18px",
                  borderRadius: "10px",
                  border:
                    "1px solid #cbd5e1",
                  background: "#ffffff",
                  color: "#334155",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={savingPatient}
                style={{
                  ...styles.searchButton,
                  minWidth: "150px",
                  fontWeight: 700,
                }}
              >
                {savingPatient
                  ? "Saving..."
                  : "Save Patient"}
              </button>
            </div>
          </form>
        )}

        {success && (
          <div
            style={{
              marginBottom: "18px",
              padding: "12px 16px",
              borderRadius: "10px",
              background: "#ecfdf5",
              border: "1px solid #a7f3d0",
              color: "#166534",
              fontSize: "14px",
              fontWeight: 600,
            }}
          >
            ✓ {success}
          </div>
        )}

        <form
          onSubmit={handleSearch}
          style={{
            ...styles.searchForm,
            marginBottom: "20px",
          }}
        >
          <input
            type="text"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search by patient name or number..."
            style={styles.searchInput}
          />

          <button
            type="submit"
            style={styles.searchButton}
            disabled={loading}
          >
            {loading
              ? "Searching..."
              : "Search"}
          </button>
        </form>

        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}

        {profileLoading && (
          <div
            style={{
              padding: "20px",
              textAlign: "center",
              color: "#627d98",
            }}
          >
            Loading patient profile...
          </div>
        )}

        {!loading &&
          patients.length === 0 &&
          !error && (
            <div
              style={{
                padding: "36px 20px",
                textAlign: "center",
                border:
                  "1px dashed #cbd5e1",
                borderRadius: "12px",
                background: "#f7fafb",
              }}
            >
              <div
                style={{
                  fontSize: "28px",
                  marginBottom: "8px",
                }}
              >
                🔎
              </div>

              <p
                style={{
                  margin: 0,
                  fontWeight: 600,
                  color: "#334155",
                }}
              >
                No patient records displayed
              </p>

              <p
                style={{
                  margin:
                    "6px 0 0",
                  color: "#627d98",
                  fontSize: "14px",
                }}
              >
                Search by patient name or patient
                number to find a record.
              </p>
            </div>
          )}

        {patients.length > 0 && (
          <div style={styles.tableWrapper}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>
                    Patient Number
                  </th>
                  <th style={styles.th}>
                    Name
                  </th>
                  <th style={styles.th}>
                    District
                  </th>
                  <th style={styles.th}>
                    Sex
                  </th>
                  <th style={styles.th}>
                    Status
                  </th>
                  <th style={styles.th}>
                    Action
                  </th>
                </tr>
              </thead>

              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id}>
                    <td style={styles.td}>
                      <strong>
                        {patient.patient_number}
                      </strong>
                    </td>

                    <td style={styles.td}>
                      <div className="care-table-person">
                        <PatientAvatar patientId={patient.id} firstName={patient.first_name} lastName={patient.last_name} size={40} radius={13} label={`Photo of ${patient.first_name} ${patient.last_name}`} />
                        <div>
                          <div style={{ fontWeight: 800, color: "#102a43" }}>{patient.first_name} {patient.last_name}</div>
                          <div style={{ marginTop: 3, fontSize: 11, color: "#64748b" }}>{patient.patient_number}</div>
                        </div>
                      </div>
                    </td>

                    <td style={styles.td}>
                      {patient.district || "—"}
                    </td>

                    <td style={styles.td}>
                      {patient.sex || "—"}
                    </td>

                    <td style={styles.td}>
                      <span
                        style={{
                          display:
                            "inline-block",
                          padding:
                            "4px 9px",
                          borderRadius:
                            "999px",
                          background:
                            patient.status ===
                            "active"
                              ? "#dcfce7"
                              : "#f1f5f9",
                          color:
                            patient.status ===
                            "active"
                              ? "#166534"
                              : "#475569",
                          fontSize:
                            "12px",
                          fontWeight: 700,
                          textTransform:
                            "capitalize",
                        }}
                      >
                        {patient.status ||
                          "Unknown"}
                      </span>
                    </td>

                    <td style={styles.td}>
                      <button
                        type="button"
                        onClick={() =>
                          handleViewProfile(
                            patient.id,
                          )
                        }
                        style={{
                          padding:
                            "7px 12px",
                          borderRadius:
                            "8px",
                          border:
                            "1px solid #cbd5e1",
                          background:
                            "#ffffff",
                          color:
                            "#2563eb",
                          cursor:
                            "pointer",
                          fontWeight: 700,
                          fontSize:
                            "13px",
                        }}
                      >
                        View Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
function FormField({
  label,
  required = false,
  fullWidth = false,
  children,
}: {
  label: string;
  required?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "7px",
        gridColumn: fullWidth
          ? "1 / -1"
          : undefined,
      }}
    >
      <label
        style={{
          fontSize: "13px",
          fontWeight: 700,
          color: "#334155",
        }}
      >
        {label}

        {required && (
          <span
            style={{
              color: "#dc2626",
              marginLeft: "4px",
            }}
          >
            *
          </span>
        )}
      </label>

      {children}
    </div>
  );
}

function ProfileField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  const humanizedValue = value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  return (
    <div className="care-profile-field">
      <div
        style={{
          fontSize: "11px",
          fontWeight: 800,
          color: "#718096",
          marginBottom: "5px",
          textTransform: "uppercase",
          letterSpacing: "0.07em",
        }}
      >
        {label}
      </div>

      <div
        style={{
          color: value === "Not provided" ? "#94a3b8" : "#102a43",
          fontSize: "14px",
          lineHeight: 1.45,
          fontWeight: value === "Not provided" ? 500 : 700,
        }}
      >
        {humanizedValue}
      </div>
    </div>
  );
}

function ProfileSummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: number;
  icon: string;
}) {
  return (
    <div className="care-profile-summary">
      <div className="care-profile-summary-icon">{icon}</div>

      <div
        style={{
          fontSize: "11px",
          fontWeight: 800,
          color: "#718096",
          textTransform: "uppercase",
          letterSpacing: "0.07em",
        }}
      >
        {title}
      </div>

      <div
        style={{
          marginTop: "5px",
          fontSize: "27px",
          lineHeight: 1,
          fontWeight: 850,
          color: "#102a43",
        }}
      >
        {value}
      </div>

      <div
        style={{
          marginTop: "8px",
          fontSize: "12px",
          color: value > 0 ? "#0f766e" : "#94a3b8",
          fontWeight: 700,
        }}
      >
        {value > 0 ? "Records available" : "No records yet"}
      </div>
    </div>
  );
}

const formInputStyle: React.CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  padding: "11px 13px",
  borderRadius: "10px",
  border: "1px solid #cbd5e1",
  background: "#ffffff",
  color: "#102a43",
  fontSize: "14px",
  outline: "none",
};

const formGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(2, minmax(0, 1fr))",
  gap: "18px",
};

const formSectionTitleStyle: React.CSSProperties = {
  marginBottom: "18px",
};

const formSectionHeadingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "17px",
  color: "#102a43",
};

const formSectionDescriptionStyle: React.CSSProperties = {
  margin: "5px 0 0",
  fontSize: "13px",
  color: "#627d98",
};

const formDividerStyle: React.CSSProperties = {
  height: "1px",
  background: "#e2e8f0",
  margin: "26px 0",
};

const profileSectionHeaderStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  gap: "12px",
  marginBottom: "22px",
};

const profileIconStyle: React.CSSProperties = {
  width: "42px",
  height: "42px",
  flex: "0 0 auto",
  borderRadius: "12px",
  background: "linear-gradient(135deg, #ccfbf1 0%, #e0f2fe 100%)",
  border: "1px solid rgba(20, 184, 166, 0.12)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "18px",
  boxShadow: "0 7px 16px rgba(15, 118, 110, 0.08)",
};

const profileHeadingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "18px",
  color: "#102a43",
};

const profileDescriptionStyle: React.CSSProperties = {
  margin: "4px 0 0",
  fontSize: "13px",
  color: "#627d98",
};

const profileGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(160px, 1fr))",
  gap: "22px",
};
function CareTeamWorkspace() {
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();
  const [clinicians, setClinicians] = useState<CareUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (currentUser?.role !== "clinician" && currentUser?.role !== "administrator") return;

    setLoading(true);
    setError("");

    listUsers({ role: "clinician", status: "active", limit: 100 })
      .then((data) => setClinicians(data))
      .catch((err: any) => {
        setError(err?.response?.data?.detail || "Unable to load the active clinician directory.");
      })
      .finally(() => setLoading(false));
  }, [currentUser?.role]);

  const teamLabel = clinicians.length === 1 ? "active clinician" : "active clinicians";

  return (
    <div className="care-team-page">
      <section className="care-team-hero">
        <div>
          <div className="care-section-kicker">Care coordination</div>
          <h1 className="care-dashboard-title">Care Team</h1>
          <p className="care-dashboard-subtitle">
            Keep the clinical team directory, review workspaces and coordination shortcuts in one place.
          </p>
        </div>
        <div className="care-team-hero-stat">
          <span className="care-team-stat-value">{loading ? "—" : clinicians.length}</span>
          <span className="care-team-stat-label">{teamLabel}</span>
        </div>
      </section>

      <section className="care-team-action-grid" aria-label="Care coordination shortcuts">
        {[
          { label: "Clinical Review", detail: "Open patient assessments and review activity", path: "/clinical-workspace", icon: "activity" as const },
          { label: "Follow-ups", detail: "Review outstanding care coordination activity", path: "/follow-ups", icon: "calendar" as const },
          { label: "Care Gaps", detail: "Inspect open documented care opportunities", path: "/care-gaps", icon: "heartPulse" as const },
          { label: "Reports", detail: "Review released and pending clinical reports", path: "/reports", icon: "file" as const },
        ].map((item, index) => (
          <button
            key={item.path}
            type="button"
            className="care-team-action-card"
            style={{ animationDelay: `${index * 60}ms` }}
            onClick={() => navigate(item.path)}
          >
            <span className="care-team-action-icon"><Icon name={item.icon} size={18} /></span>
            <span className="care-team-action-copy">
              <strong>{item.label}</strong>
              <span>{item.detail}</span>
            </span>
            <Icon name="chevronRight" size={16} className="care-quick-arrow" />
          </button>
        ))}
      </section>

      <section style={styles.panel} className="care-team-directory-panel">
        <div className="care-team-section-heading">
          <div>
            <div className="care-section-kicker">Team directory</div>
            <h2 style={{ margin: "5px 0 0", color: "#102a43" }}>Active clinicians</h2>
            <p style={{ ...styles.muted, marginTop: "7px" }}>
              Directory information is sourced from the existing CareSphere user accounts.
            </p>
          </div>
          <span className="care-team-directory-badge">Role-aware access</span>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        {loading ? (
          <div className="care-team-empty-state">Loading the active clinician directory…</div>
        ) : clinicians.length === 0 ? (
          <div className="care-team-empty-state">
            <strong>No active clinicians found.</strong>
            <span>Activate or create a clinician account in User Management to populate this directory.</span>
          </div>
        ) : (
          <div className="care-team-member-grid">
            {clinicians.map((clinician) => {
              const initials = clinician.full_name
                ?.split(/\s+/)
                .filter(Boolean)
                .slice(0, 2)
                .map((word) => word[0])
                .join("")
                .toUpperCase() || "CL";
              const isCurrentUser = clinician.id === currentUser?.id;

              return (
                <article key={clinician.id} className={`care-team-member-card ${isCurrentUser ? "is-current" : ""}`}>
                  <div className="care-team-member-top">
                    <div className="care-team-member-avatar">{initials}</div>
                    <div style={{ minWidth: 0 }}>
                      <div className="care-team-member-name">{clinician.full_name}</div>
                      <div className="care-team-member-username">@{clinician.username}</div>
                    </div>
                  </div>
                  <div className="care-team-member-meta">
                    <span><span className="care-team-meta-dot" /> Active</span>
                    {isCurrentUser && <span className="care-team-you-pill">You</span>}
                  </div>
                  <div className="care-team-member-footer">
                    <span>Clinician account #{clinician.id}</span>
                    <button type="button" onClick={() => navigate("/clinical-workspace")}>
                      Open workspace
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function UserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<CareUser[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<UserRole | "">("");
  const [statusFilter, setStatusFilter] = useState<UserStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editingUser, setEditingUser] = useState<CareUser | null>(null);
  const [selectedUser, setSelectedUser] = useState<CareUser | null>(null);
  const [form, setForm] = useState({
    username: "",
    password: "",
    full_name: "",
    role: "clinician" as UserRole,
    patient_id: "",
  });

  const loadUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listUsers({
        search: search.trim() || undefined,
        role: roleFilter || undefined,
        status: statusFilter || undefined,
        limit: 100,
      });
      setUsers(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to load users.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser?.role !== "administrator") return;
    loadUsers();
    searchPatients({ limit: 100, offset: 0 })
      .then(setPatients)
      .catch(() => undefined);
  }, [currentUser?.role]);

  const resetForm = () => {
    setEditingUser(null);
    setForm({
      username: "",
      password: "",
      full_name: "",
      role: "clinician",
      patient_id: "",
    });
  };

  const beginEdit = (record: CareUser) => {
    setEditingUser(record);
    setForm({
      username: record.username,
      password: "",
      full_name: record.full_name,
      role: record.role,
      patient_id: record.patient_id ? String(record.patient_id) : "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const saveUser = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      if (form.role === "patient" && !form.patient_id) {
        throw new Error("Select the patient record linked to this portal account.");
      }

      if (editingUser) {
        await updateUser(editingUser.id, {
          username: form.username.trim(),
          full_name: form.full_name.trim(),
          role: form.role,
          ...(form.password ? { password: form.password } : {}),
          patient_id: form.role === "patient" ? Number(form.patient_id) : null,
        });
        setSuccess(`User ${form.username.trim()} was updated successfully.`);
      } else {
        await createUser({
          username: form.username.trim(),
          password: form.password,
          full_name: form.full_name.trim(),
          role: form.role,
          patient_id: form.role === "patient" ? Number(form.patient_id) : null,
        });
        setSuccess(`User ${form.username.trim()} was created successfully.`);
      }

      resetForm();
      await loadUsers();
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to save user.",
      );
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (record: CareUser) => {
    if (record.id === currentUser?.id) return;
    const nextStatus: UserStatus = record.status === "active" ? "inactive" : "active";
    setError("");
    setSuccess("");
    try {
      await updateUserStatus(record.id, nextStatus);
      setSuccess(`${record.full_name} is now ${nextStatus}.`);
      await loadUsers();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to update user status.");
    }
  };

  const formatRole = (role: UserRole) =>
    role === "administrator" ? "Administrator" : role === "patient" ? "Patient" : "Clinician";

  const patientById = new Map(patients.map((patient) => [patient.id, patient]));

  if (currentUser?.role !== "administrator") {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="care-profile-page">
      <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", alignItems: "flex-end", flexWrap: "wrap", marginBottom: "20px" }}>
        <div>
          <div style={{ fontSize: "12px", fontWeight: 800, color: "#0f766e", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "5px" }}>
            Administration
          </div>
          <h1 style={{ ...styles.title, marginBottom: "5px" }}>User Management</h1>
          <p style={styles.subtitle}>Create and manage staff accounts. Patients create their own portal accounts and complete their own health information.</p>
        </div>
        {editingUser && (
          <button type="button" onClick={resetForm} style={{ ...styles.searchButton, background: "#ffffff", color: "#334155", border: "1px solid #dbe4ea" }}>
            Cancel edit
          </button>
        )}
      </div>

      {(error || success) && (
        <div style={{ ...styles.panel, marginBottom: "18px", padding: "14px 16px", background: error ? "#fff7f7" : "#effcf7", color: error ? "#b42318" : "#047857", borderColor: error ? "#fecaca" : "#bbf7d0" }}>
          {error || success}
        </div>
      )}

      <section className="care-profile-card" style={{ ...styles.panel, marginBottom: "20px" }}>
        <div style={profileSectionHeaderStyle}>
          <div style={profileIconStyle}>◈</div>
          <div>
            <h2 style={profileHeadingStyle}>{editingUser ? "Edit account" : "Create account"}</h2>
            <p style={profileDescriptionStyle}>Each account receives permissions according to its assigned role.</p>
          </div>
        </div>

        <form onSubmit={saveUser}>
          <div style={formGridStyle}>
            <FormField label="Full Name" required>
              <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} style={formInputStyle} placeholder="Full name" />
            </FormField>
            <FormField label="Username" required>
              <input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} style={formInputStyle} placeholder="Login username" />
            </FormField>
            <FormField label={editingUser ? "New Password (optional)" : "Password"} required={!editingUser}>
              <input type="password" required={!editingUser} minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={formInputStyle} placeholder={editingUser ? "Leave blank to keep current password" : "At least 8 characters"} />
            </FormField>
            <FormField label="Role" required>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole, patient_id: "" })} style={formInputStyle}>
                <option value="clinician">Clinician</option>
                <option value="administrator">Administrator</option>
              </select>
            </FormField>
            
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "22px" }}>
            <button type="submit" disabled={saving} style={{ ...styles.searchButton, minWidth: "160px", fontWeight: 750 }}>
              {saving ? "Saving..." : editingUser ? "Save Changes" : "Create User"}
            </button>
          </div>
        </form>
      </section>

      <section className="care-account-overview">
        <div className="care-account-stat"><span>Total shown</span><strong>{users.length}</strong><small>accounts</small></div>
        <div className="care-account-stat care-account-stat-positive"><span>Active</span><strong>{users.filter((item) => item.status === "active").length}</strong><small>enabled accounts</small></div>
        <div className="care-account-stat care-account-stat-info"><span>Clinicians</span><strong>{users.filter((item) => item.role === "clinician").length}</strong><small>clinical accounts</small></div>
        <div className="care-account-stat care-account-stat-patient"><span>Patients</span><strong>{users.filter((item) => item.role === "patient").length}</strong><small>portal accounts</small></div>
      </section>

      <section className="care-account-panel" style={styles.panel}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: "16px", flexWrap: "wrap", marginBottom: "18px" }}>
          <div>
            <h2 style={{ margin: 0, color: "#102a43" }}>CareSphere accounts</h2>
            <p style={{ ...styles.muted, margin: "5px 0 0" }}>{users.length} account{users.length === 1 ? "" : "s"} shown</p>
          </div>
          <form onSubmit={(e) => { e.preventDefault(); loadUsers(); }} style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search users..." style={{ ...formInputStyle, width: "220px" }} />
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value as UserRole | "")} style={{ ...formInputStyle, width: "150px" }}>
              <option value="">All roles</option>
              <option value="administrator">Administrators</option>
              <option value="clinician">Clinicians</option>
              <option value="patient">Patients</option>
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as UserStatus | "")} style={{ ...formInputStyle, width: "140px" }}>
              <option value="">All status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="suspended">Suspended</option>
            </select>
            <button type="submit" style={styles.searchButton}>Filter</button>
          </form>
        </div>

        <div style={styles.tableWrapper}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>User</th>
                <th style={styles.th}>Role</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Patient link</th>
                <th style={styles.th}>Last login</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={styles.td}>Loading users...</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={6} style={styles.td}>No users match the selected filters.</td></tr>
              ) : users.map((record) => (
                <tr key={record.id}>
                  <td style={styles.td}>
                    <div className="care-table-person">
                      {record.role === "patient" && record.patient_id && patientById.has(record.patient_id) ? (
                        <PatientAvatar
                          patientId={record.patient_id}
                          firstName={patientById.get(record.patient_id)?.first_name}
                          lastName={patientById.get(record.patient_id)?.last_name}
                          size={42}
                          radius={13}
                          label={`Patient photo for ${record.full_name}`}
                        />
                      ) : (
                        <div className="care-user-avatar">
                          {record.full_name?.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase() || "U"}
                        </div>
                      )}
                      <div>
                        <div style={{ fontWeight: 800, color: "#102a43" }}>{record.full_name}</div>
                        <div style={{ fontSize: "12px", color: "#64748b", marginTop: "3px" }}>@{record.username}</div>
                      </div>
                    </div>
                  </td>
                  <td style={styles.td}>{formatRole(record.role)}</td>
                  <td style={styles.td}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 9px", borderRadius: "999px", background: record.status === "active" ? "#ecfdf5" : "#f8fafc", color: record.status === "active" ? "#047857" : "#64748b", fontSize: "12px", fontWeight: 750 }}>
                      <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: record.status === "active" ? "#10b981" : "#94a3b8" }} />
                      {humanizeValue(record.status)}
                    </span>
                  </td>
                  <td style={styles.td}>{record.patient_id ? `Patient #${record.patient_id}` : "—"}</td>
                  <td style={styles.td}>{record.last_login_at ? new Date(record.last_login_at).toLocaleString() : "Never"}</td>
                  <td style={styles.td}>
                    <div style={{ display: "flex", gap: "7px", flexWrap: "wrap" }}>
                      <button type="button" onClick={() => beginEdit(record)} style={{ ...styles.searchButton, padding: "8px 11px" }}>Edit</button>
                      <button type="button" onClick={() => setSelectedUser(record)} style={{ ...styles.searchButton, padding: "8px 11px", background: "#ffffff", color: "#0f766e", border: "1px solid #99f6e4" }}>View</button>
                      <button type="button" disabled={record.id === currentUser?.id} onClick={() => changeStatus(record)} style={{ ...styles.searchButton, padding: "8px 11px", background: "#ffffff", color: "#334155", border: "1px solid #dbe4ea", opacity: record.id === currentUser?.id ? 0.55 : 1 }}>
                        {record.status === "active" ? "Deactivate" : "Activate"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selectedUser && (
        <section className="care-user-profile-drawer" style={styles.panel}>
          <div className="care-user-profile-header">
            <div>
              <div className="care-section-kicker">Account profile</div>
              <h2 style={{ margin: "4px 0 5px", color: "#102a43" }}>{selectedUser.full_name}</h2>
              <p style={{ margin: 0, color: "#627d98", fontSize: 12 }}>@{selectedUser.username}</p>
            </div>
            <button type="button" onClick={() => setSelectedUser(null)} style={{ ...styles.searchButton, background: "#fff", color: "#334155", border: "1px solid #dbe4ea" }}>Close</button>
          </div>
          <div className="care-user-profile-body">
            <div className="care-user-profile-identity">
              {selectedUser.role === "patient" && selectedUser.patient_id && patientById.has(selectedUser.patient_id) ? (
                <PatientAvatar
                  patientId={selectedUser.patient_id}
                  firstName={patientById.get(selectedUser.patient_id)?.first_name}
                  lastName={patientById.get(selectedUser.patient_id)?.last_name}
                  size={78}
                  radius={22}
                  label={`Patient photo for ${selectedUser.full_name}`}
                />
              ) : (
                <div className="care-user-avatar care-user-avatar-large">
                  {selectedUser.full_name?.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase() || "U"}
                </div>
              )}
              <div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 7 }}>
                  <span className="care-account-chip">{formatRole(selectedUser.role)}</span>
                  <span className="care-account-chip">{humanizeValue(selectedUser.status)}</span>
                </div>
                <strong style={{ color: "#102a43" }}>{selectedUser.patient_id ? `Linked patient #${selectedUser.patient_id}` : "No linked patient record"}</strong>
              </div>
            </div>
            <div className="care-user-detail-grid">
              <div><span>Account ID</span><strong>{selectedUser.id}</strong></div>
              <div><span>Created</span><strong>{new Date(selectedUser.created_at).toLocaleString()}</strong></div>
              <div><span>Updated</span><strong>{new Date(selectedUser.updated_at).toLocaleString()}</strong></div>
              <div><span>Last login</span><strong>{selectedUser.last_login_at ? new Date(selectedUser.last_login_at).toLocaleString() : "Never"}</strong></div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

function humanizeValue(value: string | null | undefined): string {
  if (!value) return "Not recorded";
  return value
    .replace(/_/g, " ")
    .split(" " )
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" " );
}

const navigationByRole = {
  administrator: [
    { label: "Dashboard", path: "/admin", icon: "home" },
    { label: "Patients", path: "/patients", icon: "patient" },
    { label: "Clinical Review", path: "/clinical-workspace", icon: "activity" },
    { label: "Task Center", path: "/tasks", icon: "activity" },
    { label: "User Management", path: "/users", icon: "users" },
    { label: "Reports", path: "/reports", icon: "file" },
    { label: "Care Gaps", path: "/care-gaps", icon: "activity" },
    { label: "Follow-ups", path: "/follow-ups", icon: "calendar" },
    { label: "Notifications", path: "/notifications", icon: "bell" },
    { label: "Audit Logs", path: "/audit-logs", icon: "shield" },
  ],
  clinician: [
    { label: "Dashboard", path: "/", icon: "home" },
    { label: "Patients", path: "/patients", icon: "patient" },
    { label: "Clinical Review", path: "/clinical-workspace", icon: "activity" },
    { label: "Task Center", path: "/tasks", icon: "activity" },
    { label: "Care Team", path: "/care-team", icon: "users" },
    { label: "Care Gaps", path: "/care-gaps", icon: "activity" },
    { label: "Follow-ups", path: "/follow-ups", icon: "calendar" },
    { label: "Notifications", path: "/notifications", icon: "bell" },
    { label: "Reports", path: "/reports", icon: "file" },
  ],
  patient: [
    { label: "My Health", path: "/patient-portal", icon: "heartPulse" },
  ],
} as const;

const RECENT_PATIENTS_KEY = "caresphere:recent-patients";

type RecentPatient = Pick<
  Patient,
  "id" | "patient_number" | "first_name" | "last_name" | "district" | "country" | "sex" | "status"
>;

function readRecentPatients(): RecentPatient[] {
  try {
    const raw = window.sessionStorage.getItem(RECENT_PATIENTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is RecentPatient => (
      item &&
      typeof item.id === "number" &&
      typeof item.patient_number === "string" &&
      typeof item.first_name === "string" &&
      typeof item.last_name === "string"
    )).slice(0, 6);
  } catch {
    return [];
  }
}

function rememberRecentPatient(patient: RecentPatient) {
  try {
    const compact: RecentPatient = {
      id: patient.id,
      patient_number: patient.patient_number,
      first_name: patient.first_name,
      last_name: patient.last_name,
      district: patient.district,
      country: patient.country,
      sex: patient.sex,
      status: patient.status,
    };
    const next = [compact, ...readRecentPatients().filter((item) => item.id !== patient.id)].slice(0, 6);
    window.sessionStorage.setItem(RECENT_PATIENTS_KEY, JSON.stringify(next));
  } catch {
    // Recent history is a convenience feature; navigation remains authoritative.
  }
}

function clearRecentPatients() {
  try {
    window.sessionStorage.removeItem(RECENT_PATIENTS_KEY);
  } catch {
    // Ignore storage failures.
  }
}

function GlobalPatientCommandCenter({
  onClose,
}: {
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [recentPatients, setRecentPatients] = useState<RecentPatient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  const workspaceActions = [
    { label: "Task Center", detail: "Clinical queues and operational work", path: "/tasks", icon: "activity" as const },
    { label: "Dashboard", detail: "Operational overview and activity", path: user?.role === "administrator" ? "/admin" : "/", icon: "home" as const },
    { label: "Patients", detail: "Search and open patient records", path: "/patients", icon: "patient" as const },
    { label: "Clinical Review", detail: "Assessments, risk and recommendations", path: "/clinical-workspace", icon: "activity" as const },
    { label: "Follow-ups", detail: "Review follow-up workflow activity", path: "/follow-ups", icon: "calendar" as const },
    { label: "Care Gaps", detail: "Review open care opportunities", path: "/care-gaps", icon: "activity" as const },
    { label: "Notifications", detail: "Review workspace notifications", path: "/notifications", icon: "bell" as const },
    { label: "Reports", detail: "Open generated clinical reports", path: "/reports", icon: "file" as const },
    ...(user?.role === "administrator"
      ? [
          { label: "User Management", detail: "Accounts, roles and access", path: "/users", icon: "users" as const },
          { label: "Audit Logs", detail: "Review governance activity", path: "/audit-logs", icon: "shield" as const },
        ]
      : []),
  ];

  const normalizedQuery = query.trim().toLowerCase();
  const filteredWorkspaceActions = normalizedQuery
    ? workspaceActions.filter((action) =>
        `${action.label} ${action.detail}`.toLowerCase().includes(normalizedQuery),
      )
    : workspaceActions.slice(0, 6);

  useEffect(() => {
    inputRef.current?.focus();
    setRecentPatients(readRecentPatients());
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      setPatients([]);
      setError("");
      return;
    }

    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const rows = await searchPatients({ search: term, limit: 12, offset: 0 });
        setPatients(rows);
      } catch (err: any) {
        setPatients([]);
        setError(err?.response?.data?.detail || "Unable to search patients.");
      } finally {
        setLoading(false);
      }
    }, 220);

    return () => window.clearTimeout(timer);
  }, [query]);

  const openClinicalReview = (patient: Patient) => {
    rememberRecentPatient(patient);
    window.sessionStorage.setItem("caresphere:quick-patient", String(patient.id));
    navigate("/clinical-workspace");
    onClose();
  };

  const openPatientRecords = (patient: Patient) => {
    rememberRecentPatient(patient);
    window.sessionStorage.setItem("caresphere:quick-patient", String(patient.id));
    navigate("/patients");
    onClose();
  };

  const openRecentPatient = (patient: RecentPatient) => {
    rememberRecentPatient(patient);
    window.sessionStorage.setItem("caresphere:quick-patient", String(patient.id));
    navigate("/clinical-workspace");
    onClose();
  };

  const handleClearRecent = () => {
    clearRecentPatients();
    setRecentPatients([]);
  };

  const openWorkspaceAction = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <div className="care-command-overlay" role="presentation" onMouseDown={onClose}>
      <div className="care-command-dialog" role="dialog" aria-modal="true" aria-label="CareSphere command center" onMouseDown={(event) => event.stopPropagation()}>
        <div className="care-command-header">
          <div>
            <div className="care-section-kicker">CareSphere command center</div>
            <h2 style={{ margin: "4px 0 4px", color: "#102a43", fontSize: 21 }}>Go anywhere</h2>
            <p style={{ margin: 0, color: "#627d98", fontSize: 12 }}>Open a workspace or search patients without leaving your current flow.</p>
          </div>
          <button type="button" className="care-command-close" onClick={onClose} aria-label="Close quick search">×</button>
        </div>

        <div className="care-command-search">
          <span aria-hidden="true">⌕</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search patients or workspace actions..."
            autoComplete="off"
            aria-label="Search patients"
          />
          <kbd>Esc</kbd>
        </div>

        {loading && <div className="care-command-status">Searching patient records…</div>}
        {error && <div className="care-command-error">{error}</div>}

        {filteredWorkspaceActions.length > 0 && (
          <div className="care-command-actions-grid">
            <div className="care-command-section-head">
              <div>
                <div className="care-section-kicker">Workspace actions</div>
                <strong>{normalizedQuery ? "Matching tools" : "Quick access"}</strong>
              </div>
              {!normalizedQuery && <span className="care-command-hint">Navigation stays role-aware</span>}
            </div>
            <div className="care-command-tool-grid">
              {filteredWorkspaceActions.map((action) => (
                <button
                  type="button"
                  key={action.path}
                  className="care-command-tool"
                  onClick={() => openWorkspaceAction(action.path)}
                >
                  <span className="care-command-tool-icon"><Icon name={action.icon} size={17} /></span>
                  <span className="care-command-tool-copy">
                    <strong>{action.label}</strong>
                    <span>{action.detail}</span>
                  </span>
                  <span className="care-command-tool-arrow">›</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {!loading && !error && normalizedQuery && filteredWorkspaceActions.length === 0 && patients.length === 0 && (
          <div className="care-command-empty">
            <div className="care-empty-icon"><Icon name="patient" size={18} /></div>
            <strong>No matching workspace or patient records</strong>
            <span>Try a patient name, patient number, or workspace name.</span>
          </div>
        )}

        {!query.trim() && recentPatients.length > 0 && (
          <div className="care-command-recent">
            <div className="care-command-section-head">
              <div>
                <div className="care-section-kicker">Workspace memory</div>
                <strong>Recently opened patients</strong>
              </div>
              <button type="button" className="care-command-clear" onClick={handleClearRecent}>Clear</button>
            </div>
            <div className="care-command-results">
              {recentPatients.map((patient) => (
                <button
                  type="button"
                  key={`recent-${patient.id}`}
                  className="care-command-result"
                  onClick={() => openRecentPatient(patient)}
                >
                  <span className="care-command-avatar">
                    <PatientAvatar patientId={patient.id} firstName={patient.first_name} lastName={patient.last_name} size={42} radius={13} />
                  </span>
                  <span className="care-command-result-main">
                    <strong>{patient.first_name} {patient.last_name}</strong>
                    <span>{patient.patient_number} · {patient.district || "Location not recorded"}</span>
                    <span>{patient.sex ? humanizeValue(patient.sex) : "Sex not recorded"} · {patient.status ? humanizeValue(patient.status) : "Status not recorded"}</span>
                  </span>
                  <span className="care-command-arrow">›</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {patients.length > 0 && (
          <div className="care-command-results">
            {patients.map((patient) => (
              <button
                type="button"
                key={patient.id}
                className={`care-command-result ${selectedPatient?.id === patient.id ? "is-selected" : ""}`}
                onClick={() => setSelectedPatient(patient)}
              >
                <span className="care-command-avatar">
                  <PatientAvatar patientId={patient.id} firstName={patient.first_name} lastName={patient.last_name} size={42} radius={13} />
                </span>
                <span className="care-command-result-main">
                  <strong>{patient.first_name} {patient.last_name}</strong>
                  <span>{patient.patient_number} · {patient.district || "Location not recorded"}</span>
                  <span>{patient.sex ? humanizeValue(patient.sex) : "Sex not recorded"} · {patient.status ? humanizeValue(patient.status) : "Status not recorded"}</span>
                </span>
                <span className="care-command-arrow">›</span>
              </button>
            ))}
          </div>
        )}

        {selectedPatient && (
          <div className="care-command-detail">
            <div className="care-command-detail-identity">
              <div className="care-avatar-ring">
                <PatientAvatar patientId={selectedPatient.id} firstName={selectedPatient.first_name} lastName={selectedPatient.last_name} size={58} radius={18} />
              </div>
              <div>
                <div className="care-section-kicker">Selected patient</div>
                <strong>{selectedPatient.first_name} {selectedPatient.last_name}</strong>
                <div className="care-patient-meta-line">
                  <span><strong>{selectedPatient.patient_number}</strong></span>
                  <span>·</span>
                  <span>{selectedPatient.district || "Location not recorded"}</span>
                  <span>·</span>
                  <span>{selectedPatient.country || "Country not recorded"}</span>
                </div>
              </div>
            </div>
            <div className="care-command-actions">
              <button type="button" className="care-command-secondary" onClick={() => openPatientRecords(selectedPatient)}>Open patient record</button>
              <button type="button" className="care-command-primary" onClick={() => openClinicalReview(selectedPatient)}>Open Clinical Review</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ProtectedLayout() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [commandCenterOpen, setCommandCenterOpen] = useState(false);

  if (loading) {
    return (
      <div style={styles.loginPage}>
        <div style={styles.loginCard}>
          <div className="care-login-mark"><Icon name="heartPulse" size={22} /></div>
          <h1 style={styles.loginLogo}>CareSphere</h1>
          <p style={styles.loginSubtitle}>Checking your secure session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const navigation = navigationByRole[user.role as keyof typeof navigationByRole] ?? navigationByRole.clinician;
  const homePath = user.role === "administrator" ? "/admin" : user.role === "patient" ? "/patient-portal" : "/";

  useEffect(() => {
    if (user.role === "patient") return;
    const handleCommandShortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandCenterOpen(true);
      }
    };
    window.addEventListener("keydown", handleCommandShortcut);
    return () => window.removeEventListener("keydown", handleCommandShortcut);
  }, [user.role]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div style={styles.app} className="care-app-shell">
      <div className={`care-nav-scrim ${mobileNavOpen ? "is-visible" : ""}`} onClick={() => setMobileNavOpen(false)} />
      <aside style={styles.sidebar} className={`care-sidebar ${mobileNavOpen ? "is-open" : ""}`}>
        <div className="care-brand-block">
          <div className="care-brand-mark"><Icon name="heartPulse" size={21} /></div>
          <div>
            <div style={styles.logo}>CareSphere</div>
            <div className="care-brand-caption">Clinical intelligence</div>
          </div>
        </div>

        <div style={styles.sidebarRoleBadge}>
          <span style={styles.sidebarRoleDot} />
          {user.role === "administrator" ? "Administrator" : user.role === "patient" ? "Patient Portal" : "Clinical Workspace"}
        </div>

        <nav className="care-sidebar-nav" aria-label="Primary navigation">
          <div className="care-nav-label">Workspace</div>
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/" || item.path === "/admin" || item.path === "/patient-portal"}
              onClick={() => setMobileNavOpen(false)}
              className={({ isActive }) => `care-nav-link ${isActive ? "is-active" : ""}`}
            >
              <span className="care-nav-icon"><Icon name={item.icon} size={17} /></span>
              <span>{item.label}</span>
              <Icon name="chevronRight" size={14} className="care-nav-chevron" />
            </NavLink>
          ))}
        </nav>

        <div className="care-sidebar-footer">
          <div className="care-sidebar-footer-icon"><Icon name="shield" size={16} /></div>
          <div><strong>Protected workspace</strong><span>Role-aware access is active</span></div>
        </div>
      </aside>

      <div style={styles.main}>
        <header style={styles.header} className="care-topbar">
          <button className="care-mobile-menu" type="button" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}><Icon name="menu" size={20} /></button>
          <div className="care-topbar-context">
            <div className="care-topbar-title">{user.role === "patient" ? "My Health" : "Care workspace"}</div>
            <div className="care-topbar-subtitle">{user.role === "administrator" ? "System oversight & governance" : user.role === "patient" ? "Your secure health space" : "Clinical review & care coordination"}</div>
          </div>
          <div className="care-topbar-tools">
            {user.role !== "patient" && (
              <button type="button" className="care-command-launcher" onClick={() => setCommandCenterOpen(true)} aria-label="Open quick patient search">
                <span aria-hidden="true">⌕</span>
                <span>Quick patient search</span>
                <kbd>Ctrl K</kbd>
              </button>
            )}
            <div style={styles.status}>
            <span style={styles.dot} />
            <span className="care-user-name">{user.full_name}</span>
            <span style={styles.headerRolePill}>
              {user.role === "administrator" ? "Administrator" : user.role === "patient" ? "Patient" : "Clinician"}
            </span>
            <button type="button" onClick={handleLogout} style={styles.logoutButton}>
              Sign out
            </button>
            </div>
          </div>
        </header>
        {commandCenterOpen && user.role !== "patient" && (
          <GlobalPatientCommandCenter onClose={() => setCommandCenterOpen(false)} />
        )}

        <main style={styles.content} className="care-content">
          <Routes>
            <Route path="/" element={user.role === "clinician" ? <Dashboard /> : <Navigate to={homePath} replace />} />
            <Route path="/admin" element={user.role === "administrator" ? <Dashboard /> : <Navigate to={homePath} replace />} />
            <Route path="/patient-portal" element={user.role === "patient" ? <PatientPortalPage /> : <Navigate to={homePath} replace />} />
            <Route path="/patients" element={user.role === "administrator" || user.role === "clinician" ? <Patients /> : <Navigate to={homePath} replace />} />
            <Route path="/clinical-workspace" element={user.role === "administrator" || user.role === "clinician" ? <ClinicalWorkspace /> : <Navigate to={homePath} replace />} />
            <Route path="/clinical-review" element={user.role === "administrator" || user.role === "clinician" ? <ClinicalWorkspace /> : <Navigate to={homePath} replace />} />
            <Route path="/clinical-reviews" element={user.role === "administrator" || user.role === "clinician" ? <ClinicalWorkspace /> : <Navigate to={homePath} replace />} />
            <Route path="/tasks" element={user.role === "administrator" || user.role === "clinician" ? <TaskCenter /> : <Navigate to={homePath} replace />} />
            <Route path="/care-team" element={user.role === "clinician" || user.role === "administrator" ? <CareTeamWorkspace /> : <Navigate to={homePath} replace />} />
            <Route path="/care-gaps" element={user.role === "clinician" || user.role === "administrator" ? <WorkflowWorkspaceFrame module="care-gaps"><CareGapsPage /></WorkflowWorkspaceFrame> : <Navigate to={homePath} replace />} />
            <Route path="/follow-ups" element={user.role === "clinician" || user.role === "administrator" ? <WorkflowWorkspaceFrame module="follow-ups"><FollowUpsPage /></WorkflowWorkspaceFrame> : <Navigate to={homePath} replace />} />
            <Route path="/notifications" element={user.role === "clinician" || user.role === "administrator" ? <WorkflowWorkspaceFrame module="notifications"><NotificationsPage /></WorkflowWorkspaceFrame> : <Navigate to={homePath} replace />} />
            <Route path="/reports" element={user.role === "administrator" || user.role === "clinician" ? <ReportsWorkspace /> : <Navigate to={homePath} replace />} />
            <Route path="/users" element={user.role === "administrator" ? <WorkflowWorkspaceFrame module="users"><UserManagement /></WorkflowWorkspaceFrame> : <Navigate to={homePath} replace />} />
            <Route path="/audit-logs" element={user.role === "administrator" ? <WorkflowWorkspaceFrame module="audit-logs"><AuditLogsPage /></WorkflowWorkspaceFrame> : <Navigate to={homePath} replace />} />
            <Route path="*" element={<Navigate to={homePath} replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function CareSphereGlobalStyles() {
  return (
    <style>{`
      :root {
        --care-ink: #102a43;
        --care-muted: #627d98;
        --care-teal: #087f78;
        --care-teal-bright: #13a69d;
        --care-cyan: #38bdf8;
        --care-line: rgba(148,163,184,0.18);
        --care-surface: rgba(255,255,255,0.94);
        --care-shadow: 0 18px 48px rgba(16,42,67,0.075);
      }

      @keyframes careFadeUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes careFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes careScaleIn {
        from { opacity: 0; transform: translateY(5px) scale(0.985); }
        to { opacity: 1; transform: translateY(0) scale(1); }
      }
      @keyframes carePulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.16); opacity: 0.72; }
      }
      @keyframes careFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
      }
      @keyframes careShimmer {
        from { transform: translateX(-120%); }
        to { transform: translateX(120%); }
      }
      @keyframes careGlow {
        0%, 100% { opacity: 0.55; }
        50% { opacity: 1; }
      }

      * { box-sizing: border-box; }
      html { scroll-behavior: smooth; }
      body {
        margin: 0;
        background:
          radial-gradient(circle at 10% 8%, rgba(45,212,191,0.09), transparent 24%),
          radial-gradient(circle at 90% 18%, rgba(56,189,248,0.08), transparent 25%),
          linear-gradient(180deg, #f7fbfd 0%, #f3f8fb 48%, #f8fbfc 100%);
        color: var(--care-ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
      }
      button, input, select, textarea { font: inherit; }
      button {
        transition: transform 180ms cubic-bezier(.2,.8,.2,1), box-shadow 180ms ease, background-color 180ms ease, border-color 180ms ease, color 180ms ease, filter 180ms ease;
      }
      button:not(:disabled):hover { transform: translateY(-2px); filter: saturate(1.03); }
      button:not(:disabled):active { transform: translateY(0); }
      button:disabled { cursor: not-allowed; }
      input, select, textarea {
        transition: border-color 180ms ease, box-shadow 180ms ease, background-color 180ms ease, transform 180ms ease;
      }
      input:hover:not(:focus), select:hover:not(:focus), textarea:hover:not(:focus) {
        border-color: rgba(13,148,136,0.34) !important;
      }
      input:focus, select:focus, textarea:focus {
        border-color: #19a7a0 !important;
        box-shadow: 0 0 0 4px rgba(25,167,160,0.12), 0 7px 20px rgba(15,118,110,0.06) !important;
        outline: none;
      }
      table tbody tr { transition: background-color 160ms ease, transform 160ms ease; }
      table tbody tr:hover { background: #f5fbfb; }
      nav a {
        transition: background-color 180ms ease, color 180ms ease, transform 180ms ease, box-shadow 180ms ease, padding-left 180ms ease;
      }
      .care-nav-link:hover { box-shadow: inset 0 0 0 1px rgba(255,255,255,0.09), 0 7px 18px rgba(0,0,0,0.08); }
      .care-nav-link.is-active { position: relative; overflow: hidden; }
      .care-nav-link.is-active::after {
        content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(255,255,255,0.04), rgba(255,255,255,0.12), rgba(255,255,255,0.04)); animation: careShimmer 2.8s ease-in-out infinite; pointer-events: none;
      }
      .care-app-shell { isolation: isolate; }
      .care-content { min-height: calc(100vh - 76px); }
      .care-glass-panel { backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }
      .care-avatar-ring {
        padding: 4px; border-radius: 24px; background: linear-gradient(135deg, rgba(20,184,166,0.55), rgba(56,189,248,0.42));
        box-shadow: 0 12px 30px rgba(8,127,120,0.18); flex: 0 0 auto;
      }
      .care-avatar-ring > div { border: 2px solid rgba(255,255,255,0.92); }
      .care-section-kicker { color: #0f766e; font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.12em; }
      .care-patient-meta-line { display: flex; flex-wrap: wrap; gap: 7px; align-items: center; color: #627d98; font-size: 12px; line-height: 1.5; }
      .care-patient-meta-line strong { color: #334e68; }
      .care-live-pill { display: inline-flex; align-items: center; gap: 7px; padding: 7px 10px; border-radius: 999px; background: rgba(236,253,245,0.86); color: #047857; border: 1px solid #bbf7d0; font-size: 10px; font-weight: 850; white-space: nowrap; }
      .care-live-pill > span { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px rgba(16,185,129,0.11); animation: carePulse 1.8s ease-in-out infinite; }
      .care-clinical-selected { animation: careScaleIn 360ms ease both; overflow: hidden; }
      .care-clinical-selected-glow { position: absolute; width: 180px; height: 180px; right: -65px; top: -90px; border-radius: 50%; background: radial-gradient(circle, rgba(45,212,191,0.22), rgba(45,212,191,0)); pointer-events: none; animation: careGlow 4s ease-in-out infinite; }
      .care-clinical-selected-actions { display: flex; align-items: flex-end; flex-direction: column; gap: 8px; }
      .care-search-panel { animation: careFadeUp 400ms ease both; }
      .care-search-row { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 10px; }
      .care-search-input-wrap { position: relative; min-width: 0; }
      .care-search-leading { position: absolute; left: 13px; top: 50%; transform: translateY(-50%); z-index: 1; color: #0f766e; font-size: 21px; line-height: 1; pointer-events: none; }
      .care-result-count { padding: 6px 10px; border-radius: 999px; background: #eef8f7; color: #0f766e; font-size: 11px; font-weight: 850; border: 1px solid #d4efeb; }
      .care-patient-results { display: grid; gap: 8px; }
      .care-patient-result {
        width: 100%; display: grid; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: 12px; text-align: left; padding: 11px 12px; border: 1px solid #e2e8f0; border-radius: 16px; background: linear-gradient(135deg, #fff 0%, #fbfdff 100%); cursor: pointer; box-shadow: 0 7px 18px rgba(15,23,42,0.035); animation: careFadeUp 320ms ease both; }
      .care-patient-result:hover { border-color: rgba(20,184,166,0.28); box-shadow: 0 12px 26px rgba(15,23,42,0.075); background: linear-gradient(135deg, #ffffff 0%, #f4fffd 100%); }
      .care-patient-result.is-selected { border-color: rgba(20,184,166,0.55); background: linear-gradient(135deg, #effcfb 0%, #f8fcff 100%); box-shadow: 0 12px 28px rgba(15,118,110,0.09), inset 3px 0 0 #14b8a6; }
      .care-patient-result-main { display: grid; gap: 5px; min-width: 0; }
      .care-patient-result-top { display: flex; justify-content: space-between; gap: 10px; align-items: center; min-width: 0; }
      .care-patient-result-top strong { color: #102a43; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .care-patient-result-meta { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; color: #627d98; font-size: 11px; line-height: 1.4; }
      .care-patient-result-arrow { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 9px; background: #eef8f7; color: #0f766e; font-size: 21px; font-weight: 500; transition: transform 160ms ease, background 160ms ease; }
      .care-patient-result:hover .care-patient-result-arrow { transform: translateX(2px); background: #dff8f3; }
      .care-empty-state { display: grid; justify-items: center; gap: 5px; padding: 28px 18px; border: 1px dashed #cbd5e1; border-radius: 16px; background: linear-gradient(180deg, #fbfdff, #f7fafc); text-align: center; color: #334e68; }
      .care-empty-state > span { color: #64748b; font-size: 12px; }
      .care-empty-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 13px; background: linear-gradient(135deg,#ccfbf1,#e0f2fe); color: #0f766e; font-size: 21px; margin-bottom: 3px; animation: careFloat 3s ease-in-out infinite; }
      .care-form-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; }
      .care-table-person { display: flex; align-items: center; gap: 11px; min-width: 190px; }
      .care-user-avatar { width: 42px; height: 42px; min-width: 42px; border-radius: 13px; display: grid; place-items: center; color: #fff; font-weight: 850; font-size: 13px; background: linear-gradient(135deg,#0f766e,#0ea5a4,#38bdf8); box-shadow: 0 8px 20px rgba(8,127,120,0.15); }
      .care-profile-avatar-shell { padding: 4px; border-radius: 28px; background: linear-gradient(135deg, rgba(15,118,110,0.42), rgba(56,189,248,0.35)); box-shadow: 0 16px 35px rgba(8,127,120,0.16); }
      .care-profile-avatar-shell > div { border: 2px solid rgba(255,255,255,0.94); }
      .care-topbar-tools { display: flex; align-items: center; gap: 10px; min-width: 0; }
      .care-command-launcher {
        display: inline-flex; align-items: center; gap: 8px; min-width: 210px;
        padding: 9px 11px; border: 1px solid rgba(20,184,166,0.18); border-radius: 13px;
        background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,250,249,0.94));
        color: #334e68; font-size: 12px; font-weight: 800; cursor: pointer;
        box-shadow: 0 8px 22px rgba(16,42,67,0.045);
      }
      .care-command-launcher > span:first-child { color: #0f766e; font-size: 18px; line-height: 1; }
      .care-command-launcher kbd, .care-command-search kbd {
        margin-left: auto; padding: 3px 6px; border-radius: 7px; border: 1px solid #dbe5ea;
        background: #fff; color: #64748b; font-size: 10px; font-weight: 800; white-space: nowrap;
      }
      .care-command-overlay {
        position: fixed; inset: 0; z-index: 2000; display: grid; place-items: start center;
        padding: 92px 20px 20px; background: rgba(7,38,52,0.38); backdrop-filter: blur(8px);
        animation: careFadeIn 180ms ease both;
      }
      .care-command-dialog {
        width: min(720px, 100%); max-height: min(760px, calc(100vh - 112px)); overflow: auto;
        border: 1px solid rgba(255,255,255,0.72); border-radius: 24px; padding: 18px;
        background: linear-gradient(180deg, rgba(255,255,255,0.985), rgba(247,252,253,0.98));
        box-shadow: 0 32px 90px rgba(7,38,52,0.22); animation: careScaleIn 220ms ease both;
      }
      .care-command-header { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; }
      .care-command-close {
        width: 34px; height: 34px; border-radius: 11px; border: 1px solid #dbe5ea;
        background: rgba(255,255,255,0.88); color: #475569; font-size: 20px; cursor: pointer; line-height: 1;
      }
      .care-command-search {
        display: flex; align-items: center; gap: 9px; margin-top: 15px; padding: 0 12px;
        border: 1px solid #cfe0e6; border-radius: 15px; background: #fff;
        box-shadow: inset 0 1px 2px rgba(16,42,67,0.025), 0 8px 20px rgba(16,42,67,0.04);
      }
      .care-command-search > span { color: #0f766e; font-size: 22px; }
      .care-command-search input {
        flex: 1; min-width: 0; border: 0 !important; box-shadow: none !important; outline: none;
        padding: 14px 2px; background: transparent; color: #102a43; font-size: 14px;
      }
      .care-command-status, .care-command-error { margin-top: 12px; padding: 10px 12px; border-radius: 11px; font-size: 12px; }
      .care-command-status { background: #f0fdfa; color: #0f766e; border: 1px solid #ccfbf1; }
      .care-command-error { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; }
      .care-command-actions-grid { margin-top: 14px; padding: 12px; border-radius: 16px; background: linear-gradient(135deg, #f7fbfc, #ffffff); border: 1px solid #e2edf0; }
      .care-command-hint { color: #829ab1; font-size: 10px; font-weight: 700; }
      .care-command-tool-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; margin-top: 10px; }
      .care-command-tool { display: grid; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: 9px; width: 100%; min-width: 0; padding: 10px; border: 1px solid #e0ebee; border-radius: 12px; background: rgba(255,255,255,0.92); text-align: left; cursor: pointer; transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease; }
      .care-command-tool:hover { transform: translateY(-1px); border-color: #b7ddd8; box-shadow: 0 8px 18px rgba(16,42,67,0.06); }
      .care-command-tool-icon { width: 30px; height: 30px; display: grid; place-items: center; border-radius: 9px; background: #ecfdf9; color: #0f766e; }
      .care-command-tool-copy { display: grid; gap: 2px; min-width: 0; }
      .care-command-tool-copy strong { color: #102a43; font-size: 11px; }
      .care-command-tool-copy span { color: #627d98; font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .care-command-tool-arrow { width: 22px; height: 22px; display: grid; place-items: center; border-radius: 7px; background: #f0fdfa; color: #0f766e; font-size: 17px; }
      .care-command-recent { margin-top: 14px; padding: 12px; border-radius: 16px; background: linear-gradient(135deg, #f7fbfc, #ffffff); border: 1px solid #e2edf0; }
      .care-command-section-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 8px; color: #102a43; font-size: 12px; }
      .care-command-clear { border: 0; background: transparent; color: #0f766e; font-size: 11px; font-weight: 850; cursor: pointer; padding: 5px 7px; border-radius: 8px; }
      .care-command-clear:hover { background: #ecfeff; }
      .care-command-results { display: grid; gap: 7px; margin-top: 13px; }
      .care-command-result {
        width: 100%; display: grid; grid-template-columns: auto minmax(0,1fr) auto; gap: 11px; align-items: center;
        text-align: left; padding: 10px 11px; border-radius: 15px; border: 1px solid #e2e8f0;
        background: #fff; cursor: pointer; box-shadow: 0 6px 16px rgba(15,23,42,0.035);
      }
      .care-command-result:hover, .care-command-result.is-selected {
        border-color: rgba(20,184,166,0.34); background: linear-gradient(135deg, #f1fffc, #f8fcff);
        box-shadow: 0 11px 24px rgba(15,118,110,0.075);
      }
      .care-command-avatar { display: block; }
      .care-command-result-main { display: grid; gap: 3px; min-width: 0; }
      .care-command-result-main strong { color: #102a43; font-size: 13px; }
      .care-command-result-main span { color: #627d98; font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .care-command-arrow { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 9px; background: #eef8f7; color: #0f766e; font-size: 21px; }
      .care-command-detail {
        margin-top: 13px; padding: 13px; border-radius: 16px; border: 1px solid #bfece6;
        background: linear-gradient(135deg, rgba(239,252,250,0.96), rgba(239,247,255,0.96));
        box-shadow: 0 12px 28px rgba(8,127,120,0.08);
      }
      .care-command-detail-identity { display: flex; align-items: center; gap: 12px; min-width: 0; }
      .care-command-detail-identity > div:last-child { min-width: 0; }
      .care-command-detail-identity strong { display: block; margin-top: 3px; color: #102a43; font-size: 16px; }
      .care-command-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
      .care-command-primary, .care-command-secondary { padding: 9px 12px; border-radius: 10px; font-size: 11px; font-weight: 800; cursor: pointer; }
      .care-command-primary { border: 1px solid #087f78; background: linear-gradient(135deg,#087f78,#13a69d); color: #fff; box-shadow: 0 8px 18px rgba(8,127,120,0.15); }
      .care-command-secondary { border: 1px solid #d1e2e7; background: #fff; color: #334e68; }
      .care-command-empty { display: grid; justify-items: center; gap: 5px; padding: 28px 16px; margin-top: 12px; border: 1px dashed #cbd5e1; border-radius: 16px; background: #fbfdff; text-align: center; color: #334e68; }

      @media (max-width: 900px) {
        .care-clinical-selected { top: 72px !important; }
        .care-clinical-selected > div { grid-template-columns: auto minmax(0,1fr) !important; }
        .care-clinical-selected-actions { grid-column: 1 / -1; align-items: stretch; flex-direction: row; justify-content: space-between; }
      }
      @media (max-width: 640px) {
        .care-team-action-grid { grid-template-columns: 1fr; }
        .care-team-hero { flex-direction: column; }
        .care-team-hero-stat { width: 100%; }
        .care-search-row, .care-form-grid-2 { grid-template-columns: 1fr; }
        .care-topbar-tools { width: 100%; justify-content: flex-end; }
        .care-command-launcher { min-width: 0; flex: 1; justify-content: center; }
        .care-command-launcher > span:nth-child(2) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .care-command-launcher kbd { display: none; }
        .care-command-overlay { padding: 76px 10px 10px; }
        .care-command-dialog { border-radius: 18px; padding: 13px; max-height: calc(100vh - 86px); }
        .care-command-tool-grid { grid-template-columns: 1fr; }
        .care-command-tool-arrow { display: none; }
        .care-command-result { grid-template-columns: auto minmax(0,1fr); }
        .care-command-arrow { display: none; }
        .care-command-actions { display: grid; grid-template-columns: 1fr; }
        .care-command-actions button { width: 100%; }
        .care-patient-result { grid-template-columns: auto minmax(0,1fr); }
        .care-patient-result-arrow { display: none; }
        .care-patient-result-top { align-items: flex-start; }
        .care-patient-result-top strong { white-space: normal; }
        .care-clinical-selected { top: 66px !important; padding: 14px !important; }
        .care-clinical-selected-actions { grid-column: 1 / -1; flex-direction: column; align-items: stretch; }
        .care-clinical-selected-actions button { width: 100%; }
        .care-avatar-ring { padding: 3px; border-radius: 21px; }
        .care-table-person { min-width: 170px; }
      }


      .care-dashboard-page { display: grid; gap: 18px; }
      .care-team-page { display:grid; gap:20px; animation:careFadeUp 420ms ease both; }
      .care-team-hero { position:relative; overflow:hidden; display:flex; align-items:center; justify-content:space-between; gap:24px; padding:26px; border-radius:22px; background:linear-gradient(135deg,#effcfb 0%,#ffffff 58%,#eef8ff 100%); border:1px solid rgba(148,163,184,.14); box-shadow:0 18px 45px rgba(16,42,67,.075); }
      .care-team-hero::after { content:""; position:absolute; width:210px; height:210px; right:-90px; top:-110px; border-radius:50%; background:radial-gradient(circle,rgba(20,184,166,.16),transparent 68%); pointer-events:none; }
      .care-team-hero-stat { position:relative; z-index:1; min-width:150px; padding:16px 18px; border:1px solid rgba(148,163,184,.17); border-radius:18px; background:rgba(255,255,255,.78); box-shadow:0 12px 28px rgba(16,42,67,.07); backdrop-filter:blur(12px); text-align:center; }
      .care-team-stat-value { display:block; font-size:30px; line-height:1; font-weight:900; color:#0f766e; letter-spacing:-.04em; }
      .care-team-stat-label { display:block; margin-top:7px; font-size:11px; font-weight:800; color:#627d98; text-transform:uppercase; letter-spacing:.06em; }
      .care-team-action-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
      .care-team-action-card { display:flex; align-items:center; gap:12px; min-width:0; padding:16px; border:1px solid #e2e8f0; border-radius:17px; background:#fff; color:inherit; text-align:left; cursor:pointer; box-shadow:0 8px 22px rgba(16,42,67,.05); animation:careFadeUp 420ms ease both; transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease; }
      .care-team-action-card:hover { transform:translateY(-3px); box-shadow:0 15px 28px rgba(16,42,67,.09); border-color:rgba(20,184,166,.22); }
      .care-team-action-icon { flex:0 0 auto; width:38px; height:38px; display:grid; place-items:center; border-radius:12px; background:linear-gradient(135deg,#ccfbf1 0%,#e0f2fe 100%); color:#0f766e; }
      .care-team-action-copy { min-width:0; flex:1; }
      .care-team-action-copy strong { display:block; color:#102a43; font-size:13px; margin-bottom:4px; }
      .care-team-action-copy span { display:block; color:#627d98; font-size:11px; line-height:1.45; }
      .care-team-directory-panel { animation:careFadeUp 480ms ease both; }
      .care-team-section-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:20px; }
      .care-team-directory-badge { padding:8px 11px; border-radius:999px; border:1px solid #ccfbf1; background:#f0fdfa; color:#0f766e; font-size:11px; font-weight:850; white-space:nowrap; }
      .care-team-member-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }
      .care-team-member-card { padding:17px; border:1px solid #e2e8f0; border-radius:17px; background:linear-gradient(180deg,#ffffff 0%,#fbfdfe 100%); box-shadow:0 8px 20px rgba(16,42,67,.045); transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease; }
      .care-team-member-card:hover { transform:translateY(-2px); box-shadow:0 13px 26px rgba(16,42,67,.08); }
      .care-team-member-card.is-current { border-color:rgba(20,184,166,.28); box-shadow:0 12px 26px rgba(15,118,110,.08); }
      .care-team-member-top { display:flex; align-items:center; gap:12px; }
      .care-team-member-avatar { width:44px; height:44px; flex:0 0 auto; display:grid; place-items:center; border-radius:14px; background:linear-gradient(135deg,#0f766e 0%,#22c1b5 55%,#38bdf8 100%); color:#fff; font-size:14px; font-weight:900; box-shadow:0 10px 20px rgba(15,118,110,.15); }
      .care-team-member-name { font-size:15px; font-weight:850; color:#102a43; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .care-team-member-username { margin-top:4px; font-size:11px; color:#7b8da0; }
      .care-team-member-meta { display:flex; align-items:center; justify-content:space-between; gap:10px; margin:15px 0; padding-top:12px; border-top:1px solid #edf2f5; font-size:11px; color:#627d98; }
      .care-team-member-meta > span:first-child { display:inline-flex; align-items:center; gap:7px; font-weight:750; }
      .care-team-meta-dot { width:7px; height:7px; border-radius:50%; background:#10b981; box-shadow:0 0 0 4px rgba(16,185,129,.09); }
      .care-team-you-pill { padding:5px 8px; border-radius:999px; background:#eef8f7; color:#0f766e; font-weight:850; }
      .care-team-member-footer { display:flex; align-items:center; justify-content:space-between; gap:12px; font-size:10px; color:#7b8da0; }
      .care-team-member-footer button { border:0; background:transparent; padding:0; color:#0f766e; font-size:11px; font-weight:850; cursor:pointer; }
      .care-team-empty-state { display:grid; gap:6px; place-items:center; padding:36px 18px; border:1px dashed #cbd5e1; border-radius:15px; background:#f8fbfc; color:#627d98; text-align:center; font-size:13px; }
      .care-team-empty-state strong { color:#334e68; font-size:14px; }

      .care-dashboard-hero {
        position: relative; overflow: hidden; display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; flex-wrap: wrap;
        padding: 26px; border-radius: 24px;
        background: radial-gradient(circle at 100% 0%, rgba(56,189,248,0.16), transparent 30%), radial-gradient(circle at 0% 100%, rgba(45,212,191,0.16), transparent 34%), linear-gradient(135deg, #ffffff 0%, #f1fbfa 52%, #eff7ff 100%);
        border: 1px solid rgba(20,184,166,0.16); box-shadow: 0 20px 48px rgba(16,42,67,0.07);
        animation: careFadeUp 420ms ease both;
      }
      .care-dashboard-hero::after { content:""; position:absolute; width:180px; height:180px; right:-70px; top:-80px; border-radius:50%; background:radial-gradient(circle, rgba(20,184,166,0.18), transparent 68%); pointer-events:none; }
      .care-dashboard-title { position: relative; z-index:1; margin:5px 0 6px; color:#102a43; font-size:clamp(27px,3vw,38px); letter-spacing:-0.045em; line-height:1.08; }
      .care-dashboard-subtitle { position:relative; z-index:1; max-width:760px; margin:0; color:#627d98; font-size:14px; line-height:1.65; }
      .care-dashboard-hero-badge { position:relative; z-index:1; display:inline-flex; align-items:center; gap:8px; padding:9px 12px; border-radius:999px; background:rgba(255,255,255,0.78); border:1px solid rgba(148,163,184,0.19); color:#0f766e; font-size:11px; font-weight:850; box-shadow:0 8px 20px rgba(15,118,110,0.08); backdrop-filter:blur(10px); }
      .care-dashboard-hero-dot { width:8px; height:8px; border-radius:50%; background:#14b8a6; box-shadow:0 0 0 4px rgba(20,184,166,0.11); animation:carePulse 1.8s ease-in-out infinite; }
      .care-dashboard-quick-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
      .care-quick-card { min-width:0; display:grid; grid-template-columns:auto minmax(0,1fr) auto; align-items:center; gap:12px; padding:15px; border-radius:18px; text-decoration:none; color:inherit; background:linear-gradient(145deg,#fff,#f8fcfd); border:1px solid rgba(148,163,184,0.17); box-shadow:0 10px 26px rgba(16,42,67,0.05); animation:careFadeUp 420ms ease both; transition:transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease; }
      .care-quick-card:hover { transform:translateY(-3px); border-color:rgba(20,184,166,0.28); box-shadow:0 18px 34px rgba(15,23,42,0.09); }
      .care-quick-icon { width:38px; height:38px; display:grid; place-items:center; border-radius:12px; background:linear-gradient(135deg,#ccfbf1,#e0f2fe); color:#0f766e; box-shadow:0 8px 18px rgba(8,127,120,0.09); }
      .care-quick-copy { min-width:0; display:grid; gap:4px; }
      .care-quick-copy strong { color:#102a43; font-size:13px; }
      .care-quick-copy span { color:#627d98; font-size:11px; line-height:1.4; }
      .care-quick-arrow { color:#0f766e; transition:transform 160ms ease; }
      .care-quick-card:hover .care-quick-arrow { transform:translateX(3px); }
      .care-dashboard-summary { display:flex; align-items:center; justify-content:space-between; gap:18px; flex-wrap:wrap; }
      .care-dashboard-summary-pills { display:flex; flex-wrap:wrap; gap:8px; }
      .care-dashboard-summary-pills span { padding:8px 10px; border-radius:999px; background:#f6fbfb; border:1px solid #dfeeee; color:#627d98; font-size:11px; }
      .care-dashboard-summary-pills strong { color:#0f766e; margin-right:4px; }
      .care-account-overview { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
      .care-account-stat { position:relative; overflow:hidden; display:grid; gap:4px; padding:16px; border-radius:18px; background:linear-gradient(145deg,#fff,#f8fbfc); border:1px solid rgba(148,163,184,0.17); box-shadow:0 10px 26px rgba(16,42,67,0.05); animation:careFadeUp 420ms ease both; }
      .care-account-stat::before { content:""; position:absolute; inset:0 auto 0 0; width:4px; background:linear-gradient(180deg,#0f766e,#38bdf8); }
      .care-account-stat span { color:#627d98; font-size:10px; font-weight:850; text-transform:uppercase; letter-spacing:.08em; }
      .care-account-stat strong { color:#102a43; font-size:27px; line-height:1; letter-spacing:-.04em; }
      .care-account-stat small { color:#7b8fa3; font-size:11px; }
      .care-account-stat-positive::before { background:linear-gradient(180deg,#10b981,#5eead4); }
      .care-account-stat-info::before { background:linear-gradient(180deg,#38bdf8,#60a5fa); }
      .care-account-stat-patient::before { background:linear-gradient(180deg,#a78bfa,#c084fc); }
      .care-account-panel { animation:careFadeUp 480ms ease both; }
      .care-account-panel table tbody tr:hover { background:linear-gradient(90deg,#f6fbfb,#ffffff); }
      .care-content { position:relative; overflow:hidden; }
      .care-content::before { content:""; position:absolute; width:420px; height:420px; right:-220px; top:60px; border-radius:50%; background:radial-gradient(circle, rgba(56,189,248,0.06), transparent 68%); pointer-events:none; z-index:0; }
      .care-content > * { position:relative; z-index:1; }
      .care-topbar { min-height:76px; box-shadow:0 7px 26px rgba(16,42,67,0.045); }
      .care-topbar-context { min-width:0; }
      .care-topbar-title { font-size:13px; font-weight:850; letter-spacing:-0.01em; color:#102a43; }
      .care-topbar-subtitle { margin-top:2px; font-size:10px; color:#8aa0b3; }
      .care-topbar .care-user-name { max-width:230px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .care-sidebar { box-shadow:12px 0 36px rgba(7,59,76,0.16) !important; }
      .care-brand-block { position:relative; }
      .care-brand-mark { box-shadow:0 12px 26px rgba(102,227,213,0.18); }
      .care-nav-label { opacity:.68; }
      .care-sidebar-footer { box-shadow:inset 0 1px 0 rgba(255,255,255,.08); }
      .care-nav-link { position:relative; overflow:hidden; }
      .care-nav-link::before { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:linear-gradient(180deg,#66e3d5,#7dd3fc); transform:scaleY(0); transform-origin:center; transition:transform 180ms ease; }
      .care-nav-link.is-active::before { transform:scaleY(1); }
      .care-glass-panel { border:1px solid rgba(255,255,255,.72) !important; box-shadow:0 20px 46px rgba(16,42,67,0.075) !important; }
      .care-patient-result:focus-visible, .care-quick-card:focus-visible, .care-nav-link:focus-visible { outline:3px solid rgba(45,212,191,.22); outline-offset:2px; }
      .care-user-avatar, .care-profile-avatar { box-shadow:0 12px 26px rgba(8,127,120,.18); }
      .care-table-person > div:last-child > div:first-child { letter-spacing:-0.01em; }
      ::selection { background:rgba(45,212,191,.22); color:#073b4c; }
      ::-webkit-scrollbar { width:10px; height:10px; }
      ::-webkit-scrollbar-track { background:#eef4f6; }
      ::-webkit-scrollbar-thumb { background:#c4d7dd; border-radius:999px; border:2px solid #eef4f6; }
      ::-webkit-scrollbar-thumb:hover { background:#9fbac4; }

      .care-dashboard-hero-visual { position:relative; z-index:1; display:grid; justify-items:center; gap:10px; min-width:150px; }
      .care-3d-logo-wrap { position:relative; width:138px; height:132px; display:grid; place-items:center; perspective:700px; transform-style:preserve-3d; }
      .care-3d-logo-core { width:74px; height:74px; border-radius:24px; display:grid; place-items:center; background:linear-gradient(145deg,#083b4c,#0f766e 58%,#22c1b5); box-shadow:0 24px 36px rgba(8,127,120,.25), inset 5px 5px 14px rgba(255,255,255,.26), inset -7px -8px 14px rgba(4,54,64,.26); transform:rotateX(14deg) rotateY(-20deg); animation:care3dFloat 4.8s ease-in-out infinite; }
      .care-3d-logo-core span { color:#fff; font-weight:950; font-size:22px; letter-spacing:-.08em; text-shadow:0 4px 12px rgba(0,0,0,.24); transform:translateZ(18px); }
      .care-3d-logo-orbit { position:absolute; border:1px solid rgba(15,118,110,.23); border-radius:50%; transform-style:preserve-3d; pointer-events:none; }
      .care-3d-orbit-a { width:118px; height:42px; transform:rotateX(63deg) rotateZ(-18deg); animation:care3dSpinA 7s linear infinite; }
      .care-3d-orbit-b { width:96px; height:96px; transform:rotateY(68deg) rotateZ(25deg); border-color:rgba(56,189,248,.22); animation:care3dSpinB 8.5s linear infinite reverse; }
      .care-3d-orbit-a::after, .care-3d-orbit-b::after { content:""; position:absolute; width:7px; height:7px; border-radius:50%; top:50%; left:50%; box-shadow:0 0 0 5px rgba(20,184,166,.09), 0 7px 18px rgba(8,127,120,.15); }
      .care-3d-orbit-a::after { transform:translate(-50%,-50%) translateX(58px); background:#14b8a6; }
      .care-3d-orbit-b::after { transform:translate(-50%,-50%) translateX(48px); background:#38bdf8; }
      .care-3d-logo-caption { position:absolute; bottom:-2px; font-size:10px; font-weight:900; letter-spacing:.12em; text-transform:uppercase; color:#0f766e; text-shadow:0 3px 10px rgba(8,127,120,.09); }
      @keyframes care3dFloat { 0%,100% { transform:rotateX(14deg) rotateY(-20deg) translateY(0) translateZ(0); } 50% { transform:rotateX(18deg) rotateY(14deg) translateY(-6px) translateZ(8px); } }
      @keyframes care3dSpinA { from { transform:rotateX(63deg) rotateZ(-18deg); } to { transform:rotateX(63deg) rotateZ(342deg); } }
      @keyframes care3dSpinB { from { transform:rotateY(68deg) rotateZ(25deg); } to { transform:rotateY(68deg) rotateZ(385deg); } }
      @media (prefers-reduced-motion: reduce) { .care-3d-logo-core, .care-3d-orbit-a, .care-3d-orbit-b { animation:none !important; } }

      @media (max-width: 900px) {
        .care-dashboard-quick-grid { grid-template-columns: 1fr; }
        .care-account-overview { grid-template-columns: repeat(2, minmax(0,1fr)); }
      }
      @media (max-width: 640px) {
        .care-dashboard-hero { padding: 20px; }
        .care-team-action-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
        .care-team-hero { padding: 20px; align-items: flex-start; }
        .care-team-hero-stat { min-width: 120px; }
        .care-dashboard-hero-visual { width:100%; justify-items:start; grid-template-columns:auto auto; align-items:center; }
        .care-dashboard-title { font-size: 27px; }
        .care-dashboard-summary { align-items: flex-start; }
        .care-dashboard-summary-pills { width: 100%; }
        .care-account-overview { grid-template-columns: 1fr; }
      }

      .care-patient-portal, .care-reports-page, .care-registration-page { animation: careFadeUp 420ms ease both; }
      .care-patient-portal > section, .care-reports-page > section { position: relative; overflow: hidden; }
      .care-patient-portal > section, .care-reports-page > section, .care-registration-page > div { transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease; }
      .care-patient-portal > section:hover, .care-reports-page > section:hover { box-shadow: 0 18px 42px rgba(16,42,67,0.075) !important; }
      .care-photo-upload-button { display:inline-flex; align-items:center; gap:7px; cursor:pointer; border:1px solid rgba(148,163,184,0.18); border-radius:11px; padding:9px 12px; color:#0f766e; font-size:12px; font-weight:800; box-shadow:0 8px 18px rgba(16,42,67,0.06); transition:transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease; }
      .care-photo-upload-button:hover { transform:translateY(-2px); border-color:rgba(20,184,166,0.32); box-shadow:0 12px 24px rgba(16,42,67,0.09); }
      .care-patient-avatar { flex:0 0 auto; }
      @media (max-width: 640px) {
        .care-dashboard-hero { align-items:flex-start; }
        .care-reports-page form { width:100%; }
      }

      .care-analytics-card { background:linear-gradient(145deg,rgba(255,255,255,0.98),rgba(247,252,252,0.95)); }
      .care-analytics-heading { display:flex; justify-content:space-between; gap:16px; align-items:flex-end; flex-wrap:wrap; margin-bottom:14px; }
      .care-analytics-note { color:#64748b; font-size:11px; font-weight:700; }
      .care-analytics-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
      .care-analytics-metric { padding:14px; border:1px solid rgba(148,163,184,0.15); border-radius:14px; background:#fff; box-shadow:0 8px 20px rgba(15,23,42,0.035); animation:careFadeUp 360ms ease both; }
      .care-analytics-metric-top { display:flex; justify-content:space-between; gap:12px; align-items:center; }
      .care-analytics-metric-top span { color:#64748b; font-size:11px; font-weight:800; }
      .care-analytics-metric-top strong { color:#0f766e; font-size:20px; letter-spacing:-.03em; }
      .care-analytics-track { height:7px; overflow:hidden; margin:11px 0 7px; border-radius:999px; background:#eaf1f4; }
      .care-analytics-track span { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,#0f766e,#38bdf8); transition:width 450ms ease; }
      .care-analytics-metric small { color:#7b8da1; font-size:10px; }
      .care-workspace-frame { display:grid; gap:16px; animation:careFadeUp 420ms ease both; }
      .care-workspace-hero { position:relative; overflow:hidden; display:flex; justify-content:space-between; gap:18px; align-items:center; flex-wrap:wrap; padding:22px 24px; border:1px solid rgba(20,184,166,0.15); border-radius:22px; background:linear-gradient(135deg,#ecfeff 0%,#ffffff 58%,#eff6ff 100%); box-shadow:0 18px 44px rgba(15,118,110,0.08); }
      .care-workspace-hero::after { content:""; position:absolute; width:220px; height:220px; right:-80px; top:-100px; border-radius:50%; background:rgba(56,189,248,0.10); pointer-events:none; }
      .care-workspace-hero-main { display:flex; align-items:center; gap:14px; min-width:0; position:relative; z-index:1; }
      .care-workspace-icon { width:46px; height:46px; flex:0 0 auto; display:grid; place-items:center; border-radius:15px; background:linear-gradient(135deg,#ccfbf1,#dbeafe); color:#0f766e; box-shadow:0 10px 24px rgba(14,165,164,0.12); }
      .care-workspace-title { margin:4px 0 5px; color:#102a43; font-size:clamp(23px,3vw,31px); letter-spacing:-.035em; }
      .care-workspace-description { margin:0; max-width:820px; color:#627d98; font-size:13px; line-height:1.6; }
      .care-workspace-status { display:inline-flex; align-items:center; gap:8px; padding:8px 11px; border-radius:999px; background:rgba(255,255,255,0.82); border:1px solid rgba(148,163,184,0.18); color:#0f766e; font-size:11px; font-weight:800; box-shadow:0 8px 20px rgba(15,23,42,0.05); position:relative; z-index:1; }
      .care-workspace-pulse { padding:16px; border-radius:18px; border:1px solid rgba(148,163,184,0.16); background:rgba(255,255,255,0.90); box-shadow:0 12px 30px rgba(15,23,42,0.045); }
      .care-workspace-pulse-heading { display:flex; justify-content:space-between; gap:16px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }
      .care-workspace-pulse-note { color:#64748b; font-size:11px; font-weight:700; }
      .care-workspace-pulse-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }
      .care-workspace-pulse-card { padding:13px; border-radius:14px; background:linear-gradient(145deg,#ffffff,#f7fbfc); border:1px solid rgba(148,163,184,0.15); box-shadow:0 8px 20px rgba(15,23,42,0.035); animation:careFadeUp 360ms ease both; }
      .care-workspace-pulse-card span { display:block; color:#64748b; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; }
      .care-workspace-pulse-card strong { display:block; margin-top:5px; color:#102a43; font-size:23px; letter-spacing:-.03em; }
      .care-workspace-pulse-card small { display:block; margin-top:3px; color:#7b8da1; font-size:10px; }
      .care-workspace-link-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:9px; }
      .care-workspace-link { min-width:0; display:flex; align-items:center; gap:8px; justify-content:flex-start; padding:10px 11px; border:1px solid rgba(148,163,184,0.16); border-radius:12px; background:#fff; color:#334e68; font-size:12px; font-weight:800; cursor:pointer; box-shadow:0 7px 18px rgba(15,23,42,0.035); }
      .care-workspace-link:hover { border-color:rgba(20,184,166,0.28); background:#f8fffe; transform:translateY(-2px); box-shadow:0 12px 24px rgba(15,23,42,0.07); }
      .care-workspace-link-icon { width:28px; height:28px; display:grid; place-items:center; flex:0 0 auto; border-radius:9px; background:#eff6ff; color:#2563eb; }
      .care-workspace-link > svg { margin-left:auto; color:#94a3b8; }
      .care-workspace-content { min-width:0; }
      .care-user-profile-drawer { margin-top:16px; background:linear-gradient(145deg,#ffffff,#f7fbff); animation:careFadeUp 320ms ease both; }
      .care-user-profile-header { display:flex; justify-content:space-between; gap:14px; align-items:center; flex-wrap:wrap; }
      .care-user-profile-body { display:grid; grid-template-columns:minmax(0,1fr) minmax(280px,1.15fr); gap:18px; margin-top:16px; padding-top:16px; border-top:1px solid #e2e8f0; }
      .care-user-profile-identity { display:flex; align-items:center; gap:14px; min-width:0; }
      .care-user-avatar-large { width:78px !important; height:78px !important; border-radius:22px !important; font-size:25px !important; }
      .care-account-chip { display:inline-flex; align-items:center; padding:6px 9px; border-radius:999px; background:#f0fdfa; border:1px solid #ccfbf1; color:#0f766e; font-size:11px; font-weight:800; }
      .care-user-detail-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }
      .care-user-detail-grid > div { padding:11px 12px; border-radius:12px; background:#fff; border:1px solid rgba(148,163,184,0.14); }
      .care-user-detail-grid span { display:block; color:#64748b; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.05em; }
      .care-user-detail-grid strong { display:block; margin-top:4px; color:#334e68; font-size:12px; line-height:1.4; word-break:break-word; }
      @media (max-width:900px) { .care-workspace-pulse-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .care-workspace-link-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .care-user-profile-body { grid-template-columns:1fr; } .care-analytics-grid { grid-template-columns:1fr; } }
      @media (max-width:600px) { .care-workspace-pulse-grid,.care-workspace-link-grid,.care-user-detail-grid { grid-template-columns:1fr; } .care-workspace-hero { padding:18px; } }

      @media (prefers-reduced-motion: reduce) {
        html { scroll-behavior: auto; }
        *, *::before, *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      }
    `}</style>
  );
}


const CareSpherePatientProfileStyles = () => (
  <style>{`
    .care-profile-page {
      animation: careFadeUp 420ms ease both;
    }
    .care-profile-hero {
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(13, 148, 136, 0.14);
      box-shadow: 0 18px 45px rgba(15, 118, 110, 0.10);
    }
    .care-profile-hero::after {
      content: "";
      position: absolute;
      width: 220px;
      height: 220px;
      right: -70px;
      top: -90px;
      border-radius: 50%;
      background: rgba(45, 212, 191, 0.13);
      pointer-events: none;
    }
    .care-profile-avatar {
      flex: 0 0 auto;
      width: 76px;
      height: 76px;
      border-radius: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 25px;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #0f766e 0%, #0ea5a4 52%, #38bdf8 100%);
      box-shadow: 0 14px 30px rgba(14, 165, 164, 0.24);
    }
    .care-profile-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .care-profile-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(248, 250, 252, 0.88);
      border: 1px solid rgba(148, 163, 184, 0.22);
      color: #475569;
      font-size: 12px;
      font-weight: 700;
    }
    .care-profile-status {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      text-transform: capitalize;
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.07);
    }
    .care-profile-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
      animation: carePulse 1.8s ease-in-out infinite;
    }
    .care-profile-card {
      animation: careFadeUp 480ms ease both;
      transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }
    .care-profile-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
      border-color: rgba(20, 184, 166, 0.22);
    }
    .care-profile-field {
      padding: 12px 13px;
      border-radius: 12px;
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
      border: 1px solid rgba(148, 163, 184, 0.15);
    }
    .care-profile-summary {
      position: relative;
      overflow: hidden;
      padding: 18px;
      border-radius: 16px;
      background: linear-gradient(145deg, #ffffff 0%, #f5fbfb 100%);
      border: 1px solid rgba(148, 163, 184, 0.17);
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
      transition: transform 180ms ease, box-shadow 180ms ease;
    }
    .care-profile-summary:hover {
      transform: translateY(-4px);
      box-shadow: 0 15px 30px rgba(15, 23, 42, 0.09);
    }
    .care-profile-summary::before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background: linear-gradient(180deg, #0f766e, #38bdf8);
    }
    .care-profile-summary-icon {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #ecfeff;
      color: #0f766e;
      font-size: 15px;
      margin-bottom: 12px;
    }
    @media (max-width: 700px) {
      .care-profile-avatar {
        width: 62px;
        height: 62px;
        border-radius: 18px;
        font-size: 21px;
      }
      .care-profile-hero-actions {
        width: 100%;
      }
      .care-profile-hero-actions button {
        flex: 1;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .care-profile-page,
      .care-profile-card {
        animation: none !important;
      }
      .care-profile-status-dot {
        animation: none !important;
      }
      .care-profile-card,
      .care-profile-summary {
        transition: none !important;
      }
    }
  `}</style>
);

function App() {
  return (
    <>
      <CareSphereGlobalStyles />
      <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register/patient" element={<PatientRegistration />} />

          <Route
            path="/*"
            element={<ProtectedLayout />}
          />
        </Routes>
      </BrowserRouter>
      </AuthProvider>
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: "100vh",
    display: "flex",
    background:
      "radial-gradient(circle at 10% 0%, rgba(29,185,177,0.08), transparent 28%), #f4f8fb",
    color: "#102a43",
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },

  sidebar: {
    width: "252px",
    minHeight: "100vh",
    background:
      "linear-gradient(180deg, #073b4c 0%, #075e62 52%, #087f78 100%)",
    color: "#ffffff",
    padding: "26px 16px",
    boxShadow: "10px 0 35px rgba(7,59,76,0.12)",
    position: "sticky",
    top: 0,
    alignSelf: "flex-start",
  },

  logo: {
    fontSize: "23px",
    fontWeight: 800,
    letterSpacing: "-0.03em",
    marginBottom: "42px",
    padding: "0 10px",
  },

  navItem: {
    display: "block",
    padding: "12px 14px",
    marginBottom: "7px",
    borderRadius: "12px",
    color: "rgba(255,255,255,0.74)",
    textDecoration: "none",
    fontSize: "14px",
    fontWeight: 600,
  },

  activeNav: {
    background: "rgba(255,255,255,0.15)",
    color: "#ffffff",
    fontWeight: 750,
    boxShadow: "inset 3px 0 0 #66e3d5, 0 8px 24px rgba(0,0,0,0.08)",
  },

  main: { flex: 1, minWidth: 0 },

  header: {
    background: "rgba(255,255,255,0.88)",
    borderBottom: "1px solid rgba(148,163,184,0.18)",
    padding: "18px 32px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    position: "sticky",
    top: 0,
    zIndex: 10,
    backdropFilter: "blur(16px)",
  },

  headerBrand: {
    fontSize: "18px",
    fontWeight: 800,
    letterSpacing: "-0.02em",
    color: "#0b5960",
  },

  status: {
    display: "flex",
    alignItems: "center",
    gap: "9px",
    color: "#496273",
    fontSize: "14px",
    fontWeight: 600,
  },

  dot: {
    width: "9px",
    height: "9px",
    borderRadius: "50%",
    background: "#18b99a",
    boxShadow: "0 0 0 5px rgba(24,185,154,0.12)",
    animation: "carePulse 2.4s ease-in-out infinite",
  },

  content: {
    padding: "34px",
    animation: "careFadeIn 420ms ease both",
  },

  title: {
    margin: 0,
    fontSize: "31px",
    lineHeight: 1.15,
    fontWeight: 800,
    letterSpacing: "-0.035em",
    color: "#102a43",
  },

  subtitle: {
    margin: "8px 0 28px",
    color: "#627d98",
    fontSize: "15px",
    lineHeight: 1.6,
  },

  cards: {
    display: "grid",
    gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
    gap: "18px",
    marginBottom: "28px",
  },

  card: {
    background:
      "linear-gradient(145deg, rgba(255,255,255,0.98), rgba(247,252,252,0.96))",
    border: "1px solid rgba(148,163,184,0.17)",
    borderRadius: "18px",
    padding: "22px",
    boxShadow: "0 12px 34px rgba(16,42,67,0.07)",
    animation: "careFadeUp 480ms ease both",
    transition: "transform 180ms ease, box-shadow 180ms ease",
  },

  cardTitle: {
    margin: 0,
    color: "#627d98",
    fontSize: "13px",
    fontWeight: 700,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },

  cardValue: {
    display: "block",
    marginTop: "10px",
    fontSize: "31px",
    lineHeight: 1,
    fontWeight: 800,
    color: "#087f78",
    letterSpacing: "-0.035em",
  },

  panel: {
    background: "rgba(255,255,255,0.94)",
    border: "1px solid rgba(148,163,184,0.18)",
    borderRadius: "20px",
    padding: "28px",
    boxShadow: "0 14px 42px rgba(16,42,67,0.065)",
    animation: "careFadeUp 500ms ease both",
  },

  muted: { color: "#627d98" },

  searchForm: {
    display: "flex",
    gap: "12px",
    marginBottom: "24px",
  },

  searchInput: {
    flex: 1,
    padding: "12px 14px",
    border: "1px solid #d4e0e7",
    borderRadius: "12px",
    background: "#fbfdfe",
    color: "#102a43",
    fontSize: "14px",
    outline: "none",
    boxShadow: "inset 0 1px 2px rgba(16,42,67,0.025)",
  },

  searchButton: {
    padding: "12px 20px",
    border: "1px solid #087f78",
    borderRadius: "12px",
    background: "linear-gradient(135deg, #087f78 0%, #13a69d 100%)",
    color: "#ffffff",
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 8px 20px rgba(8,127,120,0.18)",
  },

  tableWrapper: {
    overflowX: "auto",
    border: "1px solid rgba(148,163,184,0.16)",
    borderRadius: "15px",
  },

  table: { width: "100%", borderCollapse: "collapse" },

  th: {
    textAlign: "left",
    padding: "13px 14px",
    borderBottom: "1px solid #e4edf2",
    background: "#f7fafb",
    fontSize: "12px",
    fontWeight: 800,
    color: "#627d98",
    textTransform: "uppercase",
    letterSpacing: "0.045em",
  },

  td: {
    padding: "15px 14px",
    borderBottom: "1px solid #edf2f5",
    fontSize: "14px",
    color: "#334e68",
  },

  loginPage: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    background:
      "radial-gradient(circle at 15% 20%, rgba(38,197,187,0.22), transparent 28%), radial-gradient(circle at 85% 80%, rgba(111,168,255,0.16), transparent 30%), linear-gradient(135deg, #edf9f8 0%, #f6f9fc 55%, #eef4fb 100%)",
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },

  loginCard: {
    width: "min(420px, 100%)",
    background: "rgba(255,255,255,0.92)",
    border: "1px solid rgba(255,255,255,0.9)",
    borderRadius: "24px",
    padding: "40px",
    boxShadow: "0 28px 70px rgba(16,42,67,0.13)",
    backdropFilter: "blur(18px)",
    animation: "careFadeUp 550ms ease both",
  },

  loginBrandRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "16px",
  },

  loginSecureBadge: {
    padding: "7px 10px",
    borderRadius: "999px",
    background: "#ecfeff",
    color: "#0f766e",
    fontSize: "11px",
    fontWeight: 800,
    whiteSpace: "nowrap",
  },

  roleGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))",
    gap: "10px",
    marginBottom: "16px",
  },

  roleCard: {
    minWidth: 0,
    minHeight: "150px",
    padding: "15px 12px",
    borderRadius: "16px",
    border: "1px solid #d8e5ea",
    background: "#ffffff",
    cursor: "pointer",
    textAlign: "left",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    boxShadow: "0 5px 15px rgba(16,42,67,0.045)",
  },

  roleCardActive: {
    border: "1px solid rgba(8,127,120,0.48)",
    background: "linear-gradient(180deg, #f0fffc 0%, #ffffff 100%)",
    boxShadow: "0 12px 28px rgba(8,127,120,0.12)",
  },

  roleIcon: {
    width: "34px",
    height: "34px",
    borderRadius: "10px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    background: "linear-gradient(135deg, #ccfbf1 0%, #e0f2fe 100%)",
    color: "#0f766e",
    fontSize: "17px",
    marginBottom: "10px",
  },

  roleTitle: {
    display: "block",
    fontSize: "14px",
    fontWeight: 800,
    color: "#102a43",
    marginBottom: "5px",
  },

  roleDescription: {
    display: "block",
    fontSize: "11px",
    lineHeight: 1.45,
    color: "#627d98",
  },

  loginSelectedRole: {
    padding: "10px 12px",
    borderRadius: "11px",
    background: "#f6fbfb",
    border: "1px solid #e0ecef",
    fontSize: "12px",
    color: "#627d98",
    marginBottom: "4px",
  },

  sidebarRoleBadge: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    margin: "-26px 10px 24px",
    padding: "9px 11px",
    borderRadius: "11px",
    background: "rgba(255,255,255,0.1)",
    color: "rgba(255,255,255,0.82)",
    fontSize: "11px",
    fontWeight: 750,
  },

  sidebarRoleDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    background: "#66e3d5",
    boxShadow: "0 0 0 4px rgba(102,227,213,0.12)",
  },

  headerRolePill: {
    padding: "5px 9px",
    borderRadius: "999px",
    background: "#eef8f7",
    color: "#0f766e",
    fontSize: "11px",
    fontWeight: 800,
  },

  loginLogo: {
    margin: 0,
    fontSize: "34px",
    lineHeight: 1,
    fontWeight: 850,
    letterSpacing: "-0.045em",
    color: "#087f78",
  },

  loginSubtitle: {
    color: "#627d98",
    margin: "12px 0 30px",
    lineHeight: 1.55,
  },

  label: {
    display: "block",
    marginBottom: "8px",
    marginTop: "18px",
    fontSize: "13px",
    fontWeight: 750,
    color: "#334e68",
  },

  input: {
    width: "100%",
    boxSizing: "border-box",
    padding: "13px 14px",
    border: "1px solid #d4e0e7",
    borderRadius: "12px",
    background: "#fbfdfe",
    color: "#102a43",
    fontSize: "14px",
    outline: "none",
  },

  loginButton: {
    width: "100%",
    marginTop: "24px",
    padding: "13px",
    border: "1px solid #087f78",
    borderRadius: "12px",
    background: "linear-gradient(135deg, #087f78 0%, #13a69d 100%)",
    color: "#ffffff",
    fontSize: "15px",
    fontWeight: 750,
    cursor: "pointer",
    boxShadow: "0 10px 25px rgba(8,127,120,0.2)",
  },

  error: {
    marginTop: "16px",
    padding: "12px 14px",
    borderRadius: "12px",
    background: "#fff5f5",
    border: "1px solid #ffd6d6",
    color: "#b42318",
    fontSize: "14px",
  },

  logoutButton: {
    marginLeft: "12px",
    padding: "8px 13px",
    border: "1px solid #d4e0e7",
    borderRadius: "10px",
    background: "#ffffff",
    color: "#334e68",
    fontSize: "13px",
    fontWeight: 700,
    cursor: "pointer",
  },
};
export default App;