import os
from typing import Protocol

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


class SearchProvider(Protocol):

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict]:
        ...


class ExternalSearchService:

    def __init__(
        self,
        provider,
    ):

        self.provider = provider

    def search(
        self,
        query: str,
        max_results: int = 5,
    ):

        return self.provider.search(
            query=query,
            max_results=max_results,
        )


class TavilyProvider:
    """Concrete SearchProvider backed by Tavily — chosen for its
    'news'/'finance' topic modes, purpose-built for exactly this kind of
    agent lookup rather than a general web search API needing extra
    parsing. Requires TAVILY_API_KEY in .env."""

    def __init__(self, api_key: str | None = None):

        self.client = TavilyClient(
            api_key=api_key or os.getenv("TAVILY_API_KEY")
        )

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict]:

        response = self.client.search(
            query=query,
            topic="news",
            max_results=max_results,
        )

        return response.get("results", [])
