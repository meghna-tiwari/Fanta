from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fanta.config import AppConfig
from fanta.services.search import SearchClient, TavilySearchClient


class EventIngestionService:
    def __init__(self, config: AppConfig, search_client: SearchClient | None = None):
        self.config = config
        self.search = search_client or TavilySearchClient(config)

    def load_static_benchmarks(self) -> list[dict[str, Any]]:
        path = self.config.static_library_path
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload if isinstance(payload, list) else []

    def build_dataset(
        self,
        categories: list[str],
        locations: list[str],
        output_path: Path | None = None,
        include_static_benchmarks: bool = False,
        max_results: int = 10,
        sleep_seconds: float = 1.0,
    ) -> list[dict[str, Any]]:
        dataset: list[dict[str, Any]] = []
        static_benchmarks = self.load_static_benchmarks() if include_static_benchmarks else []

        for category in categories:
            for location in locations:
                query = (
                    f"Full list of {category} conferences {location} 2025 2026 speakers sponsors pricing"
                    if include_static_benchmarks
                    else f"List of {category} conferences and tech events in {location} 2025 2026"
                )

                search_results = self.search.search(query=query, max_results=max_results)
                urls = [result.get("url") for result in search_results if result.get("url")]
                extracted_results = self.search.extract(urls[:5] if include_static_benchmarks else urls)

                for index, extracted in enumerate(extracted_results):
                    static_reference = {}
                    if static_benchmarks:
                        static_reference = next(
                            (
                                benchmark.get("benchmarks", {})
                                for benchmark in static_benchmarks
                                if category.lower() in str(benchmark.get("category", "")).lower()
                            ),
                            {},
                        )

                    dataset.append(
                        {
                            "event_id": f"{category}_{location}_{index}",
                            "category": category,
                            "location": location,
                            "url": extracted.get("url", ""),
                            "raw_content": extracted.get("raw_content", ""),
                            "static_reference": static_reference,
                            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                time.sleep(sleep_seconds)

        target_path = output_path or self.config.dataset_path
        with target_path.open("w", encoding="utf-8") as handle:
            json.dump(dataset, handle, indent=4, ensure_ascii=False)

        if include_static_benchmarks and target_path.name != "master_event_data2.json":
            legacy_hybrid_path = target_path.parent / "master_event_data2.json"
            with legacy_hybrid_path.open("w", encoding="utf-8") as handle:
                json.dump(dataset, handle, indent=4, ensure_ascii=False)

        return dataset
