import { useEffect, useMemo, useState } from "react";
import { searchPatients, type Patient } from "../../api/patients";
import Icon from "./Icon";

export default function PatientSelector({
  value,
  onChange,
  label = "Patient",
}: {
  value: Patient | null;
  onChange: (patient: Patient | null) => void;
  label?: string;
}) {
  const [search, setSearch] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const results = await searchPatients({ search: search.trim() || undefined, limit: 40, offset: 0 });
        if (!cancelled) setPatients(results);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 220);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [search]);

  const selectedLabel = useMemo(() => {
    if (!value) return "Choose a patient";
    return `${value.first_name} ${value.last_name} · ${value.patient_number}`;
  }, [value]);

  return (
    <div className="care-selector">
      <label className="care-field-label">{label}</label>
      <div className="care-selector-shell">
        <Icon name="patient" size={17} />
        <select
          value={value?.id ?? ""}
          onChange={(event) => {
            const next = patients.find((patient) => patient.id === Number(event.target.value)) ?? null;
            onChange(next);
          }}
          aria-label={label}
        >
          <option value="">{selectedLabel}</option>
          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.first_name} {patient.last_name} · {patient.patient_number}
            </option>
          ))}
        </select>
      </div>
      <div className="care-selector-search">
        <Icon name="search" size={15} />
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search patient by name or number..." />
        {loading && <span className="care-inline-loader" />}
      </div>
    </div>
  );
}
