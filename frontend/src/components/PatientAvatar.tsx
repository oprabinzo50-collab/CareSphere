import { useEffect, useMemo, useState } from "react";
import { fetchPatientProfilePicture } from "../api/profileImages";

interface PatientAvatarProps {
  patientId: number;
  firstName?: string | null;
  lastName?: string | null;
  size?: number;
  radius?: number;
  className?: string;
  refreshKey?: number;
  label?: string;
}

function initials(firstName?: string | null, lastName?: string | null) {
  const value = `${firstName?.[0] ?? ""}${lastName?.[0] ?? ""}`.trim();
  return (value || "?").toUpperCase();
}

export default function PatientAvatar({
  patientId,
  firstName,
  lastName,
  size = 48,
  radius = 16,
  className,
  refreshKey = 0,
  label,
}: PatientAvatarProps) {
  const [src, setSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fallback = useMemo(
    () => initials(firstName, lastName),
    [firstName, lastName],
  );

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    setLoading(true);
    setSrc(null);

    fetchPatientProfilePicture(patientId)
      .then((url) => {
        if (!active) {
          if (url) URL.revokeObjectURL(url);
          return;
        }
        objectUrl = url;
        setSrc(url);
      })
      .catch(() => {
        if (active) setSrc(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [patientId, refreshKey]);

  return (
    <div
      className={["care-patient-avatar", className].filter(Boolean).join(" ")}
      aria-label={
        label || `${firstName || "Patient"} ${lastName || ""}`.trim()
      }
      style={{
        width: size,
        height: size,
        minWidth: size,
        borderRadius: radius,
        overflow: "hidden",
        display: "grid",
        placeItems: "center",
        background:
          "linear-gradient(135deg, #0f766e 0%, #0ea5a4 55%, #38bdf8 100%)",
        color: "#fff",
        fontWeight: 850,
        fontSize: Math.max(12, size * 0.34),
        letterSpacing: "-0.03em",
        boxShadow: "0 10px 26px rgba(15, 118, 110, 0.17)",
        position: "relative",
      }}
    >
      {src ? (
        <img
          src={src}
          alt=""
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: "block",
          }}
        />
      ) : (
        <span style={{ opacity: loading ? 0.72 : 1 }}>{fallback}</span>
      )}
    </div>
  );
}
