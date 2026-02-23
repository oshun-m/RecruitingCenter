INSERT INTO report_log (report_id, params_json, row_count, created_by)
VALUES (%(report_id)s, CAST(%(params_json)s AS JSON), %(row_count)s, %(created_by)s);
