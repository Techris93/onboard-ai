import tempfile
import unittest
from pathlib import Path
from unittest import mock

import saas_runtime


class SaasRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = saas_runtime.DB_PATH
        saas_runtime.DB_PATH = Path(self.tmp.name) / "onboardai.sqlite3"
        saas_runtime.init_db()

    def tearDown(self) -> None:
        saas_runtime.DB_PATH = self.original_db
        self.tmp.cleanup()

    def signup_user(self, email: str = "owner@example.com") -> dict:
        return saas_runtime.signup(
            {
                "email": email,
                "password": "strong-password",
                "name": "Owner",
                "organizationName": "Example Org",
            }
        )

    def test_signup_creates_workspace_dashboard(self) -> None:
        response = self.signup_user()
        dashboard = saas_runtime.get_dashboard(response["token"])

        self.assertEqual(dashboard["user"]["email"], "owner@example.com")
        self.assertEqual(len(dashboard["organizations"]), 1)
        self.assertEqual(len(dashboard["projects"]), 1)
        self.assertEqual(dashboard["billing"]["provider"], "mock")

    def test_job_worker_persists_onboarding_artifact(self) -> None:
        response = self.signup_user()
        dashboard = response["dashboard"]

        with mock.patch.object(
            saas_runtime,
            "run_onboarding",
            return_value={
                "status": "completed",
                "summary": "Run completed.",
                "artifacts": [
                    {
                        "label": "Onboarding brief",
                        "kind": "markdown",
                        "preview": "# Brief\n\nSafe artifact.",
                    }
                ],
            },
        ):
            job = saas_runtime.create_onboarding_job(
                response["token"],
                {
                    "organizationId": dashboard["activeOrganizationId"],
                    "projectId": dashboard["activeProjectId"],
                    "profile": {"companyName": "Acme", "useCase": "customer-support"},
                },
            )["job"]
            result = saas_runtime.run_next_job()

        self.assertEqual(result["count"], 1)
        job_detail = saas_runtime.get_job(response["token"], job["id"])
        self.assertEqual(job_detail["job"]["status"], "completed")
        self.assertEqual(job_detail["artifacts"][0]["label"], "Onboarding brief")

    def test_dataset_batch_generation_and_export(self) -> None:
        response = self.signup_user()
        dashboard = response["dashboard"]
        job = saas_runtime.create_dataset_batch_job(
            response["token"],
            {
                "organizationId": dashboard["activeOrganizationId"],
                "projectId": dashboard["activeProjectId"],
                "provider": "local",
                "requestedRows": 6,
                "profile": {
                    "companyName": "Acme",
                    "useCase": "fine-tuning-dataset",
                    "sources": ["product-dataset-pipeline", "resources-documentation"],
                },
            },
        )["job"]

        result = saas_runtime.run_next_job()
        self.assertEqual(result["processed"][0]["id"], job["id"])
        batch_id = result["processed"][0]["result"]["batchId"]
        export = saas_runtime.export_dataset_batch(response["token"], batch_id)

        self.assertEqual(export["format"], "jsonl")
        self.assertGreaterEqual(export["rowCount"], 1)
        self.assertIn("gold_reasoning", export["content"])

    def test_dashboard_artifact_list_does_not_fetch_full_content(self) -> None:
        response = self.signup_user()
        dashboard = response["dashboard"]
        with saas_runtime.connect() as conn:
            artifact_id = saas_runtime._create_artifact(
                conn,
                dashboard["activeOrganizationId"],
                dashboard["activeProjectId"],
                None,
                "Large report",
                "markdown",
                "full artifact body should stay behind the detail endpoint",
            )

        refreshed = saas_runtime.get_dashboard(response["token"])
        listed = next(item for item in refreshed["artifacts"] if item["id"] == artifact_id)

        self.assertIn("preview", listed)
        self.assertNotIn("content", listed)
        detail = saas_runtime.get_artifact(response["token"], artifact_id)
        self.assertIn("full artifact body", detail["content"])

    def test_scale_indexes_are_created_for_hot_paths(self) -> None:
        with saas_runtime.connect() as conn:
            indexes = {
                row["name"]
                for row in conn.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'index' AND name LIKE 'idx_%'
                    """
                )
            }

        self.assertIn("idx_jobs_org_status_created", indexes)
        self.assertIn("idx_artifacts_job_created", indexes)
        self.assertIn("idx_dataset_rows_batch_status_created", indexes)
        self.assertIn("idx_usage_events_org_type_created", indexes)

    def test_provider_key_is_masked_and_secret_not_returned(self) -> None:
        response = self.signup_user()
        dashboard = response["dashboard"]
        result = saas_runtime.save_provider_key(
            response["token"],
            {
                "organizationId": dashboard["activeOrganizationId"],
                "provider": "gemini",
                "secret": "gemini-secret-value",
            },
        )

        self.assertTrue(result["configured"])
        self.assertNotIn("gemini-secret-value", str(result))
        self.assertIn("...", result["maskedValue"])

    def test_tenant_isolation_blocks_cross_org_artifact(self) -> None:
        first = self.signup_user("first@example.com")
        second = self.signup_user("second@example.com")

        with saas_runtime.connect() as conn:
            org_id = first["dashboard"]["activeOrganizationId"]
            artifact_id = saas_runtime._create_artifact(
                conn,
                org_id,
                first["dashboard"]["activeProjectId"],
                None,
                "Private artifact",
                "markdown",
                "Private content",
            )

        with self.assertRaises(saas_runtime.SaasError) as ctx:
            saas_runtime.get_artifact(second["token"], artifact_id)

        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
