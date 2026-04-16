from fanta.config import AppConfig
from fanta.services.ingestion import EventIngestionService


def run_deep_scraper(categories, locations):
    service = EventIngestionService(AppConfig.from_env())
    dataset = service.build_dataset(
        categories=categories,
        locations=locations,
        include_static_benchmarks=False,
    )
    print(f"Master dataset built with {len(dataset)} records at {service.config.dataset_path}.")
    return dataset


if __name__ == "__main__":
    cats = ["AI", "SaaS", "Web3", "Mechanical Engineering", "Fintech"]
    locs = ["India", "USA", "Europe", "Singapore"]
    run_deep_scraper(cats, locs)
