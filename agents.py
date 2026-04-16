import json

from fanta.config import AppConfig
from fanta.schemas import EventInput
from fanta.services.planner import ConferencePlannerService


def orchestrator(category, location, audience_size, topic, budget):
    service = ConferencePlannerService(AppConfig.from_env())
    event = EventInput(
        category=category,
        location=location,
        audience_size=audience_size,
        topic=topic,
        budget=budget,
    )
    result = service.run(event, save_outputs=True)
    payload = result.to_dict()
    print(json.dumps(payload["final_plan"], indent=2, ensure_ascii=False))
    return payload


if __name__ == "__main__":
    orchestrator(
        category="AI",
        location="India",
        audience_size=500,
        topic="Large Language Models",
        budget="50 lakhs",
    )
