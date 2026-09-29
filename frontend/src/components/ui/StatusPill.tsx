import type { ReactNode } from "react";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

export default function StatusPill({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`care-status-pill care-status-${tone}`}>{children}</span>;
}
