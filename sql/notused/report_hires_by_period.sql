SELECT s.office_id,
       COUNT(*) AS hires
FROM Employee e
JOIN Schedule_ s ON s.job_id = e.job_id
WHERE e.enrollment BETWEEN %(start_date)s AND %(end_date)s
  AND (%(office_id)s IS NULL OR s.office_id = %(office_id)s)
GROUP BY s.office_id
ORDER BY s.office_id;
