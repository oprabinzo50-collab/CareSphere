from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, dict):
        return {
            str(key): _serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    return value


@dataclass
class ClinicalContext:
    """
    Structured clinical information prepared for an AI operation.

    ORM objects are deliberately converted into plain dictionaries
    before being sent to an external AI provider.
    """

    patient_id: int
    sections: dict[str, object] = field(default_factory=dict)

    def add_section(
        self,
        name: str,
        value: object,
    ) -> None:
        self.sections[name] = _serialize_value(value)

    def to_text(self) -> str:
        lines = [
            f"Patient ID: {self.patient_id}",
        ]

        for name, value in self.sections.items():
            lines.append("")
            lines.append(f"[{name}]")
            lines.append(str(value))

        return "\n".join(lines)