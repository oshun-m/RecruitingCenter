SELECT i.event_id
FROM interview i
WHERE i.vac_id = %(vac_id)s
  AND i.emp_id = %(emp_id)s
  AND i.date_DATE = %(date)s
LIMIT 1;
