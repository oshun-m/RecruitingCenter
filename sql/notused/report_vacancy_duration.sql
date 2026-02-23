SELECT s.office_id,
       AVG(DATEDIFF(COALESCE(v.date_close, CURRENT_DATE), v.date_open)) AS avg_days_open,
       COUNT(*) AS vacancies
FROM Vacancy v
JOIN Schedule_ s ON s.job_id = v.job_id
WHERE v.date_open BETWEEN %(start_date)s AND %(end_date)s
  AND (%(office_id)s IS NULL OR s.office_id = %(office_id)s)
GROUP BY s.office_id
ORDER BY s.office_id;
