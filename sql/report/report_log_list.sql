SELECT
  log_id, report_id, title, created_by, created_at
FROM report_log
ORDER BY created_at DESC, log_id DESC
LIMIT 200;
