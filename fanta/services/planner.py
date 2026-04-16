from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retrieve import retrieve_context

from fanta.config import AppConfig
from fanta.knowledge import EventKnowledgeBase
from fanta.schemas import EventInput, FinalPlan, PipelineResult
from fanta.services.llm import GroqLLMClient, LLMClient
from fanta.services.predictor import ConferencePredictorService
from fanta.services.search import SearchClient, TavilySearchClient
from fanta.utils import parse_json_safely


class ConferencePlannerService:
    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient | None = None,
        search_client: SearchClient | None = None,
    ):
        self.config = config
        self.knowledge_base = EventKnowledgeBase(config.dataset_path)
        self.llm = llm_client or GroqLLMClient(config)
        self.search = search_client or TavilySearchClient(config)

    def _get_context(self, event: EventInput, retrieval_category: str, top_k: int = 8) -> str:
        query = f"{event.category} conference in {event.location} about {event.topic}"
        try:
            context = retrieve_context(query=query, category=retrieval_category, top_k=top_k)
            if context and not context.startswith("Error retrieving context") and not context.startswith("No specific data found"):
                return context
        except Exception:
            pass

        return self.knowledge_base.get_context(event.category, event.location, event.topic)

    def sponsor_agent(self, event: EventInput) -> dict[str, Any]:
        context = self._get_context(event, "sponsors")
        raw = self.llm.ask(
            system_prompt="""You are a Sponsor Agent for event planning.
Analyze past event data and recommend sponsors.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "sponsors": [
    {"name": "Company Name", "industry": "Tech", "relevance_score": 9, "reason": "why recommended"}
  ]
}""",
            user_prompt=f"""Event: {event.category} conference in {event.location}
Topic: {event.topic}

Past events data:
{context}

Return JSON with top 5 sponsors.""",
        )
        return parse_json_safely(raw, {"sponsors": [], "error": "Could not parse", "raw": raw[:1000]})

    def speaker_agent(self, event: EventInput) -> dict[str, Any]:
        context = self._get_context(event, "speakers")
        raw = self.llm.ask(
            system_prompt="""You are a Speaker Agent for event planning.
Suggest speakers based on past events and topic.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "speakers": [
    {"name": "Person Name", "expertise": "AI/ML", "suggested_topic": "talk title", "why": "reason"}
  ]
}""",
            user_prompt=f"""Event category: {event.category}
Location: {event.location}
Main topic: {event.topic}

Past events data:
{context}

Return JSON with top 5 speakers.""",
        )
        return parse_json_safely(raw, {"speakers": [], "error": "Could not parse", "raw": raw[:1000]})

    def pricing_agent(self, event: EventInput) -> dict[str, Any]:
        context = self._get_context(event, "pricing")
        raw = self.llm.ask(
            system_prompt="""You are a Pricing Agent for event planning.
Predict ticket prices based on past event data.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "pricing": {
    "early_bird": 2999,
    "general": 4999,
    "vip": 9999,
    "expected_attendance": 400,
    "reasoning": "explanation here"
  }
}""",
            user_prompt=f"""Event: {event.category} in {event.location}
Target audience: {event.audience_size} people
Topic: {event.topic}

Past events data:
{context}

Return JSON with ticket pricing in INR.""",
        )
        return parse_json_safely(raw, {"pricing": {}, "error": "Could not parse", "raw": raw[:1000]})

    def venue_agent(self, event: EventInput) -> dict[str, Any]:
        live_results = self.search.search(
            query=f"conference venue {event.location} capacity {event.audience_size} people pricing",
            max_results=3,
        )
        live_context = "\n".join(result.get("content", "")[:300] for result in live_results) or (
            f"No live data available. Use reliable knowledge about venues in {event.location}."
        )

        raw = self.llm.ask(
            system_prompt="""You are a Venue Agent for event planning.
Recommend venues based on location and requirements.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "venues": [
    {"name": "Venue Name", "city": "City", "capacity": 500, "estimated_cost": "5-8 lakhs", "why": "reason"}
  ]
}""",
            user_prompt=f"""Requirements:
- Location: {event.location}
- Audience: {event.audience_size} people
- Budget: {event.budget}
- Topic: {event.topic}

Web data:
{live_context}

Return JSON with top 3 venues.""",
        )
        return parse_json_safely(raw, {"venues": [], "error": "Could not parse", "raw": raw[:1000]})

    def gtm_agent(self, event: EventInput) -> dict[str, Any]:
        context = self._get_context(event, "gtm", top_k=6)
        raw = self.llm.ask(
            system_prompt="""You are a GTM (Go-to-Market) Agent for event planning.
Suggest communities and promotion strategies.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "gtm": {
    "discord_communities": ["community1", "community2"],
    "linkedin_groups": ["group1", "group2"],
    "promotion_message": "sample message to post",
    "best_channels": ["channel1", "channel2"]
  }
}""",
            user_prompt=f"""Event: {event.category} conference in {event.location}
Topic: {event.topic}

Context from similar events:
{context}

Where should we promote this event?
Return JSON with GTM strategy.""",
        )
        return parse_json_safely(raw, {"gtm": {}, "error": "Could not parse", "raw": raw[:1000]})

    def synthesize_final_plan(self, agent_outputs: dict[str, Any]) -> FinalPlan:
        raw_final = self.llm.ask(
            system_prompt="""You are a senior conference strategist.
Combine all agent outputs into one final plan.
You MUST reply with ONLY a JSON object. No explanation. No markdown.
Use exactly this format:
{
  "summary": "2-3 line overview",
  "top_3_sponsors": ["name1", "name2", "name3"],
  "top_3_speakers": ["name1", "name2", "name3"],
  "recommended_venue": "venue name and city",
  "ticket_pricing": {"early_bird": 0, "general": 0, "vip": 0},
  "gtm_tip": "one key promotion tip"
}""",
            user_prompt="\n".join(
                [
                    f"SPONSORS: {json.dumps(agent_outputs.get('sponsors', {}))}",
                    f"SPEAKERS: {json.dumps(agent_outputs.get('speakers', {}))}",
                    f"PRICING: {json.dumps(agent_outputs.get('pricing', {}))}",
                    f"VENUES: {json.dumps(agent_outputs.get('venues', {}))}",
                    f"GTM: {json.dumps(agent_outputs.get('gtm', {}))}",
                    "",
                    "Create final conference plan JSON.",
                ]
            ),
        )
        return FinalPlan.from_dict(parse_json_safely(raw_final, {}))

    def run(self, event: EventInput, save_outputs: bool = True) -> PipelineResult:
        agent_outputs = {
            "sponsors": self.sponsor_agent(event),
            "speakers": self.speaker_agent(event),
            "pricing": self.pricing_agent(event),
            "venues": self.venue_agent(event),
            "gtm": self.gtm_agent(event),
        }

        result = PipelineResult(
            input=event,
            agent_outputs=agent_outputs,
            final_plan=self.synthesize_final_plan(agent_outputs),
        )

        predictor = ConferencePredictorService(result)
        predictor.train_and_predict()

        if save_outputs:
            self.save_plan(result, self.config.output_plan_path)
            predictor.export_for_pinecone(self.config.pinecone_export_dir)
            predictor.save_refined_output(self.config.refined_output_path)

        return result

    @staticmethod
    def save_plan(result: PipelineResult, output_path: Path) -> None:
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(result.to_dict(), handle, indent=2, ensure_ascii=False)
