-- 2) Дата последней (ЕЩЁ ОТКРЫТОЙ) вакансии с фильтрами job_id / office_id
SELECT MAX(v.date_open) AS last_opened_vacancy_date
FROM Vacancy v
JOIN Schedule_ s ON s.job_id = v.job_id
WHERE v.date_close IS NULL
  AND (%(job_id)s   IS NULL OR v.job_id   = %(job_id)s)
  AND (%(office_id)s IS NULL OR s.office_id = %(office_id)s);

