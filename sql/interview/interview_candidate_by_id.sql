SELECT c.cand_id,
       c.full_name,
       c.age,
       c.gender,
       c.job_id
FROM candidate c
WHERE c.cand_id = %(cand_id)s
LIMIT 1;
