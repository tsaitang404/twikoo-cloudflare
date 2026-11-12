-- Read-only diagnostics for Twikoo D1. Never writes or repairs data.
-- Run: wrangler d1 execute twikoo --remote --file=scripts/validate-data.sql
-- Each SELECT is independent to stay within D1's compound-query limits.
-- Non-zero anomaly counts need investigation, not automatic deletion.
SELECT 'comment_rows' AS check_name, COUNT(*) AS issue_count, '' AS examples FROM comment;

SELECT 'duplicate_comment_ids' AS check_name,
  COUNT(*) AS issue_count,
  (SELECT group_concat(sample, ', ') FROM (
    SELECT _id || ' (' || COUNT(*) || ')' AS sample
    FROM comment GROUP BY _id HAVING COUNT(*) > 1 LIMIT 10
  )) AS examples
FROM (SELECT _id FROM comment GROUP BY _id HAVING COUNT(*) > 1);

SELECT 'empty_article_url' AS check_name,
  COUNT(*) AS issue_count,
  (SELECT group_concat(_id, ', ') FROM (SELECT _id FROM comment WHERE trim(url) = '' LIMIT 10)) AS examples
FROM comment WHERE trim(url) = '';

SELECT 'reply_missing_root' AS check_name,
  COUNT(*) AS issue_count,
  (SELECT group_concat(sample, ', ') FROM (
    SELECT c._id || ' -> rid=' || c.rid AS sample FROM comment c
    WHERE c.rid <> '' AND NOT EXISTS (
      SELECT 1 FROM comment root WHERE root._id = c.rid AND root.rid = ''
    ) LIMIT 10
  )) AS examples
FROM comment c WHERE c.rid <> '' AND NOT EXISTS (
  SELECT 1 FROM comment root WHERE root._id = c.rid AND root.rid = ''
);

SELECT 'reply_missing_parent' AS check_name,
  COUNT(*) AS issue_count,
  (SELECT group_concat(sample, ', ') FROM (
    SELECT c._id || ' -> pid=' || c.pid AS sample FROM comment c
    WHERE c.pid <> '' AND NOT EXISTS (SELECT 1 FROM comment parent WHERE parent._id = c.pid)
    LIMIT 10
  )) AS examples
FROM comment c WHERE c.pid <> '' AND NOT EXISTS (
  SELECT 1 FROM comment parent WHERE parent._id = c.pid
);

SELECT 'invalid_like_json' AS check_name,
  COUNT(*) AS issue_count,
  (SELECT group_concat(_id, ', ') FROM (SELECT _id FROM comment WHERE NOT json_valid(like) LIMIT 10)) AS examples
FROM comment WHERE NOT json_valid(like);

SELECT 'config_rows' AS check_name, COUNT(*) AS issue_count, '' AS examples FROM config;
SELECT 'counter_rows' AS check_name, COUNT(*) AS issue_count, '' AS examples FROM counter;

-- Inspect the schema output for all expected columns, including ipRegion.
PRAGMA table_info(comment);
