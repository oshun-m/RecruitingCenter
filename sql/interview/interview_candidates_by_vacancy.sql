SELECT c.cand_id, c.full_name, c.age, c.gender, c.job_id
FROM candidate c
JOIN vacancy v ON v.job_id = c.job_id
WHERE v.vac_id = %(vac_id)s
ORDER BY c.full_name;
