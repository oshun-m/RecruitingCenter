-- 3) Открытые (по факту открытия) вакансии по месяцам выбранного года
SELECT
  YEAR(v.date_open)  AS year,
  MONTH(v.date_open) AS month,
  COUNT(*)           AS vacancies_opened
FROM Vacancy v
JOIN Schedule_ s ON s.job_id = v.job_id
WHERE YEAR(v.date_open) = %(year)s
  AND (%(office_id)s IS NULL OR s.office_id = %(office_id)s)
  AND (%(job_id)s   IS NULL OR v.job_id   = %(job_id)s)
GROUP BY YEAR(v.date_open), MONTH(v.date_open)
ORDER BY month;
