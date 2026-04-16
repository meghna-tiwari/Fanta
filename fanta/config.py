from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_CANDIDATES = ("master_event_data.json", "master_event_data2.json")


@dataclass(slots=True)
class AppConfig:
    tavily_api_key: str | None
    groq_api_key: str | None
    groq_model: str
    dataset_path: Path
    output_plan_path: Path
    refined_output_path: Path
    pinecone_export_dir: Path
    static_library_path: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        dataset_override = os.getenv("FANTA_DATASET_PATH")
        dataset_path = Path(dataset_override) if dataset_override else cls._resolve_dataset_path()

        return cls(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            dataset_path=dataset_path,
            output_plan_path=ROOT_DIR / "conference_plan.json",
            refined_output_path=ROOT_DIR / "refined_event_data.json",
            pinecone_export_dir=ROOT_DIR / "pinecone_upload",
            static_library_path=ROOT_DIR / "static_library.json",
        )

    @staticmethod
    def _resolve_dataset_path() -> Path:
        for candidate in DATASET_CANDIDATES:
            path = ROOT_DIR / candidate
            if path.exists():
                return path
        return ROOT_DIR / DATASET_CANDIDATES[0]
