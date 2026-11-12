# D1 migration and data-integrity checks

## Current policy

`migrations/0001_baseline.sql` records the current production schema from `schema.sql`. It is intentionally idempotent (`CREATE ... IF NOT EXISTS`) and does not rewrite comment rows. Do not edit this baseline after it has been recorded in `d1_migrations`; add a new numbered SQL file for every subsequent schema/data change.

The baseline is not a repair migration: `CREATE TABLE IF NOT EXISTS` will not add a missing column to an already-existing table. Run the read-only diagnostics first and inspect `PRAGMA table_info(comment)`. The existing deployment has no recorded migration history in this repository, so back up and inspect production before recording/applying the baseline. Do not apply it automatically from the code-deploy workflow.

## Local checks

Generate a disposable database from the baseline, then inspect it with SQLite:

```sh
python3 scripts/generate-fixture.py /tmp/twikoo-validation.sqlite
sqlite3 /tmp/twikoo-validation.sqlite < scripts/validate-data.sql
```

To produce a separate database with deliberately injected defects for checking anomaly detection:

```sh
python3 scripts/generate-fixture.py /tmp/twikoo-validation-broken.sqlite --break-integrity
sqlite3 /tmp/twikoo-validation-broken.sqlite < scripts/validate-data.sql
```

The generator refuses to overwrite an existing output. Both files contain synthetic test records only; these commands do not connect to Cloudflare. Automated assertions:

```sh
python3 scripts/test-validation.py
```

## Read-only production audit

After reviewing the target account/database and taking a backup, use the existing Wrangler authentication:

```sh
npx wrangler d1 execute twikoo --remote --file=scripts/validate-data.sql
```

The result reports total comment rows and counts for duplicate `_id`, blank article URL, replies whose `rid` root or `pid` parent is absent, malformed `like` JSON, config rows and counters. It also prints `comment` columns. Non-zero anomaly counts are findings to inspect; do not auto-delete or auto-repair them. The SQL is read-only.

Compare the production output before and after any migration. Also sample URLs and inspect image references against R2 separately; this SQL cannot prove R2 objects exist or that article URLs still map to the intended pages.

## Migration workflow

1. Add `migrations/NNNN_description.sql`; keep it forward-only, small, and safe to retry where possible.
2. Test on local D1 and representative fixture data; run `python3 scripts/test-validation.py`.
3. Take and verify a production D1 export and an independent R2 backup before a data-changing migration.
4. Review `npx wrangler d1 migrations list twikoo --remote`, then explicitly apply with `npx wrangler d1 migrations apply twikoo --remote` during a controlled release. Do not put remote migration execution in the routine Worker deploy job until an operator-approved backup/restore and release gate exists.
5. Run the read-only production audit and application smoke checks; record commit, migration name, backup reference, before/after findings and outcome.
6. Prefer expand/migrate/contract across releases. Reverting Worker code alone is not a data rollback; determine whether post-migration writes need preservation before restoring a snapshot.
