SELECT
  log_id, report_id, title, params_json, created_by, created_at
FROM report_log
WHERE log_id = %(log_id)s;
