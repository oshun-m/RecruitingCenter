SELECT s.office_id,
       SUM(c.status_ = 'Принят')    AS accepted,
       SUM(c.status_ = 'Не принят') AS rejected,
       COUNT(*)                     AS total
FROM Calls c
JOIN Interview i ON i.event_id = c.event_id
JOIN Employee e  ON e.emp_id = i.emp_id
JOIN Schedule_ s ON s.job_id = e.job_id
WHERE i.date_ BETWEEN %(start_date)s AND %(end_date)s
  AND (%(office_id)s IS NULL OR s.office_id = %(office_id)s)
GROUP BY s.office_id
ORDER BY s.office_id;
