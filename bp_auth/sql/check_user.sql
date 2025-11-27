SELECT u_id, role
FROM users
WHERE
    login = (%s)
    AND passw = (%s)
;