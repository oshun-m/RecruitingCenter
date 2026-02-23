SELECT 1
FROM vacancy
WHERE vac_id = %(vac_id)s
  AND date_close IS NULL
LIMIT 1;
