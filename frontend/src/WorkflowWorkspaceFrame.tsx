import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "./auth/AuthContext";
import { useNavigate } from "react-router-dom";
import { getDashboardSummary, type DashboardSummary } from "./api/dashboard";
import { listUsers, type CareUser } from "./api/users";
import Icon from "./components/ui/Icon";

type WorkspaceModule = "care-gaps" | "follow-ups" | "notifications" | "audit-logs" | "users";

interface WorkflowWorkspaceFrameProps {
  module: WorkspaceModule;
  children: React.ReactNode;
}

const moduleConfig: Record<WorkspaceModule, {
  eyebrow: string;
  title: string;
  description: string;
  icon: "activity" | "calendar" | "bell" | "shield" | "users";
}> = {
  "care-gaps": {
    eyebrow: "Care operations",
    title: "Care Gap Intelligence",
    description: "Surface unresolved care needs, organize attention, and move from signal to review without changing the underlying care-gap workflow.",
    icon: "activity",
  },
  "follow-ups": {
    eyebrow: "Care coordination",
    title: "Follow-up Workspace",
    description: "Keep upcoming, pending, and completed follow-up activity in one operational view while preserving the existing follow-up actions.",
    icon: "calendar",
  },
  "notifications": {
    eyebrow: "Communication center",
    title: "Notification Center",
    description: "Bring system and clinical notifications into a clearer workspace with stronger prioritization and quick navigation.",
    icon: "bell",
  },
  "audit-logs": {
    eyebrow: "Governance",
    title: "Audit & Activity Explorer",
    description: "Review system activity with a dedicated governance frame while keeping the existing audit records and filters authoritative.",
    icon: "shield",
  },
  users: {
    eyebrow: "Administration",
    title: "Account Administration",
    description: "Manage CareSphere accounts with a clearer governance overview and richer user context without changing the existing account controls.",
    icon: "users",
  },
};

const quickLinks: Array<{ key: WorkspaceModule; label: string; icon: "activity" | "calendar" | "bell" | "shield" | "users" }> = [
  { key: "care-gaps", label: "Care Gaps", icon: "activity" },
  { key: "follow-ups", label: "Follow-ups", icon: "calendar" },
  { key: "notifications", label: "Notifications", icon: "bell" },
  { key: "audit-logs", label: "Audit Logs", icon: "shield" },
  { key: "users", label: "User Management", icon: "users" },
];

export default function WorkflowWorkspaceFrame({ module, children }: WorkflowWorkspaceFrameProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [users, setUsers] = useState<CareUser[]>([]);
  const [loadingPulse, setLoadingPulse] = useState(true);
  const config = moduleConfig[module];

  useEffect(() => {
    let active = true;
    const loadPulse = async () => {
      setLoadingPulse(true);
      try {
        if (module === "users" && user?.role === "administrator") {
          const rows = await listUsers({ limit: 100 });
          if (active) setUsers(rows);
        } else {
          const data = await getDashboardSummary();
          if (active) setSummary(data);
        }
      } catch {
        // The wrapped workflow remains authoritative; this pulse is supplemental UX only.
      } finally {
        if (active) setLoadingPulse(false);
      }
    };
    void loadPulse();
    return () => {
      active = false;
    };
  }, [module, user?.role]);

  const pulse = useMemo(() => {
    if (module === "users") {
      return [
        { label: "Accounts", value: users.length, detail: "shown in workspace" },
        { label: "Active", value: users.filter((item) => item.status === "active").length, detail: "enabled accounts" },
        { label: "Clinicians", value: users.filter((item) => item.role === "clinician").length, detail: "clinical access" },
        { label: "Patients", value: users.filter((item) => item.role === "patient").length, detail: "portal accounts" },
      ];
    }

    if (!summary) return [];

    if (module === "care-gaps") {
      return [
        { label: "Health concerns", value: summary.health_concerns, detail: "documented concerns" },
        { label: "Recommendations", value: summary.recommendations, detail: "existing recommendations" },
        { label: "Pending reviews", value: summary.clinician_reviews.pending, detail: "awaiting review" },
        { label: "Active patients", value: summary.patients.active, detail: "currently active" },
      ];
    }

    if (module === "follow-ups") {
      return [
        { label: "Active patients", value: summary.patients.active, detail: "current care population" },
        { label: "Assessments", value: summary.assessments.total, detail: "documented assessments" },
        { label: "Pending reviews", value: summary.clinician_reviews.pending, detail: "requiring attention" },
        { label: "Reports", value: summary.reports, detail: "generated reports" },
      ];
    }

    if (module === "notifications") {
      return [
        { label: "Pending reviews", value: summary.clinician_reviews.pending, detail: "review signals" },
        { label: "Recommendations", value: summary.recommendations, detail: "care signals" },
        { label: "Reports", value: summary.reports, detail: "document outputs" },
        { label: "Patients", value: summary.patients.total, detail: "records in scope" },
      ];
    }

    return [
      { label: "Patients", value: summary.patients.total, detail: "records in scope" },
      { label: "Assessments", value: summary.assessments.total, detail: "documented" },
      { label: "Reports", value: summary.reports, detail: "generated" },
      { label: "Reviews", value: summary.clinician_reviews.total, detail: "clinical review events" },
    ];
  }, [module, summary, users]);

  const relevantLinks = quickLinks.filter((item) => {
    if (item.key === "users" && user?.role !== "administrator") return false;
    if (item.key === "audit-logs" && user?.role !== "administrator") return false;
    return item.key !== module;
  }).slice(0, 4);

  return (
    <div className="care-workspace-frame">
      <section className="care-workspace-hero">
        <div className="care-workspace-hero-main">
          <div className="care-workspace-icon"><Icon name={config.icon} size={21} /></div>
          <div>
            <div className="care-section-kicker">{config.eyebrow}</div>
            <h1 className="care-workspace-title">{config.title}</h1>
            <p className="care-workspace-description">{config.description}</p>
          </div>
        </div>
        <div className="care-workspace-status">
          <span className="care-dashboard-hero-dot" />
          Workspace active
        </div>
      </section>

      <section className="care-workspace-pulse" aria-label="System pulse">
        <div className="care-workspace-pulse-heading">
          <div>
            <div className="care-section-kicker">System pulse</div>
            <strong>Current CareSphere context</strong>
          </div>
          <span className="care-workspace-pulse-note">{loadingPulse ? "Refreshing…" : "Live from existing system data"}</span>
        </div>
        <div className="care-workspace-pulse-grid">
          {(pulse.length ? pulse : [
            { label: "Loading", value: "—", detail: "refreshing context" },
            { label: "Loading", value: "—", detail: "refreshing context" },
            { label: "Loading", value: "—", detail: "refreshing context" },
            { label: "Loading", value: "—", detail: "refreshing context" },
          ]).map((item, index) => (
            <div key={`${item.label}-${index}`} className="care-workspace-pulse-card" style={{ animationDelay: `${index * 55}ms` }}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <small>{item.detail}</small>
            </div>
          ))}
        </div>
      </section>

      {relevantLinks.length > 0 && (
        <nav className="care-workspace-link-grid" aria-label="Related workspaces">
          {relevantLinks.map((item) => (
            <button key={item.key} type="button" className="care-workspace-link" onClick={() => navigate(`/${item.key}`)}>
              <span className="care-workspace-link-icon"><Icon name={item.icon} size={16} /></span>
              <span>{item.label}</span>
              <Icon name="chevronRight" size={15} />
            </button>
          ))}
        </nav>
      )}

      <div className="care-workspace-content">{children}</div>
    </div>
  );
}
