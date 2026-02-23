SELECT
  rep_id, rep_year, rep_month, office_id,
  total_hires, avg_open_days, created_at
FROM recruiting_report
WHERE rep_year = %(p_year)s AND rep_month = %(p_month)s
  AND (%(p_office_id)s IS NULL OR office_id = %(p_office_id)s)
ORDER BY office_id;
