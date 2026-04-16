from __future__ import annotations

import argparse
import json

from fanta.config import AppConfig
from fanta.schemas import EventInput
from fanta.services.planner import ConferencePlannerService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the integrated Fanta conference planning pipeline.")
    parser.add_argument("--category", default="AI")
    parser.add_argument("--location", default="India")
    parser.add_argument("--audience-size", type=int, default=500)
    parser.add_argument("--topic", default="Large Language Models")
    parser.add_argument("--budget", default="50 lakhs")
    parser.add_argument("--no-save", action="store_true", help="Run the pipeline without writing output files.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    event = EventInput(
        category=args.category,
        location=args.location,
        audience_size=args.audience_size,
        topic=args.topic,
        budget=args.budget,
    )

    service = ConferencePlannerService(AppConfig.from_env())
    result = service.run(event, save_outputs=not args.no_save)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
