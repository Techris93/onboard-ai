import tempfile
import unittest
from pathlib import Path

from dataset_pipeline import QUALITY_GATES, build_dataset_pipeline, write_dataset_pipeline_artifacts


class DatasetPipelineTests(unittest.TestCase):
    def test_pipeline_spec_includes_expected_controls(self):
        spec = build_dataset_pipeline(
            {
                "companyName": "Acme AI",
                "industry": "Software / SaaS",
                "useCase": "fine-tuning-dataset",
                "sources": ["product-dataset-pipeline", "product-elm-readiness"],
                "compliance": ["SOC 2"],
            }
        )

        self.assertEqual(spec.company_name, "Acme AI")
        self.assertIn("5B to 15B", spec.target_model_family)
        self.assertIn("DeepSeek v4 Pro", spec.generator_model)
        self.assertIn("Schema validity", spec.quality_gates)
        self.assertIn("Company-data privacy", spec.quality_gates)
        self.assertEqual(spec.quality_gates, QUALITY_GATES)

    def test_writes_markdown_and_json_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_dataset_pipeline_artifacts(
                {"companyName": "Acme AI", "useCase": "fine-tuning-dataset"},
                Path(tmp),
            )

            markdown = Path(paths["markdown"])
            payload = Path(paths["json"])
            self.assertTrue(markdown.exists())
            self.assertTrue(payload.exists())
            self.assertIn("Fine-Tuning Dataset Pipeline", markdown.read_text())
            self.assertIn("quality_gates", payload.read_text())


if __name__ == "__main__":
    unittest.main()
