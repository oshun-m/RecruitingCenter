-- 1) Новые сотрудники за период (+ опц. office_id)
SELECT e.emp_id, e.full_name, e.enrollment, s.office_id, s.job_id
FROM Employee e
JOIN Schedule_ s ON s.job_id = e.job_id
WHERE e.enrollment BETWEEN %(start_date)s AND %(end_date)s
  AND (%(office_id)s IS NULL OR s.office_id = %(office_id)s)
ORDER BY e.enrollment;

