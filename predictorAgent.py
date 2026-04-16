import json

from fanta.config import AppConfig
from fanta.schemas import EventInput, FinalPlan, PipelineResult
from fanta.services.predictor import ConferencePredictorService


class ConferencePredictorAgent(ConferencePredictorService):
    def __init__(self, orchestrated_data):
        result = PipelineResult(
            input=EventInput(**orchestrated_data["input"]),
            agent_outputs=orchestrated_data.get("agent_outputs", {}),
            final_plan=FinalPlan.from_dict(orchestrated_data.get("final_plan", {})),
        )
        super().__init__(result)
        self.raw_data = self.result.to_dict()

    def train_and_predict(self):
        prediction = super().train_and_predict()
        self.raw_data = self.result.to_dict()
        return prediction

    def export_for_pinecone(self, base_dir="pinecone_upload"):
        config = AppConfig.from_env()
        target_dir = config.pinecone_export_dir if base_dir == "pinecone_upload" else config.pinecone_export_dir.parent / base_dir
        super().export_for_pinecone(target_dir)
        super().save_refined_output(config.refined_output_path)
        self.raw_data = self.result.to_dict()


if __name__ == "__main__":
    try:
        with open("conference_plan.json", "r", encoding="utf-8") as handle:
            orchestrated_json = json.load(handle)

        predictor = ConferencePredictorAgent(orchestrated_json)
        predictor.train_and_predict()
        predictor.export_for_pinecone()
    except FileNotFoundError:
        print("Error: 'conference_plan.json' not found. Run the orchestrator first.")
