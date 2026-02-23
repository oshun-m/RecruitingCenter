SELECT log_id
FROM report_log
WHERE report_id = %(report_id)s
  AND created_by = %(created_by)s
ORDER BY log_id DESC
LIMIT 1;
