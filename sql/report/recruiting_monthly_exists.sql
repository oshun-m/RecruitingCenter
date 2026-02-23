SELECT COUNT(*) AS cnt
FROM recruiting_report
WHERE rep_year = %(p_year)s AND rep_month = %(p_month)s
  AND (%(p_office_id)s IS NULL OR office_id = %(p_office_id)s);
