SELECT v.vac_id, v.job_id
FROM vacancy v
WHERE v.date_close IS NULL
ORDER BY v.vac_id DESC;
