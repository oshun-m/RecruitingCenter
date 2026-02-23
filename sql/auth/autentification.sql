SELECT
  iu.in_id,
  iu.login,
  iu.role,
  r.db_config
FROM internal_user iu
JOIN role r ON r.role = iu.role
WHERE iu.login = %(login)s AND iu.pass = %(pass)s
LIMIT 1;
