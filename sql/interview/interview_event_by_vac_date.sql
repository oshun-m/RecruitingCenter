SELECT
    event_id,
    emp_id,
    date_
FROM interview
WHERE
    vac_id = %(vac_id)s
    AND date_ = %(date)s
LIMIT 1;
