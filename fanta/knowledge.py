from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EventKnowledgeBase:
    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path
        self.events = self._load_events()

    def _load_events(self) -> list[dict[str, Any]]:
        if not self.dataset_path.exists():
            return []

        with self.dataset_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload if isinstance(payload, list) else []

    def get_context(
        self,
        category: str,
        location: str,
        topic: str | None = None,
        max_events: int = 5,
        snippet_chars: int = 700,
    ) -> str:
        category_lower = category.lower()
        location_lower = location.lower()
        topic_lower = topic.lower() if topic else ""
        scored_matches: list[tuple[int, dict[str, Any]]] = []

        for event in self.events:
            raw_content = str(event.get("raw_content", ""))
            haystack = " ".join(
                [
                    str(event.get("category", "")),
                    str(event.get("location", "")),
                    raw_content,
                    str(event.get("static_reference", "")),
                ]
            ).lower()

            score = 0
            if category_lower and category_lower in haystack:
                score += 3
            if location_lower and location_lower in haystack:
                score += 2
            if topic_lower and topic_lower in haystack:
                score += 4

            if score > 0:
                scored_matches.append((score, event))

        if not scored_matches:
            selected_events = self.events[:max_events]
        else:
            selected_events = [
                event for _, event in sorted(scored_matches, key=lambda item: item[0], reverse=True)[:max_events]
            ]

        chunks = []
        for event in selected_events:
            chunks.append(
                "\n".join(
                    [
                        f"Event: {event.get('event_name') or event.get('event_id', 'Unknown')}",
                        f"Category: {event.get('category', '')}",
                        f"Location: {event.get('location', '')}",
                        f"URL: {event.get('url', '')}",
                        f"Static Reference: {event.get('static_reference', {})}",
                        f"Content: {str(event.get('raw_content', ''))[:snippet_chars]}",
                    ]
                )
            )
        return "\n\n".join(chunks)
