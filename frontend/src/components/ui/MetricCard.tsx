import type { ReactNode } from "react";
import Icon, { type IconName } from "./Icon";

type Tone = "teal" | "blue" | "amber" | "rose";

export default function MetricCard({
  label,
  value,
  helper,
  icon,
  tone = "teal",
}: {
  label: string;
  value: string | number;
  helper?: ReactNode;
  icon: IconName;
  tone?: Tone;
}) {
  return (
    <article className={`care-metric-card care-metric-card-${tone}`}>
      <div className="care-metric-card-top">
        <span className="care-metric-icon"><Icon name={icon} size={19} /></span>
        <span className="care-metric-label">{label}</span>
      </div>
      <strong className="care-metric-value">{value}</strong>
      {helper && <div className="care-metric-helper">{helper}</div>}
    </article>
  );
}
