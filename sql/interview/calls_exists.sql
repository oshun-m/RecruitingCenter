SELECT 1
FROM calls
WHERE event_id = %(event_id)s
  AND cand_id  = %(cand_id)s
LIMIT 1;
