from __future__ import annotations

from typing import Any

from fanta.config import AppConfig

try:
    from tavily import TavilyClient
except ImportError:  # pragma: no cover
    TavilyClient = None


class SearchClient:
    def search(self, query: str, max_results: int = 3) -> list[dict[str, Any]]:
        raise NotImplementedError

    def extract(self, urls: list[str]) -> list[dict[str, Any]]:
        raise NotImplementedError


class TavilySearchClient(SearchClient):
    def __init__(self, config: AppConfig):
        self.client = None
        if TavilyClient and config.tavily_api_key:
            self.client = TavilyClient(api_key=config.tavily_api_key)

    def search(self, query: str, max_results: int = 3) -> list[dict[str, Any]]:
        if not self.client:
            return []
        response = self.client.search(query=query, search_depth="advanced", max_results=max_results)
        return list(response.get("results", []))

    def extract(self, urls: list[str]) -> list[dict[str, Any]]:
        if not self.client or not urls:
            return []
        response = self.client.extract(urls=urls)
        return list(response.get("results", []))
