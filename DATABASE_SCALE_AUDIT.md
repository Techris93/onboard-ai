# OnboardAI Database Scale Audit

This audit checks OnboardAI against five production database risks that often stay invisible in development: N+1 queries, unbounded pagination, missing indexes, unsafe connection lifecycle, and over-fetching.

Current database path:

- Runtime: SQLite through `saas_runtime.py`.
- Local default: `state/onboardai.sqlite3`.
- Production recommendation: Render persistent disk for pilot; Postgres migration before high-concurrency SaaS.

## Summary

| Risk area | Findings | Severity | Fix applied | Remaining work |
| --- | --- | --- | --- | --- |
| N+1 queries | Dashboard uses grouped queries for projects, jobs, artifacts, batches, members, providers, billing, and monitoring. Worker row inserts are per generated row but bounded by requested batch size. | Low | No N+1 hot-path loop was found in dashboard list loading. | Keep provider generation batch sizes bounded; use bulk inserts if rows grow beyond pilot scale. |
| No pagination | Dashboard list endpoints already use small limits. Dataset export intentionally returns all accepted rows for a batch. | Medium | Confirmed dashboard limits and kept export as an explicit export endpoint rather than a list endpoint. | Add streaming or cursor-based export before very large dataset batches. |
| Missing indexes | Initial schema had only a few indexes and missed several common organization/status/date filters. | High | Added composite indexes for sessions, memberships, projects, jobs, artifacts, pipelines, batches, rows, quality gates, usage events, audit logs, and API keys. | Add migration tooling when moving from SQLite bootstrap to Postgres migrations. |
| Connection lifecycle | Connections were closed with a custom context manager, but SQLite had no busy timeout or WAL mode. | Medium | Added SQLite timeout, `busy_timeout`, WAL journal mode, and normal sync mode. | Move high-concurrency production traffic to Postgres; SQLite remains a pilot path. |
| Over-fetching / `SELECT *` | Dashboard artifact lists selected full artifact content; job lists selected payload JSON even when only summary fields were needed. | High | Replaced hot dashboard/detail list queries with explicit columns that omit artifact content and job payloads. Full artifact body remains available only through the artifact detail endpoint. | Continue avoiding `SELECT *` in new list endpoints; add query-shape tests for new dashboard panels. |

## Hot Paths Reviewed

- `get_dashboard`
- `get_job`
- `get_artifact`
- `export_dataset_batch`
- `run_next_job`
- `deployment_health`
- auth/session lookup
- provider key storage
- audit and usage summaries

## Fixes Applied

Indexes added in `saas_runtime.py`:

- `idx_sessions_user_expires`
- `idx_memberships_user_status`
- `idx_memberships_org_status`
- `idx_projects_org_created`
- `idx_jobs_status_created`
- `idx_jobs_org_status_created`
- `idx_jobs_org_created`
- `idx_artifacts_org_created`
- `idx_artifacts_job_created`
- `idx_dataset_pipelines_org_created`
- `idx_dataset_pipelines_project_created`
- `idx_dataset_batches_org_created`
- `idx_dataset_batches_pipeline_created`
- `idx_dataset_rows_org_status`
- `idx_dataset_rows_batch_status_created`
- `idx_quality_gate_results_row`
- `idx_usage_events_org_type_created`
- `idx_audit_logs_org_created`
- `idx_api_keys_org_created`

Query-shape fixes:

- Dashboard jobs select only public job summary fields.
- Dashboard artifacts select only metadata and preview fields.
- Job detail artifacts select metadata only.
- Dataset export selects only fields needed for JSONL export.
- Dataset batch authorization lookup selects only batch ID and organization ID.

Connection lifecycle fixes:

- SQLite connections use a 15-second timeout.
- `PRAGMA busy_timeout = 15000`.
- `PRAGMA journal_mode = WAL`.
- `PRAGMA synchronous = NORMAL`.
- The existing `ClosingConnection` context manager still closes connections after each request/job operation.

## Intentional Exceptions

Dataset export can return all accepted rows in one batch. That is acceptable for current pilot-sized batches because it is an explicit export action, not a dashboard list. Before large production fine-tuning batches, add one of these:

- streaming JSONL response,
- cursor export endpoint,
- background export artifact job,
- object-storage export file.

## Production Recommendations

- Keep dashboard list limits small.
- Keep local/offline dataset batches modest until export streaming exists.
- Use Render persistent disk only for pilot SQLite deployments.
- Move to Postgres before multiple API/worker instances or sustained concurrent usage.
- Add migration tooling before Postgres.
- Add query logging around dashboard and worker routes before load testing.
- Load-test signup, dashboard, onboarding job, dataset batch generation, worker processing, artifact detail, and dataset export.

## Verification

Tests added:

- Dashboard artifact list does not return full artifact content.
- Scale indexes are created for hot paths.

Run:

```bash
python3 -m unittest tests/test_saas_runtime.py tests/test_research_runtime.py tests/test_dataset_pipeline.py
```

