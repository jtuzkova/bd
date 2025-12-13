SELECT u_id, role
FROM internal_users
WHERE
    login = (%s)
    AND passw = (%s)
;