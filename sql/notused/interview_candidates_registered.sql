SELECT c.cand_id, c.full_name, c.age, c.gender, c.job_id
FROM vacancy v
JOIN candidate c ON c.job_id = v.job_id
WHERE v.vac_id = %(vac_id)s
  AND v.date_close IS NULL
ORDER BY c.full_name;
