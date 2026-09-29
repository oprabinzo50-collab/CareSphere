import type { ReactNode } from "react";
import Icon, { type IconName } from "./Icon";

export default function PageHeader({
  eyebrow,
  title,
  description,
  icon,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  icon?: IconName;
  actions?: ReactNode;
}) {
  return (
    <div className="care-page-header">
      <div className="care-page-heading">
        {icon && <span className="care-page-icon"><Icon name={icon} size={20} /></span>}
        <div>
          {eyebrow && <div className="care-eyebrow">{eyebrow}</div>}
          <h1 className="care-page-title">{title}</h1>
          {description && <p className="care-page-description">{description}</p>}
        </div>
      </div>
      {actions && <div className="care-page-actions">{actions}</div>}
    </div>
  );
}
