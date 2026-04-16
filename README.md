# Fanta Backend Integration

This repo now runs as an integrated backend-style pipeline for conference planning.

## Main entrypoints

- `python main.py` runs the full planning pipeline.
- `python static_scraping.py` builds the base event dataset.
- `python static_scraping2.py` builds the hybrid dataset and writes it to the planner's active dataset path.
- `python agents.py` preserves the old orchestrator entrypoint for compatibility.
- `python predictorAgent.py` preserves the old predictor entrypoint for compatibility.
- `frontend/index.html` is the lightweight UI for presenting the pipeline and the latest generated plan.

## Environment

Copy values from `.env.example` into your environment before running the live pipeline:

- `TAVILY_API_KEY`
- `GROQ_API_KEY`
- `GROQ_MODEL` (optional)
- `FANTA_DATASET_PATH` (optional)

## Outputs

- `conference_plan.json`
- `refined_event_data.json`
- `pinecone_upload/<namespace>/<namespace>_refined.json`

## Frontend

Serve the repo root locally so the frontend can read `conference_plan.json`:

- `python -m http.server 8000`
- open `http://localhost:8000/frontend/`

The frontend is static and currently visualizes the latest backend output rather than submitting jobs directly to Python.

## Internal structure

- `fanta/config.py`: shared paths and runtime config
- `fanta/schemas.py`: shared data contracts
- `fanta/knowledge.py`: dataset loading and retrieval
- `fanta/services/planner.py`: orchestrator and agent coordination
- `fanta/services/predictor.py`: attendance prediction and Pinecone export shaping
- `fanta/services/ingestion.py`: scraper/integration pipeline
