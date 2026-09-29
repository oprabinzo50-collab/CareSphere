import { useEffect, useMemo, useState } from "react";
import { useAuth } from "./auth/AuthContext";
import { useNavigate } from "react-router-dom";
import { getDashboardSummary, type DashboardSummary } from "./api/dashboard";
import Icon from "./components/ui/Icon";

type TaskLane = {
  title: string;
  eyebrow: string;
  description: string;
  path: string;
  icon: "activity" | "calendar" | "bell" | "file" | "users" | "shield";
  count: number | null;
  countLabel: string;
  action: string;
};

export default function TaskCenter() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch((err: any) => {
        setError(err?.response?.data?.detail || "Unable to load task-center signals.");
      })
      .finally(() => setLoading(false));
  }, []);

  const lanes = useMemo<TaskLane[]>(() => {
    const pendingReviews = summary?.clinician_reviews.pending ?? 0;
    const reports = summary?.reports ?? 0;

    if (user?.role === "administrator") {
      return [
        {
          title: "Clinical review queue",
          eyebrow: "Governance",
          description: "Open the existing clinical workspace to inspect pending clinician review activity.",
          path: "/clinical-workspace",
          icon: "activity",
          count: pendingReviews,
          countLabel: "pending reviews",
          action: "Open review queue",
        },
        {
          title: "Report oversight",
          eyebrow: "Clinical reports",
          description: "Review prepared reports, release state, and patient review information.",
          path: "/reports",
          icon: "file",
          count: reports,
          countLabel: "reports recorded",
          action: "Open reports",
        },
        {
          title: "Care coordination",
          eyebrow: "Operational",
          description: "Inspect existing follow-up work, care gaps and notification activity.",
          path: "/follow-ups",
          icon: "calendar",
          count: null,
          countLabel: "existing workflow",
          action: "Open coordination",
        },
        {
          title: "System governance",
          eyebrow: "Administration",
          description: "Move from operational tasks into user access and audit review.",
          path: "/audit-logs",
          icon: "shield",
          count: null,
          countLabel: "protected workflow",
          action: "Open audit logs",
        },
      ];
    }

    return [
      {
        title: "Clinical review queue",
        eyebrow: "Clinical",
        description: "Open the existing clinical workspace to continue patient assessment and review.",
        path: "/clinical-workspace",
        icon: "activity",
        count: pendingReviews,
        countLabel: "pending reviews",
        action: "Open clinical review",
      },
      {
        title: "Follow-up work",
        eyebrow: "Care coordination",
        description: "Continue existing follow-up workflows without leaving the current clinical context.",
        path: "/follow-ups",
        icon: "calendar",
        count: null,
        countLabel: "existing workflow",
        action: "Open follow-ups",
      },
      {
        title: "Care gap review",
        eyebrow: "Care quality",
        description: "Inspect documented care-gap activity and move into the existing workflow.",
        path: "/care-gaps",
        icon: "activity",
        count: null,
        countLabel: "existing workflow",
        action: "Open care gaps",
      },
      {
        title: "Patient notifications",
        eyebrow: "Communication",
        description: "Review the existing notification workspace for care-related communication activity.",
        path: "/notifications",
        icon: "bell",
        count: null,
        countLabel: "existing workflow",
        action: "Open notifications",
      },
    ];
  }, [summary, user?.role]);

  const completion = summary?.clinician_reviews.total
    ? Math.round((summary.clinician_reviews.approved / summary.clinician_reviews.total) * 100)
    : 0;

  return (
    <div className="care-task-center">
      <style>{`
        .care-task-center { animation: careFadeUp .42s ease both; }
        .care-task-hero {
          display: grid;
          grid-template-columns: minmax(0,1fr) auto;
          gap: 24px;
          align-items: center;
          padding: 28px;
          border-radius: 26px;
          background: linear-gradient(135deg, #0f766e 0%, #0b8e88 48%, #0f4c81 100%);
          color: #fff;
          box-shadow: 0 22px 50px rgba(8, 89, 92, .22);
          position: relative;
          overflow: hidden;
        }
        .care-task-hero:after {
          content: "";
          position: absolute;
          width: 240px;
          height: 240px;
          right: -70px;
          top: -100px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(255,255,255,.20), rgba(255,255,255,0) 70%);
          pointer-events: none;
        }
        .care-task-kicker { font-size: 11px; font-weight: 850; text-transform: uppercase; letter-spacing: .11em; opacity: .78; }
        .care-task-title { margin: 7px 0 7px; font-size: clamp(27px, 4vw, 38px); line-height: 1.04; letter-spacing: -.035em; }
        .care-task-subtitle { margin: 0; max-width: 760px; color: rgba(255,255,255,.84); line-height: 1.65; font-size: 14px; }
        .care-task-hero-metric { min-width: 156px; padding: 17px 18px; border: 1px solid rgba(255,255,255,.20); border-radius: 20px; background: rgba(255,255,255,.10); backdrop-filter: blur(10px); position: relative; z-index: 1; }
        .care-task-hero-metric span { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; opacity: .72; }
        .care-task-hero-metric strong { display: block; margin-top: 6px; font-size: 31px; line-height: 1; }
        .care-task-hero-metric small { display: block; margin-top: 7px; color: rgba(255,255,255,.76); }
        .care-task-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 17px; margin-top: 19px; }
        .care-task-card { display: flex; flex-direction: column; gap: 16px; padding: 21px; border-radius: 20px; border: 1px solid rgba(148,163,184,.18); background: rgba(255,255,255,.96); box-shadow: 0 14px 36px rgba(16,42,67,.07); transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
        .care-task-card:hover { transform: translateY(-3px); box-shadow: 0 20px 42px rgba(16,42,67,.11); border-color: rgba(15,118,110,.24); }
        .care-task-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
        .care-task-icon { width: 46px; height: 46px; display: grid; place-items: center; border-radius: 15px; background: linear-gradient(145deg, #effcfb, #e6f8ff); color: #0f766e; box-shadow: inset 0 0 0 1px rgba(15,118,110,.10); }
        .care-task-count { min-width: 92px; text-align: right; }
        .care-task-count strong { display: block; color: #102a43; font-size: 22px; line-height: 1; }
        .care-task-count span { display: block; margin-top: 4px; color: #78909c; font-size: 11px; }
        .care-task-card h2 { margin: 0; color: #102a43; font-size: 19px; letter-spacing: -.02em; }
        .care-task-card p { margin: 6px 0 0; color: #627d98; line-height: 1.58; font-size: 13px; }
        .care-task-card-action { display: inline-flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%; margin-top: auto; padding: 11px 13px; border: 1px solid #dbe4ea; border-radius: 13px; background: #fff; color: #0f766e; cursor: pointer; font-weight: 800; }
        .care-task-card-action:hover { background: #f7fffe; }
        .care-task-strip { margin-top: 19px; padding: 20px; border-radius: 20px; border: 1px solid rgba(148,163,184,.18); background: #fff; box-shadow: 0 12px 32px rgba(16,42,67,.06); }
        .care-task-strip-head { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 12px; }
        .care-task-progress { height: 10px; border-radius: 999px; background: #edf2f7; overflow: hidden; }
        .care-task-progress span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #0f766e, #38bdf8); transition: width .35s ease; }
        .care-task-error { margin-top: 14px; padding: 12px 14px; border-radius: 12px; background: #fff7f7; color: #b42318; border: 1px solid #fecaca; font-size: 13px; }
        .care-task-loading { margin-top: 19px; padding: 26px; border-radius: 18px; background: #fff; border: 1px solid rgba(148,163,184,.18); color: #627d98; }
        @media (max-width: 760px) { .care-task-hero { grid-template-columns: 1fr; padding: 22px; } .care-task-grid { grid-template-columns: 1fr; } }
        @media (prefers-reduced-motion: reduce) { .care-task-center, .care-task-card { animation: none !important; transition: none !important; } }
      `}</style>

      <section className="care-task-hero">
        <div>
          <div className="care-task-kicker">Clinical operations</div>
          <h1 className="care-task-title">Task Center</h1>
          <p className="care-task-subtitle">
            One launch point for the existing clinical queues and coordination workflows. Counts shown here come only from existing CareSphere dashboard data.
          </p>
        </div>
        <div className="care-task-hero-metric">
          <span>{user?.role === "administrator" ? "Review clearance" : "Review clearance"}</span>
          <strong>{loading ? "—" : `${completion}%`}</strong>
          <small>Based on recorded clinician reviews</small>
        </div>
      </section>

      {error && <div className="care-task-error">{error}</div>}
      {loading && <div className="care-task-loading">Loading current operational signals…</div>}

      {!loading && (
        <>
          <section className="care-task-grid" aria-label="Clinical task queues">
            {lanes.map((lane, index) => (
              <article key={lane.path} className="care-task-card" style={{ animationDelay: `${index * 55}ms` }}>
                <div className="care-task-card-top">
                  <div className="care-task-icon"><Icon name={lane.icon} size={19} /></div>
                  <div className="care-task-count">
                    <strong>{lane.count === null ? "—" : lane.count}</strong>
                    <span>{lane.countLabel}</span>
                  </div>
                </div>
                <div>
                  <div className="care-task-kicker" style={{ color: "#0f766e", opacity: 1 }}>{lane.eyebrow}</div>
                  <h2>{lane.title}</h2>
                  <p>{lane.description}</p>
                </div>
                <button type="button" className="care-task-card-action" onClick={() => navigate(lane.path)}>
                  <span>{lane.action}</span>
                  <span aria-hidden="true">›</span>
                </button>
              </article>
            ))}
          </section>

          <section className="care-task-strip">
            <div className="care-task-strip-head">
              <div>
                <strong style={{ color: "#102a43" }}>Clinical review clearance</strong>
                <div style={{ marginTop: 4, color: "#627d98", fontSize: 12 }}>Visualized from the existing dashboard review counters.</div>
              </div>
              <strong style={{ color: "#0f766e" }}>{completion}%</strong>
            </div>
            <div className="care-task-progress" aria-label={`Clinical review clearance ${completion}%`}>
              <span style={{ width: `${completion}%` }} />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
