from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class EventInput:
    category: str
    location: str
    audience_size: int
    topic: str
    budget: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FinalPlan:
    summary: str = ""
    top_3_sponsors: list[str] = field(default_factory=list)
    top_3_speakers: list[str] = field(default_factory=list)
    recommended_venue: str = ""
    ticket_pricing: dict[str, Any] = field(default_factory=dict)
    gtm_tip: str = ""
    ml_insights: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FinalPlan":
        return cls(
            summary=payload.get("summary", ""),
            top_3_sponsors=list(payload.get("top_3_sponsors", [])),
            top_3_speakers=list(payload.get("top_3_speakers", [])),
            recommended_venue=payload.get("recommended_venue", ""),
            ticket_pricing=dict(payload.get("ticket_pricing", {})),
            gtm_tip=payload.get("gtm_tip", ""),
            ml_insights=dict(payload.get("ml_insights", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipelineResult:
    input: EventInput
    agent_outputs: dict[str, Any]
    final_plan: FinalPlan

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input.to_dict(),
            "agent_outputs": self.agent_outputs,
            "final_plan": self.final_plan.to_dict(),
        }
